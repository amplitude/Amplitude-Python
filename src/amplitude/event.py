import json
import logging
from typing import Callable

from amplitude import constants
from amplitude.worker import Response

logger = logging.getLogger("amplitude")


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
        self.event_callback: Callable[[EventOptions, Response, str], None] = callback


class BaseEvent(EventOptions):

    def __init__(self, event_type: str = None,
                 user_id: str | None = None,
                 device_id: str | None = None,
                 time: int | None = None,
                 app_version: str | None = None,
                 platform: str | None = None,
                 os_name: str | None = None,
                 os_version: str | None = None,
                 device_brand: str | None = None,
                 device_manufacturer: str | None = None,
                 device_model: str | None = None,
                 carrier: str | None = None,
                 country: str | None = None,
                 region: str | None = None,
                 city: str | None = None,
                 dma: str | None = None,
                 language: str | None = None,
                 price: float | None = None,
                 quantity: int | None = None,
                 revenue: float | None = None,
                 product_id: str | None = None,
                 revenue_type: str | None = None,
                 location_lat: float | None = None,
                 location_lng: float | None = None,
                 ip: str | None = None,
                 idfa: str | None = None,
                 idfv: str | None = None,
                 adid: str | None = None,
                 android_id: str | None = None,
                 event_id: int | None = None,
                 session_id: int | None = None,
                 insert_id: str | None = None,
                 plan: dict | None = None,
                 event_properties: dict | None = None,
                 user_properties: dict | None = None,
                 groups: dict | None = None,
                 group_properties: dict | None = None,
                 callback: Callable[[EventOptions, Response, str], None] | None = None):
        super().__init__(callback)
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
        self["event_type"] = event_type
        self["event_properties"] = event_properties
        self["user_properties"] = user_properties
        self["groups"] = groups
        self["group_properties"] = group_properties

    def __getitem__(self, item: str):
        if item in self.__dict__:
            return self.__dict__[item]
        return None

    def __setitem__(self, key: str, value: str | float | int | dict) -> None:
        if self._verify_property(key, value):
            self.__dict__[key] = value

    def __contains__(self, item: str) -> bool:
        if item not in self.__dict__:
            return False
        return self.__dict__[item] is not None

    def __str__(self) -> str:
        event_body = {constants.EVENT_KEY_MAPPING[k][0]: v for k, v in self.__dict__.items()
                      if k in constants.EVENT_KEY_MAPPING and v is not None}
        return json.dumps(event_body, sort_keys=True, skipkeys=True)

    def _verify_property(self, key, value) -> bool:
        if value is None:
            return True
        if key not in self.__dict__:
            logger.error(f"Unexpected event property key: {key}")
            return False
        if not isinstance(value, constants.EVENT_KEY_MAPPING[key][1]):
            logger.error(
                f"Event property value type: {type(value)}. Expect {constants.EVENT_KEY_MAPPING[key][1]}")
            return False
        if key != "plan":
            return True
        for plan_key, plan_value in value.items():
            if plan_key not in constants.PLAN_KEY_MAPPING:
                logger.error(f"Unexpected plan property key: {plan_key}")
                return False
            if not isinstance(plan_value, constants.PLAN_KEY_MAPPING[plan_key][1]):
                logger.error(
                    f"Plan property value type: {type(plan_value)}. Expect {constants.PLAN_KEY_MAPPING[plan_key][1]}")
                return False
        return True

    def callback(self, response, message=None) -> None:
        if callable(self.event_callback):
            self.event_callback(self, response, message)


class GroupIdentifyEvent(BaseEvent):

    def __init__(self, user_id: str | None = None,
                 device_id: str | None = None,
                 time: int | None = None,
                 app_version: str | None = None,
                 platform: str | None = None,
                 os_name: str | None = None,
                 os_version: str | None = None,
                 device_brand: str | None = None,
                 device_manufacturer: str | None = None,
                 device_model: str | None = None,
                 carrier: str | None = None,
                 country: str | None = None,
                 region: str | None = None,
                 city: str | None = None,
                 dma: str | None = None,
                 language: str | None = None,
                 price: float | None = None,
                 quantity: int | None = None,
                 revenue: float | None = None,
                 product_id: str | None = None,
                 revenue_type: str | None = None,
                 location_lat: float | None = None,
                 location_lng: float | None = None,
                 ip: str | None = None,
                 idfa: str | None = None,
                 idfv: str | None = None,
                 adid: str | None = None,
                 android_id: str | None = None,
                 event_id: int | None = None,
                 session_id: int | None = None,
                 insert_id: str | None = None,
                 plan: dict | None = None,
                 event_properties: dict | None = None,
                 user_properties: dict | None = None,
                 groups: dict | None = None,
                 group_properties: dict | None = None,
                 callback: Callable[[EventOptions, Response, str], None] | None = None):
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

    def __init__(self, user_id: str | None = None,
                 device_id: str | None = None,
                 time: int | None = None,
                 app_version: str | None = None,
                 platform: str | None = None,
                 os_name: str | None = None,
                 os_version: str | None = None,
                 device_brand: str | None = None,
                 device_manufacturer: str | None = None,
                 device_model: str | None = None,
                 carrier: str | None = None,
                 country: str | None = None,
                 region: str | None = None,
                 city: str | None = None,
                 dma: str | None = None,
                 language: str | None = None,
                 price: float | None = None,
                 quantity: int | None = None,
                 revenue: float | None = None,
                 product_id: str | None = None,
                 revenue_type: str | None = None,
                 location_lat: float | None = None,
                 location_lng: float | None = None,
                 ip: str | None = None,
                 idfa: str | None = None,
                 idfv: str | None = None,
                 adid: str | None = None,
                 android_id: str | None = None,
                 event_id: int | None = None,
                 session_id: int | None = None,
                 insert_id: str | None = None,
                 plan: dict | None = None,
                 event_properties: dict | None = None,
                 user_properties: dict | None = None,
                 groups: dict | None = None,
                 group_properties: dict | None = None,
                 callback: Callable[[EventOptions, Response, str], None] | None = None):
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

    def __init__(self, user_id: str | None = None,
                 device_id: str | None = None,
                 time: int | None = None,
                 app_version: str | None = None,
                 platform: str | None = None,
                 os_name: str | None = None,
                 os_version: str | None = None,
                 device_brand: str | None = None,
                 device_manufacturer: str | None = None,
                 device_model: str | None = None,
                 carrier: str | None = None,
                 country: str | None = None,
                 region: str | None = None,
                 city: str | None = None,
                 dma: str | None = None,
                 language: str | None = None,
                 price: float | None = None,
                 quantity: int | None = None,
                 revenue: float | None = None,
                 product_id: str | None = None,
                 revenue_type: str | None = None,
                 location_lat: float | None = None,
                 location_lng: float | None = None,
                 ip: str | None = None,
                 idfa: str | None = None,
                 idfv: str | None = None,
                 adid: str | None = None,
                 android_id: str | None = None,
                 event_id: int | None = None,
                 session_id: int | None = None,
                 insert_id: str | None = None,
                 plan: dict | None = None,
                 event_properties: dict | None = None,
                 user_properties: dict | None = None,
                 groups: dict | None = None,
                 group_properties: dict | None = None,
                 callback: Callable[[EventOptions, Response, str], None] | None = None):
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
