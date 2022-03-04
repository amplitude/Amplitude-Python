import json
import logging
from typing import Callable, Optional, Union

from amplitude import constants


PLAN_KEY_MAPPING = {
    "branch": ["branch", str],
    "source": ["source", str],
    "version": ["version", str]
}
logger = logging.getLogger(constants.LOGGER_NAME)


class Plan:

    def __init__(self, branch: Optional[str], source: Optional[str], version: Optional[str]):
        self.branch: Optional[str] = branch
        self.source: Optional[str] = source
        self.version: Optional[str] = version

    def get_plan_body(self) -> dict[str: str]:
        result = {}
        for key in PLAN_KEY_MAPPING:
            if not self.__dict__[key]:
                continue
            if isinstance(self.__dict__[key], PLAN_KEY_MAPPING[key][1]):
                result[PLAN_KEY_MAPPING[key][0]] = self.__dict__[key]
            else:
                logger.error(
                    f"plan.{key} value type: {type(self.__dict__[key])}. Expect {PLAN_KEY_MAPPING[key][1]}")
        return result


EVENT_KEY_MAPPING = {
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
    "plan": ["plan", Plan],
    "group_properties": ["group_properties", dict]
}


class EventOptions:

    def __init__(self, user_id: Optional[str] = None,
                 device_id: Optional[str] = None,
                 time: Optional[int] = None,
                 app_version: Optional[str] = None,
                 platform: Optional[str] = None,
                 os_name: Optional[str] = None,
                 os_version: Optional[str] = None,
                 device_brand: Optional[str] = None,
                 device_manufacturer: Optional[str] = None,
                 device_model: Optional[str] = None,
                 carrier: Optional[str] = None,
                 country: Optional[str] = None,
                 region: Optional[str] = None,
                 city: Optional[str] = None,
                 dma: Optional[str] = None,
                 language: Optional[str] = None,
                 price: Optional[float] = None,
                 quantity: Optional[int] = None,
                 revenue: Optional[float] = None,
                 product_id: Optional[str] = None,
                 revenue_type: Optional[str] = None,
                 location_lat: Optional[float] = None,
                 location_lng: Optional[float] = None,
                 ip: Optional[str] = None,
                 idfa: Optional[str] = None,
                 idfv: Optional[str] = None,
                 adid: Optional[str] = None,
                 android_id: Optional[str] = None,
                 event_id: Optional[int] = None,
                 session_id: Optional[int] = None,
                 insert_id: Optional[str] = None,
                 plan: Optional[Plan] = None,
                 callback=None):
        self.user_id: Optional[str] = None
        self.device_id: Optional[str] = None
        self.time: Optional[int] = None
        self.app_version: Optional[str] = None
        self.platform: Optional[str] = None
        self.os_name: Optional[str] = None
        self.os_version: Optional[str] = None
        self.device_brand: Optional[str] = None
        self.device_manufacturer: Optional[str] = None
        self.device_model: Optional[str] = None
        self.carrier: Optional[str] = None
        self.country: Optional[str] = None
        self.region: Optional[str] = None
        self.city: Optional[str] = None
        self.dma: Optional[str] = None
        self.language: Optional[str] = None
        self.price: Optional[float] = None
        self.quantity: Optional[int] = None
        self.revenue: Optional[str] = None
        self.product_id: Optional[str] = None
        self.revenue_type: Optional[str] = None
        self.location_lat: Optional[float] = None
        self.location_lng: Optional[float] = None
        self.ip: Optional[str] = None
        self.idfa: Optional[str] = None
        self.idfv: Optional[str] = None
        self.adid: Optional[str] = None
        self.android_id: Optional[str] = None
        self.event_id: Optional[int] = None
        self.session_id: Optional[int] = None
        self.insert_id: Optional[str] = None
        self.plan: Optional[Plan] = None
        self["user_id"] = user_id
        self["device_id"] = device_id
        self["time"] = time
        self["app_version"] = app_version
        self["platform"] = platform
        self["os_name"] = os_name
        self["os_version"] = os_version
        self["device_brand"] = device_brand
        self["device_manufacturer"] = device_manufacturer
        self["device_model"] = device_model
        self["carrier"] = carrier
        self["country"] = country
        self["region"] = region
        self["city"] = city
        self["dma"] = dma
        self["language"] = language
        self["price"] = price
        self["quantity"] = quantity
        self["revenue"] = revenue
        self["product_id"] = product_id
        self["revenue_type"] = revenue_type
        self["location_lat"] = location_lat
        self["location_lng"] = location_lng
        self["ip"] = ip
        self["idfa"] = idfa
        self["idfv"] = idfv
        self["adid"] = adid
        self["android_id"] = android_id
        self["event_id"] = event_id
        self["session_id"] = session_id
        self["insert_id"] = insert_id
        self["plan"] = plan
        self.event_callback: Optional[Callable[[EventOptions, int, Optional[str]], None]] = callback

    def __getitem__(self, item: str):
        if item in self.__dict__:
            return self.__dict__[item]
        return None

    def __setitem__(self, key: str, value: Union[str, float, int, dict, Plan]) -> None:
        if self._verify_property(key, value):
            self.__dict__[key] = value

    def __contains__(self, item: str) -> bool:
        if item not in self.__dict__:
            return False
        return self.__dict__[item] is not None

    def __str__(self) -> str:
        event_body = {}
        for key, value in EVENT_KEY_MAPPING.items():
            if attribute_value := self[key]:
                event_body[value[0]] = attribute_value
        if "plan" in event_body:
            event_body["plan"] = event_body["plan"].get_plan_body()
        return json.dumps(event_body, sort_keys=True, skipkeys=True)

    def _verify_property(self, key, value) -> bool:
        if value is None:
            return True
        if key not in self.__dict__:
            logger.error(f"Unexpected event property key: {key}")
            return False
        if not isinstance(value, EVENT_KEY_MAPPING[key][1]):
            logger.error(
                f"Event property value type: {type(value)}. Expect {EVENT_KEY_MAPPING[key][1]}")
            return False
        return True

    def callback(self, status_code: int, message=None) -> None:
        if callable(self.event_callback):
            self.event_callback(self, status_code, message)


