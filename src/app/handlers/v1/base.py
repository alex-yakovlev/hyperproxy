import aiohttp.web
import sqlalchemy

from app import exceptions, app_logging
from app.utils import finance
from app.database import models


class BaseHandler(aiohttp.web.View):
    async def _get_balance(self, session, params):
        return (await session.scalars(
            models.Balance.select_by_partnership(params['partnership'])
        )).first()

    async def _get_fee_terms(self, session, params):
        fee_terms = (await session.scalars(
            models.ServiceFee.select_by_partnership(params['partnership'])
            .where(models.ServiceFee.service_type == params['service_type'])
            .where(models.ServiceFee.active_from <= params['active_at'])
            .where(sqlalchemy.or_(
                models.ServiceFee.active_until > params['active_at'],
                models.ServiceFee.active_until.is_(None),
            ))
            # при наличии нескольких подходящих записей выбирается самая новая
            .order_by(models.ServiceFee.created_at.desc())
            .limit(1)
        )).first()

        if fee_terms is None:
            raise exceptions.UnknownFeeTerms(params['service_type'])

        return fee_terms

    async def _get_service_currency(self, session, params):
        service_currency = (await session.scalars(
            models.ServiceCurrency.select_by_partnership(params['partnership'])
            .where(models.ServiceCurrency.service_type == params['service_type'])
        )).first()

        if service_currency is None:
            raise exceptions.UnknownCurrencySettings(params['service_type'])

        return service_currency

    def _operation_success(self, operation, balance):
        return {
            'success': True,
            'opid': operation.opid,
            'initiator_opid': operation.initiator_opid,
            'balance': finance.quantize(balance.amount, balance.currency),
            'ext_info': {},
        }

    def _extend_logger(self, extra):
        logger = self.request['mdw_shared']['logger'] = app_logging.LoggerAdapter(
            self.request.app['logger'],
            {
                'api_method': self.request['mdw_shared'].get('api_method'),
                **extra,
            }
        )

        return logger
