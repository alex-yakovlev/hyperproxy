import unittest.mock as mock
import pytest
import aiohttp.test_utils as aio_test_utils

import aiohttp.web
from multidict import MultiDict
import cerberus.errors

from app.handlers.input_params.validation.validator import Validator
from app.handlers.input_params.validation.custom_rules import MultiValueErrors
from app.handlers.input_params.validation.middleware import with_validated_params


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
        data = MultiDict([
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
        data = MultiDict([
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
        data = MultiDict([
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

    @pytest.mark.parametrize('data, is_document_valid_expected', [
        (MultiDict({'foo': 'bar'}), True),
        (MultiDict(), False),
    ])
    def test_is_document_valid_prop(self, data, is_document_valid_expected):
        validator = Validator({'foo': {'required': True}})
        validator.validate(data)
        assert validator.is_document_valid is is_document_valid_expected


class TestMiddleware:
    @staticmethod
    @pytest.fixture
    @mock.patch('app.handlers.input_params.validation.middleware.Validator', autospec=True)
    def decorated_handler(ValidatorMock):
        type(ValidatorMock.return_value).is_document_valid = mock.PropertyMock(return_value=True)
        type(ValidatorMock.return_value).errors = mock.PropertyMock(
            return_value=mock.sentinel.validation_errors
        )
        ValidatorMock.return_value.validated.return_value = mock.sentinel.params_normalized

        class DummyHandler(aiohttp.web.View):
            @with_validated_params(mock.sentinel.schema)
            async def get(self):
                return aiohttp.web.Response(text='decorated handler response')

            _ValidatorMock = ValidatorMock

        return DummyHandler

    @staticmethod
    @pytest.fixture
    def request_mock():
        request = aio_test_utils.make_mocked_request('GET', '/foo')
        request.app['templates'] = {'response': mock.sentinel.response_template}
        request['method_params_raw'] = mock.sentinel.params_parsed

        return request

    def test_decorator(self, decorated_handler):
        ValidatorMock = decorated_handler._ValidatorMock
        ValidatorMock.assert_called_once_with(mock.sentinel.schema, error_handler=mock.ANY)

    @pytest.mark.asyncio
    @mock.patch('app.handlers.input_params.validation.middleware.render_response', autospec=True)
    async def test_successful_validation(self, patched_render, decorated_handler, request_mock):
        response = await decorated_handler(request_mock)

        ValidatorMock = decorated_handler._ValidatorMock
        ValidatorMock.return_value.validated.assert_called_once_with(mock.sentinel.params_parsed)
        assert request_mock.get('method_params') == mock.sentinel.params_normalized
        assert 'method_params_raw' not in request_mock
        assert response.text == 'decorated handler response'

    @pytest.mark.asyncio
    @mock.patch('app.handlers.input_params.validation.middleware.render_response', autospec=True)
    async def test_failed_validation(self, patched_render, decorated_handler, request_mock):
        ValidatorMock = decorated_handler._ValidatorMock
        type(ValidatorMock.return_value).is_document_valid = mock.PropertyMock(return_value=False)
        patched_render.return_value = aiohttp.web.Response(text='decorator error response')

        response = await decorated_handler(request_mock)

        ValidatorMock.return_value.validated.assert_called_once_with(mock.sentinel.params_parsed)
        patched_render.assert_called_once_with(mock.sentinel.response_template, mock.ANY)
        assert response.text == 'decorator error response'
        render_context = patched_render.call_args.args[1]
        assert set(render_context.items()).issuperset([
            ('success', False),
            ('error_code', 1),
            ('validation_errors', mock.sentinel.validation_errors),
        ])
