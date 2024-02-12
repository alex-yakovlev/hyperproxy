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

TEMPLATES_ROOT = os.path.join(os.path.dirname(__file__), 'handlers/templates')


async def prepare_templates(app):
    loader = TemplateLoader(TEMPLATES_ROOT)

    async def load_template(key, filepath):
        return key, await loader.load(filepath)

    templates = {'response': 'response.xml'}
    app['templates'] = dict(await asyncio.gather(*[
        load_template(key, tp) for key, tp in templates.items()
    ]))


def make_app():
    app = aiohttp.web.Application()

    query_router = router.QueryRouter(query_param=constants.ROUTING_QUERY_PARAM)
    ''' /?function=check '''
    query_router.add_view('check', handlers.CheckHandler)
    ''' /?function=payment '''
    query_router.add_view('payment', handlers.PaymentHandler)

    class RootHandler(aiohttp.web.View):
        @router.custom_router(query_router, QUERY_HANDLER)
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
