import unittest
from unittest.mock import MagicMock

from amplitude import Config, BaseEvent, EventLogLevel
from amplitude.http_client import Response, HttpStatus
from amplitude.processor import ResponseProcessor


class ResponseProcessorTestCase(unittest.TestCase):
    def test_process_response_with_unknown_status_retries_events(self):
        processor = ResponseProcessor()
        configuration = Config()
        configuration.callback = MagicMock()
        configuration.logger = MagicMock()
        storage = MagicMock()
        storage.push = MagicMock(return_value=(True, None))
        processor.setup(configuration, storage)

        event_callback = MagicMock()
        event = BaseEvent("test_event", "test_user", callback=event_callback)
        processor.process_response(Response(HttpStatus.UNKNOWN), [event])

        self.assertEqual(1, event.retry)
        storage.push.assert_called_once_with(event, delay=0)
        configuration.callback.assert_not_called()
        event_callback.assert_not_called()

    def _process_success(self, configuration):
        configuration.logger = MagicMock()
        processor = ResponseProcessor()
        processor.setup(configuration, MagicMock())
        event = BaseEvent("test_event", "test_user")
        processor.process_response(Response(HttpStatus.SUCCESS), [event])
        return event

    def test_log_event_at_info_level_by_default(self):
        configuration = Config()
        event = self._process_success(configuration)
        configuration.logger.info.assert_called_once_with(
            "Event sent successfully.", extra={'code': 200, 'event': event})
        configuration.logger.debug.assert_not_called()

    def test_log_event_at_debug_level(self):
        configuration = Config(event_log_level=EventLogLevel.DEBUG)
        event = self._process_success(configuration)
        configuration.logger.debug.assert_called_once_with(
            "Event sent successfully.", extra={'code': 200, 'event': event})
        configuration.logger.info.assert_not_called()

    def test_log_event_disabled(self):
        configuration = Config(event_log_level=EventLogLevel.NONE)
        self._process_success(configuration)
        configuration.logger.info.assert_not_called()
        configuration.logger.debug.assert_not_called()


if __name__ == '__main__':
    unittest.main()
