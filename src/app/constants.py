from datetime import timezone
import enum


APP_TIMEZONE = timezone.utc


FINGERPRINT_LEN = 64


V1_ROUTING_QUERY_PARAM = 'function'

V2_ROUTING_QUERY_PARAM = 'ACTION'


class OperationStatus(enum.StrEnum):
    NEW = enum.auto()
    PAYMENT_INITIALIZED = enum.auto()
    # PAYMENT_MADE = enum.auto()
    COMPLETED = enum.auto()
    PAYMENT_FAILED = enum.auto()
    EXPIRED = enum.auto()


@enum.verify(enum.UNIQUE)
class ErrorCode(enum.IntFlag):
    APP_ERROR = 0x100  # 256

    PARAMS_ERROR = 0x110  # 272
    VALIDATION_ERROR = 0x111  # 273
    UNKNOWN_INITIATOR = 0x112  # 274
    UNKNOWN_SERVICE_TYPE = 0x113  # 275

    ACCESS_ERROR = 0x120  # 288
    INITIATOR_INACTIVE = 0x121  # 289
    LOW_BALANCE = 0x122  # 290

    USAGE_ERROR = 0x130  # 304

    OPERATION_ERROR = 0x140  # 320
    EXTERNAL_ERROR = 0x141  # 321

    UNEXPECTED_ERROR = 0x200  # 512
