"""Amplitude event module with Classes of events and special events wrappers.

Classes:
    EventOptions: Base Class of all events. Holds common attributes that apply to all events.
    BaseEvent: Basic event class. Subclass of EventOptions.
    Identify: A class used to create identify and group identify event.
    IdentifyEvent: A special event class. Used to update user properties without an actual event.
    GroupIdentifyEvent: A special event class. Used to update group properties without an actual event
    Revenue: A class used to create revenue event.
    RevenueEvent: A special event class. Used to record revenue information.
    Plan: Tracking plan info includes branch, source, version, version_id.
"""

import copy
import enum
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
logger = logging.getLogger(constants.LOGGER_NAME)


class Plan:
    """Plan holds tracking plan information. Instance of Plan class can be value of event's `plan` attribute.

    Args:
        branch (str, optional): Branch of the tracking plan the event class belong to.
        source (str, optional): The source of the tracking plan event sent from.
        version (str, optional): The version of the tracking plan source code.
        version_id (str, optional): The version id of the tracking plan source code.

    Methods:
        get_plan_body(): return a dict object that contains tracking plan information.
    """

    def __init__(self, branch: Optional[str] = None, source: Optional[str] = None,
                 version: Optional[str] = None, version_id: Optional[str] = None):
        """The constructor for the Plan class

        Args:
            branch (str, optional): Branch of the tracking plan the event class belong to.
            source (str, optional): The source of the tracking plan event sent from.
            version (str, optional): The version of the tracking plan source code.
            version_id (str, optional): The version id of the tracking plan source code.
        """
        self.branch: Optional[str] = branch
        self.source: Optional[str] = source
        self.version: Optional[str] = version
        self.version_id: Optional[str] = version_id

    def get_plan_body(self):
        """Convert the Plan instance to dict instance

        Returns:
          A dictionary with data of the tracking plan stored in Plan instance
        """
        result = {}
        for key in PLAN_KEY_MAPPING:
            if not self.__dict__[key]:
                continue
            if isinstance(self.__dict__[key], PLAN_KEY_MAPPING[key][1]):
                result[PLAN_KEY_MAPPING[key][0]] = self.__dict__[key]
            else:
                logger.error(
                    f"Plan.{key} expected {PLAN_KEY_MAPPING[key][1]} but received {type(self.__dict__[key])}.")
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
    """ Base Class of all events. Hold common attributes of all kinds of events.

    Args:
        user_id (str, optional): A user identifier. Required if device_id isn't present.
        device_id (str, optional): A device-specific identifier. Required if user_id isn't present.
        time (int, optional): The timestamp of the event in milliseconds since epoch.
        app_version (str, optional): The current version of your application.
        platform (str, optional): Platform of the device.
        os_name (str, optional): The name of the mobile operating system or browser that the user is using.
        os_version (str, optional): The version of the mobile operating system or browser the user is using.
        device_brand (str, optional): The device brand that the user is using.
        device_manufacturer (str, optional): The device manufacturer that the user is using.
        device_model (str, optional): The device model that the user is using.
        carrier (str, optional): The carrier that the user is using.
        country (str, optional): The current country of the user.
        region (str, optional): The current region of the user.
        city (str, optional): The current city of the user.
        dma (str, optional): The current Designated Market Area of the user.
        language (str, optional): The language set by the user.
        price (float, optional): The price of the item purchased.
        quantity (int, optional): The quantity of the item purchased.
        revenue (float, optional): revenue = price * quantity. If all 3 fields (price, quantity, revenue) present
            then (price * quantity) will be used as the revenue value.
        product_id (str, optional): An identifier for the item purchased.
        revenue_type (str, optional): The type of revenue for the item purchased.
        location_lat (float, optional): The current Latitude of the user.
        location_lng (float, optional): The current Longitude of the user.
        ip (str, optional): The IP address of the user.
        idfa (str, optional): (iOS) Identifier for Advertiser.
        idfv (str, optional): (iOS) Identifier for Advertiser.
        adid (str, optional): (Android) Google Play Services advertising ID
        android_id (str, optional): (Android) Android ID (not the advertising ID)
        event_id (int, optional):  An incrementing counter to distinguish events with the same user_id and timestamp
            from each other.
        session_id (int, optional): The start timestamp of the session in milliseconds.
        insert_id (str, optional): A unique identifier for the event. Events sent with the same insert_id and device_id
            we have already seen before within the past 7 days will be deduplicated.
        plan (Plan, optional): Tracking plan properties.
        partner_id (str, optional): The partner id.
        callback (callable, optional): Event level callback method. Triggered when event is sent or failed. Take three
            parameters: an event instance, an integer code of response status, an optional string message.

    Properties:
        retry (int): The retry attempt of the event instance.

    Methods:
        get_event_body(): Retrun a dictionary with data of the event instance
        callback(code, message): Trigger callback method of the event instance.
    """

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
        """The constructor of EventOptions class"""
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
        """Convert the event instance to a dict instance

        Returns:
          A dictionary with the attributes and values of the event.
        """

        event_body = {}
        for key, value in EVENT_KEY_MAPPING.items():
            if key in self and self[key] is not None:
                event_body[value[0]] = self[key]
        if "plan" in event_body:
            event_body["plan"] = event_body["plan"].get_plan_body()
        for properties in ["user_properties", "event_properties", "group_properties"]:
            if properties in event_body:
                for key, value in event_body[properties].items():
                    if isinstance(value, enum.Enum):
                        event_body[properties][key] = value.value
        return utils.truncate(event_body)

    def _verify_property(self, key, value) -> bool:
        if value is None:
            return True
        if key not in self.__dict__:
            logger.error(f"Unexpected event property key: {key}")
            return False
        if not isinstance(value, EVENT_KEY_MAPPING[key][1]):
            logger.error(
                f"Event property {key} expected {EVENT_KEY_MAPPING[key][1]} but received {type(value)}.")
            return False
        if isinstance(value, dict):
            return is_validate_object(value)
        return True

    def callback(self, status_code: int, message=None) -> None:
        """Trigger the event level callback method.

        Args:
            status_code (int): The status code of the http api response.
            message (str, optional): A string message.
        """
        if callable(self.event_callback):
            self.event_callback(self, status_code, message)

    @property
    def retry(self):
        return self.__retry

    @retry.setter
    def retry(self, n: int):
        self.__retry = n


