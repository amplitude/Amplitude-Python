import logging
from typing import Optional, Callable, List

from amplitude import constants
from amplitude.storage import InMemoryStorageProvider, StorageProvider, Storage


class Config:

    def __init__(self):
        self.storage_provider: StorageProvider = InMemoryStorageProvider()
        self.batch_size: int = constants.BATCH_SIZE
        self.batch_interval: float = constants.BATCH_INTERVAL
        self.buffer_capacity: int = constants.MAX_BUFFER_CAPACITY
        self.retry_delay: List[int] = constants.RETRY_DELAY[:]
        self.api_url: str = constants.HTTP_API_URL
        self.batch_api_url: str = constants.BATCH_API_URL
        self.api_url_eu: str = constants.HTTP_API_URL_EU
        self.batch_api_url_eu: str = constants.BATCH_API_URL_EU
        self.logger = logging.getLogger(__name__)
        self.min_id_length: Optional[int] = None
        self.callback: Optional[Callable] = None
        self.is_eu: bool = False
        self.is_batch_mode: bool = False
        self.options = None
        self.timeout = constants.CONNECTION_TIMEOUT

    def get_storage(self, destination) -> Storage:
        return self.storage_provider.get_storage(destination)
