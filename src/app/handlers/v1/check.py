from collections import OrderedDict
import uuid

import aiohttp.web

from app import constants, utils
from app.database import models
from .middlewares import (
    with_public_response, with_parsed_params, with_validated_params, with_initial_db_data
)
from .input_params.validation_schemas import CHECK_PARAMS_SCHEMA


async def _get_fee_conditions(session, partnership, input_params):
    return (await session.scalars(
        models.ServiceFee.build_select_query_by_partnership(partnership)
        .where(models.ServiceFee.service_type == input_params['PaymSubjTp'])
    )).first()


async def _get_service_currency(session, partnership, input_params):
    return (await session.scalars(
        models.ServiceCurrency.build_select_query_by_partnership(partnership)
        .where(models.ServiceCurrency.service_type == input_params['PaymSubjTp'])
    )).first()


async def _get_balance(session, partnership, input_params):
    return (await session.scalars(
        models.Balance.build_select_query_by_partnership(partnership)
    )).first()


class CheckHandler(aiohttp.web.View):
    @with_public_response()
    @with_parsed_params()
    @with_validated_params(CHECK_PARAMS_SCHEMA)
    @with_initial_db_data()
    async def post(self):
        '''
        Проверка возможности перевода
        '''

        now = utils.get_current_datetime()

        partnership = self.request['partnership']
        payment_system = self.request['payment_system']

        input_params = self.request['method_params']
        amount_initial = input_params['Amount']

        paymentAPI = await self.request.app['payment_service'].get_payment_API(payment_system)
        exchange_rates = await paymentAPI.get_exchange_rates(date=now.date())

        async with self.request.app['db_sessionmaker'].begin() as session:
            fee_conditions = await _get_fee_conditions(session, partnership, input_params)
            service_currency = await _get_service_currency(session, partnership, input_params)
            balance = await _get_balance(session, partnership, input_params)

            customer_currency = service_currency.currency
            rate_initial_to_balance = exchange_rates[
                (fee_conditions.initiator_currency, balance.currency)
            ]
            rate_balance_to_customer = exchange_rates[(balance.currency, customer_currency)]

            amount_to_deduct = amount_initial * rate_initial_to_balance
            amount_adjusted = (
                amount_initial * (1 - fee_conditions.percent - fee_conditions.insurance)
                - fee_conditions.fix
            )
            amount_customer = (
                amount_adjusted
                * rate_initial_to_balance
                * (1 - fee_conditions.payment_system_percent)
                * rate_balance_to_customer
            )
            rate_customer = amount_customer / amount_initial

            # 🫡
            dummy_customer = uuid.uuid4()

            opid = str(uuid.uuid4())
            operation = models.Operation(
                opid=opid,
                partnership_id=partnership.id,
                initiator_opid=input_params['PaymExtId'],
                status=constants.OperationStatus.NEW,
                initial_amount=amount_initial,
                initiator_currency=fee_conditions.initiator_currency,
                customer_amount=amount_customer,
                customer_currency=customer_currency,
                amount_to_deduct=amount_to_deduct,
                balance_currency=balance.currency,
            )

            session.add(operation)

        return {
            'success': True,
            'description': 'Выполнено',
            'opid': opid,
            'initiator_opid': input_params['PaymExtId'],
            'ext_info': OrderedDict([
                ('customerAcc', dummy_customer.hex),
                ('customerId', dummy_customer.node),
                ('customerAmount', amount_customer),
                ('customerCurrency', customer_currency),
                ('customerRate', rate_customer),
                ('customerFee', 0),
            ]),
        }
