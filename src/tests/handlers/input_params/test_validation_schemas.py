import unittest.mock as mock
import pytest

from datetime import date
from decimal import Decimal
from multidict import MultiDict
import cerberus.errors

from app.handlers.input_params.validation.validator import Validator
from app.handlers.input_params.validation.schemas import CHECK_PARAMS_SCHEMA, PAYMENT_PARAMS_SCHEMA


DELETE_DICT_KEY = mock.sentinel.delete_dict_key


def _merge_dicts(d1, d2):
    updated = d1.copy()
    updated.update(d2)
    for key, value in d2.items():
        if value == DELETE_DICT_KEY:
            del updated[key]
    return updated


COMMON_SUCCESS_CASES = [
    # пример из ТЗ
    (
        lambda default_params: _merge_dicts(default_params, {}),
        lambda default_normalized: _merge_dicts(default_normalized, {}),
    ),

    # 901 вместо набора 920, 921, 922
    (
        lambda default_params: _merge_dicts(default_params, {
            '901': 'ИВАНОВ ИВАН ИВАНОВИЧ',
            '920': DELETE_DICT_KEY,
            '921': DELETE_DICT_KEY,
            '922': DELETE_DICT_KEY,
        }),
        lambda default_normalized: _merge_dicts(default_normalized, {
            '901': 'ИВАНОВ ИВАН ИВАНОВИЧ',
            '920': DELETE_DICT_KEY,
            '921': DELETE_DICT_KEY,
            '922': DELETE_DICT_KEY,
        }),
    ),

    # IBAN проверяется только по регулярке
    (
        lambda default_params: _merge_dicts(default_params, {
            '1': 'TR790000000000000000000000',
        }),
        lambda default_normalized: _merge_dicts(default_normalized, {
            '1': 'TR790000000000000000000000',
        }),
    ),

    # номер карты тоже
    (
        lambda default_params: _merge_dicts(default_params, {
            '1': '1111111111111111',
        }),
        lambda default_normalized: _merge_dicts(default_normalized, {
            '1': '1111111111111111',
        }),
    ),
]

COMMON_FAILURE_CASES = [
    # названия параметров чувствительны к регистру
    (
        lambda default_params: _merge_dicts(default_params, {'amount': '5000'}),
        MultiDict({
            'amount': 'UNKNOWN_FIELD',
        })
    ),

    # запятая вместо точки как десятичный разделитель
    (
        lambda default_params: _merge_dicts(default_params, {'Amount': '5000,50'}),
        MultiDict({
            'Amount': 'COERCION_FAILED',
        })
    ),

    # IBAN с группами, разделенными пробелами
    (
        lambda default_params: _merge_dicts(default_params, {
            '1': 'TR79 0006 7010 0000 0051 0018 58',
        }),
        MultiDict([
            ('1', 'REGEX_MISMATCH'),
            ('1', 'ANYOF'),
        ])
    ),

    # номер карты с группами, разделенными пробелами
    (
        lambda default_params: _merge_dicts(default_params, {
            '1': '3714 4963 5398 431',
        }),
        MultiDict([
            ('1', 'REGEX_MISMATCH'),
            ('1', 'ANYOF'),
        ])
    ),

    # отличный от ISO 8601 формат даты
    (
        lambda default_params: _merge_dicts(default_params, {
            '807': '11.04.1969',
        }),
        MultiDict({
            '807': 'COERCION_FAILED',
        })
    ),

    # номер телефона с символом "+"
    (
        lambda default_params: _merge_dicts(default_params, {
            '904': '+79601231212',
        }),
        MultiDict({
            '904': 'REGEX_MISMATCH',
        })
    ),

    # поле присутствует, но значение пустое
    (
        lambda default_params: _merge_dicts(default_params, {
            '910': '',
        }),
        MultiDict({
            '910': 'EMPTY_NOT_ALLOWED',
        })
    ),

    # взаимоисключающие параметры
    (
        lambda default_params: _merge_dicts(default_params, {
            '901': 'Петров Петр Петрович',
        }),
        MultiDict({
            '901': 'EXCLUDES_FIELD',
            '920': 'EXCLUDES_FIELD',
            '921': 'EXCLUDES_FIELD',
            '922': 'EXCLUDES_FIELD',
        })
    ),
]