class BaseEvent(EventOptions):
    """The basic event class. A subclass of EventOptions. Have all available event attributes.

    Args:
        event_type (str): Required. The type of the event e.g. "Button Click", "Sign Up", "Song Played"
        user_id (str, optional): A user identifier. Required if device_id isn't present.
        device_id (str, optional): A device-specific identifier. Required if user_id isn't present.
        time (int, optional): The timestamp of the event in milliseconds since epoch.
        event_properties (dict, optional): Additional user defined event properties not included in event attributes.
        user_properties (dict, optional): Additional user properties tied to the user.
        groups (dict, optional): This feature is only available to Enterprise customers who have purchased the Accounts add-on.
            This field adds a dictionary of key-value pairs that represent groups of users to the event as an event-level group.
        group_properties (dict, optional): Additional group properties tied to the group.
        app_version (str, optional): The current version of your application.
        platform (str, optional): Platform of the device.
        os_name (str, optional): The name of the mobile operating system or browser that the user is using.
        os_version (str, optional): The version of the mobile operating system or browser the user is using.
        device_brand (str, optional): The device brand that the user is using.
        device_manufacturer (str, optional): The device manufacturer that the user is using.
        device_model (str, optional): The device model that the user is using.
        carrier (str, optional): The carrier that the user is using.
        country (str, optional): The current country of the user.
        region (str, optional): The current region of the user.
        city (str, optional): The current city of the user.
        dma (str, optional): The current Designated Market Area of the user.
        language (str, optional): The language set by the user.
        price (float, optional): The price of the item purchased.
        quantity (int, optional): The quantity of the item purchased.
        revenue (float, optional): revenue = price * quantity. If all 3 fields (price, quantity, revenue) present
            then (price * quantity) will be used as the revenue value.
        product_id (str, optional): An identifier for the item purchased.
        revenue_type (str, optional): The type of revenue for the item purchased.
        location_lat (float, optional): The current Latitude of the user.
        location_lng (float, optional): The current Longitude of the user.
        ip (str, optional): The IP address of the user.
        idfa (str, optional): (iOS) Identifier for Advertiser.
        idfv (str, optional): (iOS) Identifier for Advertiser.
        adid (str, optional): (Android) Google Play Services advertising ID
        android_id (str, optional): (Android) Android ID (not the advertising ID)
        event_id (int, optional):  An incrementing counter to distinguish events with the same user_id and timestamp
            from each other.
        session_id (int, optional): The start timestamp of the session in milliseconds.
        insert_id (str, optional): A unique identifier for the event. Events sent with the same insert_id and device_id
            we have already seen before within the past 7 days will be deduplicated.
        plan (Plan, optional): Tracking plan properties.
        partner_id (str, optional): The partner id.
        callback (callable, optional): Event level callback method. Triggered when event is sent or failed. Take three
            parameters: an event instance, an integer code of response status, an optional string message.

    Methods:
        load_event_options(event_options): Update event instance with values in input EventOptions instance
    """

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
        """The constructor of the BaseEvent class"""
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
        """Update event instance with values in input EventOptions instance. Existing values will be overwritten.

        Args:
            event_options: A EventOptions instance stored attributes values.
        """
        if not event_options:
            return
        for key in EVENT_KEY_MAPPING:
            if key in event_options:
                self[key] = copy.deepcopy(event_options[key])


