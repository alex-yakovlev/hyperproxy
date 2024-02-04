import functools

import aiohttp.web


def with_template_response(template):
    '''

    Args:
    '''

    def wrapper(handler):
        '''

        Args:
            handler(function): декорируемый обработчик, метод class-based view
        '''

        @functools.wraps(handler)
        async def wrapped(self):
            context = await handler(self)
            response = template.render(context)
            return aiohttp.web.Response(text=response, content_type='text/xml')

        return wrapped

    return wrapper
