import asyncio
import contextvars
import json
from functools import partial
import os

import aiohttp.web
import aiohttp.web_exceptions
import sqlalchemy
import sqlalchemy.ext.asyncio as async_alchemy

from app import constants
from app.database import models, migrations
from app import handlers
from app.handlers.templating import TemplateLoader
from app.handlers import payment_apis
from app import app_logging, router
from app.utils import config


QUERY_HANDLER = contextvars.ContextVar('query_handler')

TEMPLATES_ROOT = os.path.join(os.path.dirname(__file__), 'handlers')


async def prepare_database(app):
    engine = async_alchemy.create_async_engine(
        sqlalchemy.URL.create(
            drivername='postgresql+asyncpg',
            host=config.get('DB_HOST'),
            port=config.get('DB_PORT'),
            username=config.get('DB_USER'),
            password=config.get('DB_PASSWORD'),
            database=config.get('DB_NAME'),
        ),
        # JSON-поля есть только в таблице `logs`
        json_serializer=partial(json.dumps, cls=app_logging.JSONEncoder, ensure_ascii=False),
        echo=config.get('DEBUG_SQL') or False
    )

    Session = async_alchemy.async_sessionmaker(engine)
    app['db_sessionmaker'] = Session

    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)

    await migrations.apply_migrations(Session)

    yield

    await engine.dispose()


async def prepare_logging(app):
    service = app_logging.LoggingService(app.get('db_sessionmaker'))
    await service.start()
    app['logger'] = service.logger

    yield

    await service.stop()


async def prepare_payment_APIs(app):
    service = payment_apis.PaymentService()
    app['payment_service'] = service

    yield

    await service.cleanup()


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

    class RootHandler(aiohttp.web.View):
        @router.custom_routing(QUERY_HANDLER, v1_query_router)
        async def post(self):
            query_handler = QUERY_HANDLER.get()
            return await query_handler(self.request)

    app.router.add_view('/', RootHandler)

    app.cleanup_ctx.append(prepare_database)
    app.cleanup_ctx.append(prepare_logging)
    app.cleanup_ctx.append(prepare_payment_APIs)
    app.on_startup.append(prepare_templates)

    return app


def main():
    app = make_app()
    aiohttp.web.run_app(app, host='localhost', port=config.get('APP_LISTEN_PORT'))


if __name__ == '__main__':
    main()
