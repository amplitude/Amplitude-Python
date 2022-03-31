import json
import logging
from typing import Callable, Optional, Union

from amplitude import constants
from amplitude import utils

PLAN_KEY_MAPPING = {
    "branch": ["branch", str],
    "source": ["source", str],
    "version": ["version", str],
    "version_id": ["versionId", str]
}
logger = logging.getLogger(__name__)


class Plan:

    def __init__(self, branch: Optional[str] = None, source: Optional[str] = None,
                 version: Optional[str] = None, version_id: Optional[str] = None):
        self.branch: Optional[str] = branch
        self.source: Optional[str] = source
        self.version: Optional[str] = version
        self.version_id: Optional[str] = version_id

    def get_plan_body(self):
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
    "library": ["library", str],
    "plan": ["plan", Plan],
    "group_properties": ["group_properties", dict],
    "partner_id": ["partner_id", str]
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
                 partner_id: Optional[str] = None,
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
        self.library: Optional[str] = None
        self.plan: Optional[Plan] = None
        self.partner_id: Optional[str] = None
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
        self["partner_id"] = partner_id
        self.event_callback: Optional[Callable[[EventOptions, int, Optional[str]], None]] = callback
        self.__retry: int = 0

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
        return json.dumps(self.get_event_body(), sort_keys=True, skipkeys=True)

    def get_event_body(self) -> dict:
        event_body = {}
        for key, value in EVENT_KEY_MAPPING.items():
            if key in self and self[key] is not None:
                event_body[value[0]] = self[key]
        if "plan" in event_body:
            event_body["plan"] = event_body["plan"].get_plan_body()
        return utils.truncate(event_body)

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

    @property
    def retry(self):
        return self.__retry

    @retry.setter
    def retry(self, n: int):
        self.__retry = n


class BaseEvent(EventOptions):

    def __init__(self, event_type: str,
                 user_id: Optional[str] = None,
                 device_id: Optional[str] = None,
                 time: Optional[int] = None,
                 event_properties: Optional[dict] = None,
                 user_properties: Optional[dict] = None,
                 groups: Optional[dict] = None,
                 group_properties: Optional[dict] = None,
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
                 partner_id: Optional[str] = None,
                 callback: Optional[Callable[[EventOptions, int, Optional[str]], None]] = None):
        super().__init__(user_id=user_id,
                         device_id=device_id,
                         time=time,
                         app_version=app_version,
                         platform=platform,
                         os_name=os_name,
                         os_version=os_version,
                         device_brand=device_brand,
                         device_manufacturer=device_manufacturer,
                         device_model=device_model,
                         carrier=carrier,
                         country=country,
                         region=region,
                         city=city,
                         dma=dma,
                         language=language,
                         price=price,
                         quantity=quantity,
                         revenue=revenue,
                         product_id=product_id,
                         revenue_type=revenue_type,
                         location_lat=location_lat,
                         location_lng=location_lng,
                         ip=ip,
                         idfa=idfa,
                         idfv=idfv,
                         adid=adid,
                         android_id=android_id,
                         event_id=event_id,
                         session_id=session_id,
                         insert_id=insert_id,
                         plan=plan,
                         partner_id=partner_id,
                         callback=callback)
        self.event_type: str = event_type
        self.event_properties: Optional[dict] = None
        self.user_properties: Optional[dict] = None
        self.groups: Optional[dict] = None
        self.group_properties: Optional[dict] = None
        self["event_properties"] = event_properties
        self["user_properties"] = user_properties
        self["groups"] = groups
        self["group_properties"] = group_properties

    def load_event_options(self, event_options: EventOptions):
        if not event_options:
            return
        for key in EVENT_KEY_MAPPING:
            if key in event_options:
                self[key] = event_options[key]


