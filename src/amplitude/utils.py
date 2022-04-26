import logging
import time

from amplitude import constants

logger = logging.getLogger(constants.LOGGER_NAME)


def current_milliseconds() -> int:
    return int(time.time() * 1000)


def truncate(obj):
    if isinstance(obj, dict):
        if not obj:
            return {}
        if len(obj) > constants.MAX_PROPERTY_KEYS:
            logger.error(f"Too many properties. {constants.MAX_PROPERTY_KEYS} maximum.")
            return {}
        for key, value in obj.items():
            obj[key] = truncate(value)
    elif isinstance(obj, list):
        if not obj:
            return []
        for i, element in enumerate(obj):
            obj[i] = truncate(element)
    elif isinstance(obj, str):
        obj = obj[:constants.MAX_STRING_LENGTH]
    return obj
