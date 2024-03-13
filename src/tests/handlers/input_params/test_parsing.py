import pytest

from app.handlers.input_params.parsing.parsing import parse_params

import yarl
import multidict


class TestParseParams:
    @pytest.mark.parametrize('query_string, parsed_params_expected', [
        # пример из ТЗ
        (
            'ACTION=payment&ACCOUNT=TR000000000000000000001234&SERVICECODE=123&PAY_ID=2001967202&PAY_DATE=22.05.2023_13:49:41&CURR_RATE=0.2101&AMOUNT=3000.00&CURRENCY=RUB&SETTLEMENT_CURR=RUB&SENDER_FIO=IVANOV IVAN IVANOVICH&SENDER_BIRTHDAY=31.12.1970&ID_SERIES_NUMBER=1234123456&SENDER_PHONE=79001231234&SENDER_ADDRESS=MOSKVA&RECEIVER_PHONE=79003214321&RECEIVER_FIO=PETROV PETR PETROVICH&RECEIVER_BIRTHDAY=16.03.1989&OPER_ID=X236RRTG',  # noqa: E501
            multidict.MultiDict([
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
        ),

        # семантика параметров не учитывается
        (
            'foo=bar&baz=quux',
            multidict.MultiDict([
                ('foo', 'bar'),
                ('baz', 'quux'),
            ])
        ),

        # параметры с пустым значением
        (
            'foo=&bar',
            multidict.MultiDict([
                ('foo', ''),
                ('bar', ''),
            ])
        ),

        # не переданы никакие параметры
        (
            '',
            multidict.MultiDict()
        ),
    ])
    def test_parse(self, query_string, parsed_params_expected):
        url = yarl.URL.build(query=query_string)
        parsed_params = parse_params(url.query)
        assert parsed_params == parsed_params_expected
