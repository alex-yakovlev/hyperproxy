from collections import OrderedDict
from datetime import date, timedelta
import random

import aiohttp.web
import sqlalchemy

from app import constants, utils
from app.database import models
from .middlewares import (
    with_public_response, with_parsed_params, with_validated_params, with_initial_db_data
)
from .input_params.validation_schemas import PAYMENT_PARAMS_SCHEMA


async def _get_service_currency(session, partnership, input_params):
    return (await session.scalars(
        models.ServiceCurrency.build_select_query_by_partnership(partnership)
        .where(models.ServiceCurrency.service_type == input_params['PaymSubjTp'])
    )).first()


async def _get_operation(session, partnership, input_params):
    return (await session.scalars(
        models.Operation.build_select_query_by_partnership(partnership)
        .where(models.Operation.opid == input_params['id'])
    )).first()


# 🫡
def _get_dummy_birth_date():
    today = date.today()
    min_date = today - timedelta(days=365 * 60)
    max_date = today - timedelta(days=365 * 20)

    return date.fromordinal(
        random.randrange(min_date.toordinal(), max_date.toordinal())
    )


class PaymentHandler(aiohttp.web.View):
    @with_public_response()
    @with_parsed_params()
    @with_validated_params(PAYMENT_PARAMS_SCHEMA)
    @with_initial_db_data()
    async def post(self):
        '''
        Подтверждение перевода
        '''

        partnership = self.request['partnership']
        payment_system = self.request['payment_system']

        input_params = self.request['method_params']
        opid = input_params['id']

        paymentAPI = await self.request.app['payment_service'].get_payment_API(payment_system)

        Session = self.request.app['db_sessionmaker']
        async with Session(expire_on_commit=False) as session:
            async with session.begin():
                service_currency = await _get_service_currency(session, partnership, input_params)
                operation = await _get_operation(session, partnership, input_params)

                operation.status = constants.OperationStatus.PAYMENT_INITIALIZED
                session.add(operation)

            await paymentAPI.place_order({
                'amount': operation.customer_amount,
                'currency': operation.customer_currency,
                'PAN': input_params['1'],
                'client': {
                    'name': input_params['801'],
                    'country': service_currency.country,
                    'birth_date': _get_dummy_birth_date(),
                },
                'internal_opid': opid,
            })

            async with session.begin():
                operation.status = constants.OperationStatus.COMPLETED
                operation.finished_at = utils.get_current_datetime()
                session.add(operation)

                await session.execute(
                    sqlalchemy
                    .update(models.Balance)
                    .where(models.Balance.partnership == partnership)
                    .values(balance=models.Balance.balance - operation.amount_to_deduct)
                )

        return {
            'success': True,
            'description': 'Платеж принят',
            'opid': opid,
            'payment_no': opid,
            'bill_reg_id': opid,
            'initiator_opid': input_params['PaymExtId'],
            'payment_date': operation.finished_at,
            'ext_info': OrderedDict([
                ('customerTransactionId', opid),
                ('customerTransactionDate', operation.finished_at),
            ]),
        }
