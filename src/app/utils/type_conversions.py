from collections.abc import Iterable, Sequence


def is_string(obj):
    return isinstance(obj, (str, bytes))


def is_nonstring_iterable(obj):
    return isinstance(obj, Iterable) and not is_string(obj)


def is_nonstring_sequence(obj):
    return isinstance(obj, Sequence) and not is_string(obj)


def wrap_in_list(obj, wrap_none=False):
    if obj is None and not wrap_none:
        return []
    return list(obj) if is_nonstring_iterable(obj) else [obj]
