import time
import unittest
from collections import defaultdict
import random
from threading import Thread
from unittest.mock import MagicMock

from amplitude import Config, BaseEvent
from amplitude.storage import InMemoryStorage
from amplitude.worker import Workers
from amplitude.http_client import HttpClient, Response, HttpStatus


class AmplitudeWorkersTestCase(unittest.TestCase):

    def setUp(self) -> None:
        self.workers = Workers()
        self.workers.setup(Config(), InMemoryStorage())
        self.workers.storage.setup(self.workers.configuration, self.workers)
        self.events_dict = defaultdict(set)

        def callback_func(event, code, message=None):
            self.events_dict[code].add(event)

        self.workers.configuration.callback = callback_func

    def tearDown(self) -> None:
        with self.workers.storage.lock:
            self.workers.storage.lock.notify()

    def test_worker_initialize_setup_success(self):
        self.assertTrue(self.workers.is_active)
        self.assertFalse(self.workers.is_started)
        self.assertIsNotNone(self.workers.storage)
        self.assertIsNotNone(self.workers.configuration)
        self.assertIsNotNone(self.workers.threads_pool)
        self.assertIsNotNone(self.workers.consumer_lock)
        self.assertIsNotNone(self.workers.response_processor)

    def test_worker_stop_success(self):
        self.workers.storage.pull_all = MagicMock()
        self.workers.stop()
        self.assertFalse(self.workers.is_active)
        self.assertTrue(self.workers.is_started)
        self.workers.storage.pull_all.assert_called_once()

    def test_worker_get_payload_success(self):
        events = [BaseEvent("test_event1", "test_user"), BaseEvent("test_event2", "test_user")]
        self.workers.configuration.api_key = "TEST_API_KEY"
        expect_payload = b'{"api_key": "TEST_API_KEY", "events": [{"event_type": "test_event1", "user_id": ' \
                         b'"test_user"}, {"event_type": "test_event2", "user_id": "test_user"}]}'
        self.assertEqual(expect_payload, self.workers.get_payload(events))
        self.workers.configuration.min_id_length = 3
        expect_payload = b'{"api_key": "TEST_API_KEY", "events": [{"event_type": "test_event1", "user_id": ' \
                         b'"test_user"}, {"event_type": "test_event2", "user_id": "test_user"}], "options": {' \
                         b'"min_id_length": 3}}'
        self.assertEqual(expect_payload, self.workers.get_payload(events))

    def test_worker_consume_storage_events_success(self):
        success_response = Response(HttpStatus.SUCCESS)
        HttpClient.post = MagicMock()
        HttpClient.post.return_value = success_response
        self.workers.configuration.flush_interval_millis = 10
        for i in range(50):
            self.workers.storage.push(BaseEvent("test_event_" + str(i), "test_user"))
        time.sleep(self.workers.configuration.flush_interval_millis / 1000 + 1)
        self.assertEqual(50, len(self.events_dict[200]))
        HttpClient.post.assert_called()

    def test_worker_flush_events_in_storage_success(self):
        success_response = Response(HttpStatus.SUCCESS)
        HttpClient.post = MagicMock()
        HttpClient.post.return_value = success_response
        for i in range(50):
            self.workers.storage.push(BaseEvent("test_event_" + str(i), "test_user"))
        self.workers.flush()
        self.assertEqual(50, len(self.events_dict[200]))
        HttpClient.post.assert_called()

    def test_worker_send_events_with_success_response_trigger_callback(self):
        events = self.get_events_list(100)
        success_response = Response(HttpStatus.SUCCESS)
        HttpClient.post = MagicMock()
        HttpClient.post.return_value = success_response
        self.workers.send(events)
        self.assertEqual(self.events_dict[200], set(events))

    def test_worker_send_events_with_invalid_request_response_trigger_callback(self):
        events = self.get_events_list(100)
        success_response = Response(HttpStatus.SUCCESS)
        invalid_response = Response(HttpStatus.INVALID_REQUEST)
        invalid_response.body = {
            "code": 400,
            "error": "Test error",
            "events_with_invalid_fields": {
                "time": [0, 1, 2, 3, 4, 5]
            },
            "events_with_missing_fields": {
                "event_type": [5, 6, 7, 8, 9]
            },
            "events_with_invalid_id_lengths": {
                "user_id": [10, 11, 12],
                "device_id": [13, 14, 15]
            },
            "silenced_events": [16, 17, 18, 19]
        }
        HttpClient.post = MagicMock()
        HttpClient.post.side_effect = [invalid_response, success_response]
        self.workers.send(events)
        self.workers.flush()
        self.assertEqual(self.events_dict[200], set(events[20:]))
        for i in range(20, 100):
            self.assertEqual(1, events[i].retry)
        self.assertEqual(self.events_dict[400], set(events[:20]))
        self.assertEqual(2, HttpClient.post.call_count)

    def test_worker_send_events_with_invalid_response_missing_field_no_retry(self):
        events = self.get_events_list(100)
        invalid_response = Response(HttpStatus.INVALID_REQUEST)
        invalid_response.body = {
            "code": 400,
            "error": "Test error",
            "missing_field": "api_key"
        }
        HttpClient.post = MagicMock()
        HttpClient.post.return_value = invalid_response
        self.workers.send(events)
        self.assertEqual(100, len(self.events_dict[400]))
        for e in events:
            self.assertEqual(0, e.retry)

    def test_worker_send_events_with_invalid_response_raise_api_key_error_no_callback(self):
        events = self.get_events_list(100)
        invalid_response = Response(HttpStatus.INVALID_REQUEST)
        invalid_response.body = {
            "code": 400,
            "error": "Invalid API key: TEST_API_KEY"
        }
        HttpClient.post = MagicMock()
        HttpClient.post.return_value = invalid_response
        with self.assertLogs(None, "ERROR") as cm:
            self.workers.send(events)
            self.assertEqual(0, len(self.events_dict[400]))
            self.assertEqual(["ERROR:amplitude:Invalid API Key"], cm.output)

    def test_worker_send_events_with_payload_too_large_response_decrease_flush_queue_size(self):
        events = self.get_events_list(30)
        success_response = Response(HttpStatus.SUCCESS)
        payload_too_large_response = Response(HttpStatus.PAYLOAD_TOO_LARGE)
        HttpClient.post = MagicMock()
        HttpClient.post.side_effect = [payload_too_large_response, payload_too_large_response, success_response]
        self.workers.configuration.flush_queue_size = 30
        self.workers.send(events)
        self.assertEqual(15, self.workers.configuration.flush_queue_size)
        self.workers.flush()
        self.assertEqual(10, self.workers.configuration.flush_queue_size)
        self.workers.flush()
        self.assertEqual(30, len(self.events_dict[200]))

    def test_worker_send_events_with_timeout_and_failed_response_retry_all_events(self):
        events = self.get_events_list(100)
        success_response = Response(HttpStatus.SUCCESS)
        failed_response = Response(HttpStatus.FAILED)
        timeout_response = Response(HttpStatus.TIMEOUT)
        HttpClient.post = MagicMock()
        HttpClient.post.side_effect = [timeout_response, failed_response, success_response]
        self.workers.send(events)
        self.workers.flush()
        self.workers.flush()
        self.assertEqual(100, len(self.events_dict[200]))
        self.assertEqual(3, HttpClient.post.call_count)

    def test_worker_send_events_with_unknown_error_trigger_callback(self):
        unknown_error_response = Response(HttpStatus.UNKNOWN)
        HttpClient.post = MagicMock()
        HttpClient.post.return_value = unknown_error_response
        self.workers.send(self.get_events_list(100))
        self.assertEqual(100, len(self.events_dict[-1]))
        HttpClient.post.assert_called_once()
        self.workers.flush()
        HttpClient.post.assert_called_once()

    def test_worker_send_events_with_too_many_requests_response_callback_and_retry(self):
        success_response = Response(HttpStatus.SUCCESS)
        too_many_requests_response = Response(HttpStatus.TOO_MANY_REQUESTS, body={
            "code": 429,
            "error": "Too many requests for some devices and users",
            "eps_threshold": 10,
            "throttled_devices": {"test_throttled_device": 11},
            "throttled_users": {"test_throttled_user": 12},
            "exceeded_daily_quota_users": {"test_throttled_user2": 500200},
            "exceeded_daily_quota_devices": {"test_throttled_device2": 600200},
            "throttled_events": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
        })
        events = self.get_events_list(100)
        events[0].user_id = "test_throttled_user2"
        events[1].device_id = "test_throttled_device2"
        HttpClient.post = MagicMock()
        HttpClient.post.side_effect = [too_many_requests_response, success_response, success_response]
        self.workers.send(events)
        self.assertEqual(self.events_dict[429], set(events[:2]))
        i = -1
        while i > -15:
            self.assertEqual(events[16 + i], self.workers.storage.buffer_data[i][1])
            i -= 1
        self.workers.flush()
        self.assertEqual(self.events_dict[200], set(events[2:]))

    def test_worker_multithreading_with_random_response_success(self):
        success_response = Response(HttpStatus.SUCCESS)
        timeout_response = Response(HttpStatus.TIMEOUT)
        unknown_error_response = Response(HttpStatus.UNKNOWN)
        too_many_requests_response = Response(HttpStatus.TOO_MANY_REQUESTS, body={
            "code": 429,
            "error": "Too many requests for some devices and users",
            "eps_threshold": 10,
            "exceeded_daily_quota_users": {"test_user": 500200},
            "throttled_events": [0]
        })
        failed_response = Response(HttpStatus.FAILED)
        payload_too_large_response = Response(HttpStatus.PAYLOAD_TOO_LARGE)
        invalid_response = Response(HttpStatus.INVALID_REQUEST, body={
            "code": 400,
            "error": "Test error",
            "events_with_invalid_fields": {
                "time": [0]
            }
        })

        def dummy_post(url, payload, header=None):
            i = random.randint(0, 100)
            if i == 0:
                return timeout_response
            if i == 1:
                return unknown_error_response
            if i == 2:
                return too_many_requests_response
            if i == 3:
                return failed_response
            if i == 4:
                return payload_too_large_response
            if i == 5:
                return invalid_response
            return success_response

        HttpClient.post = dummy_post
        # Test multithreading with workers.send(events)
        with self.subTest():
            threads = []
            self.events_dict.clear()
            for _ in range(50):
                t = Thread(target=self.workers.send, args=(self.get_events_list(100),))
                threads.append(t)
                t.start()
            for t in threads:
                t.join()
            while self.workers.storage.total_events:
                time.sleep(0.01)
            total_events = sum([len(self.events_dict[s]) for s in self.events_dict])
            self.assertEqual(5000, total_events)
        # Test multithreading with storage.push(event)
        with self.subTest():
            threads = []
            self.events_dict.clear()
            for _ in range(50):
                t = Thread(target=self.push_event, args=(100,))
                threads.append(t)
                t.start()
            for t in threads:
                t.join()
            while self.workers.storage.total_events:
                time.sleep(0.01)
            total_events = sum([len(self.events_dict[s]) for s in self.events_dict])
            self.assertEqual(5000, total_events)

    def push_event(self, n):
        for event in self.get_events_list(n):
            self.workers.storage.push(event)

    @staticmethod
    def get_events_list(n):
        events = []
        for i in range(n):
            events.append(BaseEvent("test_event_" + str(i), "test_user"))
        return events


if __name__ == '__main__':
    unittest.main()
