import itertools
import functools
import multidict

from app import constants


CODED_PARAMS_SEPARATOR = ';'
CODED_PARAM_KV_SEPARATOR = ' '


def _parse_coded_param(params, pair_raw):
    '''
    Функция-предикат для `functools.reduce`

    Args:
        params (multidict.MultiDict): словарь-аккумулятор
        pair_raw (str): строка, содержащая одну пару код-значение, разделенные пробелом

    Returns:
        multidict.MultiDict: словарь-аккумулятор с добавленной парой код-значение
    '''

    code, value, *_ = itertools.chain(
        pair_raw.strip().split(CODED_PARAM_KV_SEPARATOR, maxsplit=1),
        # дефолтные значения для распаковки на случай,
        # если у параметра нет значения или входная строка вообще пустая
        ['', '']
    )
    if code:
        params.add(code, value)
    return params


def _parse_coded_params(params_raw_list):
    '''
    Парсит составные параметры запроса

    Args:
        params_raw_list (list(str)): список строк, каждая из которых либо содержит
        набор составных параметров, либо пустая

    Returns:
        multidict.MultiDict: словарь пар код-значение из всех входных строк
    '''

    return functools.reduce(
        _parse_coded_param,
        CODED_PARAMS_SEPARATOR.join(params_raw_list).split(CODED_PARAMS_SEPARATOR),
        multidict.MultiDict()
    )


def parse_params(query_dict):
    '''
    Парсит URL параметры запроса

    Args:
        query_dict (multidict.MultiDictProxy): `request.query`
        (где `request` — инстанс `aiohttp.web.Request`)

    Returns:
        multidict.MultiDict
    '''

    # к именованным относятся все параметры, кроме `ACTION`
    params = query_dict.copy()
    params.pop(constants.ROUTING_QUERY_PARAM, None)

    return params
