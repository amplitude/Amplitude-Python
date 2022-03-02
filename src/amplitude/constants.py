from typing import Dict, List, Type

HTTP_API_URL = "https://api2.amplitude.com/2/httpapi"
HTTP_API_URL_EU = "https://api.eu.amplitude.com/2/httpapi"
BATCH_API_URL = "https://api2.amplitude.com/batch"
BATCH_API_URL_EU = "https://api.eu.amplitude.com/batch"

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
    "plan": ["plan", dict],
    "group_properties": ["group_properties", dict]
}
PLAN_KEY_MAPPING = {
    "branch": ["branch", str],
    "source": ["source", str],
    "version": ["version", str]
}

IDENTIFY_EVENT = "$identify"
GROUP_IDENTIFY_EVENT = "$groupidentify"
AMP_REVENUE_EVENT = "revenue_amount"
MAX_PROPERTY_KEYS = 1024
MAX_STRING_LENGTH = 1024