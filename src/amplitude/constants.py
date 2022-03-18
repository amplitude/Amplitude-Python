from typing import Final

SDK_LIBRARY = "amplitude-python"
SDK_VERSION = "0.0.1"

EU_ZONE = "EU"
HTTP_API_URL: Final = "https://api2.amplitude.com/2/httpapi"
HTTP_API_URL_EU: Final = "https://api.eu.amplitude.com/2/httpapi"
BATCH_API_URL: Final = "https://api2.amplitude.com/batch"
BATCH_API_URL_EU: Final = "https://api.eu.amplitude.com/batch"

IDENTIFY_EVENT = "$identify"
GROUP_IDENTIFY_EVENT = "$groupidentify"
IDENTITY_OP_ADD = "$add"
IDENTITY_OP_APPEND = "$append"
IDENTITY_OP_CLEAR_ALL = "$clearAll"
IDENTITY_OP_PREPEND = "$prepend"
IDENTITY_OP_SET = "$set"
IDENTITY_OP_SET_ONCE = "$setOnce"
IDENTITY_OP_UNSET = "$unset"
IDENTITY_OP_PRE_INSERT = "$preInsert"
IDENTITY_OP_POST_INSERT = "$postInsert"
IDENTITY_OP_REMOVE = "$remove"
UNSET_VALUE = "-"

REVENUE_PRODUCT_ID = "$productId"
REVENUE_QUANTITY = "$quantity"
REVENUE_PRICE = "$price"
REVENUE_TYPE = "$revenueType"
REVENUE_RECEIPT = "$receipt"
REVENUE_RECEIPT_SIG = "$receiptSig"
REVENUE = "$revenue"
AMP_REVENUE_EVENT = "revenue_amount"

MAX_PROPERTY_KEYS = 1024
MAX_STRING_LENGTH = 1024
FLUSH_QUEUE_SIZE = 200
FLUSH_INTERVAL_MILLIS = 10000
FLUSH_MAX_RETRIES = 12
CONNECTION_TIMEOUT = 10.0  # seconds float
MAX_BUFFER_CAPACITY = 20000