class BaseEvent(EventOptions):

    def __init__(self, event_type: str,
                 user_id: Optional[str] = None,
                 device_id: Optional[str] = None,
                 time: Optional[int] = None,
                 app_version: Optional[str] = None,
                 platform: Optional[str] = None,
                 os_name: Optional[str] = None,
                 os_version: Optional[str] = None,
                 device_brand: Optional[str] = None,
                 device_manufacturer: Optional[str] = None,
                 device_model: Optional[str] = None,
                 carrier: Optional[str] = None,
                 country: Optional[str] = None,
                 region: Optional[str] = None,
                 city: Optional[str] = None,
                 dma: Optional[str] = None,
                 language: Optional[str] = None,
                 price: Optional[float] = None,
                 quantity: Optional[int] = None,
                 revenue: Optional[float] = None,
                 product_id: Optional[str] = None,
                 revenue_type: Optional[str] = None,
                 location_lat: Optional[float] = None,
                 location_lng: Optional[float] = None,
                 ip: Optional[str] = None,
                 idfa: Optional[str] = None,
                 idfv: Optional[str] = None,
                 adid: Optional[str] = None,
                 android_id: Optional[str] = None,
                 event_id: Optional[int] = None,
                 session_id: Optional[int] = None,
                 insert_id: Optional[str] = None,
                 plan: Optional[Plan] = None,
                 event_properties: Optional[dict] = None,
                 user_properties: Optional[dict] = None,
                 groups: Optional[dict] = None,
                 group_properties: Optional[dict] = None,
                 callback: Optional[Callable[[EventOptions, int, Optional[str]], None]] = None):
        super().__init__(user_id,
                         device_id,
                         time,
                         app_version,
                         platform,
                         os_name,
                         os_version,
                         device_brand,
                         device_manufacturer,
                         device_model,
                         carrier,
                         country,
                         region,
                         city,
                         dma,
                         language,
                         price,
                         quantity,
                         revenue,
                         product_id,
                         revenue_type,
                         location_lat,
                         location_lng,
                         ip,
                         idfa,
                         idfv,
                         adid,
                         android_id,
                         event_id,
                         session_id,
                         insert_id,
                         plan,
                         callback)
        self.event_type: str = event_type
        self.event_properties: Optional[dict] = None
        self.user_properties: Optional[dict] = None
        self.groups: Optional[dict] = None
        self.group_properties: Optional[dict] = None
        self["event_properties"] = event_properties
        self["user_properties"] = user_properties
        self["groups"] = groups
        self["group_properties"] = group_properties


