import asyncio
import contextvars
import os

import aiohttp.web
import aiohttp.web_exceptions

from app import constants
from app import handlers
from app.handlers.templating import TemplateLoader
from app import router
from app.utils import config


QUERY_HANDLER = contextvars.ContextVar('query_handler')

TEMPLATES_ROOT = os.path.join(os.path.dirname(__file__), 'handlers')


async def prepare_templates(app):
    loader = TemplateLoader(TEMPLATES_ROOT)

    async def load_template(key, filepath):
        return key, await loader.load(filepath)

    templates = {
        'v1_response': 'v1/templates/response.xml',
        'v2_response': 'v2/templates/response.xml',
    }
    app['templates'] = dict(await asyncio.gather(*[
        load_template(key, tp) for key, tp in templates.items()
    ]))


def make_app():
    app = aiohttp.web.Application()

    v1_query_router = router.QueryRouter(query_param=constants.V1_ROUTING_QUERY_PARAM)
    ''' /?function=check '''
    v1_query_router.add_view('check', handlers.v1.CheckHandler)
    ''' /?function=payment '''
    v1_query_router.add_view('payment', handlers.v1.PaymentHandler)

    v2_query_router = router.QueryRouter(query_param=constants.V2_ROUTING_QUERY_PARAM)
    ''' /?ACTION=nmtcheck '''
    v2_query_router.add_view('nmtcheck', handlers.v2.NMT_CheckHandler)
    ''' /?ACTION=clientcheck '''
    v2_query_router.add_view('clientcheck', handlers.v2.ClientCheckHandler)
    ''' /?ACTION=payment '''
    v2_query_router.add_view('payment', handlers.v2.PaymentHandler)

    class RootHandler(aiohttp.web.View):
        @router.custom_routing(QUERY_HANDLER, v1_query_router, v2_query_router)
        async def post(self):
            query_handler = QUERY_HANDLER.get()
            return await query_handler(self.request)

    app.router.add_view('/', RootHandler)

    app.on_startup.append(prepare_templates)

    return app


def main():
    app = make_app()
    aiohttp.web.run_app(app, port=config.get('APP_LISTEN_PORT'))


if __name__ == '__main__':
    main()
