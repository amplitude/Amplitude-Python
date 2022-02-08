from config import DEFAULT_CONFIG
from timeline import Timeline
import worker


class Amplitude:

    def __init__(self, apiKey, config=DEFAULT_CONFIG):
        self.config = config
        self.timeline = Timeline()
        self.apiKey = apiKey
        self.workers = worker.create_workers_pool()

    def track(self, event):
        pass

    def identify(self, identify_obj):
        pass

    def groupIdentify(self, identify_obj):
        pass

    def revenue(self, revenue_obj):
        pass

    def flush(self):
        pass

    def add(self, plugin):
        pass

    def remove(self, plugin):
        pass
