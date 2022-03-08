import time
from amplitude.event import BaseEvent


def verify_event(event):
    if (not isinstance(event, BaseEvent)) or \
            (not event["event_type"]) or \
            (not event["user_id"] and not event["device_id"]):
        return False
    return True


def current_milliseconds() -> int:
    return int(time.time() * 1000)
