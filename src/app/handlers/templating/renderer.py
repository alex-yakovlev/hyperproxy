import aiohttp.web


async def render_response(template, context, content_type='text/xml', **response_kwargs):
    '''
    Возвращает ответ для обработчика запроса, отрендеренный из шаблона

    Args:
        template (object): объект с асинхронным методом `render`, возвращающим строку
        context (dict): данные для шаблона

    Keyword Args:
        см. аргументы конструктора `aiohttp.web.Response`, кроме `text` и `body`
        https://docs.aiohttp.org/en/stable/web_reference.html#aiohttp.web.Response

    Returns:
        aiohttp.web.Response
    '''

    response_text = await template.render(**(context or {}))
    return aiohttp.web.Response(text=response_text, content_type=content_type, **response_kwargs)
