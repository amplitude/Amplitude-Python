from amplitude.event import BaseEvent


def verify_event(event):
    if not isinstance(event, BaseEvent):
        return False
    if not event["event_type"]:
        return False
    if not event["user_id"] and not event["device_id"]:
        return False
    return True
