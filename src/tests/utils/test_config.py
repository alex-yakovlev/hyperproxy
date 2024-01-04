import pytest
from app.utils import config

import os


class TestGet:
    @staticmethod
    def cleanup():
        os.environ.pop('TEST_ENV_VAR', None)

    @pytest.fixture(scope='class', autouse=True)
    def setup_all(self):
        self.cleanup()

    @pytest.fixture(autouse=True)
    def setup_each(self):
        yield
        self.cleanup()

    @pytest.mark.parametrize('raw, retrieved', [
        ('"json_string"', 'json_string'),
        ('non_json_string', 'non_json_string'),
        ('', ''),
        ('10', 10),
        (' 10 ', 10),
        ('false', False),
        ('null', None),
        (' "foo" ', 'foo'),
        ('{"foo": "bar"}', {'foo': 'bar'}),
        ('["foo", "bar"]', ['foo', 'bar']),
        ('foo, bar', 'foo, bar'),
    ])
    def test_env_retrieval(self, raw, retrieved):
        os.environ['TEST_ENV_VAR'] = raw
        assert config.get('TEST_ENV_VAR') == retrieved

    def test_missing_env_retrieval(self):
        assert config.get('TEST_ENV_VAR') is None