class Identify:
    """A class to help generate IdentifyEvent or GroupIdentifyEvent instance with special event_type and
        user_properties/group_properties.

    Properties:
        user_properties (dict): A dictionary with a set of operations and values

    Methods:
        set(key, value): Set the user_properties key to the input value
        set_once(key ,value): Set the value of a property, prevent overriding the property value
        append(key, value): Append the value to a user property array
        prepend(key, value): Prepend the value to a user property array
        pre_insert(key, value): Add the specified values to the beginning of the list of properties
            for the user property if the values do not already exist in the list.
        post_insert(key, value): Add the specified values to the end of the list of properties for the user property
            if the values do not already exist in the list.
        remove(key, value): Remove all instances of the values specified from the input.
        add(key, value): Add a numeric value to a numeric property
        unset(key): Remove a user property from this user
        clear_all(): Remove all user properties of this user
        is_valid(): True if user_properties of Identify instance is not empty
    """

    def __init__(self):
        """The constructor of Identify class"""
        self._properties_set = set()
        self._properties = {}

    @property
    def user_properties(self):
        return copy.deepcopy(self._properties)

    def set(self, key: str, value: Union[int, float, str, list, dict, bool]):
        """Set the value of a property

        Args:
            key (str): The name of the user property to set.
            value (Union[int, float, str, list, dict, bool]): The value of the property.

        Returns:
            The Identify instance itself
        """
        self._set_user_property(constants.IDENTITY_OP_SET, key, value)
        return self

    def set_once(self, key: str, value: Union[int, float, str, list, dict, bool]):
        """Set the value of a property, prevent overriding the property value

        Args:
            key (str): The name of the user property to set.
            value (Union[int, float, str, list, dict, bool]): The value of the property.

        Returns:
            The Identify instance itself
        """
        self._set_user_property(constants.IDENTITY_OP_SET_ONCE, key, value)
        return self

    def append(self, key: str, value: Union[int, float, str, list, dict, bool]):
        """Append the value to a user property array

        Args:
            key (str): The name of the user property.
            value (Union[int, float, str, list, dict, bool]): The value of the user property.

        Returns:
            The Identify instance itself
        """
        self._set_user_property(constants.IDENTITY_OP_APPEND, key, value)
        return self

    def prepend(self, key: str, value: Union[int, float, str, list, dict, bool]):
        """Prepend the value to a user property array

        Args:
            key (str): The name of the user property.
            value (Union[int, float, str, list, dict, bool]): The value of the property.

        Returns:
            The Identify instance itself
        """
        self._set_user_property(constants.IDENTITY_OP_PREPEND, key, value)
        return self

    def pre_insert(self, key: str, value: Union[int, float, str, list, dict, bool]):
        """Add the specified values to the beginning of the list of properties
            for the user property if the values do not already exist in the list.

        Args:
            key (str): The name of the user property.
            value (Union[int, float, str, list, dict, bool]): The value of the property.

        Returns:
            The Identify instance itself
        """
        self._set_user_property(constants.IDENTITY_OP_PRE_INSERT, key, value)
        return self

    def post_insert(self, key: str, value: Union[int, float, str, list, dict, bool]):
        """Add the specified values to the end of the list of properties for the user property
            if the values do not already exist in the list.

        Args:
            key (str): The name of the user property.
            value (Union[int, float, str, list, dict, bool]): The value of the property.

        Returns:
            The Identify instance itself
        """
        self._set_user_property(constants.IDENTITY_OP_POST_INSERT, key, value)
        return self

    def remove(self, key: str, value: Union[int, float, str, list, dict, bool]):
        """Remove all instances of the values specified from the input.

        Args:
            key (str): The name of the user property.
            value (Union[int, float, str, list, dict, bool]): The values to be removed.

        Returns:
            The Identify instance itself
        """
        self._set_user_property(constants.IDENTITY_OP_REMOVE, key, value)
        return self

    def add(self, key: str, value: Union[int, float]):
        """Add a numeric value to a numeric property

        Args:
            key (str): The name of the user property.
            value (Union[int, float]): A numeric value.

        Returns:
            The Identify instance itself
        """
        self._set_user_property(constants.IDENTITY_OP_ADD, key, value)
        return self

    def unset(self, key: str):
        """Remove the user property from the user profile.

        Args:
            key (str): The name of the user property to remove.

        Returns:
            The Identify instance itself
        """
        self._set_user_property(constants.IDENTITY_OP_UNSET, key, constants.UNSET_VALUE)
        return self

    def clear_all(self):
        """Remove all user properties of this user

        Returns:
            The Identify instance itself
        """
        self._properties = {constants.IDENTITY_OP_CLEAR_ALL: constants.UNSET_VALUE}
        return self

    def is_valid(self):
        """Check if the Identify object has properties.

        Returns:
            return True if valid, otherwise return False
        """
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
            logger.error("Key or clear all operation already set.")
            return False
        if operation == constants.IDENTITY_OP_ADD:
            return isinstance(value, (float, int))
        if operation != constants.IDENTITY_OP_UNSET:
            return is_validate_properties(key, value)
        return True


