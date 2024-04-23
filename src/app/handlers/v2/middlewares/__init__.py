from functools import partial

from app import exceptions
from app.handlers import input_params, templating
from ..input_params.parsing import parse_params


TEMPLATE_KEY = 'v2_response'


def get_error_response_data(error):
    context = {'success': False}
    response_params = {}

    if isinstance(error, exceptions.InputValidationError):
        return {**context, 'error_code': 1, 'validation_errors': error.errors}, response_params

    return context, response_params


with_parsed_params = partial(input_params.with_parsed_params, parse_params)

with_validated_params = partial(input_params.with_validated_params)

with_public_response = partial(
    templating.with_public_response,
    TEMPLATE_KEY, TEMPLATE_KEY, get_error_response_data
)
