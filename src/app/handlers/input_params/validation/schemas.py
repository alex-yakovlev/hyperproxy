from datetime import date
from decimal import Decimal

from .utils import merge_schemas


NON_EMPTY_STRING_RULESET = {
    'type': 'string',
    # "честная" непустая строка (пробелы в начале/конце вырезаются на этапе парсинга)
    'empty': False,
}

INTL_PHONE_NUMBER_RULESET = {
    **NON_EMPTY_STRING_RULESET,
    'regex': r'\d{10,11}',
}

ISO_DATE_RULESET = {
    'coerce': date.fromisoformat,
}

DECIMAL_NUMBER_RULESET = {
    'coerce': Decimal,
}


COMMON_PARAMS_SCHEMA = {
    'Amount': {
        **DECIMAL_NUMBER_RULESET,
        'required': True,
    },
    'PaymExtId': {
        **NON_EMPTY_STRING_RULESET,
        'regex': r'^[\da-fA-F]+$',
        'required': True,
    },
    'PaymSubjTp': {
        **NON_EMPTY_STRING_RULESET,
        'regex': r'^\d{4}$',
        'required': True,
    },
    'TermType': {
        **NON_EMPTY_STRING_RULESET,
        'required': True,
    },
    'TermId': {
        **NON_EMPTY_STRING_RULESET,
        'regex': r'^\d{4}$',
        'required': True,
    },

    '1': {
        **NON_EMPTY_STRING_RULESET,
        'anyof': [
            # IBAN
            {'regex': r'^[A-Z]{2}\d{2}[\dA-Z]{1,30}$'},
            # номер карты
            {'regex': r'^\d{8,19}$'},
        ],
    },
    '801': {
        **NON_EMPTY_STRING_RULESET,
    },
    '804': {
        **INTL_PHONE_NUMBER_RULESET,
    },
    '807': {
        **ISO_DATE_RULESET,
    },
    '901': {
        **NON_EMPTY_STRING_RULESET,
        'excludes': ['920', '921', '922'],
    },
    '903': {
        **NON_EMPTY_STRING_RULESET,
        'regex': r'^\d+$',
    },
    '904': {
        **INTL_PHONE_NUMBER_RULESET,
    },
    '907': {
        **ISO_DATE_RULESET,
    },
    '910': {
        **NON_EMPTY_STRING_RULESET,
    },
    '920': {
        **NON_EMPTY_STRING_RULESET,
        'dependencies': ['921', '922'],
        'excludes': ['901'],
    },
    '921': {
        **NON_EMPTY_STRING_RULESET,
        'dependencies': ['920', '922'],
        'excludes': ['901'],
    },
    '922': {
        **NON_EMPTY_STRING_RULESET,
        'dependencies': ['920', '921'],
        'excludes': ['901'],
    },
}

CHECK_PARAMS_SCHEMA = merge_schemas(
    COMMON_PARAMS_SCHEMA,

    {
        '1': {
            'required': True,
        },
        '901': {
            'required': True,
        },
        '903': {
            'required': True,
        },
        '904': {
            'required': True,
        },
        '907': {
            'required': True,
        },
        '910': {
            'required': True,
        },
        '920': {
            'required': True,
        },
        '921': {
            'required': True,
        },
        '922': {
            'required': True,
        },
    }
)

PAYMENT_PARAMS_SCHEMA = merge_schemas(
    COMMON_PARAMS_SCHEMA,

    {
        'id': {
            **NON_EMPTY_STRING_RULESET,
            'regex': r'^[\da-fA-F]{8}-[\da-fA-F]{4}-[\da-fA-F]{4}-[\da-fA-F]{4}-[\da-fA-F]{12}$',
            'required': True,
        },

        '1': {
            'required': True,
        },
        '2': {
            **DECIMAL_NUMBER_RULESET,
        },
        '801': {
            'required': True,
        },
        '804': {
            'required': True,
        },
        '807': {
            'required': True,
        },
        '907': {
            'required': True,
        },
    }
)
