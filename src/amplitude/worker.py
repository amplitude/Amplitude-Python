from concurrent.futures import ThreadPoolExecutor
from enum import Enum
from threading import Thread, Condition
from typing import Optional


class HttpStatus(Enum):
    SUCCESS = 200
    BAD_REQUEST = 400
    TIMEOUT = 408
    PAYLOAD_TOO_LARGE = 413
    TOO_MANY_REQUESTS = 429
    FAILED = 500


class Response:

    def __init__(self, status: HttpStatus, body: Optional[dict] = None):
        self.status = status
        self.body = body

    def parse(self, response: dict) -> None:
        if not self.body:
            self.body = {}


class Worker:

    def __init__(self):
        self.threads_pool = ThreadPoolExecutor(max_workers=20)
        self.is_active = True
        self.consumer = Thread(target=self.buffer_consumer)
        self.storage = None
        self.batch_interval = 10000
        self.batch_size = 500

    def start(self):
        self.consumer.start()

    def stop(self):
        self.flush()
        self.is_active = False
        self.consumer.join()

    def flush(self):
        pass

    def send(self, events):
        pass

    def buffer_consumer(self):
        while self.is_active:
            pass
