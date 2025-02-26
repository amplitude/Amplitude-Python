import logging
import time
import unittest
from unittest.mock import MagicMock

from amplitude import Amplitude, Config, BaseEvent, Identify, EventOptions, IdentifyEvent, GroupIdentifyEvent, \
    RevenueEvent, Revenue, EventPlugin, DestinationPlugin, PluginType
from amplitude.http_client import HttpClient, Response, HttpStatus


class AmplitudeClientTestCase(unittest.TestCase):

    def setUp(self) -> None:
        self.client = Amplitude(api_key="test api key",
                                configuration=Config(flush_queue_size=10, flush_interval_millis=500))

    def tearDown(self) -> None:
        self.client.shutdown()
    
    def test_amplitude_client_init_multiple_instance(self):
        #  test multiple instance inited with different API keys
        client1 = Amplitude(api_key="test api key 1")
        client2 = Amplitude(api_key="test api key 2")
        self.assertNotEqual(client1.configuration.api_key, client2.configuration.api_key)
        self.assertNotEqual(client1.configuration.storage_provider, client2.configuration.storage_provider)

    def test_amplitude_client_track_success(self):
        post_method = MagicMock()
        HttpClient.post = post_method
        res = Response(HttpStatus.SUCCESS)
        post_method.return_value = res
        events = []
        self.assertion_errors = []

        def callback_func(event, code, message=None):
            try:
                self.assertEqual(200, code)
                events.append(event.event_properties["id"])
                self.assertEqual('USD', event.currency)
            except AssertionError as e:
                self.assertion_errors.append(str(e))

        self.client.configuration.callback = callback_func
        for use_batch in (True, False):
            with self.subTest(use_batch=use_batch):
                post_method.reset_mock()
                events.clear()
                self.client.configuration.use_batch = use_batch
                for i in range(25):
                    self.client.track(BaseEvent("test_event", "test_user_id",
                                                event_properties={"id": i}, currency='USD'))
                for flush_future in self.client.flush():
                    if flush_future:
                        flush_future.result()
                self.assertEqual(25, len(events))
                post_method.assert_called()
                self.assertEqual(0, len(self.assertion_errors))

    def test_amplitude_client_track_invalid_api_key_log_error(self):
        post_method = MagicMock()
        HttpClient.post = post_method
        res = Response(HttpStatus.INVALID_REQUEST)
        res.body["error"] = "Invalid API key: " + self.client.configuration.api_key
        post_method.return_value = res
        for use_batch in (True, False):
            with self.subTest(use_batch=use_batch):
                post_method.reset_mock()
                self.client.configuration.use_batch = use_batch
                with self.assertLogs("test", "ERROR") as cm:
                    self.client.configuration.logger = logging.getLogger("test")
                    self.client.track(BaseEvent("test_event", "test_user_id"))
                    for flush_future in self.client.flush():
                        if flush_future:
                            flush_future.result()
                    post_method.assert_called_once()
                    self.assertEqual(["ERROR:test:Invalid API Key"], cm.output)

    def test_amplitude_client_track_invalid_response_then_success_response(self):
        post_method = MagicMock()
        HttpClient.post = post_method
        invalid_res = Response(HttpStatus.INVALID_REQUEST)
        invalid_res.body = {
            "code": 400,
            "error": "Invalid events",
            "events_with_invalid_fields": {
                "time": [1, 5, 8]
            },
            "events_with_missing_fields": {
                "event_type": [2, 5, 6]
            }
        }
        success_res = Response(HttpStatus.SUCCESS)
        events = []
        self.assertion_errors = []

        def callback_func(event, code, message=None):
            try:
                if event.event_properties["id"] in (1, 2, 5, 6, 8):
                    self.assertEqual(400, code)
                else:
                    self.assertEqual(200, code)
                events.append((event.event_properties["id"], event.retry))
            except AssertionError as e:
                self.assertion_errors.append(str(e))

        self.client.configuration.callback = callback_func
        for use_batch in (True, False):
            with self.subTest(use_batch=use_batch):
                post_method.reset_mock()
                post_method.side_effect = [invalid_res, success_res]
                events.clear()
                self.client.configuration.use_batch = use_batch
                for i in range(10):
                    self.client.track(BaseEvent("test_event", "test_user_id", event_properties={"id": i}))
                self.client.flush()
                while len(events) < 10:
                    time.sleep(0.1)
                self.assertEqual(2, post_method.call_count)
                self.assertEqual([(1, 0), (2, 0), (5, 0), (6, 0), (8, 0),
                                  (0, 1), (3, 1), (4, 1), (7, 1), (9, 1)], events)
                self.assertEqual(0, len(self.assertion_errors))

    def test_amplitude_client_identify_invalid_log_error_then_success(self):
        post_method = MagicMock()
        HttpClient.post = post_method
        res = Response(HttpStatus.SUCCESS)
        post_method.return_value = res
        self.assertion_errors = []

        def callback_func(event, code, message=None):
            try:
                self.assertEqual(200, code)
                self.assertTrue(isinstance(event, IdentifyEvent))
                self.assertTrue("user_properties" in event)
                self.assertEqual("$identify", event["event_type"])
                self.assertEqual("test_user_id", event["user_id"])
                self.assertEqual("test_device_id", event["device_id"])
            except AssertionError as e:
                self.assertion_errors.append(str(e))

        self.client.configuration.callback = callback_func
        for use_batch in (True, False):
            with self.subTest(use_batch=use_batch):
                post_method.reset_mock()
                self.client.configuration.use_batch = use_batch
                identify_obj = Identify()
                self.assertFalse(identify_obj.is_valid())
                with self.assertLogs("test", "ERROR") as cm:
                    self.client.configuration.logger = logging.getLogger("test")
                    self.client.identify(identify_obj,
                                         EventOptions(user_id="test_user_id", device_id="test_device_id"))
                    self.assertEqual(["ERROR:test:Empty identify properties"], cm.output)
                identify_obj.set("birth_date", "4-1-2022")
                self.assertTrue(identify_obj.is_valid())
                self.assertEqual({"$set": {"birth_date": "4-1-2022"}}, identify_obj.user_properties)
                self.client.identify(identify_obj, EventOptions(user_id="test_user_id", device_id="test_device_id"))
                for flush_future in self.client.flush():
                    if flush_future:
                        flush_future.result()
                post_method.assert_called_once()
                self.assertEqual(0, len(self.assertion_errors))

    def test_amplitude_client_group_identify_invalid_log_error_then_success(self):
        post_method = MagicMock()
        HttpClient.post = post_method
        res = Response(HttpStatus.SUCCESS)
        post_method.return_value = res
        self.assertion_errors = []

        def callback_func(event, code, message=None):
            try:
                self.assertEqual(200, code)
                self.assertTrue(isinstance(event, GroupIdentifyEvent))
                self.assertTrue("group_properties" in event)
                self.assertEqual("$groupidentify", event["event_type"])
                self.assertEqual("test_user_id", event["user_id"])
                self.assertEqual("test_device_id", event["device_id"])
                self.assertEqual({"Sports": "Football"}, event["groups"])
            except AssertionError as e:
                self.assertion_errors.append(str(e))

        self.client.configuration.callback = callback_func
        for use_batch in (True, False):
            with self.subTest(use_batch=use_batch):
                post_method.reset_mock()
                self.client.configuration.use_batch = use_batch
                identify_obj = Identify()
                self.assertFalse(identify_obj.is_valid())
                with self.assertLogs("test", "ERROR") as cm:
                    self.client.configuration.logger = logging.getLogger("test")
                    self.client.group_identify("Sports", "Football", identify_obj,
                                               EventOptions(user_id="test_user_id", device_id="test_device_id"))
                    self.assertEqual(["ERROR:test:Empty group identify properties"], cm.output)
                identify_obj.set("team_name", "Super Power")
                self.assertTrue(identify_obj.is_valid())
                self.assertEqual({"$set": {"team_name": "Super Power"}}, identify_obj.user_properties)
                self.client.group_identify("Sports", "Football", identify_obj,
                                           EventOptions(user_id="test_user_id", device_id="test_device_id"))
                for flush_future in self.client.flush():
                    if flush_future:
                        flush_future.result()
                post_method.assert_called_once()
                self.assertEqual(0, len(self.assertion_errors))

    def test_amplitude_set_group_success(self):
        post_method = MagicMock()
        HttpClient.post = post_method
        res = Response(HttpStatus.SUCCESS)
        post_method.return_value = res
        self.assertion_errors = []

        def callback_func(event, code, message=None):
            try:
                self.assertEqual(200, code)
                self.assertTrue(isinstance(event, IdentifyEvent))
                self.assertTrue("groups" in event)
                self.assertEqual("$identify", event["event_type"])
                self.assertEqual("test_user_id", event["user_id"])
                self.assertEqual("test_device_id", event["device_id"])
                self.assertEqual({"type": ["test_group", "test_group_2"]}, event.groups)
                self.assertEqual({"$set": {"type": ["test_group", "test_group_2"]}}, event.user_properties)
            except AssertionError as e:
                self.assertion_errors.append(str(e))

        self.client.configuration.callback = callback_func
        for use_batch in (True, False):
            with self.subTest(use_batch=use_batch):
                post_method.reset_mock()
                self.client.configuration.use_batch = use_batch
                self.client.set_group("type", ["test_group", "test_group_2"],
                                      EventOptions(user_id="test_user_id", device_id="test_device_id"))
                for flush_future in self.client.flush():
                    if flush_future:
                        flush_future.result()
                post_method.assert_called_once()
                self.assertEqual(0, len(self.assertion_errors))

    def test_amplitude_client_revenue_invalid_log_error_then_success(self):
        post_method = MagicMock()
        HttpClient.post = post_method
        res = Response(HttpStatus.SUCCESS)
        post_method.return_value = res
        self.assertion_errors = []

        def callback_func(event, code, message=None):
            try:
                self.assertEqual(200, code)
                self.assertTrue(isinstance(event, RevenueEvent))
                self.assertTrue("event_properties" in event)
                self.assertEqual("revenue_amount", event["event_type"])
                self.assertEqual("test_user_id", event["user_id"])
                self.assertEqual("test_device_id", event["device_id"])
                self.assertEqual({'$price': 60.2, '$productId': 'P63', '$quantity': 3, '$receipt': 'A0001',
                                  '$currency': 'USD', '$receiptSig': '0001A', 'other_property': 'test'},
                                 event["event_properties"])
            except AssertionError as e:
                self.assertion_errors.append(str(e))

        self.client.configuration.callback = callback_func
        for use_batch in (True, False):
            with self.subTest(use_batch=use_batch):
                post_method.reset_mock()
                self.client.configuration.use_batch = use_batch
                revenue_obj = Revenue(price="abc", quantity=3, product_id="P63", currency="USD", properties={"other_property": "test"})
                self.assertFalse(revenue_obj.is_valid())
                with self.assertLogs("test", "ERROR") as cm:
                    self.client.configuration.logger = logging.getLogger("test")
                    self.client.revenue(revenue_obj, EventOptions(user_id="test_user_id", device_id="test_device_id"))
                    self.assertEqual(["ERROR:test:Invalid price for revenue event"], cm.output)
                revenue_obj.price = 60.2
                self.assertTrue(revenue_obj.is_valid())
                revenue_obj.set_receipt("A0001", "0001A")
                self.client.revenue(revenue_obj, EventOptions(user_id="test_user_id", device_id="test_device_id"))
                for flush_future in self.client.flush():
                    if flush_future:
                        flush_future.result()
                post_method.assert_called_once()
                self.assertEqual(0, len(self.assertion_errors))

    def test_amplitude_client_flush_success(self):
        post_method = MagicMock()
        HttpClient.post = post_method
        res = Response(HttpStatus.SUCCESS)
        post_method.return_value = res
        self.assertion_errors = []

        def callback_func(event, code, message=None):
            try:
                self.assertEqual(200, code)
                self.assertEqual("flush_test", event["event_type"])
                self.assertEqual("test_user_id", event["user_id"])
                self.assertEqual("test_device_id", event["device_id"])
            except AssertionError as e:
                self.assertion_errors.append(str(e))

        self.client.configuration.callback = callback_func
        for use_batch in (True, False):
            with self.subTest(use_batch=use_batch):
                post_method.reset_mock()
                self.client.configuration.use_batch = use_batch
                self.client.track(BaseEvent(event_type="flush_test", user_id="test_user_id",
                                            device_id="test_device_id"))
                for flush_future in self.client.flush():
                    if flush_future:
                        flush_future.result()
                post_method.assert_called_once()
                for flush_future in self.client.flush():
                    if flush_future:
                        flush_future.result()
                post_method.assert_called_once()
                self.assertEqual(0, len(self.assertion_errors))

    def test_amplitude_add_remove_plugins_success(self):
        timeline = self.client._Amplitude__timeline
        before_plugin = EventPlugin(PluginType.BEFORE)
        enrich_plugin = EventPlugin(plugin_type=PluginType.ENRICHMENT)
        destination_plugin = DestinationPlugin()
        self.assertEqual(destination_plugin.plugin_type, PluginType.DESTINATION)
        self.assertEqual(1, len(timeline.plugins[PluginType.BEFORE]))
        self.client.add(before_plugin)
        self.assertEqual(2, len(timeline.plugins[PluginType.BEFORE]))
        self.assertEqual(timeline.plugins[PluginType.BEFORE][-1], before_plugin)
        self.assertEqual(0, len(timeline.plugins[PluginType.ENRICHMENT]))
        self.client.add(enrich_plugin)
        self.assertEqual(1, len(timeline.plugins[PluginType.ENRICHMENT]))
        self.assertEqual(timeline.plugins[PluginType.ENRICHMENT][-1], enrich_plugin)
        self.assertEqual(1, len(timeline.plugins[PluginType.DESTINATION]))
        self.client.add(destination_plugin)
        self.assertEqual(2, len(timeline.plugins[PluginType.DESTINATION]))
        self.assertEqual(timeline.plugins[PluginType.DESTINATION][-1], destination_plugin)
        self.client.remove(before_plugin)
        self.assertEqual(1, len(timeline.plugins[PluginType.BEFORE]))
        self.assertNotEqual(timeline.plugins[PluginType.BEFORE][-1], before_plugin)
        self.client.remove(enrich_plugin)
        self.assertEqual(0, len(timeline.plugins[PluginType.ENRICHMENT]))
        self.client.remove(destination_plugin)
        self.assertEqual(1, len(timeline.plugins[PluginType.DESTINATION]))
        self.assertNotEqual(timeline.plugins[PluginType.DESTINATION][-1], destination_plugin)


if __name__ == '__main__':
    unittest.main()
