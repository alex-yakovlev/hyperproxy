import aiohttp.web

from .middlewares import with_parsed_params, with_validated_params, with_public_response
from .input_params.validation_schemas import CLIENT_CHECK_PARAMS_SCHEMA


class ClientCheckHandler(aiohttp.web.View):
    @with_public_response()
    @with_parsed_params()
    @with_validated_params(CLIENT_CHECK_PARAMS_SCHEMA)
    async def post(self):
        return {'success': True}
