import unittest.mock as mock
import pytest

from datetime import datetime, date
from decimal import Decimal
from multidict import MultiDict
import cerberus.errors
# import iso_4217

from app.handlers.input_params.validation.validator import Validator
from app.handlers.input_params.validation.schemas import PAYMENT_PARAMS_SCHEMA


DELETE_DICT_KEY = mock.sentinel.delete_dict_key


def _merge_dicts(d1, d2):
    updated = d1.copy()
    updated.update(d2)
    for key, value in d2.items():
        if value == DELETE_DICT_KEY:
            del updated[key]
    return updated


# PAYMENT_PARAMS_SCHEMA включает в себя CLIENT_CHECK_PARAMS_SCHEMA,
# а CLIENT_CHECK_PARAMS_SCHEMA включает в себя NMT_CHECK_PARAMS_SCHEMA,
# поэтому достаточно проверить PAYMENT_PARAMS_SCHEMA
class TestPaymentSchema:
    @pytest.fixture(autouse=True)
    def setup_each(self):
        self.validator = Validator(PAYMENT_PARAMS_SCHEMA)
        self.default_params = MultiDict([
            ('ACCOUNT', 'TR000000000000000000001234'),
            ('SERVICECODE', '123'),
            ('PAY_ID', '2001967202'),
            ('PAY_DATE', '22.05.2023_13:49:41'),
            ('CURR_RATE', '0.2101'),
            ('AMOUNT', '3000.00'),
            ('CURRENCY', 'RUB'),
            ('SETTLEMENT_CURR', 'RUB'),
            ('SENDER_FIO', 'IVANOV IVAN IVANOVICH'),
            ('SENDER_BIRTHDAY', '31.12.1970'),
            ('ID_SERIES_NUMBER', '1234123456'),
            ('SENDER_PHONE', '79001231234'),
            ('SENDER_ADDRESS', 'MOSKVA'),
            ('RECEIVER_PHONE', '79003214321'),
            ('RECEIVER_FIO', 'PETROV PETR PETROVICH'),
            ('RECEIVER_BIRTHDAY', '16.03.1989'),
            ('OPER_ID', 'X236RRTG'),
        ])
        self.default_normalized_params = {
            'ACCOUNT': 'TR000000000000000000001234',
            'SERVICECODE': '123',
            'PAY_ID': '2001967202',
            'PAY_DATE': datetime(2023, 5, 22, 13, 49, 41),
            'CURR_RATE': Decimal('0.2101'),
            'AMOUNT': Decimal('3000.00'),
            'CURRENCY': 'RUB',
            'SETTLEMENT_CURR': 'RUB',
            'SENDER_FIO': 'IVANOV IVAN IVANOVICH',
            'SENDER_BIRTHDAY': date(1970, 12, 31),
            'ID_SERIES_NUMBER': '1234123456',
            'SENDER_PHONE': '79001231234',
            'SENDER_ADDRESS': 'MOSKVA',
            'RECEIVER_PHONE': '79003214321',
            'RECEIVER_FIO': 'PETROV PETR PETROVICH',
            'RECEIVER_BIRTHDAY': date(1989, 3, 16),
            'OPER_ID': 'X236RRTG',
        }

    @pytest.mark.parametrize('params_maker, normalized_params_maker', [
        # пример из ТЗ
        (
            lambda default_params: _merge_dicts(default_params, {}),
            lambda default_normalized: _merge_dicts(default_normalized, {}),
        ),

        # IBAN проверяется только по регулярке
        (
            lambda default_params: _merge_dicts(default_params, {
                'ACCOUNT': 'TR790000000000000000000000',
            }),
            lambda default_normalized: _merge_dicts(default_normalized, {
                'ACCOUNT': 'TR790000000000000000000000',
            }),
        ),

        # номер карты тоже
        (
            lambda default_params: _merge_dicts(default_params, {
                'ACCOUNT': '1111111111111111',
            }),
            lambda default_normalized: _merge_dicts(default_normalized, {
                'ACCOUNT': '1111111111111111',
            }),
        ),
    ])
    def test_success(self, params_maker, normalized_params_maker):
        params = params_maker(self.default_params)
        normalized_params_expected = normalized_params_maker(self.default_normalized_params)
        params_normalized = self.validator.validated(params)

        assert not self.validator.errors
        assert params_normalized == normalized_params_expected

    @pytest.mark.parametrize('params_maker, errors_expected', [
        # отсутствуют обязательные поля
        (
            lambda _: MultiDict(),
            MultiDict({
                'ACCOUNT': 'REQUIRED_FIELD',
                'AMOUNT': 'REQUIRED_FIELD',
                'SERVICECODE': 'REQUIRED_FIELD',
                'CURRENCY': 'REQUIRED_FIELD',
                'SETTLEMENT_CURR': 'REQUIRED_FIELD',
                'CURR_RATE': 'REQUIRED_FIELD',
                'SENDER_FIO': 'REQUIRED_FIELD',
                'SENDER_PHONE': 'REQUIRED_FIELD',
                'SENDER_BIRTHDAY': 'REQUIRED_FIELD',
                'ID_SERIES_NUMBER': 'REQUIRED_FIELD',
                'RECEIVER_FIO': 'REQUIRED_FIELD',
                'RECEIVER_PHONE': 'REQUIRED_FIELD',
                'PAY_DATE': 'REQUIRED_FIELD',
                'OPER_ID': 'REQUIRED_FIELD',
                'PAY_ID': 'REQUIRED_FIELD',
            })
        ),

        # названия параметров чувствительны к регистру
        (
            lambda default_params: _merge_dicts(default_params, {'amount': '5000'}),
            MultiDict({
                'amount': 'UNKNOWN_FIELD',
            })
        ),

        # невалидная валюта
        (
            lambda default_params: _merge_dicts(default_params, {'CURRENCY': 'RUR'}),
            MultiDict({
                'CURRENCY': 'CUSTOM',
            })
        ),

        # запятая вместо точки как десятичный разделитель
        (
            lambda default_params: _merge_dicts(default_params, {'AMOUNT': '5000,50'}),
            MultiDict({
                'AMOUNT': 'COERCION_FAILED',
            })
        ),

        # IBAN с группами, разделенными пробелами
        (
            lambda default_params: _merge_dicts(default_params, {
                'ACCOUNT': 'TR79 0006 7010 0000 0051 0018 58',
            }),
            MultiDict([
                ('ACCOUNT', 'REGEX_MISMATCH'),
                ('ACCOUNT', 'ANYOF'),
            ])
        ),

        # номер карты с группами, разделенными пробелами
        (
            lambda default_params: _merge_dicts(default_params, {
                'ACCOUNT': '3714 4963 5398 431',
            }),
            MultiDict([
                ('ACCOUNT', 'REGEX_MISMATCH'),
                ('ACCOUNT', 'ANYOF'),
            ])
        ),

        # неверный формат даты
        (
            lambda default_params: _merge_dicts(default_params, {
                'SENDER_BIRTHDAY_ORIGINAL': '11.04.1969',
            }),
            MultiDict({
                'SENDER_BIRTHDAY_ORIGINAL': 'COERCION_FAILED',
            })
        ),

        # неверный формат даты
        (
            lambda default_params: _merge_dicts(default_params, {
                'PAY_DATE': '2024-03-05T13:03:26',
            }),
            MultiDict({
                'PAY_DATE': 'COERCION_FAILED',
            })
        ),

        # номер телефона с символом "+"
        (
            lambda default_params: _merge_dicts(default_params, {
                'SENDER_PHONE': '+79001231234',
            }),
            MultiDict({
                'SENDER_PHONE': 'REGEX_MISMATCH',
            })
        ),

        # поле присутствует, но значение пустое
        (
            lambda default_params: _merge_dicts(default_params, {
                'SENDER_ADDRESS': '',
            }),
            MultiDict({
                'SENDER_ADDRESS': 'EMPTY_NOT_ALLOWED',
            })
        ),
    ])
    def test_failure(self, params_maker, errors_expected):
        params = params_maker(self.default_params)
        self.validator.validate(params)

        # проверяем, что есть все ошибки из `errors_expected`
        for param, error in errors_expected.items():
            assert getattr(cerberus.errors, error) in \
                (self.validator.document_error_tree.get(param) or [])

        # проверяем, что нет неучтенных в `errors_expected` ошибок
        param_names = set(params).union(self.default_params)
        assert (
            {param: len(self.validator.errors.get(param, [])) for param in param_names}
            == {param: len(errors_expected.getall(param, [])) for param in param_names}
        )
