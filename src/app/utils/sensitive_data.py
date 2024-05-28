import re


REDACTED = 'REDACTED'

ALPHANUMERIC = re.compile(r'\w')


def _redact_value(value):
    return re.sub(ALPHANUMERIC, '*', value) if isinstance(value, str) else REDACTED


def redact_sensitive_data(allow_list, data):
    '''
    Cкрывает значения в объекте с данными, кроме разрешенных

    Args:
        allow_list (collections.abc.Collection): список разрешенных ключей
        data (collections.abc.Mapping): объект, содержащий значения, которые нужно скрыть

    Returns:
        dict
    '''

    return {
        key: value if key in allow_list else _redact_value(value)
        for key, value in data.items()
    }
