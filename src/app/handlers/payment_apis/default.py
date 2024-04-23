from decimal import Decimal
import json
from functools import partial

import aiohttp

from . import base


class PaymentAPI(base.PaymentAPI):
    '''
    См. базовый класс
    '''

    def __init__(self, session):
        self._session = session

    async def get_exchange_rates(self, date):
        # TODO обработка ошибок от API
        async with self._session.get('/exchange_rates', params={'date': date.isoformat()}) as resp:
            exchange_rates = (await resp.json())['exchange_rates']
            return {
                (pair['from'], pair['to']): Decimal(pair['rate'])
                for pair in exchange_rates
            }

    async def place_order(self, params):
        # TODO обработка ответа и ошибок от API
        client_name = params['client']['name']
        (client_first_name, client_last_name) = client_name.split(' ')
        async with self._session.post('/orders/credit', json={
            'amount': params['amount'],
            'currency': params['currency'],
            'pan': params['PAN'],
            'card': {
                'holder': client_name,
            },
            'client': {
                'name': client_name,
                'country': params['client']['country'],
            },
            'custom_fields': {
                'recipient_birth_date': params['client']['birth_date'].isoformat(),
                'recipient_first_name': client_first_name,
                'recipient_last_name': client_last_name,
            },
            'merchant_order_id': params['internal_opid'],
        }):
            pass


class JSONEncoder(json.JSONEncoder):
    '''
    Расширяет дефолтный JSONEncoder, сериализуя числа типа `Decimal` в строку
    '''

    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        return super().default(obj)


class PaymentProvider(base.PaymentProvider):
    '''
    См. базовый класс
    '''

    def __init__(self):
        self._session = None

    @property
    def is_started(self):
        return self._session is not None

    async def start(self, base_url):
        if self.is_started:
            return

        self._session = aiohttp.ClientSession(
            base_url,
            json_serialize=partial(json.dumps, cls=JSONEncoder)
        )

    def get_API(self):
        return PaymentAPI(self._session)

    async def cleanup(self):
        if not self.is_started:
            return

        await self._session.close()
        self._session = None
