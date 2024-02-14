import cerberus.errors

from .custom_rules import MultiValueErrors


DEFAULT_ERROR_MESSAGE = 'неверное значение (код: {code})'

MULTI_VALUE_MESSAGES = {
    MultiValueErrors.SEQUENCE_OF_MANY: 'передано несколько значений',
    MultiValueErrors.NOT_A_SEQUENCE: 'ошибка обработки параметра (код: 0x01)',
    MultiValueErrors.EMPTY_SEQUENCE: 'ошибка обработки параметра (код: 0x02)',
}


def _coercion_failed_msg(field, error):
    '''
    Текст сообщения об ошибке преобразования типов зависит от того,
    "обычное" это преобразование или приведение списка значений параметра к единственному значению
    (т.к. технически это сделано с помошью правила `coerce`)

    Args:
        field (str): название поля документа
        error (cerberus.errors.ValidationError): ошибка его валидации

    Returns:
        str: сообщение об ошибке
    '''

    error_info = error.info[0]
    # if error_info in MultiValueErrors:  # TODO начиная с Python 3.12
    if error_info in list(MultiValueErrors):
        return MULTI_VALUE_MESSAGES[error_info]

    return 'неверный формат значения'


class InputParamsErrorHandler(cerberus.errors.BasicErrorHandler):
    '''
    Класс для использования с `.validator.Validator` при валидации входных параметров API.
    Переопределяет дефолтные сообщения об ошибках на те, которые должны возвращаться в ответах API.
    '''

    # см. https://docs.python-cerberus.org/api.html#error-codes
    messages = {
        0x00: '{0}',
        0x02: 'обязательный параметр',
        0x03: 'неизвестный параметр',
        0x04: 'требуются параметры {0}',
        0x06: 'параметр исключает параметры {0}',
        0x22: 'значение отсутствует',
        0x23: 'значение отсутствует',
        0x24: 'неверный тип данных',
        0x26: 'количество элементов должна быть {0}',
        0x27: 'длина должна быть не меньше {constraint}',
        0x28: 'длина должна быть не больше {constraint}',
        0x41: 'строка неверного формата',
        0x42: 'значение должно быть не меньше {constraint}',
        0x43: 'значение должно быть не больше {constraint}',
        0x44: 'недопустимое значение',
        0x45: 'недопустимые значения {0}',
        0x46: 'недопустимое значение',
        0x47: 'недопустимые значения {0}',
        0x48: 'обязательны элементы {0}',
        0x61: _coercion_failed_msg,
    }

    def _format_message(self, field, error):
        '''
        Args:
            field (str): название поля документа
            error (cerberus.errors.ValidationError): ошибка его валидации

        Returns:
            str: сообщение об ошибке
        '''

        message = self.messages.get(error.code)
        if not message:
            return DEFAULT_ERROR_MESSAGE.format(code=error.code)

        if callable(message):
            return message(field, error)

        return super()._format_message(field, error)
