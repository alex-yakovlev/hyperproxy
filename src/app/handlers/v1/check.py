from collections import OrderedDict
import uuid

from app import constants, exceptions, utils
from app.utils import finance
from app.database import models
from ..payment_apis import exceptions as payment_exceptions
from .middlewares import (
    with_shared_context,
    with_public_response,
    with_parsed_params, with_validated_params,
    with_initial_db_data
)
from .input_params.validation import CHECK_PARAMS_SCHEMA
from .base import BaseHandler
from .utils import redact_input_data


# 🫡
def _create_dummy_customer():
    dummy_customer = uuid.uuid4()
    return {'id': dummy_customer.node, 'account': dummy_customer.hex}


class CheckHandler(BaseHandler):
    @with_shared_context(lambda req: {'api_method': 'check', 'opid': str(uuid.uuid4())})
    @with_public_response()
    @with_parsed_params()
    @with_validated_params(CHECK_PARAMS_SCHEMA)
    @with_initial_db_data()
    async def post(self):
        '''
        Проверка возможности перевода
        '''

        call_start = utils.get_current_datetime()

        mdw_shared = self.request['mdw_shared']
        partnership = mdw_shared['partnership']
        payment_system = mdw_shared['payment_system']

        input_params = mdw_shared['method_params']
        amount_initial = input_params['Amount']
        service_type = input_params['PaymSubjTp']

        opid = mdw_shared['opid']
        fingerprint = models.Operation.generate_fingerprint(
            input_params['1'], amount_initial, service_type
        )

        logger = self._extend_logger({
            'partnership_id': partnership.id,
            'opid': opid,
            'initiator_opid': input_params['PaymExtId'],
        })
        logger.info(
            'Первичные проверки прошли успешно; начало работы метода `check`',
            extra={'params': redact_input_data(input_params)}
        )

        Session = self.request.app['db_sessionmaker']
        async with Session(expire_on_commit=False) as session:
            async with session.begin():
                balance = await self._get_balance(session, {'partnership': partnership})

                logger.info('Проверка активных операций с таким отпечатком')
                operation = await self._get_current_operation(
                    session,
                    {'fingerprint': fingerprint, 'active_at': call_start}
                )
                if operation and operation.status == constants.OperationStatus.NEW:
                    logger.warning(
                        'Метод вызван повторно после создания операции; '
                        'вызов не будет обработан'
                    )
                    return self._operation_success(operation, balance, _create_dummy_customer())

                logger.info('Поиск условий расчёта комиссий')
                fee_terms = await self._get_fee_terms(
                    session,
                    {
                        'partnership': partnership,
                        'service_type': service_type,
                        'active_at': call_start
                    }
                )
                service_currency = await self._get_service_currency(
                    session,
                    {'partnership': partnership, 'service_type': service_type}
                )

            logger.info('Запрос курсов валют от API')
            paymentAPI = await self.request.app['payment_service'].get_payment_API(payment_system)
            try:
                exchange_rates = await paymentAPI.get_exchange_rates(date=call_start.date())
            except payment_exceptions.API_Error as error:
                raise exceptions.CurrencyConversionError() from error

            logger.info('Определение курса конвертации из валюты инициатора в валюту получателя')
            customer_currency = service_currency.currency
            try:
                rate_initial_to_balance = exchange_rates[
                    (fee_terms.initiator_currency, balance.currency)
                ]
                rate_balance_to_customer = exchange_rates[(balance.currency, customer_currency)]
            except KeyError:
                raise exceptions.CurrencyConversionError(exchange_rates)

            logger.info('Вычисление суммы к получению')
            amount_to_deduct = amount_initial * rate_initial_to_balance
            amount_adjusted = (
                amount_initial * (1 - fee_terms.percent - fee_terms.insurance)
                - fee_terms.fix
            )
            amount_customer = (
                amount_adjusted
                * rate_initial_to_balance
                * (1 - fee_terms.payment_system_percent)
                * rate_balance_to_customer
            )

            if amount_customer <= 0:
                raise exceptions.NegativeTransferAmount()

            async with session.begin():
                logger.info('Проверка баланса инициатора')
                await session.refresh(balance)
                if balance.amount - amount_to_deduct <= 0:
                    raise exceptions.InsufficientBalance(balance.amount)

                logger.info('Сохранение операции в базу')
                # на последнем шаге суммы округляются
                operation = models.Operation(
                    opid=opid,
                    fingerprint=fingerprint,
                    partnership_id=partnership.id,
                    initiator_opid=input_params['PaymExtId'],
                    status=constants.OperationStatus.NEW,
                    initial_amount=finance.quantize(amount_initial, fee_terms.initiator_currency),
                    initiator_currency=fee_terms.initiator_currency,
                    customer_amount=finance.quantize(amount_customer, customer_currency),
                    customer_currency=customer_currency,
                    amount_to_deduct=finance.quantize(amount_to_deduct, balance.currency),
                    balance_currency=balance.currency,
                )
                session.add(operation)

        logger.info('Завершение работы метода `check`')
        return self._operation_success(operation, balance, _create_dummy_customer())

    async def _get_current_operation(self, session, params):
        '''
        Находит недавнюю (чья давность не превышает `OPERATION_LIFETIME`) операцию
        в статусе `NEW` с таким же фингерпринтом, как у параметров запроса

        Returns:
            models.Operation|None: операция, если такая есть
                (т.е. при повторном запросе с теми же параметрами)

        Raises:
            exceptions.OperationInProgress: если у недавней совпадающей по фингерпринту операции
                статус `PAYMENT_INITIALIZED` (уже обрабатывается запрос payment для этой операции)
            exceptions.AmbiguousOperation: если есть несколько совпадающих по фингерпринту операций
                в статусе `NEW` или `PAYMENT_INITIALIZED`
        '''

        partnership = self.request['mdw_shared']['partnership']

        operations = await self._get_operations(
            session,
            {
                'partnership': partnership,
                'fingerprint': params['fingerprint'],
                'active_at': params['active_at'],
            }
        )

        # по логике работы метода не должно происходить, но на всякий случай
        if len(operations) > 1:
            raise exceptions.AmbiguousOperation(params['fingerprint'])

        try:
            operation = operations[0]
        except IndexError:
            return None

        if operation.status == constants.OperationStatus.PAYMENT_INITIALIZED:
            raise exceptions.OperationInProgress()

        return operation

    def _operation_success(self, operation, balance, customer):
        return {
            **super()._operation_success(operation, balance),
            'description': 'Выполнено',
            'ext_info': OrderedDict([
                ('customerAcc', customer['account']),
                ('customerId', customer['id']),
                ('customerAmount', operation.customer_amount),
                ('customerCurrency', operation.customer_currency),
                ('customerRate', operation.customer_amount / operation.initial_amount),
                ('customerFee', 0),
            ]),
        }

    async def _get_operations(self, session, params):
        Operation = models.Operation
        return (await session.scalars(
            Operation.select_active(params['partnership'], params['active_at'])
            .where(Operation.fingerprint == params['fingerprint'])
            .where(Operation.status.in_([
                constants.OperationStatus.NEW,
                constants.OperationStatus.PAYMENT_INITIALIZED,
            ]))
        )).all()
