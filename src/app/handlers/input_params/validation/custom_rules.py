from enum import StrEnum, auto

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
    Возвращает первое значение из списка.
    Используется для преобразования списка значений параметра к единственному значению.

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