class GroupIdentifyEvent(BaseEvent):

    def __init__(self, user_id: Optional[str] = None,
                 device_id: Optional[str] = None,
                 time: Optional[int] = None,
                 app_version: Optional[str] = None,
                 platform: Optional[str] = None,
                 os_name: Optional[str] = None,
                 os_version: Optional[str] = None,
                 device_brand: Optional[str] = None,
                 device_manufacturer: Optional[str] = None,
                 device_model: Optional[str] = None,
                 carrier: Optional[str] = None,
                 country: Optional[str] = None,
                 region: Optional[str] = None,
                 city: Optional[str] = None,
                 dma: Optional[str] = None,
                 language: Optional[str] = None,
                 price: Optional[float] = None,
                 quantity: Optional[int] = None,
                 revenue: Optional[float] = None,
                 product_id: Optional[str] = None,
                 revenue_type: Optional[str] = None,
                 location_lat: Optional[float] = None,
                 location_lng: Optional[float] = None,
                 ip: Optional[str] = None,
                 idfa: Optional[str] = None,
                 idfv: Optional[str] = None,
                 adid: Optional[str] = None,
                 android_id: Optional[str] = None,
                 event_id: Optional[int] = None,
                 session_id: Optional[int] = None,
                 insert_id: Optional[str] = None,
                 plan: Optional[Plan] = None,
                 event_properties: Optional[dict] = None,
                 user_properties: Optional[dict] = None,
                 groups: Optional[dict] = None,
                 group_properties: Optional[dict] = None,
                 callback: Optional[Callable[[EventOptions, int, Optional[str]], None]] = None):
        super().__init__(constants.GROUP_IDENTIFY_EVENT, user_id,
                         device_id,
                         time,
                         app_version,
                         platform,
                         os_name,
                         os_version,
                         device_brand,
                         device_manufacturer,
                         device_model,
                         carrier,
                         country,
                         region,
                         city,
                         dma,
                         language,
                         price,
                         quantity,
                         revenue,
                         product_id,
                         revenue_type,
                         location_lat,
                         location_lng,
                         ip,
                         idfa,
                         idfv,
                         adid,
                         android_id,
                         event_id,
                         session_id,
                         insert_id,
                         plan,
                         event_properties,
                         user_properties,
                         groups,
                         group_properties,
                         callback)


