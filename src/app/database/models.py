from functools import partial

import sqlalchemy
from sqlalchemy import orm
from sqlalchemy import types as sql_types
from sqlalchemy import func as sql_functions

from app import constants


timestamp_column = partial(orm.mapped_column, sql_types.TIMESTAMP(timezone=True))
timestamp_column_with_default = partial(timestamp_column, server_default=sql_functions.now())

# домен, напр. `foobar-proxy.example`
url_hostname_column = partial(orm.mapped_column, sql_types.Unicode(256))

# схема+домен+порт, напр. `https://foobar-paymentgateway.example`
url_origin_column = url_hostname_column

external_opid_column = partial(orm.mapped_column, sql_types.String(256))

# ISO 4217
# TODO enum вместо простой строки
currency_column = partial(orm.mapped_column, sql_types.String(3))

# см. https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html#preventing-implicit-io-when-using-asyncsession  # noqa: E501
# см. https://docs.sqlalchemy.org/en/20/orm/queryguide/relationships.html#summary-of-relationship-loading-styles  # noqa: E501
relationship = partial(orm.relationship, lazy='raise')


LAST_COLUMN_INDEX = 1000


class Base(orm.DeclarativeBase):
    id = orm.mapped_column(sql_types.Integer, primary_key=True, sort_order=-1)
    created_at = timestamp_column_with_default(nullable=False, sort_order=LAST_COLUMN_INDEX)
    updated_at = timestamp_column(onupdate=sql_functions.now(), sort_order=LAST_COLUMN_INDEX)


class SelectBuilderMixin:
    @classmethod
    def build_select_query_by_partnership(Model, partnership):
        '''
        Args:
            partnership (Partnership)
        '''

        return sqlalchemy.select(Model).where(Model.partnership == partnership)


class PaymentSystem(Base):
    __tablename__ = 'payment_systems'

    # используется для сопоставления записи в базе модулю в коде, работающему с соответствующим API
    # (см. app.handlers.payment_apis.PaymentService)
    name = orm.mapped_column(sql_types.Unicode(50), default='default', nullable=False)
    api_origin = url_origin_column(unique=True, nullable=False)


class Partnership(Base):
    __tablename__ = 'domains'

    domain = url_hostname_column(unique=True, nullable=False)
    initiator_domain = url_hostname_column()
    payment_system_id = orm.mapped_column(
        sqlalchemy.ForeignKey('payment_systems.id'), nullable=False
    )
    is_active = orm.mapped_column(sql_types.Boolean(), default=True, nullable=False)

    payment_system = relationship(PaymentSystem)


class Balance(Base, SelectBuilderMixin):
    __tablename__ = 'balances'

    partnership_id = orm.mapped_column(sqlalchemy.ForeignKey('domains.id'), nullable=False)
    balance = orm.mapped_column(sql_types.Numeric, default=0, nullable=False)
    currency = currency_column(nullable=False)

    partnership = relationship(Partnership)


class ServiceCurrency(Base, SelectBuilderMixin):
    __tablename__ = 'service_currencies'

    partnership_id = orm.mapped_column(sqlalchemy.ForeignKey('domains.id'), nullable=False)
    service_type = orm.mapped_column(sqlalchemy.String(16), nullable=False)
    currency = currency_column(nullable=False)
    # ISO 3166-1 alpha-3
    country = orm.mapped_column(sql_types.String(3), nullable=False)

    partnership = relationship(Partnership)


class ServiceFee(Base, SelectBuilderMixin):
    __tablename__ = 'conditions'

    partnership_id = orm.mapped_column(sqlalchemy.ForeignKey('domains.id'), nullable=False)
    service_type = orm.mapped_column(sqlalchemy.String(16), nullable=False)
    fix = orm.mapped_column(sql_types.Numeric, nullable=False)
    percent = orm.mapped_column(sql_types.Numeric, nullable=False)
    payment_system_percent = orm.mapped_column(sql_types.Numeric, nullable=False)
    insurance = orm.mapped_column(sql_types.Numeric, nullable=False)
    initiator_currency = currency_column(nullable=False)
    active_from = timestamp_column_with_default(nullable=False)
    active_until = timestamp_column()

    partnership = relationship(Partnership)


class Operation(Base, SelectBuilderMixin):
    __tablename__ = 'operations'

    # RFC 4122
    opid = orm.mapped_column(sql_types.String(36), unique=True, nullable=False)
    partnership_id = orm.mapped_column(sqlalchemy.ForeignKey('domains.id'), nullable=False)
    initiator_opid = external_opid_column(nullable=False)
    payment_system_opid = external_opid_column()
    status = orm.mapped_column(sql_types.Enum(constants.OperationStatus), nullable=False)
    payment_system_status = orm.mapped_column(sql_types.String(256))
    initial_amount = orm.mapped_column(sql_types.Numeric, nullable=False)
    initiator_currency = currency_column(nullable=False)
    customer_amount = orm.mapped_column(sql_types.Numeric, nullable=False)
    customer_currency = currency_column(nullable=False)
    amount_to_deduct = orm.mapped_column(sql_types.Numeric, nullable=False)
    balance_currency = currency_column(nullable=False)
    finished_at = timestamp_column(sort_order=LAST_COLUMN_INDEX + 1)

    partnership = orm.relationship(Partnership)
