import multidict
import cerberus.errors

from app.handlers.input_params.validation.validator import Validator
from app.handlers.input_params.validation.custom_rules import MultiValueErrors


class TestValidator:
    def test_success(self):
        import math

        schema = {
            'foo': {
                # собственные `coerce` схемы не конфликтуют с тем, который подмешивает валидатор
                'coerce': str,
            },
            'bar': {
                'coerce': [float, math.ceil],
            },
            'baz': {
                'empty': False,
            },
        }
        validator = Validator(schema, require_all=True)
        data = multidict.MultiDict([
            ('foo', 123), ('bar', '1.9'), ('baz', 'quux')
        ])

        data_normalized = validator.validated(data)
        assert data_normalized == {'foo': '123', 'bar': 2, 'baz': 'quux'}
        assert len(validator.errors) == 0

    def test_coercion_failure(self):
        schema = {
            'foo': {
                'coerce': int,
            },
            'bar': {
                'type': 'string',
            },
        }
        validator = Validator(schema, require_all=True)
        data = multidict.MultiDict([
            ('foo', 'bar'), ('bar', 'baz')
        ])

        data_normalized = validator.validated(data)
        assert data_normalized is None
        assert len(validator.errors) == 1
        assert cerberus.errors.COERCION_FAILED in validator.document_error_tree['foo']

    def test_multiple_values(self):
        schema = {
            'foo': {
                'type': 'integer',
            },
            'bar': {
                'type': 'string',
            },
        }
        validator = Validator(schema, require_all=True)
        data = multidict.MultiDict([
            ('foo', 123), ('bar', 'baz'), ('foo', 456)
        ])

        data_normalized = validator.validated(data)
        assert data_normalized is None
        assert len(validator.errors) == 1
        assert cerberus.errors.COERCION_FAILED in validator.document_error_tree['foo']
        error = validator.document_error_tree['foo'][cerberus.errors.COERCION_FAILED]
        assert error.info == (MultiValueErrors.SEQUENCE_OF_MANY,)

    def test_regular_dict(self):
        schema = {
            'foo': {
                'type': 'integer',
            },
            'bar': {
                'type': 'string',
            },
        }
        validator = Validator(schema, require_all=True)
        data = {'foo': 123, 'bar': 'baz'}

        data_normalized = validator.validated(data)
        assert data_normalized is None
        assert len(validator.errors) == 2

        assert cerberus.errors.COERCION_FAILED in validator.document_error_tree['foo']
        error_foo = validator.document_error_tree['foo'][cerberus.errors.COERCION_FAILED]
        assert error_foo.info == (MultiValueErrors.NOT_A_SEQUENCE,)

        assert cerberus.errors.COERCION_FAILED in validator.document_error_tree['bar']
        error_bar = validator.document_error_tree['bar'][cerberus.errors.COERCION_FAILED]
        assert error_bar.info == (MultiValueErrors.NOT_A_SEQUENCE,)
