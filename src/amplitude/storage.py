import abc
from threading import Condition
from typing import List, Tuple, Optional

from amplitude.event import BaseEvent
from amplitude import utils


class Storage(abc.ABC):

    @abc.abstractmethod
    def __init__(self):
        pass

    @abc.abstractmethod
    def push(self, event: BaseEvent) -> None:
        pass

    @abc.abstractmethod
    def pull(self, batch_size: int) -> List[BaseEvent]:
        pass

    @abc.abstractmethod
    def pull_all(self) -> List[BaseEvent]:
        pass


class StorageProvider(abc.ABC):

    @abc.abstractmethod
    def get_storage(self) -> Storage:
        pass


class InMemoryStorage(Storage):
    def __init__(self):
        self.total_events: int = 0
        self.new_events: int = 0
        self.retry_events: int = 0
        self.buffer_data: List[Tuple[int, BaseEvent]] = []
        self.buffer_lock_cv = Condition()
        self.configuration = None

    @property
    def lock(self):
        return self.buffer_lock_cv

    @property
    def max_retry(self) -> int:
        return max(1, len(self.configuration.retry_timeouts))

    @property
    def first_timestamp(self) -> int:
        if self.buffer_data:
            return self.buffer_data[0][0]
        return utils.current_milliseconds()

    def setup(self, configuration):
        self.configuration = configuration

    def push(self, event: BaseEvent, delay: int = 0) -> Tuple[bool, Optional[str]]:
        if event.retry and self.total_events > self.configuration.buffer_capacity:
            return False, "Destination buffer full. Retry temporarily disabled"
        if event.retry >= self.max_retry:
            return False, f"Event reached max retry times {self.max_retry}."
        time_stamp = delay + self._get_retry_delay(event.retry) + utils.current_milliseconds()
        self._insert_event(time_stamp, event)
        return True, None

    def pull(self, batch_size: int) -> List[BaseEvent]:
        result = []
        current_time = utils.current_milliseconds()
        with self.lock:
            index = 0
            new_count, retry_count = 0, 0
            while index < self.total_events and index < batch_size and current_time > self.buffer_data[index][0]:
                event = self.buffer_data[index][1]
                if event.retry:
                    retry_count += 1
                else:
                    new_count += 1
                result.append(event)
                index += 1
            self.buffer_data = self.buffer_data[index:]
            self.total_events -= index
            self.new_events -= new_count
            self.retry_events -= retry_count
        return result

    def pull_all(self) -> List[BaseEvent]:
        with self.lock:
            self.total_events = 0
            self.new_events = 0
            self.retry_events = 0
            result = [element[1] for element in self.buffer_data]
            self.buffer_data = []
            return result

    def _insert_event(self, time_stamp: int, event: BaseEvent):
        with self.lock:
            left, right = 0, len(self.buffer_data) - 1
            while left < right:
                mid = (left + right) // 2
                if self.buffer_data[mid][0] > time_stamp:
                    right = mid - 1
                else:
                    left = mid + 1
            self.buffer_data.insert(left, (time_stamp, event))
            self.total_events += 1
            if event.retry:
                self.retry_events += 1
            else:
                self.new_events += 1
            if self.total_events >= self.configuration.flush_queue_size:
                self.lock.notify()

    def _get_retry_delay(self, retry: int) -> int:
        retry_delay = self.configuration.retry_timeouts
        if retry >= len(retry_delay):
            return retry_delay[-1]
        if retry < 0:
            return retry_delay[0]
        return retry_delay[retry]


class InMemoryStorageProvider(StorageProvider):

    def get_storage(self) -> InMemoryStorage:
        return InMemoryStorage()
