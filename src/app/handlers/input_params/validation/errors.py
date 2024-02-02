from enum import StrEnum, auto


class errors(StrEnum):
    '''
    Enum для проверки типов ошибок нормализации/валидации при использовании `.validator.Validator`
    '''

    NOT_A_SEQUENCE = auto()
    EMPTY_SEQUENCE = auto()
    SEQUENCE_OF_MANY = auto()
