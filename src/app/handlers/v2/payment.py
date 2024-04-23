import aiohttp.web

from .middlewares import with_parsed_params, with_validated_params, with_public_response
from .input_params.validation_schemas import PAYMENT_PARAMS_SCHEMA


class PaymentHandler(aiohttp.web.View):
    @with_public_response()
    @with_parsed_params()
    @with_validated_params(PAYMENT_PARAMS_SCHEMA)
    async def post(self):
        return {'success': True}
