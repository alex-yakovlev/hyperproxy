import functools

from app import exceptions
from .validator import Validator
from .error_handling import InputParamsErrorHandler


def with_validated_params(schema):
    '''
    Декоратор, валидирущий входные параметры. В случае успешной валидации сохраняет
    нормализованные параметры в объекте `request` и передает управление исходному обработчику,
    иначе бросает исключение, содержащее описание ошибок валидации.
    Зависит от декоратора `with_parsed_params`.
    Полагается на то, что декоратор `with_public_response` ловит возможные исключения.

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

            Raises:
                exceptions.InputValidationError: в случае неуспешной валидации
            '''

            mdw_shared = self.request['mdw_shared'] = self.request.get('mdw_shared', {})
            params = mdw_shared.get('method_params_raw', {})
            params_normalized = validator.validated(params)
            if not validator.is_document_valid:
                raise exceptions.InputValidationError(validator.errors)

            mdw_shared.pop('method_params_raw', None)
            mdw_shared['method_params'] = params_normalized

            return await handler(self)

        return wrapped

    return wrapper
