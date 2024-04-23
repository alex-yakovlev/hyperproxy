class AppException(Exception):
    pass


class InputValidationError(AppException):
    def __init__(self, errors):
        self.errors = errors


class MissingDomainHeader(AppException):
    pass


class PartnershipNotFound(AppException):
    def __init__(self, domain):
        self.domain = domain


class PartnershipInactive(AppException):
    def __init__(self, domain):
        self.domain = domain
