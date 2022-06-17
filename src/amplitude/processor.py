from amplitude.exception import InvalidAPIKeyError
from amplitude.http_client import HttpStatus


class ResponseProcessor:
    def __init__(self):
        self.configuration = None
        self.storage = None

    def setup(self, configuration, storage):
        self.configuration = configuration
        self.storage = storage

    def process_response(self, res, events):
        if res.status == HttpStatus.SUCCESS:
            self.callback(events, res.code, "Event sent successfully.")
            self.log(events, res.code, "Event sent successfully.")
        elif res.status == HttpStatus.TIMEOUT or res.status == HttpStatus.FAILED:
            self.push_to_storage(events, 0, res)
        elif res.status == HttpStatus.PAYLOAD_TOO_LARGE:
            if len(events) == 1:
                self.callback(events, res.code, res.error)
                self.log(events, res.code, res.error)
            else:
                self.configuration._increase_flush_divider()
                self.push_to_storage(events, 0, res)
        elif res.status == HttpStatus.INVALID_REQUEST:
            if res.error.startswith("Invalid API key:"):
                raise InvalidAPIKeyError(res.error)
            if res.missing_field:
                self.callback(events, res.code, f"Request missing required field {res.missing_field}")
                self.log(events, res.code, f"Request missing required field {res.missing_field}")
            else:
                invalid_index_set = res.invalid_or_silenced_index()
                events_for_retry = []
                events_for_callback = []
                for index, event in enumerate(events):
                    if index in invalid_index_set:
                        events_for_callback.append(event)
                    else:
                        events_for_retry.append(event)
                self.callback(events_for_callback, res.code, res.error)
                self.log(events_for_callback, res.code, res.error)
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
            self.callback(events, res.code, res.error or "Unknown error")
            self.log(events, res.code, res.error or "Unknown error")

    def push_to_storage(self, events, delay, res):
        for event in events:
            event.retry += 1
            success, message = self.storage.push(event, delay=delay)
            if not success:
                self.callback([event], res.code, message)
                self.log([event], res.code, message)

    def callback(self, events, code, message):
        for event in events:
            try:
                if callable(self.configuration.callback):
                    self.configuration.callback(event, code, message)
                event.callback(code, message)
            except Exception:
                self.configuration.logger.exception(f"Error callback for event {event}")
    
    def log(self, events, code, message):
        for event in events:
            self.configuration.logger.info(message, extra={'code':code, 'event':event})