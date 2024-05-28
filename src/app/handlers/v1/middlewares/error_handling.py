from http import HTTPStatus

from app.app_logging import LoggerAdapter
from app import exceptions
from app.constants import ErrorCode
from ..utils import redact_input_data


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
        case exceptions.OperationIneligible():
            return {
                'error_code': ErrorCode.EXTERNAL_ERROR,
                'description': 'Операция уже завершена'
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

        case exceptions.PaymentError():
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


def _get_method_param_with_fallback(mdw_shared, key):
    return mdw_shared.get('method_params', {}).get(
        key,
        mdw_shared.get('method_params_raw', {}).get(key)
    )


def _log_error(request, error):
    '''
    Логирует ошибку и дополнительный контекст

    Args:
        request (aiohttp.web.Request)
        error (exceptions.AppException)
    '''

    mdw_shared = request.get('mdw_shared', {})
    logger = mdw_shared.get('logger')
    # логгер становится доступен после того, как управление пришло в основной обработчик
    # после всех декораторов
    if not logger:
        logger = LoggerAdapter(request.app['logger'], {
            'api_method': mdw_shared.get('api_method'),
            'opid': mdw_shared.get(
                'opid',
                _get_method_param_with_fallback(mdw_shared, 'id')
            ),
            'initiator_opid': _get_method_param_with_fallback(mdw_shared, 'PaymExtId'),
        })
    logger = LoggerAdapter(logger, {
        'error_type': type(error).__name__,
        'error_data': error.__dict__,
        'error_cause': error.__cause__,
    })

    match error:
        case exceptions.InputValidationError():
            logger.error(
                'Параметры запроса невалидны',
                extra={'params': redact_input_data(mdw_shared.get('method_params_raw'))}
            )
        case exceptions.MissingDomainHeader():
            logger.error('Не передан заголовок `X-Forwarded-Host`')
        case exceptions.PartnershipNotFound():
            logger.error('Не найден инициатор по заголовку `X-Forwarded-Host`')
        case exceptions.PartnershipInactive():
            logger.error(
                'Обслуживание инициатора отключено',
                extra={'partnership_id': error.partnership.id}
            )

        case exceptions.OperationInProgress():
            logger.error('Метод вызван повторно, операция уже в процессе обработки')
        case exceptions.NonCheckedOperation():
            logger.error('Вызову метода `payment` не предшествовал вызов `check`')
        case exceptions.NonMatchingFingerprints():
            logger.error('Методы `check` и `payment` вызваны с разными параметрами')
        case exceptions.OperationExpired():
            logger.error('Время для завершения операции истекло')
        case exceptions.OperationIneligible():
            logger.error('Метод вызван повторно, операция уже обработана')
        case exceptions.AmbiguousOperation():
            logger.error('Найдено несколько активных операций с таким отпечатком')

        case exceptions.UnknownFeeTerms():
            logger.error('Не найдены условия комиссий по параметру `PaymSubjTp`')
        case exceptions.UnknownCurrencySettings():
            logger.error('Не найдена валюта получателя по параметру `PaymSubjTp`')
        case exceptions.CurrencyConversionError():
            if error.__cause__:
                logger.error('Ошибка вызова API для получения курсов валют')
            else:
                logger.error('Не найдена валютная пара в курсах валют')
        case exceptions.NegativeTransferAmount():
            logger.error('Сумма к переводу после вычета комиссий нулевая или отрицательная')
        case exceptions.InsufficientBalance():
            logger.error('Недостаточно средств на балансе инициатора')
        case exceptions.PaymentError():
            logger.error('Ошибка вызова API для совершения перевода')

        # все подвиды `AppException` должны быть учтены выше,
        # дефолтный кейс не должен матчиться
        case _:
            logger.error('Неклассифицированая ошибка')


def handle_error_response(request, error):
    '''
    Функция для использования с декоратором `with_public_response`

    Args:
        error (exceptions.AppException)

    Returns:
        (dict, dict): пара из контекста для шаблона и параметров конструктора `aiohttp.web.Response`
    '''

    _log_error(request, error)

    context = {
        'success': False,
        'error_code': ErrorCode.APP_ERROR,
        **_get_error_context(error),
    }
    response_params = {'status': _get_http_status(context['error_code'])}

    return context, response_params
