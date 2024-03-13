from enum import StrEnum, auto

import iso_4217

from app.utils.type_conversions import is_nonstring_sequence


class MultiValueErrors(StrEnum):
    '''
    Enum для проверки типов ошибок нормализации с помощью `multi_to_single`
    '''

    NOT_A_SEQUENCE = auto()
    EMPTY_SEQUENCE = auto()
    SEQUENCE_OF_MANY = auto()


def multi_to_single(obj, fail_if_multiple=True):
    '''
    Функция для использования в схеме валидации в правиле `coerce`.
    Преобразует список значений поля к единственному (первому) значению.

    Args:
        obj (list|*): список, из которого нужно первое значение
        fail_if_multiple (bool): кидать ли ошибку, если в списке больше одного элемента

    Raises:
        TypeError: если `obj` не список (точнее, не реализует интерфейс `Sequence`)
        ValueError: если список пуст
        ValueError: если в списке больше одного элемента и передан соответствующий флаг

    Returns:
        *: первый элемент списка
    '''

    # не должно происходить при нормальном использовании
    if not is_nonstring_sequence(obj):
        raise TypeError(MultiValueErrors.NOT_A_SEQUENCE)

    # не должно происходить при нормальном использовании
    if len(obj) == 0:
        raise ValueError(MultiValueErrors.EMPTY_SEQUENCE)

    if fail_if_multiple and len(obj) > 1:
        raise ValueError(MultiValueErrors.SEQUENCE_OF_MANY)

    return obj[0]


def validate_currency(field, value, error):
    '''
    Функция для использования в схеме валидации в правиле `check_with`.
    Проверяет, входит ли валюта в перечень ISO 4217.

    Args:
        field (str): название поля
        value (*): значение поля (код валюты)
        error (function): функция, вызов которой передает ошибку валидатору
    '''

    # if value not in iso_4217.Currency:  # TODO начиная с Python 3.12
    try:
        cur = iso_4217.Currency[value]
    except KeyError:
        error(field, 'несуществующая валюта')

    if len(cur.entities) == 0:
        error(field, 'неиспользуемая валюта')