class IdentifyEvent(BaseEvent):

    def __init__(self, user_id: Optional[str] = None,
                 device_id: Optional[str] = None,
                 time: Optional[int] = None,
                 app_version: Optional[str] = None,
                 platform: Optional[str] = None,
                 os_name: Optional[str] = None,
                 os_version: Optional[str] = None,
                 device_brand: Optional[str] = None,
                 device_manufacturer: Optional[str] = None,
                 device_model: Optional[str] = None,
                 carrier: Optional[str] = None,
                 country: Optional[str] = None,
                 region: Optional[str] = None,
                 city: Optional[str] = None,
                 dma: Optional[str] = None,
                 language: Optional[str] = None,
                 price: Optional[float] = None,
                 quantity: Optional[int] = None,
                 revenue: Optional[float] = None,
                 product_id: Optional[str] = None,
                 revenue_type: Optional[str] = None,
                 location_lat: Optional[float] = None,
                 location_lng: Optional[float] = None,
                 ip: Optional[str] = None,
                 idfa: Optional[str] = None,
                 idfv: Optional[str] = None,
                 adid: Optional[str] = None,
                 android_id: Optional[str] = None,
                 event_id: Optional[int] = None,
                 session_id: Optional[int] = None,
                 insert_id: Optional[str] = None,
                 plan: Optional[Plan] = None,
                 event_properties: Optional[dict] = None,
                 user_properties: Optional[dict] = None,
                 groups: Optional[dict] = None,
                 group_properties: Optional[dict] = None,
                 callback: Optional[Callable[[EventOptions, int, Optional[str]], None]] = None):
        super().__init__(constants.IDENTIFY_EVENT, user_id,
                         device_id,
                         time,
                         app_version,
                         platform,
                         os_name,
                         os_version,
                         device_brand,
                         device_manufacturer,
                         device_model,
                         carrier,
                         country,
                         region,
                         city,
                         dma,
                         language,
                         price,
                         quantity,
                         revenue,
                         product_id,
                         revenue_type,
                         location_lat,
                         location_lng,
                         ip,
                         idfa,
                         idfv,
                         adid,
                         android_id,
                         event_id,
                         session_id,
                         insert_id,
                         plan,
                         event_properties,
                         user_properties,
                         groups,
                         group_properties,
                         callback)


class RevenueEvent(BaseEvent):

    def __init__(self, user_id: Optional[str] = None,
                 device_id: Optional[str] = None,
                 time: Optional[int] = None,
                 app_version: Optional[str] = None,
                 platform: Optional[str] = None,
                 os_name: Optional[str] = None,
                 os_version: Optional[str] = None,
                 device_brand: Optional[str] = None,
                 device_manufacturer: Optional[str] = None,
                 device_model: Optional[str] = None,
                 carrier: Optional[str] = None,
                 country: Optional[str] = None,
                 region: Optional[str] = None,
                 city: Optional[str] = None,
                 dma: Optional[str] = None,
                 language: Optional[str] = None,
                 price: Optional[float] = None,
                 quantity: Optional[int] = None,
                 revenue: Optional[float] = None,
                 product_id: Optional[str] = None,
                 revenue_type: Optional[str] = None,
                 location_lat: Optional[float] = None,
                 location_lng: Optional[float] = None,
                 ip: Optional[str] = None,
                 idfa: Optional[str] = None,
                 idfv: Optional[str] = None,
                 adid: Optional[str] = None,
                 android_id: Optional[str] = None,
                 event_id: Optional[int] = None,
                 session_id: Optional[int] = None,
                 insert_id: Optional[str] = None,
                 plan: Optional[Plan] = None,
                 event_properties: Optional[dict] = None,
                 user_properties: Optional[dict] = None,
                 groups: Optional[dict] = None,
                 group_properties: Optional[dict] = None,
                 callback: Optional[Callable[[EventOptions, int, Optional[str]], None]] = None):
        super().__init__(constants.AMP_REVENUE_EVENT, user_id,
                         device_id,
                         time,
                         app_version,
                         platform,
                         os_name,
                         os_version,
                         device_brand,
                         device_manufacturer,
                         device_model,
                         carrier,
                         country,
                         region,
                         city,
                         dma,
                         language,
                         price,
                         quantity,
                         revenue,
                         product_id,
                         revenue_type,
                         location_lat,
                         location_lng,
                         ip,
                         idfa,
                         idfv,
                         adid,
                         android_id,
                         event_id,
                         session_id,
                         insert_id,
                         plan,
                         event_properties,
                         user_properties,
                         groups,
                         group_properties,
                         callback)


class Identify:

    def __init__(self):
        pass


class Revenue:

    def __init__(self):
        pass