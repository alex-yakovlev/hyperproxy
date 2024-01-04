import abc
import functools

import aiohttp.web
import aiohttp.web_exceptions

from app import handlers
from app.utils import config


class CustomRouter:
    '''
    Роутер, которым можно матчить запросы по произвольным правилам.
    Используется в дополнение к обычным обработчикам с помощью декоратора `custom_router`.
    (Этот класс — альтернатива `aiohttp.abc.AbstractRouter`, чтобы конкретные реализации имели
    более простую сигнатуру метода `resolve`, не требующую, чтобы возвращаемое значение
    соответствовало интерфейсу `aiohttp.abc.AbstractMatchInfo`)
    '''

    @abc.abstractmethod
    async def resolve(self, request):
        '''
        Должен возвращать инстанс `aiohttp.abc.AbstractView`,
        или функцию вида `aiohttp.typedefs.Handler`, или `None`
        '''


class QueryRouter(CustomRouter):
    '''
    Роутер, которым можно матчить запросы по заданному параметру URL.
    Поддерживает только class-based views в качестве обработчиков.

    Args:
        query_param(str): название URL-параметра, по которому будут проверяться запросы
    '''

    def __init__(self, query_param):
        super().__init__()
        self._routes = {}
        self._query_param = query_param

    def add_view(self, query, handler):
        '''
        Регистрирует обработчик запроса (аналогично `aiohttp.web.UrlDispatcher.add_view`)

        Args:
            query(str): значение параметра `query_param` (см. конструктор)
            handler(aiohttp.abc.AbstractView): обработчик
        '''
        self._routes[query] = handler

    async def resolve(self, request):
        route = request.query.get(self._query_param)
        return self._routes.get(route)


def custom_router(sub_router):
    '''
    Декоратор для использования вложенного роутера в class-based views.

    Args:
        sub_router(CustomRouter): роутер, которым должны проверяться запросы
        в дополнение к стандартному
    '''
    def decorator(handler):
        '''
        Args:
            handler(function): метод-обработчик запроса class-based view,
            но принимающий дополнительный аргумент `sub_handler` — обработчик,
            которому может быть делегирован запрос
            (`sub_handler` может быть обработчиком-функцией или class-based view)
        '''
        @functools.wraps(handler)
        async def wrapper(self):
            sub_handler = await sub_router.resolve(self.request)
            if not sub_handler:
                raise aiohttp.web_exceptions.HTTPNotAcceptable()
            return await handler(self, sub_handler)

        return wrapper

    return decorator


def make_app():
    app = aiohttp.web.Application()

    query_router = QueryRouter(query_param='function')
    ''' /?function=check '''
    query_router.add_view('check', handlers.CheckHandler)
    ''' /?function=payment '''
    query_router.add_view('payment', handlers.PaymentHandler)

    class RootHandler(aiohttp.web.View):
        @custom_router(query_router)
        async def post(self, query_handler):
            return await query_handler(self.request)

    app.router.add_view('/', RootHandler)
    return app


def main():
    app = make_app()
    aiohttp.web.run_app(app, port=config.get('APP_LISTEN_PORT'))


if __name__ == '__main__':
    main()
