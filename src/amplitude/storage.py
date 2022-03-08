import abc
import threading
from typing import List, Tuple

from amplitude.event import EventOptions
from amplitude import utils


class Storage(abc.ABC):

    @abc.abstractmethod
    def __init__(self):
        pass

    @abc.abstractmethod
    def push(self, event: EventOptions) -> None:
        pass

    @abc.abstractmethod
    def pull(self, batch_size: int) -> List[EventOptions]:
        pass

    @abc.abstractmethod
    def pull_all(self) -> List[EventOptions]:
        pass


class InMemoryStorage(Storage):
    def __init__(self, max_capacity, retry_delay):
        self.max_capacity: int = max_capacity
        self.total_events: int = 0
        self.new_events: int = 0
        self.retry_events: int = 0
        self.retry_delay: List[int] = retry_delay
        self.max_retry: int = len(retry_delay)
        self.buffer_data: List[Tuple[int, EventOptions]] = []
        self.buffer_lock = threading.Lock()
        self.amplitude_client = None

    def push(self, event: EventOptions, delay: int = 0) -> None:
        if (self.total_events > self.max_capacity and event.retry) or \
                (event.retry >= self.max_retry):
            if self.amplitude_client:
                self.amplitude_client.callback(event)
            return
        time_stamp = delay + self.get_retry_delay(event.retry) + utils.current_milliseconds()
        self._insert_event(time_stamp, event)

    def pull(self, batch_size: int) -> List[EventOptions]:
        result = []
        current_time = utils.current_milliseconds()
        with self.buffer_lock:
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

    def pull_all(self) -> List[EventOptions]:
        with self.buffer_lock:
            self.total_events = 0
            self.new_events = 0
            self.retry_events = 0
            result = [element[1] for element in self.buffer_data]
            self.buffer_data = []
            return result

    def _insert_event(self, time_stamp: int, event: EventOptions):
        with self.buffer_lock:
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
