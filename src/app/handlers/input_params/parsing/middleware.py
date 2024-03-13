import functools

from .parsing import parse_params


def with_parsed_params():
    '''
    Декоратор, который парсит входные параметры и сохраняет их в объекте `request`
    для дальнейшего использования

    Returns:
        function: декоратор
    '''

    # `wrapper` для единообразия с остальными декораторами, здесь можно было бы обойтись без него
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
                *: результат вызова исходного обработчика
            '''

            params = parse_params(self.request.query)
            self.request['method_params_raw'] = params

            return await handler(self)

        return wrapped

    return wrapper
