from functools import partial

from app.utils.sensitive_data import redact_sensitive_data
from .input_params.validation import PARAMS_PLAINTEXT_VALUES


redact_input_data = partial(redact_sensitive_data, PARAMS_PLAINTEXT_VALUES)