class Identify:

    def __init__(self):
        self._properties_set = set()
        self._properties = {}

    @property
    def user_properties(self):
        return self._properties.copy()

    def set(self, key: str, value: Union[int, float, str, list, dict, bool]):
        self._set_user_property(constants.IDENTITY_OP_SET, key, value)
        return self

    def set_once(self, key: str, value: Union[int, float, str, list, dict, bool]):
        self._set_user_property(constants.IDENTITY_OP_SET_ONCE, key, value)
        return self

    def append(self, key: str, value: Union[int, float, str, list, dict, bool]):
        self._set_user_property(constants.IDENTITY_OP_APPEND, key, value)
        return self

    def prepend(self, key: str, value: Union[int, float, str, list, dict, bool]):
        self._set_user_property(constants.IDENTITY_OP_PREPEND, key, value)
        return self

    def pre_insert(self, key: str, value: Union[int, float, str, list, dict, bool]):
        self._set_user_property(constants.IDENTITY_OP_PRE_INSERT, key, value)
        return self

    def post_insert(self, key: str, value: Union[int, float, str, list, dict, bool]):
        self._set_user_property(constants.IDENTITY_OP_POST_INSERT, key, value)
        return self

    def remove(self, key: str, value: Union[int, float, str, list, dict, bool]):
        self._set_user_property(constants.IDENTITY_OP_REMOVE, key, value)
        return self

    def add(self, key: str, value: Union[int, float]):
        self._set_user_property(constants.IDENTITY_OP_ADD, key, value)
        return self

    def unset(self, key: str):
        self._set_user_property(constants.IDENTITY_OP_UNSET, key, constants.UNSET_VALUE)
        return self

    def clear_all(self):
        self._properties = {constants.IDENTITY_OP_CLEAR_ALL: constants.UNSET_VALUE}
        return self

    def is_valid(self):
        if self._properties:
            return True
        return False

    def _set_user_property(self, operation, key, value):
        if self._validate(operation, key, value):
            if operation not in self._properties:
                self._properties[operation] = {}
            self._properties[operation][key] = value
            self._properties_set.add(key)

    def _validate(self, operation, key, value):
        if constants.IDENTITY_OP_CLEAR_ALL in self._properties or key in self._properties_set:
            return False
        if operation == constants.IDENTITY_OP_ADD:
            return isinstance(value, int) or isinstance(value, float)
        if operation != constants.IDENTITY_OP_UNSET:
            return is_validate_properties(key, value)
        return True


class GroupIdentifyEvent(BaseEvent):

    def __init__(self, user_id: Optional[str] = None,
                 device_id: Optional[str] = None,
                 time: Optional[int] = None,
                 event_properties: Optional[dict] = None,
                 user_properties: Optional[dict] = None,
                 groups: Optional[dict] = None,
                 group_properties: Optional[dict] = None,
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
                 partner_id: Optional[str] = None,
                 callback: Optional[Callable[[EventOptions, int, Optional[str]], None]] = None,
                 identify_obj: Optional[Identify] = None):
        super().__init__(constants.GROUP_IDENTIFY_EVENT, user_id=user_id,
                         device_id=device_id,
                         time=time,
                         event_properties=event_properties,
                         user_properties=user_properties,
                         groups=groups,
                         group_properties=group_properties,
                         app_version=app_version,
                         platform=platform,
                         os_name=os_name,
                         os_version=os_version,
                         device_brand=device_brand,
                         device_manufacturer=device_manufacturer,
                         device_model=device_model,
                         carrier=carrier,
                         country=country,
                         region=region,
                         city=city,
                         dma=dma,
                         language=language,
                         price=price,
                         quantity=quantity,
                         revenue=revenue,
                         product_id=product_id,
                         revenue_type=revenue_type,
                         location_lat=location_lat,
                         location_lng=location_lng,
                         ip=ip,
                         idfa=idfa,
                         idfv=idfv,
                         adid=adid,
                         android_id=android_id,
                         event_id=event_id,
                         session_id=session_id,
                         insert_id=insert_id,
                         plan=plan,
                         partner_id=partner_id,
                         callback=callback)
        if identify_obj:
            self.group_properties = identify_obj.user_properties


class IdentifyEvent(BaseEvent):

    def __init__(self, user_id: Optional[str] = None,
                 device_id: Optional[str] = None,
                 time: Optional[int] = None,
                 event_properties: Optional[dict] = None,
                 user_properties: Optional[dict] = None,
                 groups: Optional[dict] = None,
                 group_properties: Optional[dict] = None,
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
                 partner_id: Optional[str] = None,
                 callback: Optional[Callable[[EventOptions, int, Optional[str]], None]] = None,
                 identify_obj: Optional[Identify] = None):
        super().__init__(constants.IDENTIFY_EVENT, user_id=user_id,
                         device_id=device_id,
                         time=time,
                         event_properties=event_properties,
                         user_properties=user_properties,
                         groups=groups,
                         group_properties=group_properties,
                         app_version=app_version,
                         platform=platform,
                         os_name=os_name,
                         os_version=os_version,
                         device_brand=device_brand,
                         device_manufacturer=device_manufacturer,
                         device_model=device_model,
                         carrier=carrier,
                         country=country,
                         region=region,
                         city=city,
                         dma=dma,
                         language=language,
                         price=price,
                         quantity=quantity,
                         revenue=revenue,
                         product_id=product_id,
                         revenue_type=revenue_type,
                         location_lat=location_lat,
                         location_lng=location_lng,
                         ip=ip,
                         idfa=idfa,
                         idfv=idfv,
                         adid=adid,
                         android_id=android_id,
                         event_id=event_id,
                         session_id=session_id,
                         insert_id=insert_id,
                         plan=plan,
                         partner_id=partner_id,
                         callback=callback)
        if identify_obj:
            self.user_properties = identify_obj.user_properties


