import aiohttp


response = '''
<Response>
    <Result>OK</Result>
    <ErrCode>0</ErrCode>
    <ExtInfo></ExtInfo>
</Response>
'''


class PaymentHandler(aiohttp.web.View):
    async def post(self):
        return aiohttp.web.Response(text=response, content_type='text/xml')
