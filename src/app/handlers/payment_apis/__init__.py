import asyncio

from app.utils import config
from . import default


class PaymentService:
    '''
    Посредник для работы с API платежных систем в обработчиках запросов.
    Синглтон, инициализирующийся одновременно с приложением
    и затем доступный каждому обработчику через объект `request['app']`.
    '''

    def __init__(self):
        self._providers = {
            'default': default.PaymentProvider(
                basic_user=config.get('PAYMENT_API_DEFAULT_USER'),
                basic_pwd=config.get('PAYMENT_API_DEFAULT_PWD'),
                cert_path=config.get('PAYMENT_API_DEFAULT_CERT_PATH'),
                cert_pwd=config.get('PAYMENT_API_DEFAULT_CERT_PWD')
            ),
        }

    async def get_payment_API(self, payment_system):
        '''
        Вызывается обработчиком;
        выбирает модуль для работы с API нужной платежной системы

        Args:
            payment_system (app.database.models.PaymentSystem)

        Returns:
            app.handlers.payment_apis.base.PaymentAPI
        '''

        provider = self._providers[payment_system.name]
        await provider.start(payment_system.api_origin)

        return provider.get_API()

    async def cleanup(self):
        await asyncio.gather(*[
            provider.cleanup() for provider in self._providers.values()
        ])
        self._providers = {}