class BaseTestSchema:
    def setup_each(self, schema):
        self.validator = Validator(schema)
        self.default_params = MultiDict([
            ('Amount', '300000'),
            ('PaymExtId', '7b9bb88e5b'),
            ('PaymSubjTp', '6301'),
            ('TermType', '003-10'),
            ('TermId', '7621'),
            ('1', 'TR790006701000000051001858'),
            ('904', '79601231212'),
            ('903', '1234123456'),
            ('910', 'г. Чита'),
            ('920', 'ИВАНОВ'),
            ('921', 'ИВАН'),
            ('922', 'ИВАНОВИЧ'),
            ('907', '1969-04-11'),
            ('804', '79601231212'),
            ('801', 'Alexandra Mankovskaya'),
            ('807', '1983-10-30'),
        ])
        self.default_normalized_params = {
            'Amount': Decimal(300000),
            'PaymExtId': '7b9bb88e5b',
            'PaymSubjTp': '6301',
            'TermType': '003-10',
            'TermId': '7621',
            '1': 'TR790006701000000051001858',
            '904': '79601231212',
            '903': '1234123456',
            '910': 'г. Чита',
            '920': 'ИВАНОВ',
            '921': 'ИВАН',
            '922': 'ИВАНОВИЧ',
            '907': date(1969, 4, 11),
            '804': '79601231212',
            '801': 'Alexandra Mankovskaya',
            '807': date(1983, 10, 30),
        }

    def _test_success(self, params_maker, normalized_params_maker):
        params = params_maker(self.default_params)
        normalized_params_expected = normalized_params_maker(self.default_normalized_params)
        params_normalized = self.validator.validated(params)

        assert not self.validator.errors
        assert params_normalized == normalized_params_expected

    def _test_failure(self, params_maker, errors_expected):
        params = params_maker(self.default_params)
        self.validator.validate(params)

        # проверяем, что нет неучтенных в `errors_expected` ошибок
        for field in params:
            assert (
                len(self.validator.errors.get(field, [])) == len(errors_expected.getall(field, []))
            )
        # проверяем, что есть все ошибки из `errors_expected`
        for field, error in errors_expected.items():
            assert getattr(cerberus.errors, error) in \
                (self.validator.document_error_tree.get(field) or [])


class TestCheckSchema(BaseTestSchema):
    @pytest.fixture(autouse=True)
    def setup_each(self):
        super().setup_each(CHECK_PARAMS_SCHEMA)

    @pytest.mark.parametrize('params_maker, normalized_params_maker', [
        *COMMON_SUCCESS_CASES,
    ])
    def test_success(self, params_maker, normalized_params_maker):
        super()._test_success(params_maker, normalized_params_maker)

    @pytest.mark.parametrize('params_maker, errors_expected', [
        *COMMON_FAILURE_CASES,

        # отсутствуют обязательные поля
        (
            lambda _: MultiDict(),
            MultiDict({
                'Amount': 'REQUIRED_FIELD',
                'PaymExtId': 'REQUIRED_FIELD',
                'PaymSubjTp': 'REQUIRED_FIELD',
                'TermType': 'REQUIRED_FIELD',
                'TermId': 'REQUIRED_FIELD',
                '1': 'REQUIRED_FIELD',
                '901': 'REQUIRED_FIELD',
                '903': 'REQUIRED_FIELD',
                '904': 'REQUIRED_FIELD',
                '907': 'REQUIRED_FIELD',
                '910': 'REQUIRED_FIELD',
                '920': 'REQUIRED_FIELD',
                '921': 'REQUIRED_FIELD',
                '922': 'REQUIRED_FIELD',
            })
        ),

        # не хватает обязательных параметров из группы
        (
            lambda default_params: _merge_dicts(default_params, {
                '921': DELETE_DICT_KEY,
                '922': DELETE_DICT_KEY,
            }),
            MultiDict([
                ('920', 'DEPENDENCIES_FIELD'),  # 921
                ('920', 'DEPENDENCIES_FIELD'),  # 922
                ('921', 'REQUIRED_FIELD'),
                ('922', 'REQUIRED_FIELD'),
            ])
        ),
    ])
    def test_failure(self, params_maker, errors_expected):
        super()._test_failure(params_maker, errors_expected)


class TestPaymentSchema(BaseTestSchema):
    @pytest.fixture(autouse=True)
    def setup_each(self):
        super().setup_each(PAYMENT_PARAMS_SCHEMA)
        op_id = '9d06b30c-8fc2-11ee-b9d1-0242ac120002'
        self.default_params['id'] = op_id
        self.default_normalized_params['id'] = op_id
        self.default_params['2'] = '1.25'
        self.default_normalized_params['2'] = Decimal('1.25')

    @pytest.mark.parametrize('params_maker, normalized_params_maker', [
        *COMMON_SUCCESS_CASES,
    ])
    def test_success(self, params_maker, normalized_params_maker):
        super()._test_success(params_maker, normalized_params_maker)

    @pytest.mark.parametrize('params_maker, errors_expected', [
        *COMMON_FAILURE_CASES,

        # отсутствуют обязательные поля
        (
            lambda _: MultiDict(),
            MultiDict({
                'id': 'REQUIRED_FIELD',
                '1': 'REQUIRED_FIELD',
                '801': 'REQUIRED_FIELD',
                '804': 'REQUIRED_FIELD',
                '807': 'REQUIRED_FIELD',
                '907': 'REQUIRED_FIELD',
            })
        ),

        # не хватает необязательных параметров из группы
        (
            lambda default_params: _merge_dicts(default_params, {
                '921': DELETE_DICT_KEY,
                '922': DELETE_DICT_KEY,
            }),
            MultiDict([
                ('920', 'DEPENDENCIES_FIELD'),  # 921
                ('920', 'DEPENDENCIES_FIELD'),  # 922
            ])
        ),
    ])
    def test_failure(self, params_maker, errors_expected):
        super()._test_failure(params_maker, errors_expected)
