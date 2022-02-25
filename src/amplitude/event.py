import json

from amplitude.exception import EventPropertyKeyError, EventPropertyValueError
from amplitude.constants import EVENT_KEY_MAPPING, PLAN_KEY_MAPPING


class EventOptions:

    def __init__(self, callback=None):
        self.user_id = None
        self.device_id = None
        self.time = None
        self.app_version = None
        self.platform = None
        self.os_name = None
        self.os_version = None
        self.device_brand = None
        self.device_manufacturer = None
        self.device_model = None
        self.carrier = None
        self.country = None
        self.region = None
        self.city = None
        self.dma = None
        self.language = None
        self.price = None
        self.quantity = None
        self.revenue = None
        self.product_id = None
        self.revenue_type = None
        self.location_lat = None
        self.location_lng = None
        self.ip = None
        self.idfa = None
        self.idfv = None
        self.adid = None
        self.android_id = None
        self.event_id = None
        self.session_id = None
        self.insert_id = None
        self.plan = None
        self.event_callback = callback


class BaseEvent(EventOptions):

    def __init__(self, callback=None, **kwargs):
        super().__init__(callback)
        self.event_type = None
        self.event_properties = None
        self.user_properties = None
        self.groups = None
        for key, value in kwargs.items():
            self[key] = value

    def __getitem__(self, item: str):
        if item in self.__dict__:
            return self.__dict__[item]
        return None

    def __setitem__(self, key: str, value: str | float | int | dict) -> None:
        self._verify_property(key, value)
        self.__dict__[key] = value

    def __contains__(self, item: str) -> bool:
        if item not in self.__dict__:
            return False
        return self.__dict__[item] is not None

    def __str__(self) -> str:
        event_body = {EVENT_KEY_MAPPING[k][0]: v for k, v in self.__dict__.items()
                      if k in EVENT_KEY_MAPPING and v is not None}
        return json.dumps(event_body, sort_keys=True, skipkeys=True)

    def _verify_property(self, key, value) -> None:
        if key not in self.__dict__:
            raise EventPropertyKeyError(f"Unexpected event property key: {key}")
        if not isinstance(value, EVENT_KEY_MAPPING[key][1]):
            raise EventPropertyValueError(
                f"Event property value type: {type(value)}. Expect {EVENT_KEY_MAPPING[key][1]}")
        if key != "plan":
            return
        for plan_key, plan_value in value.items():
            if plan_key not in PLAN_KEY_MAPPING:
                raise EventPropertyKeyError(f"Unexpected plan property key: {plan_key}")
            if not isinstance(plan_value, PLAN_KEY_MAPPING[plan_key][1]):
                raise EventPropertyValueError(
                    f"Plan property value type: {type(plan_value)}. Expect {PLAN_KEY_MAPPING[plan_key][1]}")

    def callback(self, response, message=None) -> None:
        if callable(self.event_callback):
            self.event_callback(self, response, message)


class GroupIdentifyEvent(BaseEvent):

    def __init__(self, callback=None, **kwargs):
        super().__init__(callback, **kwargs)


class IdentifyEvent(BaseEvent):

    def __init__(self, callback=None, **kwargs):
        super().__init__(callback, **kwargs)


class RevenueEvent(BaseEvent):

    def __init__(self, callback=None, **kwargs):
        super().__init__(callback, **kwargs)


class Identify:

    def __init__(self):
        pass


class Revenue:

    def __init__(self):
        pass
