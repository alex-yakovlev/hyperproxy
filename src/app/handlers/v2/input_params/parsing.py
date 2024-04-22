from app import constants


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
    params.pop(constants.V2_ROUTING_QUERY_PARAM, None)

    return params
