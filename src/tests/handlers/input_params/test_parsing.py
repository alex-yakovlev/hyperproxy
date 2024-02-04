import pytest

from app.handlers.input_params.parsing.parsing import parse_params

import yarl
import multidict


class TestParseParams:
    @pytest.mark.parametrize('query_string, parsed_params_expected', [
        # пример из ТЗ
        (
            'function=check&Amount=300000&PaymExtId=7b9bb88e5b&PaymSubjTp=6301&TermType=003-10&TermId=7621&Params= 1 TR790006701000000051001858;904 79601231212;903 1234123456;920 ИВАНОВ;921 ИВАН;922 ИВАНОВИЧ;907 1969-04-11;804 79601231212;801 Alexandra Mankovskaya;807 1983-10-30',  # noqa: E501
            multidict.MultiDict([
                ('Amount', '300000'),
                ('PaymExtId', '7b9bb88e5b'),
                ('PaymSubjTp', '6301'),
                ('TermType', '003-10'),
                ('TermId', '7621'),
                ('1', 'TR790006701000000051001858'),
                ('904', '79601231212'),
                ('903', '1234123456'),
                ('920', 'ИВАНОВ'),
                ('921', 'ИВАН'),
                ('922', 'ИВАНОВИЧ'),
                ('907', '1969-04-11'),
                ('804', '79601231212'),
                ('801', 'Alexandra Mankovskaya'),
                ('807', '1983-10-30'),
            ])
        ),

        # еще пример из ТЗ
        (
            'function=payment&id=9d06b30c-8fc2-11ee-b9d1-0242ac120002&Amount=300000&PaymExtId=7b9bb88e5b&PaymSubjTp=6301&TermType=003-10&TermId=7621&Params= 1 TR790006701000000051001858;904 79601231212;903 1234123456;920 ИВАНОВ;921 ИВАН;922 ИВАНОВИЧ;907 1969-04-11;804 79601231212;801 Alexandra Mankovskaya;807 1983-10-30',  # noqa: E501
            multidict.MultiDict([
                ('id', '9d06b30c-8fc2-11ee-b9d1-0242ac120002'),
                ('Amount', '300000'),
                ('PaymExtId', '7b9bb88e5b'),
                ('PaymSubjTp', '6301'),
                ('TermType', '003-10'),
                ('TermId', '7621'),
                ('1', 'TR790006701000000051001858'),
                ('904', '79601231212'),
                ('903', '1234123456'),
                ('920', 'ИВАНОВ'),
                ('921', 'ИВАН'),
                ('922', 'ИВАНОВИЧ'),
                ('907', '1969-04-11'),
                ('804', '79601231212'),
                ('801', 'Alexandra Mankovskaya'),
                ('807', '1983-10-30'),
            ])
        ),

        # ключ `params` может быть с маленькой буквы
        (
            'function=foo&Amount=45000&PaymExtId=7b9bb88e5b&PaymSubjTp=6301&TermType=003-10&TermId=7621&params= 1 TR790006701000000051001858;904 79601231212;903 1234123456;920 ИВАНОВ;921 ИВАН;922 ИВАНОВИЧ;907 1969-04-11;804 79601231212;801 Alexandra Mankovskaya;807 1983-10-30',  # noqa: E501
            multidict.MultiDict([
                ('Amount', '45000'),
                ('PaymExtId', '7b9bb88e5b'),
                ('PaymSubjTp', '6301'),
                ('TermType', '003-10'),
                ('TermId', '7621'),
                ('1', 'TR790006701000000051001858'),
                ('904', '79601231212'),
                ('903', '1234123456'),
                ('920', 'ИВАНОВ'),
                ('921', 'ИВАН'),
                ('922', 'ИВАНОВИЧ'),
                ('907', '1969-04-11'),
                ('804', '79601231212'),
                ('801', 'Alexandra Mankovskaya'),
                ('807', '1983-10-30'),
            ])
        ),

        # семантика параметров не учитывается
        (
            'params=9999 foo;bar baz&foo=bar&baz=quux',
            multidict.MultiDict([
                ('foo', 'bar'),
                ('baz', 'quux'),
                ('9999', 'foo'),
                ('bar', 'baz'),
            ])
        ),

        # лишние разделители в составных параметрах
        (
            'foo=bar&baz=quux&params=; 9999 foo;;bar baz  ;',
            multidict.MultiDict([
                ('foo', 'bar'),
                ('baz', 'quux'),
                ('9999', 'foo'),
                ('bar', 'baz'),
            ])
        ),

        # не переданы именованные параметры
        (
            'params=9999 foo;bar baz',
            multidict.MultiDict([
                ('9999', 'foo'),
                ('bar', 'baz'),
            ])
        ),

        # не переданы составные параметры (нет ключа `params`)
        (
            'foo=bar&baz=quux',
            multidict.MultiDict([
                ('foo', 'bar'),
                ('baz', 'quux'),
            ])
        ),

        # не переданы составные параметры (ключ `params` с пустым значением)
        (
            'foo=bar&baz=quux&params= ',
            multidict.MultiDict([
                ('foo', 'bar'),
                ('baz', 'quux'),
            ])
        ),

        # параметры с пустым значением
        (
            'params=9999;bar ;&foo=&baz',
            multidict.MultiDict([
                ('foo', ''),
                ('baz', ''),
                ('9999', ''),
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
