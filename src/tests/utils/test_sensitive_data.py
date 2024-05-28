import pytest
from app.utils.sensitive_data import redact_sensitive_data


class TestRedact:
    @pytest.mark.parametrize('data, redacted', [
        (
            {'foo': 'plaintext value', 'non-foo': 'redacted value'},
            {'foo': 'plaintext value', 'non-foo': '******** *****'}
        ),
        (
            {'non-foo': 'кириллица'},
            {'non-foo': '*********'}
        ),
        (
            {'bar': 123, 'non-bar': 456},
            {'bar': 123, 'non-bar': 'REDACTED'}
        ),
        (
            {'non-foo': ['non-string value']},
            {'non-foo': 'REDACTED'}
        ),
        ({}, {}),
    ])
    def test_redacted_data(self, data, redacted):
        assert redact_sensitive_data({'foo', 'bar'}, data) == redacted

    def test_none_allowed(self):
        assert redact_sensitive_data([], {'foo': 'redacted value', 'bar': 123}) ==\
            {'foo': '******** *****', 'bar': 'REDACTED'}
