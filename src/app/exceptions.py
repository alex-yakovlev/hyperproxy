class AppException(Exception):
    pass


class InputValidationError(AppException):
    def __init__(self, errors):
        self.errors = errors


class MissingDomainHeader(AppException):
    pass


# ------------------------- BEGIN ------------------------- #

class PartnershipError(AppException):
    def __init__(self, domain):
        self.domain = domain


class PartnershipNotFound(PartnershipError):
    pass


class PartnershipInactive(PartnershipError):
    pass

# -------------------------- END -------------------------- #


# ------------------------- BEGIN ------------------------- #

class OperationLookupError(AppException):
    def __init__(self, opid):
        self.opid = opid


class NonCheckedOperation(OperationLookupError):
    pass


class OperationInProgress(OperationLookupError):
    pass


class OperationFailed(OperationLookupError):
    pass


class OperationExpired(OperationLookupError):
    pass


class NonMatchingFingerprints(OperationLookupError):
    pass

# -------------------------- END -------------------------- #


class AmbiguousOperation(AppException):
    def __init__(self, fingerprint):
        self.fingerprint = fingerprint


class InsufficientBalance(AppException):
    pass


class NegativeTransferAmount(AppException):
    pass


class UnknownServiceType(AppException):
    def __init__(self, service_type):
        self.service_type = service_type


class CurrencyConversionError(AppException):
    pass


class PaymentError(AppException):
    pass
