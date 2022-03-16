from typing import Optional, Callable

from amplitude.config import Config
from amplitude.event import Revenue, BaseEvent, Identify, IdentifyEvent, GroupIdentifyEvent, Plan
from amplitude.plugin import AmplitudeDestinationPlugin
from amplitude.timeline import Timeline


class Amplitude:

    def __init__(self, api_key: Optional[str] = None, configuration=Config()):
        self.configuration = configuration
        self.configuration.api_key = api_key
        self.__timeline = Timeline(configuration)
        amplitude_destination = AmplitudeDestinationPlugin()
        self.add(amplitude_destination)

    def track(self, event: BaseEvent):
        self.__timeline.process(event)

    def identify(self, identify_obj: Identify, user_id: Optional[str] = None,
                 device_id: Optional[str] = None,
                 time: Optional[int] = None,
                 event_properties: Optional[dict] = None,
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
                 callback: Optional[Callable[[BaseEvent, int, Optional[str]], None]] = None):
        if not identify_obj.is_valid():
            self.configuration.logger.error("Empty identify properties")
        else:
            event = IdentifyEvent(user_id,
                                  device_id,
                                  time,
                                  event_properties,
                                  identify_obj.user_properties,
                                  None,
                                  None,
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
            self.track(event)

    def group_identify(self, group_type: str, group_name: str, identify_obj: Identify,
                       user_id: Optional[str] = None,
                       device_id: Optional[str] = None,
                       time: Optional[int] = None,
                       event_properties: Optional[dict] = None,
                       user_properties: Optional[dict] = None,
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
                       callback: Optional[Callable[[BaseEvent, int, Optional[str]], None]] = None
                       ):
        if not identify_obj.is_valid():
            self.configuration.logger.error("Empty group identify properties")
        else:
            event = GroupIdentifyEvent(user_id,
                                       device_id,
                                       time,
                                       event_properties,
                                       user_properties,
                                       {group_type: group_name},
                                       identify_obj.user_properties,
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
            self.track(event)

    def revenue(self, revenue_obj: Revenue, user_id: Optional[str] = None,
                device_id: Optional[str] = None,
                time: Optional[int] = None,
                user_properties: Optional[dict] = None,
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
                callback: Optional[Callable[[BaseEvent, int, Optional[str]], None]] = None):
        if not revenue_obj.is_valid():
            self.configuration.logger.error("Missing price for revenue event")
        else:
            event = revenue_obj.to_revenue_event()
            event["user_id"] = user_id
            event["device_id"] = device_id
            event["time"] = time
            event["app_version"] = app_version
            event["platform"] = platform
            event["os_name"] = os_name
            event["os_version"] = os_version
            event["device_brand"] = device_brand
            event["device_manufacturer"] = device_manufacturer
            event["device_model"] = device_model
            event["carrier"] = carrier
            event["country"] = country
            event["region"] = region
            event["city"] = city
            event["dma"] = dma
            event["language"] = language
            event["price"] = price
            event["quantity"] = quantity
            event["revenue"] = revenue
            event["product_id"] = product_id
            event["revenue_type"] = revenue_type
            event["location_lat"] = location_lat
            event["location_lng"] = location_lng
            event["ip"] = ip
            event["idfa"] = idfa
            event["idfv"] = idfv
            event["adid"] = adid
            event["android_id"] = android_id
            event["event_id"] = event_id
            event["session_id"] = session_id
            event["insert_id"] = insert_id
            event["plan"] = plan
            event["user_properties"] = user_properties
            event.event_callback = callback
            self.track(event)

    def flush(self):
        self.__timeline.flush()

    def add(self, plugin):
        self.__timeline.add(plugin)
        plugin.setup(self)
        return self

    def remove(self, plugin):
        self.__timeline.remove(plugin)
        return self
