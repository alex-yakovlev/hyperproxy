import functools

from app.handlers.templating import render_response
from .validator import Validator
from .error_handling import InputParamsErrorHandler


def with_validated_params(schema):
    '''
    Декоратор, валидирущий входные параметры. В случае успешной валидации сохраняет
    нормализованные параметры в объекте `request` и передает управление исходному обработчику,
    иначе возвращает ответ, содержащий описание ошибок валидации.
    Зависит от декоратора `with_parsed_params`.

    Args:
        schema (dict): схема в формате Cerberus

    Returns:
        function: декоратор
    '''

    validator = Validator(schema, error_handler=InputParamsErrorHandler)

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
                или сразу ответ (`aiohttp.web.Response`) в случае неуспешной валидации
            '''

            params = self.request.pop('method_params_raw', {})
            params_normalized = validator.validated(params)
            if not validator.is_document_valid:
                return await render_response(
                    self.request.app['templates']['response'],
                    {'success': False, 'error_code': 1, 'validation_errors': validator.errors}
                )

            self.request['method_params'] = params_normalized

            return await handler(self)

        return wrapped

    return wrapper
