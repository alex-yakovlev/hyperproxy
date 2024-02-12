import aiohttp.web

from .templating import with_template_response
from .input_params import with_parsed_params, with_validated_params, CHECK_PARAMS_SCHEMA


class CheckHandler(aiohttp.web.View):
    @with_parsed_params()
    @with_validated_params(CHECK_PARAMS_SCHEMA)
    @with_template_response('response')
    async def post(self):
        return {'success': True}
