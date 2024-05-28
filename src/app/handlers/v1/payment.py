from collections import OrderedDict
from datetime import date, timedelta
import random

import sqlalchemy

from app import constants, exceptions, utils
from app.database import models
from ..payment_apis import exceptions as payment_exceptions
from .middlewares import (
    with_shared_context,
    with_public_response,
    with_parsed_params, with_validated_params,
    with_initial_db_data
)
from .input_params.validation import PAYMENT_PARAMS_SCHEMA
from .base import BaseHandler
from .utils import redact_input_data


# 🫡
def _create_dummy_birth_date():
    today = date.today()
    min_date = today - timedelta(days=365 * 60)
    max_date = today - timedelta(days=365 * 20)

    return date.fromordinal(
        random.randrange(min_date.toordinal(), max_date.toordinal())
    )


class PaymentHandler(BaseHandler):
    @with_shared_context(lambda req: {'api_method': 'payment'})
    @with_public_response()
    @with_parsed_params()
    @with_validated_params(PAYMENT_PARAMS_SCHEMA)
    @with_initial_db_data()
    async def post(self):
        '''
        Подтверждение перевода
        '''

        call_start = utils.get_current_datetime()

        mdw_shared = self.request['mdw_shared']
        partnership = mdw_shared['partnership']
        payment_system = mdw_shared['payment_system']
        input_params = mdw_shared['method_params']

        logger = self._extend_logger({
            'partnership_id': partnership.id,
            'opid': input_params['id'],
            'initiator_opid': input_params['PaymExtId'],
        })
        logger.info(
            'Первичные проверки прошли успешно; начало работы метода `payment`',
            extra={'params': redact_input_data(input_params)}
        )

        Session = self.request.app['db_sessionmaker']
        async with Session(expire_on_commit=False) as session:
            async with session.begin():
                balance = await self._get_balance(session, {'partnership': partnership})

                logger.info('Поиск операции по идентификатору')
                operation = await self._get_current_operation(session)
                if operation.status == constants.OperationStatus.COMPLETED:
                    logger.warning(
                        'Метод вызван повторно после успешного завершения операции; '
                        'вызов не будет обработан'
                    )
                    return self._operation_success(operation, balance)
                # операция может быть фактически истекшей, но еще не помеченной обходчиком
                if operation.is_expired(call_start):
                    raise exceptions.OperationExpired()

                logger.info('Проверка баланса инициатора')
                if balance.amount <= 0:
                    raise exceptions.InsufficientBalance()

                service_currency = await self._get_service_currency(
                    session,
                    {'partnership': partnership, 'service_type': input_params['PaymSubjTp']}
                )

                logger.info('Обновление статуса операции')
                operation.status = constants.OperationStatus.PAYMENT_INITIALIZED
                session.add(operation)

            logger.info('Запрос к API на выполнение перевода')
            paymentAPI = await self.request.app['payment_service'].get_payment_API(payment_system)
            try:
                payment = await paymentAPI.place_order({
                    'amount': operation.customer_amount,
                    'currency': operation.customer_currency,
                    'PAN': input_params['1'],
                    'client': {
                        'name': input_params['801'],
                        'country': service_currency.country,
                        'birth_date': _create_dummy_birth_date(),
                    },
                    'internal_opid': operation.opid,
                })
            except payment_exceptions.API_Error as error:
                async with session.begin():
                    logger.info('Перевод не выполнен; обновление статуса операции')
                    operation.status = constants.OperationStatus.PAYMENT_FAILED
                    operation.finished_at = utils.get_current_datetime()
                    session.add(operation)

                raise exceptions.PaymentError() from error

            async with session.begin():
                logger.info('Обновление данных операции')
                operation.status = constants.OperationStatus.COMPLETED
                operation.payment_system_opid = payment['opid']
                operation.payment_system_status = payment['status']
                operation.finished_at = utils.get_current_datetime()
                session.add(operation)

                logger.info('Обновление баланса инициатора')
                # Возвращаемое значение — сумма баланса *в момент начала транзакции*,
                # уменьшенная на сумму платежа,
                # но в результате транзакции обновление происходит корректно
                # (без race condition-ов для одновременных запросов к прокси).
                # -------------------------------------------------- #
                # Холдирования нет, поэтому баланс может получиться отрицательным,
                # если после первичной проверки баланса были другие запросы.
                balance = (await session.execute(
                    sqlalchemy
                    .update(models.Balance)
                    .where(models.Balance.partnership == partnership)
                    .values(amount=models.Balance.amount - operation.amount_to_deduct)
                    .returning(models.Balance)
                )).scalar_one()

        logger.info('Завершение работы метода `payment`')
        return self._operation_success(operation, balance)

    async def _get_current_operation(self, session):
        '''
        Находит операцию с таким же `opid`, как в параметре запроса,
        в статусе `NEW` или `COMPLETED`

        Returns:
            models.Operation

        Raises:
            exceptions.NonCheckedOperation: если такой операции нет
                (не предшествовал запрос check с теми же параметрами)
            exceptions.NonMatchingFingerprints: если у найденной операции другой фингерпринт
                (отличаются сумма, валюта или получатель)
            exceptions.OperationInProgress: если у найденной операции статус `PAYMENT_INITIALIZED`
                (уже обрабатывается более ранний запрос payment для этой операции)
            exceptions.OperationIneligible: если найденная операция в статусе,
                исключающем проведение платежа
                (был запрос payment для этой операции, закончившийся неуспешно,
                или в процессе периодического обхода незаконченная операция была помечена
                как истекшая)
        '''

        partnership = self.request['mdw_shared']['partnership']

        input_params = self.request['mdw_shared']['method_params']
        opid = input_params['id']

        operations = await self._get_operations(
            session, {'partnership': partnership, 'opid': opid}
        )

        try:
            operation = operations[0]
        except IndexError:
            raise exceptions.NonCheckedOperation()

        fingerprint = models.Operation.generate_fingerprint(
            input_params['1'],
            input_params['Amount'],
            input_params['PaymSubjTp']
        )
        if operation.fingerprint != fingerprint:
            raise exceptions.NonMatchingFingerprints()

        match operation.status:
            case constants.OperationStatus.NEW | constants.OperationStatus.COMPLETED:
                return operation
            case constants.OperationStatus.PAYMENT_INITIALIZED:
                raise exceptions.OperationInProgress()
            case _:
                raise exceptions.OperationIneligible()

    async def _get_operations(self, session, params):
        return (await session.scalars(
            models.Operation.select_by_partnership(params['partnership'])
            .where(models.Operation.opid == params['opid'])
        )).all()

    def _operation_success(self, operation, balance):
        return {
            **super()._operation_success(operation, balance),
            'description': 'Платеж принят',
            'payment_no': operation.opid,
            'bill_reg_id': operation.opid,
            'payment_date': operation.finished_at,
            'ext_info': OrderedDict([
                ('customerTransactionId', operation.opid),
                ('customerTransactionDate', operation.finished_at),
            ]),
        }