class GroupIdentifyEvent(BaseEvent):
    """A special event that update properties of particular groups.

    Args:
        user_id (str, optional): A user identifier. Required if device_id isn't present.
        device_id (str, optional): A device-specific identifier. Required if user_id isn't present.
        time (int, optional): The timestamp of the event in milliseconds since epoch.
        event_properties (dict, optional): Additional user defined event properties not included in event attributes.
        user_properties (dict, optional): Additional user properties tied to the user.
        groups (dict, optional): This feature is only available to Enterprise customers who have purchased the Accounts add-on.
            This field adds a dictionary of key-value pairs that represent groups of users to the event as an event-level group.
        group_properties (dict, optional): Additional group properties tied to the group.
        app_version (str, optional): The current version of your application.
        platform (str, optional): Platform of the device.
        os_name (str, optional): The name of the mobile operating system or browser that the user is using.
        os_version (str, optional): The version of the mobile operating system or browser the user is using.
        device_brand (str, optional): The device brand that the user is using.
        device_manufacturer (str, optional): The device manufacturer that the user is using.
        device_model (str, optional): The device model that the user is using.
        carrier (str, optional): The carrier that the user is using.
        country (str, optional): The current country of the user.
        region (str, optional): The current region of the user.
        city (str, optional): The current city of the user.
        dma (str, optional): The current Designated Market Area of the user.
        language (str, optional): The language set by the user.
        price (float, optional): The price of the item purchased.
        quantity (int, optional): The quantity of the item purchased.
        revenue (float, optional): revenue = price * quantity. If all 3 fields (price, quantity, revenue) present
            then (price * quantity) will be used as the revenue value.
        product_id (str, optional): An identifier for the item purchased.
        revenue_type (str, optional): The type of revenue for the item purchased.
        location_lat (float, optional): The current Latitude of the user.
        location_lng (float, optional): The current Longitude of the user.
        ip (str, optional): The IP address of the user.
        idfa (str, optional): (iOS) Identifier for Advertiser.
        idfv (str, optional): (iOS) Identifier for Advertiser.
        adid (str, optional): (Android) Google Play Services advertising ID
        android_id (str, optional): (Android) Android ID (not the advertising ID)
        event_id (int, optional):  An incrementing counter to distinguish events with the same user_id and timestamp
            from each other.
        session_id (int, optional): The start timestamp of the session in milliseconds.
        insert_id (str, optional): A unique identifier for the event. Events sent with the same insert_id and device_id
            we have already seen before within the past 7 days will be deduplicated.
        plan (Plan, optional): Tracking plan properties.
        partner_id (str, optional): The partner id.
        callback (callable, optional): Event level callback method. Triggered when event is sent or failed. Take three
            parameters: an event instance, an integer code of response status, an optional string message.
        identify_obj (Identify, optional): An Identify instance used to update the event's group_properties
    """

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
        """The constructor of GroupIdentifyEvent"""
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
    """A special event that update properties of particular user.

    Args:
        user_id (str, optional): A user identifier. Required if device_id isn't present.
        device_id (str, optional): A device-specific identifier. Required if user_id isn't present.
        time (int, optional): The timestamp of the event in milliseconds since epoch.
        event_properties (dict, optional): Additional user defined event properties not included in event attributes.
        user_properties (dict, optional): Additional user properties tied to the user.
        groups (dict, optional): This feature is only available to Enterprise customers who have purchased the Accounts add-on.
            This field adds a dictionary of key-value pairs that represent groups of users to the event as an event-level group.
        group_properties (dict, optional): Additional group properties tied to the group.
        app_version (str, optional): The current version of your application.
        platform (str, optional): Platform of the device.
        os_name (str, optional): The name of the mobile operating system or browser that the user is using.
        os_version (str, optional): The version of the mobile operating system or browser the user is using.
        device_brand (str, optional): The device brand that the user is using.
        device_manufacturer (str, optional): The device manufacturer that the user is using.
        device_model (str, optional): The device model that the user is using.
        carrier (str, optional): The carrier that the user is using.
        country (str, optional): The current country of the user.
        region (str, optional): The current region of the user.
        city (str, optional): The current city of the user.
        dma (str, optional): The current Designated Market Area of the user.
        language (str, optional): The language set by the user.
        price (float, optional): The price of the item purchased.
        quantity (int, optional): The quantity of the item purchased.
        revenue (float, optional): revenue = price * quantity. If all 3 fields (price, quantity, revenue) present
            then (price * quantity) will be used as the revenue value.
        product_id (str, optional): An identifier for the item purchased.
        revenue_type (str, optional): The type of revenue for the item purchased.
        location_lat (float, optional): The current Latitude of the user.
        location_lng (float, optional): The current Longitude of the user.
        ip (str, optional): The IP address of the user.
        idfa (str, optional): (iOS) Identifier for Advertiser.
        idfv (str, optional): (iOS) Identifier for Advertiser.
        adid (str, optional): (Android) Google Play Services advertising ID
        android_id (str, optional): (Android) Android ID (not the advertising ID)
        event_id (int, optional):  An incrementing counter to distinguish events with the same user_id and timestamp
            from each other.
        session_id (int, optional): The start timestamp of the session in milliseconds.
        insert_id (str, optional): A unique identifier for the event. Events sent with the same insert_id and device_id
            we have already seen before within the past 7 days will be deduplicated.
        plan (Plan, optional): Tracking plan properties.
        partner_id (str, optional): The partner id.
        callback (callable, optional): Event level callback method. Triggered when event is sent or failed. Take three
            parameters: an event instance, an integer code of response status, an optional string message.
        identify_obj (Identify, optional): An Identify instance used to update the event's user_properties
    """

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
    """A class that help generate revenue event with special event type and revenue information like price,
        quantity, product id, receipt etc.

    Args:
        price (float): The price of the item purchased.
        quantity(int): The quantity of the item purchased. Default to 1.
        product_id (str, optional): An identifier for the item purchased.
        revenue_type (str, optional): The type of revenue for the item purchased.
        receipt (str, optional): The receipt number of the order.
        receipt_sig (str, optional): The receipt signature of the order.
        properties (dict, optional): Additional event properties included in the revenue event.
        revenue (float, optional): Total revenue of the order. If price and quantity are present,
            (price * quantity) will be used as revenue number.

    Methods:
        set_receipt(receipt, receipt_signature): Set the receipt and signature
        is_valid(): Check if a revenue instance is a valid one
        to_revenue_event(): Create and return a RevenueEvent instance
        get_event_properties(): Return a dictionary of revenue instance data used as event_properties of RevenueEvent
    """

    def __init__(self, price: float,
                 quantity: int = 1,
                 product_id: Optional[str] = None,
                 revenue_type: Optional[str] = None,
                 receipt: Optional[str] = None,
                 receipt_sig: Optional[str] = None,
                 properties: Optional[dict] = None,
                 revenue: Optional[float] = None):
        """The constructor of the Revenue class"""
        self.price: float = price
        self.quantity: int = quantity
        self.product_id: Optional[str] = product_id
        self.revenue_type: Optional[str] = revenue_type
        self.receipt: Optional[str] = receipt
        self.receipt_sig: Optional[str] = receipt_sig
        self.properties: Optional[dict] = properties
        self.revenue: Optional[float] = revenue

    def set_receipt(self, receipt: str, receipt_signature: str):
        """Set the receipt and signature

        Args:
            receipt (str): The receipt identifier
            receipt_signature (str): The receipt signature

        Returns:
            the Revenue instance itself
        """
        self.receipt = receipt
        self.receipt_sig = receipt_signature
        return self

    def is_valid(self):
        """Check if a revenue instance has a valid float price and a positive integer quantity.

        Returns:
            True if the revenue instance is valid, False otherwise
        """
        return isinstance(self.price, float) & isinstance(self.quantity, int) and self.quantity > 0

    def to_revenue_event(self):
        """Create and return a RevenueEvent instance, set revenue information as event_properties.

        Returns:
          A RevenueEvent object
        """
        return RevenueEvent(event_properties=self.get_event_properties())

    def get_event_properties(self):
        """Return a dictionary of revenue instance data used as event_properties of RevenueEvent

        Returns:
          A dict object
        """
        event_properties = {}
        if self.properties:
            event_properties = copy.deepcopy(self.properties)
        event_properties.update({constants.REVENUE_PRODUCT_ID: self.product_id,
                                 constants.REVENUE_QUANTITY: self.quantity,
                                 constants.REVENUE_PRICE: self.price,
                                 constants.REVENUE_TYPE: self.revenue_type,
                                 constants.REVENUE_RECEIPT: self.receipt,
                                 constants.REVENUE_RECEIPT_SIG: self.receipt_sig,
                                 constants.REVENUE: self.revenue})
        return {key: value for key, value in event_properties.items() if value is not None}


