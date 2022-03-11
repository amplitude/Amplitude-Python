import json
import logging
from socket import timeout
from concurrent.futures import ThreadPoolExecutor
from enum import Enum
from threading import Thread
from typing import Optional
from urllib import request, response

from amplitude import constants
from amplitude.exception import InvalidAPIKeyError

JSON_HEADER = {
    "Content-Type": "application/json; charset=UTF-8",
    "Accept": "*/*"
}


class HttpStatus(Enum):
    SUCCESS = 200
    INVALID_REQUEST = 400
    TIMEOUT = 408
    PAYLOAD_TOO_LARGE = 413
    TOO_MANY_REQUESTS = 429
    FAILED = 500
    UNKNOWN = -1


class Response:

    def __init__(self, status: HttpStatus = HttpStatus.UNKNOWN, body: Optional[dict] = None):
        self.status: HttpStatus = status
        self.code: int = status.value
        self.body = body
        if not self.body:
            self.body = {}

    def parse(self, res: response):
        res_body = json.loads(res.read().decode("utf8"))
        self.code = res_body["code"]
        self.status = self.get_status(self.code)
        self.body = res_body
        return self

    @property
    def error(self):
        if "error" in self.body:
            return self.body["error"]
        return ""

    @property
    def missing_field(self):
        if "missing_field" in self.body:
            return self.body["missing_field"]
        return None

    @property
    def events_with_invalid_fields(self):
        if "events_with_invalid_fields" in self.body:
            return self.body["events_with_invalid_fields"]
        return None

    @property
    def events_with_missing_fields(self):
        if "events_with_missing_fields" in self.body:
            return self.body["events_with_missing_fields"]
        return None

    @property
    def silenced_events(self):
        if "silenced_events" in self.body:
            return self.body["silenced_events"]
        return None

    @property
    def throttled_events(self):
        if "throttled_events" in self.body:
            return self.body["throttled_events"]
        return None

    def exceed_daily_quota(self, event) -> bool:
        if "exceeded_daily_quota_users" in self.body and event.user_id in self.body["exceeded_daily_quota_users"]:
            return True
        if "exceeded_daily_quota_devices" in self.body and event.device_id in self.body["exceeded_daily_quota_devices"]:
            return True
        return False

    @staticmethod
    def get_status(code: int) -> HttpStatus:
        if 200 <= code < 300:
            return HttpStatus.SUCCESS
        elif code == 429:
            return HttpStatus.TOO_MANY_REQUESTS
        elif code == 413:
            return HttpStatus.PAYLOAD_TOO_LARGE
        elif code == 408:
            return HttpStatus.TIMEOUT
        elif 400 <= code < 500:
            return HttpStatus.INVALID_REQUEST
        elif code >= 500:
            return HttpStatus.FAILED
        return HttpStatus.UNKNOWN


class Workers:

    def __init__(self, destination):
        self.threads_pool = ThreadPoolExecutor(max_workers=16)
        self.is_active = True
        self.consumer = Thread(target=self.buffer_consumer)
        self.__amplitude_client = None
        self.destination = destination

    def setup(self, client):
        self.__amplitude_client = client

    @property
    def storage(self):
        return self.destination.storage

    @property
    def batch_interval(self) -> float:
        if self.__amplitude_client:
            return self.__amplitude_client.configuration.batch_interval
        return constants.BATCH_INTERVAL

    @property
    def batch_size(self):
        if self.__amplitude_client:
            return self.__amplitude_client.configuration.batch_size
        return constants.BATCH_SIZE

    @property
    def logger(self):
        if self.__amplitude_client:
            return self.__amplitude_client.logger
        return logging.getLogger(__name__)

    @property
    def timeout(self):
        if self.__amplitude_client:
            return self.__amplitude_client.configuration.timeout
        return constants.CONNECTION_TIMEOUT

    def start(self):
        self.consumer.start()

    def stop(self):
        self.flush()
        self.is_active = False
        self.consumer.join()

    def flush(self):
        events = self.storage.pull_all()
        self.send(events)

    def send(self, events):
        url = self.destination.endpoint
        payload = self.destination.get_payload([event.get_event_body() for event in events])
        res = self.post(url, payload)
        self.process_response(res, events)

    def process_response(self, res, events):
        if res.status == HttpStatus.SUCCESS:
            self.callback(events, res.code, "Event sent successful.")
        elif res.status == HttpStatus.TIMEOUT or res.status == HttpStatus.FAILED:
            self.push_to_storage(events, 0, res)
        elif res.status == HttpStatus.PAYLOAD_TOO_LARGE:
            if self.__amplitude_client:
                self.__amplitude_client.configuration.batch_size //= 2
            self.push_to_storage(events, 0, res)
        elif res.status == HttpStatus.INVALID_REQUEST:
            if res.error.startswith("Invalid API key:"):
                raise InvalidAPIKeyError(f"Invalid API key: {self.destination.api_key}")
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
            self.storage.push(event, delay=delay, response=res)

    def callback(self, events, code, message):
        for event in events:
            if self.__amplitude_client:
                self.__amplitude_client.callback(event, code, message)
            else:
                event.callback(code, message)

    def buffer_consumer(self):
        while self.is_active:
            with self.storage.lock:
                while self.storage.total_events == 0:
                    self.storage.lock.wait(self.batch_interval)
                events = self.storage.pull(self.batch_size)
                if events:
                    self.threads_pool.submit(self.send, events)

    def post(self, url: str, payload: bytes, header=None) -> Response:
        result = Response()
        try:
            if not header:
                req = request.Request(url, data=payload, headers=JSON_HEADER)
            else:
                req = request.Request(url, data=payload, headers=header)
            res = request.urlopen(req, timeout=self.timeout)
            result.parse(res)
        except timeout:
            result.code = 408
            result.status = HttpStatus.TIMEOUT
        except Exception:
            self.logger.error(f"Error sending http requests to {url} with payload {payload.decode('utf8')}")
        return result
