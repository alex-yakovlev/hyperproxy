import abc
import functools

import aiohttp.web_exceptions


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


def custom_router(sub_router, sub_handler_var):
    '''
    Декоратор для использования вложенного роутера в class-based views.

    Args:
        sub_router(CustomRouter): роутер, которым должны проверяться запросы
        в дополнение к стандартному; его обработчики могут быть функциями или class-based view

        sub_handler_var(contextvars.ContextVar): context variable, с помощью которой
        внешнему обработчику передается дополнительный
    '''

    def decorator(handler):
        '''
        Если в `sub_router` найден матч запроса, сохраняет обработчик в `sub_handler_var`,
        откуда внешний обработчик может его взять, чтобы делегировать запрос;
        иначе кидает 406 Not Acceptable

        Args:
            handler(function): декорируемый обработчик, метод class-based view
        '''

        @functools.wraps(handler)
        async def wrapper(self):
            sub_handler = await sub_router.resolve(self.request)
            if not sub_handler:
                raise aiohttp.web_exceptions.HTTPNotAcceptable()

            sub_handler_var.set(sub_handler)
            return await handler(self)

        return wrapper

    return decorator
