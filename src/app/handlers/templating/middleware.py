import functools

import aiohttp.web

from app import exceptions
from .rendering import render_response


def with_public_response(
    template_key, error_template_key, error_response_handler, response_kwargs=None
):
    '''
    Декоратор, который на основе данных от обработчика рендерит шаблон и возвращает ответ
    с этим содержимым. В случае возникновения исключения при вызове обработчика рендерит
    специальный шаблон.
    Для использования обработчики должны возвращать словарь-контекст шаблона или
    бросать какой-либо подвид базового исключения `exceptions.AppException`.

    Args:
        template_key (str): ключ, соответствующий шаблону успешного ответа в объекте приложения
        (см. инициализацию приложения)
        error_template_key (str): ключ, соответствующий шаблону ответа с ошибкой
        error_response_handler (function): функция, возвращающая контекст для шаблона и
            параметры ответа (имеют приоритет над `response_kwargs`) в зависимости от вида ошибки
        response_kwargs (obj): см. аргументы конструктора `aiohttp.web.Response`,
            кроме `text` и `body`
            https://docs.aiohttp.org/en/stable/web_reference.html#aiohttp.web.Response

    Returns:
        function: декоратор
    '''

    response_kwargs = response_kwargs or {}

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
            Returns:
                aiohttp.web.Response
            '''

            template_registry = self.request.app['templates']

            try:
                context = await handler(self)
                if isinstance(context, aiohttp.web.StreamResponse):
                    return context

                template = template_registry[template_key]
                return await render_response(template, context, **response_kwargs)
            except exceptions.AppException as error:
                error_template = template_registry[error_template_key]
                context, error_resp_kwargs = error_response_handler(error)
                return await render_response(
                    error_template, context, **{**response_kwargs, **error_resp_kwargs}
                )
            except Exception:
                # TODO не пропускать непредвиденные исключения пользователям
                raise

        return wrapped

    return wrapper
