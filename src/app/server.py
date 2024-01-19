import contextvars

import aiohttp.web
import aiohttp.web_exceptions

from app import handlers
from app import router
from app.utils import config


QUERY_HANDLER = contextvars.ContextVar('query_handler')


def make_app():
    app = aiohttp.web.Application()

    query_router = router.QueryRouter(query_param='function')
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
    return app


def main():
    app = make_app()
    aiohttp.web.run_app(app, port=config.get('APP_LISTEN_PORT'))


if __name__ == '__main__':
    main()
