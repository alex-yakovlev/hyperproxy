class AppException(Exception):
    pass


class InputValidationError(AppException):
    def __init__(self, errors):
        self.errors = errors


class MissingDomainHeader(AppException):
    pass


# ------------------------- BEGIN ------------------------- #

class PartnershipError(AppException):
    pass


class PartnershipNotFound(PartnershipError):
    def __init__(self, domain):
        self.domain = domain


class PartnershipInactive(PartnershipError):
    def __init__(self, partnership):
        self.partnership = partnership

# -------------------------- END -------------------------- #


# ------------------------- BEGIN ------------------------- #

class OperationLookupError(AppException):
    pass


class NonCheckedOperation(OperationLookupError):
    pass


class OperationInProgress(OperationLookupError):
    pass


class OperationIneligible(OperationLookupError):
    pass


class OperationExpired(OperationLookupError):
    pass


class NonMatchingFingerprints(OperationLookupError):
    pass

# -------------------------- END -------------------------- #


# ------------------------- BEGIN ------------------------- #

class UnknownServiceType(AppException):
    def __init__(self, service_type):
        self.service_type = service_type


class UnknownFeeTerms(UnknownServiceType):
    pass


class UnknownCurrencySettings(UnknownServiceType):
    pass

# -------------------------- END -------------------------- #


class AmbiguousOperation(AppException):
    def __init__(self, fingerprint):
        self.fingerprint = fingerprint


class InsufficientBalance(AppException):
    def __init__(self, balance):
        self.balance = balance


class NegativeTransferAmount(AppException):
    pass


class CurrencyConversionError(AppException):
    def __init__(self, exchange_rates=None):
        self.exchange_rates = exchange_rates


class PaymentError(AppException):
    pass
