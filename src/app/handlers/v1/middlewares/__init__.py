import functools

import sqlalchemy

from app import exceptions
from app.database import models
from app.handlers import input_params, templating
from ..input_params.parsing import parse_params
from .error_handling import get_error_response_data


TEMPLATE_KEY = 'v1_response'


with_parsed_params = functools.partial(input_params.with_parsed_params, parse_params)

with_validated_params = functools.partial(input_params.with_validated_params)

with_public_response = functools.partial(
    templating.with_public_response,
    TEMPLATE_KEY, TEMPLATE_KEY, get_error_response_data
)


def with_initial_db_data():
    '''
    Декоратор, загружающий из базы связку инициатор-прокси-платежная система,
    соответствующую запросу (поиск соответствия ведется по заголовку `X-Forwarded-Host`,
    содержащему домен прокси)

    Returns:
        function: декоратор
    '''

    def wrapper(handler):
        '''
        Args:
            handler (function): декорируемый обработчик, метод class-based view

        Returns:
            function: декорированный обработчик
        '''

        @functools.wraps(handler)
        async def wrapped(self):
            '''
            Записывает в объект `request` объекты `models.Partnership` и `models.PaymentSystem`

            Raises:
                exceptions.MissingDomainHeader: если не передан заголовок `X-Forwarded-Host`
                exceptions.PartnershipNotFound: если связка не найдена
                exceptions.PartnershipInactive: если связка отключена
            '''

            proxy_domain = self.request.headers.get('X-Forwarded-Host')
            if not proxy_domain:
                raise exceptions.MissingDomainHeader()

            Session = self.request.app['db_sessionmaker']
            # опция `expire_on_commit=False` используется, чтобы ссылки-relationship
            # были доступны вне блока `with`, в вызываемом ниже обработчике
            # см. https://docs.sqlalchemy.org/en/20/orm/session_api.html#sqlalchemy.orm.Session.params.expire_on_commit  # noqa: E501
            # (здесь это скорее предосторожность,т.к. запросы только на чтение и
            # ни явной, ни неявной транзакции нет, а сбрасываются ссылки только после commit-а)
            async with Session(expire_on_commit=False) as session:
                partnership = (await session.scalars(
                    sqlalchemy
                    .select(models.Partnership)
                    .where(models.Partnership.domain == proxy_domain)
                    .options(sqlalchemy.orm.joinedload(models.Partnership.payment_system))
                    )
                ).first()

            if not partnership:
                raise exceptions.PartnershipNotFound(proxy_domain)

            if not partnership.is_active:
                raise exceptions.PartnershipInactive(partnership.domain)

            self.request['partnership'] = partnership
            self.request['payment_system'] = partnership.payment_system

            return await handler(self)

        return wrapped

    return wrapper
