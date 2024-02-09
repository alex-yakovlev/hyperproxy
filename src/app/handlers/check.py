import aiohttp.web

from .templating import with_template_response
from .input_params import with_parsed_params, with_validated_params, CHECK_PARAMS_SCHEMA


class SuccessTemplate():
    async def render(self, **context):
        return '''
        <Response>
            <Result>OK</Result>
            <ErrCode>0</ErrCode>
            <Description></Description>
        </Response>
        '''


class CheckHandler(aiohttp.web.View):
    @with_parsed_params()
    @with_validated_params(CHECK_PARAMS_SCHEMA)
    @with_template_response(SuccessTemplate())
    async def post(self):
        return {}
