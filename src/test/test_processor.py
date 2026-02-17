import unittest
from unittest.mock import MagicMock

from amplitude import Config, BaseEvent
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


if __name__ == '__main__':
    unittest.main()
