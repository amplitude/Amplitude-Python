import logging
import time

from amplitude import constants

logger = logging.getLogger(constants.LOGGER_NAME)


def current_milliseconds() -> int:
    """Return system current time in milliseconds

    Returns:
         current time in milliseconds in integer
    """
    return int(time.time() * 1000)


def truncate(obj):
    """Truncate an object: Cut string values that exceed the maximum length limit. Return empty dict if number of
        items exceed maximum properties key limit. Truncate operation applies to dict and str type, values of
        dict and elements of list.

    Args:
         obj: The object to be truncated.

    Returns:
        The truncated object
    """
    if isinstance(obj, dict):
        if len(obj) > constants.MAX_PROPERTY_KEYS:
            logger.error(f"Too many properties. {constants.MAX_PROPERTY_KEYS} maximum.")
            return {}
        for key, value in obj.items():
            obj[key] = truncate(value)
    elif isinstance(obj, list):
        for i, element in enumerate(obj):
            obj[i] = truncate(element)
    elif isinstance(obj, str):
        obj = obj[:constants.MAX_STRING_LENGTH]
    return obj
