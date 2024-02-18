import unittest.mock as mock
import pytest
import aiohttp.test_utils as aio_test_utils

from http import HTTPStatus
import aiohttp.web
import genshi.template

from app.handlers.templating.rendering import Template, render_response
from app.handlers.templating.middleware import with_template_response


class TestTemplate:
    @pytest.mark.asyncio
    @pytest.mark.parametrize('template_str, context, rendered_expected', [
        ('<foo>${foo}</foo>', {'foo': 'BAR'}, '<foo>BAR</foo>'),
        (
            '<foo xmlns:py="http://genshi.edgewall.org/" py:content="foo"></foo>',
            {'foo': 'BAZ'},
            '<foo>BAZ</foo>'
        ),
    ])
    async def test_wrapper(self, template_str, context, rendered_expected):
        template = Template(template_str)
        assert await template.render(**context) == rendered_expected

    @pytest.mark.parametrize('template_str', [
        # интерполяция в атрибутах
        '<foo ${foo}></foo>',
        # незакрытый тег
        '<foo>${foo}<foo>',
        # не указан неймспейс при использовании директив
        '<foo py:content="foo"></foo>',
    ])
    def test_invalid_template(self, template_str):
        with pytest.raises(genshi.template.base.TemplateSyntaxError):
            Template(template_str)


class TestRenderer:
    @pytest.mark.asyncio
    @pytest.mark.parametrize('kwargs, attrs_expected', [
        ({}, {'content_type': 'text/xml', 'status': 200}),
        ({'content_type': 'text/plain'}, {'content_type': 'text/plain', 'status': 200}),
        ({'status': HTTPStatus.IM_A_TEAPOT}, {'content_type': 'text/xml', 'status': 418}),
    ])
    async def test_render_response(self, kwargs, attrs_expected):
        template = mock.NonCallableMock(name='template', spec_set=Template)
        template.render.return_value = 'rendered response'
        context = {'foo': 'bar'}

        response = await render_response(template, context, **kwargs)

        assert isinstance(response, aiohttp.web.Response)
        assert response.text == 'rendered response'
        template.render.assert_called_once_with(**context)
        for name, attr in attrs_expected.items():
            assert getattr(response, name) == attr


class TestMiddleware:
    @staticmethod
    @pytest.fixture
    def request_mock():
        request = aio_test_utils.make_mocked_request('GET', '/baz')
        request.app['templates'] = {
            'foo': mock.sentinel.foo_template,
            'bar': mock.sentinel.bar_template,
        }

        return request

    @pytest.mark.asyncio
    @mock.patch('app.handlers.templating.middleware.render_response', autospec=True)
    async def test_handler_context(self, patched_render, request_mock):
        class DecoratedHandler(aiohttp.web.View):
            @with_template_response('foo')
            async def get(self):
                return mock.sentinel.render_context

        patched_render.return_value = aiohttp.web.Response(text='decorator response')

        response = await DecoratedHandler(request_mock)

        assert response.text == 'decorator response'
        patched_render.assert_called_once_with(
            mock.sentinel.foo_template, mock.sentinel.render_context
        )

    @pytest.mark.asyncio
    @mock.patch('app.handlers.templating.middleware.render_response', autospec=True)
    async def test_handler_response(self, patched_render, request_mock):
        class DecoratedHandler(aiohttp.web.View):
            @with_template_response('foo')
            async def get(self):
                return aiohttp.web.Response(text='decorated handler response')

        response = await DecoratedHandler(request_mock)

        assert response.text == 'decorated handler response'
        patched_render.assert_not_called()
