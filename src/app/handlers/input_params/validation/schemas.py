from datetime import datetime, date
from decimal import Decimal

from .custom_rules import validate_currency


def strptime_curried(dt_fmt):
    return lambda dt_str: datetime.strptime(dt_str, dt_fmt)


def strptime_date_curried(date_fmt):
    strptime = strptime_curried(date_fmt)
    return lambda date_str: strptime(date_str).date()


NON_EMPTY_STRING_RULESET = {
    'type': 'string',
    # "честная" непустая строка (пробелы в начале/конце вырезаются на этапе парсинга)
    'empty': False,
}

DECIMAL_NUMBER_RULESET = {
    'coerce': Decimal,
}

INTL_PHONE_NUMBER_RULESET = {
    **NON_EMPTY_STRING_RULESET,
    'regex': r'\d{10,11}',
}

ISO_DATE_RULESET = {
    'coerce': date.fromisoformat,
}

CUSTOM_DATE_RULESET = {
    'coerce': strptime_date_curried('%d.%m.%Y'),
}

CUSTOM_DATETIME_RULESET = {
    'coerce': strptime_curried('%d.%m.%Y_%H:%M:%S'),
}

CURRENCY_RULESET = {
    'check_with': validate_currency,
}


NMT_CHECK_PARAMS_SCHEMA = {
    'ACCOUNT': {
        **NON_EMPTY_STRING_RULESET,
        'anyof': [
            # IBAN
            {'regex': r'^[A-Z]{2}\d{2}[\dA-Z]{1,30}$'},
            # номер карты
            {'regex': r'^\d{8,19}$'},
        ],
        'required': True,
    },
    'AMOUNT': {
        **DECIMAL_NUMBER_RULESET,
        'required': True,
    },
    'SERVICECODE': {
        **NON_EMPTY_STRING_RULESET,
        'required': True,
    },
    'CURRENCY': {
        **CURRENCY_RULESET,
        'required': True,
    },
    'SETTLEMENT_CURR': {
        **CURRENCY_RULESET,
        'required': True,
    },
    'OPER_ID': {
        **NON_EMPTY_STRING_RULESET,
        'required': True,
    },
}

CLIENT_CHECK_PARAMS_SCHEMA = {
    **NMT_CHECK_PARAMS_SCHEMA,

    'SENDER_FIO': {
        **NON_EMPTY_STRING_RULESET,
        'required': True,
    },
    'SENDER_BIRTHDAY': {
        **CUSTOM_DATE_RULESET,
        'required': True,
    },
    'SENDER_BIRTHDAY_ORIGINAL': {
        **ISO_DATE_RULESET,
    },
    'ID_SERIES_NUMBER': {
        **NON_EMPTY_STRING_RULESET,
        'regex': r'^\d+$',
        'required': True,
    },
    'SENDER_PHONE': {
        **INTL_PHONE_NUMBER_RULESET,
        'required': True,
    },
    'SENDER_ADDRESS': {
        **NON_EMPTY_STRING_RULESET,
    },
}

PAYMENT_PARAMS_SCHEMA = {
    **CLIENT_CHECK_PARAMS_SCHEMA,

    'CURR_RATE': {
        **DECIMAL_NUMBER_RULESET,
        'required': True,
    },
    'PAY_DATE': {
        **CUSTOM_DATETIME_RULESET,
        'required': True,
    },
    'PAY_ID': {
        **NON_EMPTY_STRING_RULESET,
        'required': True,
    },
    'RECEIVER_BIRTHDAY': {
        **CUSTOM_DATE_RULESET,
    },
    'RECEIVER_FIO': {
        **NON_EMPTY_STRING_RULESET,
        'required': True,
    },
    'RECEIVER_PHONE': {
        **INTL_PHONE_NUMBER_RULESET,
        'required': True,
    },
}