class Revenue:

    def __init__(self, price: float,
                 quantity: int = 1,
                 product_id: Optional[str] = None,
                 revenue_type: Optional[str] = None,
                 receipt: Optional[str] = None,
                 receipt_sig: Optional[str] = None,
                 properties: Optional[dict] = None,
                 revenue: Optional[float] = None):
        self.price: float = price
        self.quantity: int = quantity
        self.product_id: Optional[str] = product_id
        self.revenue_type: Optional[str] = revenue_type
        self.receipt: Optional[str] = receipt
        self.receipt_sig: Optional[str] = receipt_sig
        self.properties: Optional[dict] = properties
        self.revenue: Optional[float] = revenue

    def set_receipt(self, receipt: str, receipt_signature: str):
        self.receipt = receipt
        self.receipt_sig = receipt_signature
        return self

    def is_valid(self):
        return isinstance(self.price, float)

    def to_revenue_event(self):
        return RevenueEvent(event_properties=self.get_event_properties())

    def get_event_properties(self):
        event_properties = {}
        if self.properties:
            event_properties = self.properties.copy()
        event_properties.update({constants.REVENUE_PRODUCT_ID: self.product_id,
                                 constants.REVENUE_QUANTITY: self.quantity,
                                 constants.REVENUE_PRICE: self.price,
                                 constants.REVENUE_TYPE: self.revenue_type,
                                 constants.REVENUE_RECEIPT: self.receipt,
                                 constants.REVENUE_RECEIPT_SIG: self.receipt_sig,
                                 constants.REVENUE: self.revenue})
        return event_properties


class RevenueEvent(BaseEvent):

    def __init__(self, user_id: Optional[str] = None,
                 device_id: Optional[str] = None,
                 time: Optional[int] = None,
                 event_properties: Optional[dict] = None,
                 user_properties: Optional[dict] = None,
                 groups: Optional[dict] = None,
                 group_properties: Optional[dict] = None,
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
                 partner_id: Optional[str] = None,
                 callback: Optional[Callable[[EventOptions, int, Optional[str]], None]] = None,
                 revenue_obj: Optional[Revenue] = None):
        super().__init__(constants.AMP_REVENUE_EVENT, user_id=user_id,
                         device_id=device_id,
                         time=time,
                         event_properties=event_properties,
                         user_properties=user_properties,
                         groups=groups,
                         group_properties=group_properties,
                         app_version=app_version,
                         platform=platform,
                         os_name=os_name,
                         os_version=os_version,
                         device_brand=device_brand,
                         device_manufacturer=device_manufacturer,
                         device_model=device_model,
                         carrier=carrier,
                         country=country,
                         region=region,
                         city=city,
                         dma=dma,
                         language=language,
                         price=price,
                         quantity=quantity,
                         revenue=revenue,
                         product_id=product_id,
                         revenue_type=revenue_type,
                         location_lat=location_lat,
                         location_lng=location_lng,
                         ip=ip,
                         idfa=idfa,
                         idfv=idfv,
                         adid=adid,
                         android_id=android_id,
                         event_id=event_id,
                         session_id=session_id,
                         insert_id=insert_id,
                         plan=plan,
                         partner_id=partner_id,
                         callback=callback)
        if revenue_obj:
            if not self.event_properties:
                self.event_properties = {}
            self.event_properties.update(revenue_obj.get_event_properties())


def is_validate_properties(key, value):
    if not isinstance(key, str):
        return False
    if isinstance(value, list):
        result = True
        for element in value:
            if isinstance(element, list):
                return False
            if isinstance(element, dict):
                result = result and is_validate_object(element)
            elif not (isinstance(element, str) or isinstance(element, int) or isinstance(element, float)):
                result = False
            if not result:
                break
        return result
    if isinstance(value, dict):
        return is_validate_object(value)
    if not (isinstance(value, str) or isinstance(value, int) or isinstance(value, float) or isinstance(value, bool)):
        return False
    return True


def is_validate_object(obj):
    for key, value in obj.items():
        if not is_validate_properties(key, value):
            return False
    return True
