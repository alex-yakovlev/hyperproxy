from datetime import timezone
from enum import Enum


APP_TIMEZONE = timezone.utc


V1_ROUTING_QUERY_PARAM = 'function'

V2_ROUTING_QUERY_PARAM = 'ACTION'


class OperationStatus(Enum):
    NEW = 100
    PAYMENT_INITIALIZED = 200
    PAYMENT_MADE = 300
    COMPLETED = 400
    PAYMENT_FAILED = 500
    EXPIRED = 600
