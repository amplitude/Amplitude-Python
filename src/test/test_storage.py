import time
import unittest
import random
from threading import Thread
from unittest.mock import MagicMock

import amplitude.utils
from amplitude.storage import InMemoryStorageProvider
from amplitude import constants, Config, BaseEvent
from amplitude.worker import Workers


class AmplitudeStorageTestCase(unittest.TestCase):

    def setUp(self) -> None:
        self.provider = InMemoryStorageProvider()
        self.storage = self.provider.get_storage()
        worker = Workers()
        self.storage.setup(Config(), worker)

    def test_storage_empty_in_memory_storage_pull_return_empty_list(self):
        self.assertEqual(0, self.storage.total_events)
        self.assertEqual([], self.storage.pull(20))

    def test_storage_empty_in_memory_storage_pull_all_return_empty_list(self):
        self.assertEqual(0, self.storage.total_events)
        self.assertEqual([], self.storage.pull_all())

    def test_storage_empty_in_memory_storage_wait_time_return_flush_interval(self):
        self.assertEqual(0, self.storage.total_events)
        self.assertEqual(constants.FLUSH_INTERVAL_MILLIS, self.storage.wait_time)

    def test_storage_in_memory_storage_push_new_event_success(self):
        self.storage.workers.start = MagicMock()
        event_list = []
        for i in range(50):
            event = BaseEvent("test_event_" + str(i), user_id="test_user")
            self.storage.push(event)
            event_list.append(event)
        self.assertEqual(50, self.storage.total_events)
        self.assertEqual(event_list, self.storage.ready_queue)
        self.assertEqual(event_list[:30], self.storage.pull(30))
        self.assertEqual(20, self.storage.total_events)
        self.assertEqual(event_list[30:], self.storage.pull_all())
        self.assertEqual(50, self.storage.workers.start.call_count)
        self.assertEqual(0, self.storage.total_events)

    def test_storage_im_memory_storage_push_events_with_delay_success(self):
        event_set = set()
        self.storage.workers.start = MagicMock()
        self.push_event(self.storage, event_set, 50)
        self.assertEqual(50, self.storage.total_events)
        self.assertEqual(50, len(self.storage.ready_queue) + len(self.storage.buffer_data))
        self.assertEqual(event_set, set(self.storage.pull_all()))
        self.assertEqual(50, self.storage.workers.start.call_count)

    def test_storage_in_memory_storage_multithreading_push_event_success(self):
        event_set = set()
        self.storage.workers.start = MagicMock()
        threads = []
        for _ in range(50):
            t = Thread(target=self.push_event, args=(self.storage, event_set, 100))
            t.start()
            threads.append(t)
        for t in threads:
            t.join()
        self.assertEqual(5000, self.storage.workers.start.call_count)
        self.assertEqual(5000, self.storage.total_events)
        self.assertEqual(5000, len(self.storage.ready_queue) + len(self.storage.buffer_data))
        self.assertEqual(event_set, set(self.storage.pull_all()))

    def test_storage_in_memory_storage_push_retry_event_exceed_max_capacity_failed(self):
        self.storage.workers.start = MagicMock()
        self.push_event(self.storage, set(), constants.MAX_BUFFER_CAPACITY)
        self.assertEqual(constants.MAX_BUFFER_CAPACITY, self.storage.total_events)
        event = BaseEvent("test_event", "test_user")
        event.retry += 1
        self.storage.workers.start.reset_mock()
        is_success, message = self.storage.push(event)
        self.assertFalse(is_success)
        self.assertEqual("Destination buffer full. Retry temporarily disabled", message)
        self.assertEqual(constants.MAX_BUFFER_CAPACITY, self.storage.total_events)
        self.storage.workers.start.assert_not_called()

    def test_storage_in_memory_storage_push_event_exceed_max_retry_failed(self):
        self.storage.workers.start = MagicMock()
        event = BaseEvent("test_event", "test_user")
        event.retry = self.storage.max_retry
        is_success, message = self.storage.push(event)
        self.assertFalse(is_success)
        self.assertEqual(f"Event reached max retry times {self.storage.max_retry}.", message)
        self.assertEqual(0, self.storage.total_events)
        self.storage.workers.start.assert_not_called()

    def test_storage_in_memory_storage_wait_time_events_in_ready_queue_zero(self):
        self.storage.workers.start = MagicMock()
        self.storage.push(BaseEvent("test_event", "test_user"))
        self.assertEqual(0, self.storage.wait_time)

    def test_storage_in_memory_storage_wait_time_event_in_buffer_flush_interval_maximum(self):
        self.storage.workers.start = MagicMock()
        self.storage.push(BaseEvent("test_event", "test_user"), 200)
        self.assertTrue(0 < self.storage.wait_time <= 200)
        self.storage.pull_all()
        self.storage.push(BaseEvent("test_event", "test_user"), constants.FLUSH_INTERVAL_MILLIS + 500)
        self.assertTrue(constants.FLUSH_INTERVAL_MILLIS >= self.storage.wait_time)

    def test_storage_in_memory_storage_retry_event_verify_retry_delay_success(self):
        self.storage.workers.start = MagicMock()
        expect_delay = [0, 100, 100, 200, 200, 400, 400, 800, 800, 1600, 1600, 3200, 3200]
        for retry, delay in enumerate(expect_delay):
            event = BaseEvent("test_event", "test_user")
            event.retry = retry
            self.assertEqual(delay, self.storage._get_retry_delay(event.retry))

    def test_storage_pull_events_from_ready_queue_and_buffer_data_success(self):
        self.storage.workers.start = MagicMock()
        self.push_event(self.storage, set(), 200)
        first_event_in_buffer_data = self.storage.buffer_data[0][1]
        # wait 100 ms - max delay of push_event()
        time.sleep(0.1)
        events = self.storage.pull(len(self.storage.ready_queue) + 1)
        self.assertEqual(first_event_in_buffer_data, events[-1])
        self.assertEqual(200 - len(events), self.storage.total_events)
        self.assertEqual(self.storage.total_events, len(self.storage.buffer_data))

    @staticmethod
    def push_event(storage, event_set, count):
        for i in range(count):
            event = BaseEvent("test_event_" + str(i), user_id="test_user")
            storage.push(event, random.randint(0, 100))
            event_set.add(event)


if __name__ == '__main__':
    unittest.main()
