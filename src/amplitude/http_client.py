import json
from enum import Enum
from socket import timeout
from typing import Optional
from urllib import request, response, error

from amplitude import constants

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
    def events_with_invalid_id_lengths(self):
        if "events_with_invalid_id_lengths" in self.body:
            return self.body["events_with_invalid_id_lengths"]
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

    def invalid_or_silenced_index(self):
        result = set()
        if self.events_with_missing_fields:
            for field in self.events_with_missing_fields:
                result.update(self.events_with_missing_fields[field])
        if self.events_with_invalid_fields:
            for field in self.events_with_invalid_fields:
                result.update(self.events_with_invalid_fields[field])
        if self.events_with_invalid_id_lengths:
            for field in self.events_with_invalid_id_lengths:
                result.update(self.events_with_invalid_id_lengths[field])
        if self.silenced_events:
            result.update(self.silenced_events)
        return result

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


class HttpClient:

    @staticmethod
    def post(url: str, payload: bytes, header=None) -> Response:
        result = Response()
        try:
            if not header:
                req = request.Request(url, data=payload, headers=JSON_HEADER)
            else:
                req = request.Request(url, data=payload, headers=header)
            res = request.urlopen(req, timeout=constants.CONNECTION_TIMEOUT)
            result.parse(res)
        except timeout:
            result.code = 408
            result.status = HttpStatus.TIMEOUT
        except error.HTTPError as e:
            try:
                result.parse(e)
            except:
                result = Response()
                result.code = e.code
                result.status = Response.get_status(e.code)
                result.body = {'error': e.reason}
        except error.URLError as e:
            result.body = {'error': str(e.reason)}
        return result
