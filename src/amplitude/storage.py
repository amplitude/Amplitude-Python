import abc
from threading import Condition
from typing import List, Tuple, Optional

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
    def get_storage(self) -> Storage:
        pass


class InMemoryStorage(Storage):
    def __init__(self):
        self.total_events: int = 0
        self.buffer_data: List[Tuple[int, BaseEvent]] = []
        self.ready_queue: List[BaseEvent] = []
        self.buffer_lock_cv = Condition()
        self.configuration = None
        self.workers = None

    @property
    def lock(self):
        return self.buffer_lock_cv

    @property
    def max_retry(self) -> int:
        return self.configuration.flush_max_retries

    @property
    def wait_time(self) -> int:
        if self.ready_queue:
            return 0
        if self.buffer_data:
            return min(self.buffer_data[0][0] - utils.current_milliseconds(), self.configuration.flush_interval_millis)
        return self.configuration.flush_interval_millis

    def setup(self, configuration, workers):
        self.configuration = configuration
        self.workers = workers

    def push(self, event: BaseEvent, delay: int = 0) -> Tuple[bool, Optional[str]]:
        if event.retry and self.total_events >= constants.MAX_BUFFER_CAPACITY:
            return False, "Destination buffer full. Retry temporarily disabled"
        if event.retry >= self.max_retry:
            return False, f"Event reached max retry times {self.max_retry}."
        total_delay = delay + self._get_retry_delay(event.retry)
        self._insert_event(total_delay, event)
        self.workers.start()
        return True, None

    def pull(self, batch_size: int) -> List[BaseEvent]:
        current_time = utils.current_milliseconds()
        with self.lock:
            result = self.ready_queue[:batch_size]
            self.ready_queue = self.ready_queue[batch_size:]
            index = 0
            while index < len(self.buffer_data) and index < (batch_size - len(result)) and \
                    current_time >= self.buffer_data[index][0]:
                event = self.buffer_data[index][1]
                result.append(event)
                index += 1
            self.buffer_data = self.buffer_data[index:]
            self.total_events -= len(result)
        return result

    def pull_all(self) -> List[BaseEvent]:
        with self.lock:
            self.total_events = 0
            result = self.ready_queue + [element[1] for element in self.buffer_data]
            self.buffer_data = []
            self.ready_queue = []
            return result

    def _insert_event(self, total_delay: int, event: BaseEvent):
        current_time = utils.current_milliseconds()
        with self.lock:
            while self.buffer_data and self.buffer_data[0][0] <= current_time:
                self.ready_queue.append(self.buffer_data.pop(0)[1])
            if total_delay == 0:
                self.ready_queue.append(event)
            else:
                time_stamp = current_time + total_delay
                left, right = 0, len(self.buffer_data) - 1
                while left <= right:
                    mid = (left + right) // 2
                    if self.buffer_data[mid][0] > time_stamp:
                        right = mid - 1
                    else:
                        left = mid + 1
                self.buffer_data.insert(left, (time_stamp, event))
            self.total_events += 1
            if len(self.ready_queue) >= self.configuration.flush_queue_size:
                self.lock.notify()

    def _get_retry_delay(self, retry: int) -> int:
        if retry > self.configuration.flush_max_retries:
            return 3200
        if retry <= 0:
            return 0
        return 100 * (2 ** ((retry - 1) // 2))


class InMemoryStorageProvider(StorageProvider):

    def get_storage(self) -> InMemoryStorage:
        return InMemoryStorage()
