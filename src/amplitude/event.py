import json
import logging
from typing import Callable, Optional

from amplitude import constants
from amplitude.worker import Response

logger = logging.getLogger("amplitude")


class EventOptions:

    def __init__(self, callback=None):
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
        self.plan: Optional[dict[str: str]] = None
        self.event_callback: Optional[Callable[[EventOptions, Response, str], None]] = callback


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
                 plan: Optional[dict] = None,
                 event_properties: Optional[dict] = None,
                 user_properties: Optional[dict] = None,
                 groups: Optional[dict] = None,
                 group_properties: Optional[dict] = None,
                 callback: Optional[Callable[[EventOptions, Response, str], None]] = None):
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
        self.event_type: str = event_type
        self.event_properties: Optional[dict] = None
        self.user_properties: Optional[dict] = None
        self.groups: Optional[dict] = None
        self.group_properties: Optional[dict] = None
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
                 plan: Optional[dict] = None,
                 event_properties: Optional[dict] = None,
                 user_properties: Optional[dict] = None,
                 groups: Optional[dict] = None,
                 group_properties: Optional[dict] = None,
                 callback: Optional[Callable[[EventOptions, Response, str], None]] = None):
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
                 plan: Optional[dict] = None,
                 event_properties: Optional[dict] = None,
                 user_properties: Optional[dict] = None,
                 groups: Optional[dict] = None,
                 group_properties: Optional[dict] = None,
                 callback: Optional[Callable[[EventOptions, Response, str], None]] = None):
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
                 plan: Optional[dict] = None,
                 event_properties: Optional[dict] = None,
                 user_properties: Optional[dict] = None,
                 groups: Optional[dict] = None,
                 group_properties: Optional[dict] = None,
                 callback: Optional[Callable[[EventOptions, Response, str], None]] = None):
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
