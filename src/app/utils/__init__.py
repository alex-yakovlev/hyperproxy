from datetime import datetime

from app import constants


def get_current_datetime():
    return datetime.now(constants.APP_TIMEZONE)