class RevenueEvent(BaseEvent):
    """A special event that record/verify revenue information.

    Args:
        user_id (str, optional): A user identifier. Required if device_id isn't present.
        device_id (str, optional): A device-specific identifier. Required if user_id isn't present.
        time (int, optional): The timestamp of the event in milliseconds since epoch.
        event_properties (dict, optional): Additional user defined event properties not included in event attributes.
        user_properties (dict, optional): Additional user properties tied to the user.
        groups (dict, optional): This feature is only available to Enterprise customers who have purchased the Accounts add-on.
            This field adds a dictionary of key-value pairs that represent groups of users to the event as an event-level group.
        group_properties (dict, optional): Additional group properties tied to the group.
        app_version (str, optional): The current version of your application.
        platform (str, optional): Platform of the device.
        os_name (str, optional): The name of the mobile operating system or browser that the user is using.
        os_version (str, optional): The version of the mobile operating system or browser the user is using.
        device_brand (str, optional): The device brand that the user is using.
        device_manufacturer (str, optional): The device manufacturer that the user is using.
        device_model (str, optional): The device model that the user is using.
        carrier (str, optional): The carrier that the user is using.
        country (str, optional): The current country of the user.
        region (str, optional): The current region of the user.
        city (str, optional): The current city of the user.
        dma (str, optional): The current Designated Market Area of the user.
        language (str, optional): The language set by the user.
        price (float, optional): The price of the item purchased.
        quantity (int, optional): The quantity of the item purchased.
        revenue (float, optional): revenue = price * quantity. If all 3 fields (price, quantity, revenue) present
            then (price * quantity) will be used as the revenue value.
        product_id (str, optional): An identifier for the item purchased.
        revenue_type (str, optional): The type of revenue for the item purchased.
        location_lat (float, optional): The current Latitude of the user.
        location_lng (float, optional): The current Longitude of the user.
        ip (str, optional): The IP address of the user.
        idfa (str, optional): (iOS) Identifier for Advertiser.
        idfv (str, optional): (iOS) Identifier for Advertiser.
        adid (str, optional): (Android) Google Play Services advertising ID
        android_id (str, optional): (Android) Android ID (not the advertising ID)
        event_id (int, optional):  An incrementing counter to distinguish events with the same user_id and timestamp
            from each other.
        session_id (int, optional): The start timestamp of the session in milliseconds.
        insert_id (str, optional): A unique identifier for the event. Events sent with the same insert_id and device_id
            we have already seen before within the past 7 days will be deduplicated.
        plan (Plan, optional): Tracking plan properties.
        partner_id (str, optional): The partner id.
        callback (callable, optional): Event level callback method. Triggered when event is sent or failed. Take three
            parameters: an event instance, an integer code of response status, an optional string message.
        revenue_obj (Revenue, optional): An Revenue instance used to update the event's event_properties
    """

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
        """The constructor of RevenueEvent class"""
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
    """ Check if the key-value pair is a valid property

    Args:
        key: The property key
        value: The property value

    Returns:
         True if inputs are valid key-value pair, False otherwise.
    """
    if not isinstance(key, str):
        return False
    if isinstance(value, list):
        result = True
        for element in value:
            if isinstance(element, list):
                return False
            if isinstance(element, dict):
                result = result and is_validate_object(element)
            elif not isinstance(element, (float, int, str)):
                result = False
            if not result:
                break
        return result
    if isinstance(value, dict):
        return is_validate_object(value)
    if not isinstance(value, (bool, float, int, str, enum.Enum)):
        return False
    return True


def is_validate_object(obj):
    """Check if a dictionary object is a valid property value

    Args:
        obj: The object to be checked

    Returns:
        True if obj is a valid property value, False otherwise.
    """
    for key, value in obj.items():
        if not is_validate_properties(key, value):
            return False
    return True
