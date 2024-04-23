import abc


class PaymentAPI(metaclass=abc.ABCMeta):
    '''
    Адаптер для работы с различными платежными системами.
    Создание инстанса конкретного класса-наследника инициируется обработчиком запроса
    и уничтожается вместе с ним;
    каждый наследник может иметь много инстансов в один момент времени.
    '''

    @abc.abstractmethod
    async def get_exchange_rates(self, date):
        '''
        Метод для запроса курсов валют

        Args:
            date (date): дата курсов валют

        Returns:
            dict: словарь, ключи которого — валютные пары,
            а значения — соответствующие курсы конвертации; пример:
            {('EUR', 'USD'): Decimal('1.06212')}
        '''

        pass

    @abc.abstractmethod
    async def place_order(self, params):
        '''
        Метод для проведения платежа

        Args:
            params (dict): данные платежа:

            params.amount (Decimal): сумма платежа
            params.currency (str): валюта платежа
            params.PAN (str): номер карты получателя
            params.client.name (str): имя получателя
            params.client.country (str): страна получателя
            params.client.birth_date (date): год рождения получателя
            params.internal_opid (str): идентификатор платежа в нашей системе
        '''

        pass


class PaymentProvider(metaclass=abc.ABCMeta):
    '''
    Фабрика объектов `PaymentAPI`, шарящая между ними сессию HTTP-клиента.
    Срок жизни инстанса конкретного класса-наследника — всё время жизни приложения;
    каждый наследник имеет по одному инстансу.
    '''

    @abc.abstractmethod
    async def start(self):
        '''
        Инициализирует сессию HTTP-клиента;
        повторные вызовы не должны приводить к созданию новых сессий
        '''

        pass

    @abc.abstractmethod
    def get_API(self):
        '''
        Создает объект `PaymentAPI`, передавая ему сессию

        Returns:
            PaymentAPI
        '''

        pass

    @abc.abstractmethod
    async def cleanup(self):
        '''
        Закрывает сессию HTTP-клиента
        '''

        pass
