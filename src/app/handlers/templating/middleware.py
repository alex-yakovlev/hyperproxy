import functools

import aiohttp.web

from .rendering import render_response


def with_template_response(template_key, **response_kwargs):
    '''
    Декоратор, который на основе данных от обработчика рендерит шаблон и возвращает ответ
    с этим содержимым.
    Для использования обработчики должны возвращать словарь-контекст шаблона.

    Args:
        template_key (object): ключ, соответствующий нужному шаблону в объекте приложения
        (см. инициализацию приложения)

    Keyword Args:
        см. аргументы конструктора `aiohttp.web.Response`, кроме `text` и `body`
        https://docs.aiohttp.org/en/stable/web_reference.html#aiohttp.web.Response

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
            Returns:
                aiohttp.web.Response
            '''

            context = await handler(self)
            if isinstance(context, aiohttp.web.StreamResponse):
                return context

            return await render_response(
                self.request.app['templates'][template_key], context, **response_kwargs
            )

        return wrapped

    return wrapper
