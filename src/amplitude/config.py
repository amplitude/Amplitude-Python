import logging
from typing import Optional, Callable, List

from amplitude import constants
from amplitude.event import BaseEvent
from amplitude.storage import InMemoryStorageProvider, StorageProvider, Storage


class Config:

    def __init__(self):
        self.api_key = None
        self.storage_provider: StorageProvider = InMemoryStorageProvider()
        self.flush_queue_size: int = constants.FLUSH_SIZE
        self.flush_interval: float = constants.FLUSH_INTERVAL
        self.logger = logging.getLogger(__name__)
        self.min_id_length: Optional[int] = None
        self.callback: Optional[Callable[[BaseEvent, int, Optional[str]], None]] = None
        self.is_eu: bool = False
        self.is_batch_mode: bool = False
        self.timeout: float = constants.CONNECTION_TIMEOUT
        self._url: Optional[str] = None

    def get_storage(self) -> Storage:
        return self.storage_provider.get_storage()

    def is_valid(self) -> bool:
        if (not self.api_key) or (self.flush_queue_size <= 0) or (
                self.flush_interval <= 0) or (not self.is_min_id_length_valid()):
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
        if self.is_eu:
            if self.is_batch_mode:
                return constants.BATCH_API_URL_EU
            else:
                return constants.BATCH_API_URL
        else:
            if self.is_batch_mode:
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
