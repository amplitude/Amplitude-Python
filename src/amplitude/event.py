import abc
import json

from amplitude.exception import EventPropertyKeyError, EventPropertyValueError


class AbstractEvent(abc.ABC):

    def __init__(self, callback=None, **kwargs):
        self.event_body = {}
        self.event_callback = callback
        for key, value in kwargs.items():
            self[key] = value

    @abc.abstractmethod
    def __getitem__(self, item):
        pass

    @abc.abstractmethod
    def __setitem__(self, key, value):
        pass

    @abc.abstractmethod
    def __contains__(self, item):
        pass

    def __str__(self):
        return json.dumps(self.event_body)

    def callback(self, response, message=None):
        if callable(self.event_callback):
            self.event_callback(self, response, message)


class Event(AbstractEvent):
    _event_properties = {
        "user_id": ["user_id", str],
        "device_id": ["device_id", str],
        "event_type": ["event_type", str],
        "time": ["time", int],
        "event_properties": ["event_properties", dict],
        "user_properties": ["user_properties", dict],
        "groups": ["groups", dict],
        "app_version": ["app_version", str],
        "platform": ["platform", str],
        "os_name": ["os_name", str],
        "os_version": ["os_version", str],
        "device_brand": ["device_brand", str],
        "device_manufacturer": ["device_manufacturer", str],
        "device_model": ["device_model", str],
        "carrier": ["carrier", str],
        "country": ["country", str],
        "region": ["region", str],
        "city": ["city", str],
        "dma": ["dma", str],
        "language": ["language", str],
        "price": ["price", float],
        "quantity": ["quantity", int],
        "revenue": ["revenue", float],
        "product_id": ["productId", str],
        "revenue_type": ["revenueType", str],
        "location_lat": ["location_lat", float],
        "location_lng": ["location_lng", float],
        "ip": ["ip", str],
        "idfa": ["idfa", str],
        "idfv": ["idfv", str],
        "adid": ["adid", str],
        "android_id": ["android_id", str],
        "event_id": ["event_id", int],
        "session_id": ["session_id", int],
        "insert_id": ["insert_id", str],
        "plan": ["plan", dict]
    }
    _plan_properties = {
        "branch": ["branch", str],
        "source": ["source", str],
        "version": ["version", str]
    }

    def __getitem__(self, item):
        if item in self.event_body:
            return self.event_body[item]
        return None

    def __setitem__(self, key, value):
        self._verify_property(key, value)
        self._put_property(key, value)

    def __contains__(self, item):
        if item not in self.__class__._event_properties:
            return False
        property_key = self.__class__._event_properties[item]
        return property_key in self.event_body

    @classmethod
    def _verify_property(cls, key, value):
        if key not in cls._event_properties:
            raise EventPropertyKeyError(f"Unexpected event property key: {key}")
        if not isinstance(value, cls._event_properties[key][1]):
            raise EventPropertyValueError(
                f"Event property value type: {type(value)}. Expect {cls._event_properties[key][1]}")
        if key != "plan":
            return
        for plan_key, plan_value in value.items():
            if plan_key not in cls._plan_properties:
                raise EventPropertyKeyError(f"Unexpected plan property key: {plan_key}")
            if not isinstance(plan_value, cls._plan_properties[plan_key][1]):
                raise EventPropertyValueError(
                    f"Plan property value type: {type(plan_value)}. Expect {cls._plan_properties[plan_key][1]}")

    def _put_property(self, key, value):
        property_key = self.__class__._event_properties[key][0]
        self.event_body[property_key] = value


class GroupIdentifyEvent(AbstractEvent):

    def __getitem__(self, item):
        pass

    def __setitem__(self, key, value):
        pass

    def __contains__(self, item):
        pass


class IdentifyEvent(AbstractEvent):

    def __getitem__(self, item):
        pass

    def __setitem__(self, key, value):
        pass

    def __contains__(self, item):
        pass


class RevenueEvent(AbstractEvent):

    def __getitem__(self, item):
        pass

    def __setitem__(self, key, value):
        pass

    def __contains__(self, item):
        pass


class Identify:

    def __init__(self):
        pass


class Revenue:

    def __init__(self):
        pass


if __name__ == "__main__":
    e = Event(callback="99", event_type="abc", user_id="jdlsajsld", plan={"branch": "main", "source": "python"})
    print(e)
    e.event_body['a'] = 9
    print(e)
