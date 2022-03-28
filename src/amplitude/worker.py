import json
from concurrent.futures import ThreadPoolExecutor
from threading import Thread

from amplitude.http_client import HttpClient
from amplitude import utils
from amplitude.processor import ResponseProcessor


class Workers:

    def __init__(self):
        self.threads_pool = ThreadPoolExecutor(max_workers=16)
        self.is_active = True
        self.consumer = Thread(target=self.buffer_consumer)
        self.configuration = None
        self.storage = None
        self.response_processor = ResponseProcessor(self)

    def setup(self, configuration, storage):
        self.configuration = configuration
        self.storage = storage
        self.response_processor.setup(configuration)

    def start(self):
        self.consumer.start()

    def stop(self):
        self.flush()
        self.is_active = False
        self.consumer.join()
        self.threads_pool.shutdown()

    def flush(self):
        events = self.storage.pull_all()
        self.send(events)

    def send(self, events):
        url = self.configuration.server_url
        payload = self.get_payload(events)
        res = HttpClient.post(url, payload)
        self.response_processor.process_response(res, events)

    def get_payload(self, events) -> bytes:
        payload_body = {
            "api_key": self.configuration.api_key,
            "events": []
        }
        for event in events:
            event_body = event.get_event_body()
            if event_body:
                payload_body["events"].append(event_body)
        if self.configuration.options:
            payload_body["options"] = self.configuration.options
        return json.dumps(payload_body).encode('utf8')

    def buffer_consumer(self):
        while self.is_active:
            with self.storage.lock:
                events = self.storage.pull(self.configuration.flush_queue_size)
                if events:
                    self.threads_pool.submit(self.send, events)
                else:
                    wait_time = self.storage.wait_time / 1000
                    if wait_time > 0:
                        self.storage.lock.wait(wait_time)

