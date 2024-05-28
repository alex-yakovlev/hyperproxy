import decimal
import json
from functools import partial

import aiohttp

from . import base
from .exceptions import API_Error


class PaymentAPI(base.PaymentAPI):
    '''
    См. базовый класс
    '''

    def __init__(self, session):
        self._session = session

    async def get_exchange_rates(self, date):
        resp_data, resp = await self._call_api(
            'GET', '/exchange_rates', params={'date': date.isoformat()}
        )
        try:
            exchange_rates = resp_data['exchange_rates']
            return {
                (pair['from'], pair['to']): decimal.Decimal(pair['rate'])
                for pair in exchange_rates
            }
        except (KeyError, decimal.InvalidOperation) as error:
            raise API_Error('incompatible response format', resp.url, resp_data) from error

    async def place_order(self, params):
        client_name = params['client']['name']
        (client_first_name, client_last_name) = client_name.split(' ')
        resp_data, resp = await self._call_api('POST', '/orders/credit', json={
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
        })
        try:
            order = resp_data['orders'][0]
            return {
                'opid': order['id'],
                'status': order.get('status'),
                'amount': order.get('amount'),
            }

        except (KeyError, IndexError) as error:
            raise API_Error('incompatible response format', resp.url, resp_data) from error

    async def _call_api(self, method, url, **kwargs):
        try:
            async with self._session.request(method, url, **kwargs) as resp:
                if not resp.ok:
                    raise API_Error('bad status', resp.url, await resp.text())

                resp_data = await resp.json(content_type=None)
                if resp_data is None:
                    raise API_Error('blank response', resp.url)
                if not isinstance(resp_data, dict):
                    raise API_Error('incompatible response format', resp.url, resp_data)
                if 'failure_type' in resp_data:
                    raise API_Error('response failure', resp.url, resp_data)

                return resp_data, resp

        except json.JSONDecodeError as error:
            raise API_Error('malformed JSON', resp.url, await resp.text()) from error


class JSONEncoder(json.JSONEncoder):
    '''
    Расширяет дефолтный JSONEncoder, сериализуя числа типа `Decimal` в строку
    '''

    def default(self, obj):
        if isinstance(obj, decimal.Decimal):
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

        # дефолтный совокупный таймаут — 5 мин.
        # см. https://docs.aiohttp.org/en/stable/client_quickstart.html#timeouts
        self._session = aiohttp.ClientSession(
            base_url,
            # raise_for_status=True,
            json_serialize=partial(json.dumps, cls=JSONEncoder)
        )

    def get_API(self):
        return PaymentAPI(self._session)

    async def cleanup(self):
        if not self.is_started:
            return

        await self._session.close()
        self._session = None
