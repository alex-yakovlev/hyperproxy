import aiohttp.web

from .middlewares import with_parsed_params, with_validated_params, with_template_response
from .input_params.validation_schemas import NMT_CHECK_PARAMS_SCHEMA


class NMT_CheckHandler(aiohttp.web.View):
    @with_parsed_params()
    @with_validated_params(NMT_CHECK_PARAMS_SCHEMA)
    @with_template_response()
    async def post(self):
        return {'success': True}
