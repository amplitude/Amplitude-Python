from amplitude.exception import InvalidAPIKeyError
from amplitude.http_client import HttpStatus


class ResponseProcessor:

    def __init__(self, worker):
        self.configuration = worker.configuration
        self.storage = worker.storage

    def process_response(self, res, events):
        if res.status == HttpStatus.SUCCESS:
            self.callback(events, res.code, "Event sent successful.")
        elif res.status == HttpStatus.TIMEOUT or res.status == HttpStatus.FAILED:
            self.push_to_storage(events, 0, res)
        elif res.status == HttpStatus.PAYLOAD_TOO_LARGE:
            self.configuration.flush_queue_size //= 2
            self.push_to_storage(events, 0, res)
        elif res.status == HttpStatus.INVALID_REQUEST:
            if res.error.startswith("Invalid API key:"):
                raise InvalidAPIKeyError(f"Invalid API key: {self.configuration.api_key}")
            if res.missing_field:
                self.callback(events, res.code, f"Request missing required field {res.missing_field}")
            else:
                invalid_set = set()
                events_for_retry = []
                if res.events_with_invalid_fields:
                    for field in res.events_with_invalid_fields:
                        events_for_callback = []
                        for index in res.events_with_invalid_fields[field]:
                            if index in invalid_set:
                                continue
                            invalid_set.add(index)
                            events_for_callback.append(events[index])
                        message = f"Invalid field {field}"
                        self.callback(events_for_callback, res.code, message)
                if res.events_with_missing_fields:
                    for field in res.events_with_missing_fields:
                        events_for_callback = []
                        for index in res.events_with_missing_fields[field]:
                            if index in invalid_set:
                                continue
                            invalid_set.add(index)
                            events_for_callback.append(events[index])
                        message = f"Missing field {field}"
                        self.callback(events_for_callback, res.code, message)
                if res.silenced_events:
                    events_for_callback = []
                    for index in res.silenced_events:
                        if index in invalid_set:
                            continue
                        invalid_set.add(index)
                        events_for_callback.append(events[index])
                    self.callback(events_for_callback, res.code, "Silenced device for event")
                for index, event in enumerate(events):
                    if index not in invalid_set:
                        events_for_retry.append(event)
                self.push_to_storage(events_for_retry, 0, res)
        elif res.status == HttpStatus.TOO_MANY_REQUESTS:
            events_for_callback = []
            events_for_retry_delay = []
            events_for_retry = []
            for index, event in enumerate(events):
                if res.throttled_events and index in res.throttled_events:
                    if res.exceed_daily_quota(event):
                        events_for_callback.append(event)
                    else:
                        events_for_retry_delay.append(event)
                else:
                    events_for_retry.append(event)
            self.callback(events_for_callback, res.code, "Exceeded daily quota")
            self.push_to_storage(events_for_retry_delay, 30000, res)
            self.push_to_storage(events_for_retry, 0, res)
        else:
            self.callback(events, res.code, "Unknown error")

    def push_to_storage(self, events, delay, res):
        for event in events:
            event.retry += 1
            success, message = self.storage.push(event, delay=delay)
            if not success:
                self.callback([event], res.code, message)

    def callback(self, events, code, message):
        for event in events:
            if callable(self.configuration.callback):
                self.configuration.callback(event, code, message)
            event.callback(code, message)
