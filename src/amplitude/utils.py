from amplitude.event import Event


def verify_event(event):
    if not isinstance(event, Event):
        return False
    if not event["event_type"]:
        return False
    if not event["user_id"] and not event["device_id"]:
        return False
    return True
