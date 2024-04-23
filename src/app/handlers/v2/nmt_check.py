import aiohttp.web

from .middlewares import with_parsed_params, with_validated_params, with_public_response
from .input_params.validation_schemas import NMT_CHECK_PARAMS_SCHEMA


class NMT_CheckHandler(aiohttp.web.View):
    @with_public_response()
    @with_parsed_params()
    @with_validated_params(NMT_CHECK_PARAMS_SCHEMA)
    async def post(self):
        return {'success': True}
