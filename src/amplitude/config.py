import logging
from typing import Optional, Callable

from amplitude import constants
from amplitude.event import BaseEvent
from amplitude.storage import InMemoryStorageProvider, StorageProvider, Storage


class Config:

    def __init__(self):
        self.api_key = None
        self.storage_provider: StorageProvider = InMemoryStorageProvider()
        self.flush_queue_size: int = constants.FLUSH_SIZE
        self.flush_interval_millis: int = constants.FLUSH_INTERVAL_MILLIS
        self.flush_max_retries = 12
        self.logger = logging.getLogger(__name__)
        self.min_id_length: Optional[int] = None
        self.callback: Optional[Callable[[BaseEvent, int, Optional[str]], None]] = None
        self.server_zone: str = "US"
        self.use_batch: bool = False
        self.opt_out = False
        self._url: Optional[str] = None

    def get_storage(self) -> Storage:
        return self.storage_provider.get_storage()

    def is_valid(self) -> bool:
        if (not self.api_key) or (self.flush_queue_size <= 0) or (
                self.flush_interval_millis <= 0) or (not self.is_min_id_length_valid()):
            return False
        return True

    def is_min_id_length_valid(self) -> bool:
        if self.min_id_length is None or \
                (isinstance(self.min_id_length, int) and self.min_id_length > 0):
            return True
        return False

    @property
    def server_url(self):
        if self._url:
            return self._url
        if self.server_zone == constants.EU_ZONE:
            if self.use_batch:
                return constants.BATCH_API_URL_EU
            else:
                return constants.BATCH_API_URL
        else:
            if self.use_batch:
                return constants.HTTP_API_URL_EU
            else:
                return constants.HTTP_API_URL

    @server_url.setter
    def server_url(self, url):
        self._url = url

    @property
    def options(self):
        if self.is_min_id_length_valid():
            return {"min_id_length": self.min_id_length}
        return None
