import abc
from threading import Condition
from typing import List, Tuple

from amplitude.event import BaseEvent
from amplitude import utils, constants


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
    def get_storage(self, destination) -> Storage:
        pass


class InMemoryStorage(Storage):
    def __init__(self, destination):
        self.total_events: int = 0
        self.new_events: int = 0
        self.retry_events: int = 0
        self.buffer_data: List[Tuple[int, BaseEvent]] = []
        self.buffer_lock_cv = Condition()
        self.destination = destination
        self.__amplitude_client = None

    @property
    def lock(self):
        return self.buffer_lock_cv

    @property
    def max_capacity(self) -> int:
        if self.__amplitude_client:
            return self.__amplitude_client.configuration.buffer_capacity
        return constants.MAX_BUFFER_CAPACITY

    @property
    def retry_delay(self) -> List[int]:
        if self.__amplitude_client:
            return self.__amplitude_client.configuration.retry_delay
        return constants.RETRY_DELAY[:]

    @property
    def max_retry(self) -> int:
        return len(self.retry_delay)

    def setup(self, client):
        self.__amplitude_client = client

    def push(self, event: BaseEvent, delay: int = 0, response=None) -> None:
        code = 0
        if response:
            code = response = code
        if event.retry and self.total_events > self.max_capacity:
            self.callback(event, code, "Destination buffer full. Retry temporarily disabled")
            return
        if event.retry >= self.max_retry:
            self.callback(event, code, f"Event reached max retry times {self.max_retry}.")
            return
        time_stamp = delay + self._get_retry_delay(event.retry) + utils.current_milliseconds()
        self._insert_event(time_stamp, event)

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

    def callback(self, event, code, message):
        if self.__amplitude_client:
            self.__amplitude_client.callback(event, code, message)
        else:
            event.callback(code, message)

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
            if self.total_events >= self.destination.batch_size:
                self.lock.notify()

    def _get_retry_delay(self, retry: int) -> int:
        retry_delay = self.retry_delay
        if retry >= len(retry_delay):
            return retry_delay[-1]
        if retry < 0:
            return retry_delay[0]
        return retry_delay[retry]


class InMemoryStorageProvider(StorageProvider):

    def get_storage(self, destination) -> InMemoryStorage:
        return InMemoryStorage(destination)
