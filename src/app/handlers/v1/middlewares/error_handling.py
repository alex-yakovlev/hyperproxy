from http import HTTPStatus

from app import exceptions
from app.constants import ErrorCode


def _get_error_context(error):
    '''
    Возвращает контекст для рендеринга шаблона

    Args:
        error (exceptions.AppException)

    Returns:
        dict
    '''

    match error:
        case exceptions.InputValidationError():
            return {
                'error_code': ErrorCode.VALIDATION_ERROR,
                'validation_errors': error.errors,
            }
        case exceptions.MissingDomainHeader() | exceptions.PartnershipNotFound():
            return {
                'error_code': ErrorCode.UNKNOWN_INITIATOR,
                'description': 'Инициатор неизвестен',
            }
        case exceptions.UnknownServiceType():
            return {
                'error_code': ErrorCode.UNKNOWN_SERVICE_TYPE,
                'validation_errors': {'PaymSubjTp': ['неизвестное значение']},
            }

        case exceptions.PartnershipInactive():
            return {
                'error_code': ErrorCode.INITIATOR_INACTIVE,
                'description': 'Инициатор не обслуживается',
            }
        case exceptions.InsufficientBalance():
            return {
                'error_code': ErrorCode.LOW_BALANCE,
                'description': 'Недостаточно средств',
            }

        case exceptions.OperationInProgress():
            return {
                'error_code': ErrorCode.USAGE_ERROR,
                'description': 'Операция в процессе обработки',
            }
        case exceptions.NonCheckedOperation():
            return {
                'error_code': ErrorCode.USAGE_ERROR,
                'description': 'Не найден предшествующий вызов "check"',
            }
        case exceptions.NonMatchingFingerprints():
            return {
                'error_code': ErrorCode.USAGE_ERROR,
                'description': 'Методы "check" и "payment" вызваны с разными параметрами',
            }
        case exceptions.OperationExpired():
            return {
                'error_code': ErrorCode.USAGE_ERROR,
                'description': 'Время для завершения операции истекло',
            }
        case exceptions.AmbiguousOperation():
            return {
                'error_code': ErrorCode.USAGE_ERROR,
                'description': 'Повторный вызов метода "check" с теми же параметрами',
            }

        case exceptions.NegativeTransferAmount():
            return {
                'error_code': ErrorCode.OPERATION_ERROR,
                'description': 'Комиссии превышают сумму перевода',
            }

        case exceptions.CurrencyConversionError():
            return {
                'error_code': ErrorCode.EXTERNAL_ERROR,
                'description': 'Невозможно совершить конвертацию валют'
            }

        case exceptions.PaymentError() | exceptions.OperationFailed():
            return {
                'error_code': ErrorCode.EXTERNAL_ERROR,
                'description': 'Невозможно выполнить операцию'
            }

        # какой-то еще подвид `AppException`, кроме перечисленных выше
        case _:
            return {'error_code': ErrorCode.APP_ERROR, 'description': 'Ошибка'}


def _get_http_status(error_code):
    '''
    Сопоставляет HTTP-код бизнес-коду ошибки

    Args:
        error_code (int): бизнес-код ошибки

    Returns:
        HTTPStatus|int
    '''

    if (
        error_code & ErrorCode.PARAMS_ERROR == ErrorCode.PARAMS_ERROR
        or error_code & ErrorCode.USAGE_ERROR == ErrorCode.USAGE_ERROR
    ):
        return HTTPStatus.BAD_REQUEST

    if error_code & ErrorCode.ACCESS_ERROR == ErrorCode.ACCESS_ERROR:
        return HTTPStatus.FORBIDDEN

    return HTTPStatus.UNPROCESSABLE_ENTITY


def get_error_response_data(error):
    '''
    Функция для использования с декоратором `with_public_response`

    Args:
        error (exceptions.AppException)

    Returns:
        (dict, dict): пара из контекста для шаблона и параметров конструктора `aiohttp.web.Response`
    '''

    context = {
        'success': False,
        'error_code': ErrorCode.APP_ERROR,
        **_get_error_context(error),
    }
    response_params = {'status': _get_http_status(context['error_code'])}

    return context, response_params
