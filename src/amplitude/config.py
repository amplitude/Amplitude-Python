"""Amplitude config module.

Classes:
    Config: Class that store configurations of Amplitude client
"""

import logging
from typing import Optional, Callable

from amplitude import constants
from amplitude.event import BaseEvent, Plan
from amplitude.storage import InMemoryStorageProvider, StorageProvider, Storage


class Config:
    """Amplitude client configuration class used to config client behavior

    Args:
        api_key (str): The API key of Amplitude project that events sent to. Required
        flush_queue_size (int, optional): The events buffered in memory will flush when exceed flush_queue_size.
            Must be positive.
        flush_interval_millis (int, optional): The events buffered in memory will wait no longer than
            flush_interval_millis. Must be positive.
        flush_max_retries (int, optional): The maximum retry attempts for an event when receiving error response.
        logger (optional): The logger used by Amplitude client. Default to logging.getLogger(constants.LOGGER_NAME).
        min_id_length (int, optional): The minimum length of user_id and device_id for events. Default to 5.
        callback (callable, optional): The client level callback function. Triggered on every events sent or failed.
            Take three parameters: an event instance, an integer code of response status, an optional string message.
        server_zone (str, optional): The server zone of project. Default to 'US'. Support 'EU'.
        use_batch(bool, optional): True to use batch API endpoint, False to use HTTP V2 API endpoint. Default to False.
        server_url (str, optional): API endpoint url. Default to None. Auto selected by configured server_zone
            and use_batch if set to None. Support customized url by setting string value.
        storage_provider (amplitude.storage.StorageProvider, optional): Default to InMemoryStorageProvider.
            Provide storage instance for events buffer.
        plan (amplitude.event.Plan, optional): Tracking plan information. Default to None.

    Properties:
        options: A dictionary contains minimum id length information. None if min_id_length not set.

    Methods:
        get_storage(): Return a Storage instance using configured StorageProvider.
        is_valid(): Return True if the Config instance is valid, False otherwise.
        is_min_id_length_valid(): Return True if min_id_length not set or set to positive integer, False otherwise.

    """

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
                 storage_provider: StorageProvider = InMemoryStorageProvider(),
                 plan: Plan = None):
        """The constructor of Config class"""
        self.api_key: str = api_key
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
        self.opt_out: bool = False
        self.plan: Plan = plan

    def get_storage(self) -> Storage:
        """Use configured StorageProvider to create a Storage instance then return.

        Returns:
            A Storage instance
        """
        return self.storage_provider.get_storage()

    def is_valid(self) -> bool:
        """Config instance is valid if api_key is set, flush_queue_size, flush_interval_millis are positive integer,
            min_id_length is valid.

        Returns:
            True if valid. False otherwise.
        """
        if (not self.api_key) or (self.flush_queue_size <= 0) or (
                self.flush_interval_millis <= 0) or (not self.is_min_id_length_valid()):
            return False
        return True

    def is_min_id_length_valid(self) -> bool:
        """min_id_length is valid when set to positive integer or None.

        Returns:
             True if valid. False otherwise.
        """
        if self.min_id_length is None or \
                (isinstance(self.min_id_length, int) and self.min_id_length > 0):
            return True
        return False

    def _increase_flush_divider(self):
        self._flush_size_divider += 1

    def _reset_flush_divider(self):
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
        if self.is_min_id_length_valid() and self.min_id_length:
            return {"min_id_length": self.min_id_length}
        return None
