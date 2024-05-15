from decimal import Decimal

import iso_4217


def quantize(amount, code):
    '''
    Округляет денежную сумму с точностью до мельчайшей разменной единицы для её валюты;
    для округления используется banker's rounding (`ROUND_HALF_EVEN`)

    Args:
        amount (Decimal): сумма
        code (str): код валюты по ISO 4217

    Returns:
        Decimal
    '''

    places = iso_4217.Currency[code].subunit_exp or 0
    quantizer = Decimal(10) ** -places
    return amount.quantize(quantizer)
