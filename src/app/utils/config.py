import json
import os


def get(env_var):
    '''
    Парсит значение переменной среды `env_var` как JSON;
    строки, не обернутые в кавычки, и прочий невалидный JSON возвращает как есть
    '''

    raw_value = os.getenv(env_var)
    if not raw_value:
        return raw_value
    try:
        return json.loads(raw_value)
    except json.decoder.JSONDecodeError:
        return raw_value
