import functools

import aiohttp.web

from .renderer import render_response


def with_template_response(template, **response_kwargs):
    '''
    Декоратор, который на основе данных от обработчика рендерит шаблон и возвращает ответ
    с этим содержимым.
    Для использования обработчики должны возвращать словарь-контекст шаблона.

    Args:
        template (object): объект с асинхронным методом `render`, возвращающим строку

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

            return await render_response(template, context, **response_kwargs)

        return wrapped

    return wrapper
