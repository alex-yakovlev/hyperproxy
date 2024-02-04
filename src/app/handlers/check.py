import aiohttp.web

from .input_params import with_parsed_params, with_validated_params, CHECK_PARAMS_SCHEMA


RESPONSE = '''
<Response>
    <Result>OK</Result>
    <ErrCode>0</ErrCode>
    <Description></Description>
</Response>
'''


class CheckHandler(aiohttp.web.View):
    @with_parsed_params()
    @with_validated_params(CHECK_PARAMS_SCHEMA)
    async def post(self):
        return aiohttp.web.Response(text=RESPONSE, content_type='text/xml')
