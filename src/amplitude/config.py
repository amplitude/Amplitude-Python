import logging
from typing import Optional, Callable

from amplitude import constants
from amplitude.event import BaseEvent
from amplitude.storage import InMemoryStorageProvider, StorageProvider, Storage


class Config:

    def __init__(self, api_key: str = None,
                 flush_queue_size: int = constants.FLUSH_QUEUE_SIZE,
                 flush_interval_millis: int = constants.FLUSH_INTERVAL_MILLIS,
                 flush_max_retries: int = constants.FLUSH_MAX_RETRIES,
                 logger=logging.getLogger(constants.LOGGER_NAME),
                 min_id_length: Optional[int] = None,
                 callback: Optional[Callable[[BaseEvent, int, Optional[str]], None]] = None,
                 server_zone: str = constants.DEFAULT_ZONE,
                 use_batch: bool = False,
                 server_url: Optional[str] = None,
                 storage_provider: StorageProvider = InMemoryStorageProvider()):
        self.api_key = api_key
        self._flush_queue_size: int = flush_queue_size
        self._flush_size_divider: int = 1
        self.flush_interval_millis: int = flush_interval_millis
        self.flush_max_retries: int = flush_max_retries
        self.logger = logger
        self.min_id_length: Optional[int] = min_id_length
        self.callback: Optional[Callable[[BaseEvent, int, Optional[str]], None]] = callback
        self.server_zone: str = server_zone
        self.use_batch: bool = use_batch
        self._url: Optional[str] = server_url
        self.storage_provider: StorageProvider = storage_provider
        self.opt_out = False

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

    def increase_flush_divider(self):
        self._flush_size_divider += 1

    def reset_flush_divider(self):
        self._flush_size_divider = 1

    @property
    def flush_queue_size(self):
        return max(1, self._flush_queue_size // self._flush_size_divider)

    @flush_queue_size.setter
    def flush_queue_size(self, size: int):
        self._flush_queue_size = size
        self._flush_size_divider = 1

    @property
    def server_url(self):
        if self._url:
            return self._url
        return constants.SERVER_URL[self.server_zone][constants.BATCH if self.use_batch else constants.HTTP_V2]

    @server_url.setter
    def server_url(self, url: str):
        self._url = url

    @property
    def options(self):
        if self.is_min_id_length_valid():
            return {"min_id_length": self.min_id_length}
        return None
