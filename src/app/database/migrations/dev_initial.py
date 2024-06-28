from datetime import timedelta
from decimal import Decimal

import sqlalchemy
from sqlalchemy import func as sql_functions

from app import constants
from app import utils
from app.utils import config
from .. import models


async def apply(session):
    if config.get('APP_ENV') != 'dev':
        return

    now = utils.get_current_datetime()

    dummy_payment_system = models.PaymentSystem(
        api_origin=config.get('PAYMENT_API_MOCK_ORIGIN'),
        name='default'
    )
    dummy_partnership = models.Partnership(
        domain='foobar-proxy.example',
        initiator_domain='foobar-bank.example',
        payment_system=dummy_payment_system,
    )
    dummy_balance = models.Balance(
        partnership=dummy_partnership, amount=10000, currency='USD'
    )
    dummy_conditions = [
        models.ServiceFee(
            partnership=dummy_partnership,
            service_type='0001',
            initiator_currency='EUR',
            fix=1,
            percent=Decimal('0.02'),
            payment_system_percent=Decimal('0.02'),
            insurance=Decimal('0.02'),
            active_from=now - timedelta(days=5),
            active_until=now + timedelta(hours=1),
        ),
        models.ServiceFee(
            partnership=dummy_partnership,
            service_type='0001',
            initiator_currency='EUR',
            fix=2,
            percent=Decimal('0.02'),
            payment_system_percent=Decimal('0.02'),
            insurance=Decimal('0.02'),
            active_from=now,
        ),
    ]
    dummy_currency = models.ServiceCurrency(
        partnership=dummy_partnership, service_type='0001', currency='CAD', country='CAN'
    )
    dummy_operation = models.Operation(
        opid='098c4cef-9161-4f2e-a039-f63a5a7ab105',
        fingerprint='85d10c5edfbe11303840fb4e0c6a5b897883f04f33b9904eb86325f4b2c1507a',
        partnership=dummy_partnership,
        initiator_opid='7b9bb88e5b',
        status=constants.OperationStatus.NEW,
        initial_amount=100,
        initiator_currency=dummy_conditions[0].initiator_currency,
        customer_amount=Decimal('136.3710471589199998225373425'),
        customer_currency=dummy_currency.currency,
        amount_to_deduct=Decimal('106.212'),
        balance_currency=dummy_balance.currency,
    )

    do_populate = await session.scalar(
        sqlalchemy
        .select(sql_functions.count())
        .select_from(models.Partnership)
        .where(models.Partnership.domain == dummy_partnership.domain)
    ) == 0

    if do_populate:
        session.add_all([
            dummy_payment_system,
            dummy_partnership,
            dummy_balance,
            *dummy_conditions,
            dummy_currency,
            dummy_operation
        ])
