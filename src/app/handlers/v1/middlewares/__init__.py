from functools import partial

from app.handlers import input_params, templating
from ..input_params.parsing import parse_params


TEMPLATE_KEY = 'v1_response'


async def render_error(templates, validation_errors):
    return await templating.render_response(
        templates[TEMPLATE_KEY],
        {'success': False, 'error_code': 1, 'validation_errors': validation_errors}
    )


with_parsed_params = partial(input_params.with_parsed_params, parse_params)

with_validated_params = partial(input_params.with_validated_params, render_error)

with_template_response = partial(templating.with_template_response, TEMPLATE_KEY)
