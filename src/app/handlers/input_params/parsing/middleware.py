import functools


def with_parsed_params(params_parser):
    '''
    Декоратор, который парсит входные параметры и сохраняет их в объекте `request`
    для дальнейшего использования

    Args:
        params_parser (function): функция, которая парсит параметры

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
                *: результат вызова исходного обработчика
            '''

            params = params_parser(self.request.query)
            self.request['method_params_raw'] = params

            return await handler(self)

        return wrapped

    return wrapper
