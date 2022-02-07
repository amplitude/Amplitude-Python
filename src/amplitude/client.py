from config import DEFAULT_CONFIG
from timeline import Timeline
import worker


class Amplitude:

    def __init__(self, config=None):
        if config is None:
            self.config = DEFAULT_CONFIG
        else:
            self.config = config
        self.timeline = Timeline()
        self.workers = worker.create_workers_pool(config.worker_number)

    def track(self, event):
        pass

    def identify(self, id):
        pass

    def groupIdentify(self, id):
        pass

    def revenue(self, event):
        pass

    def flush(self):
        pass

    def add(self, plugin):
        pass

    def remove(self, plugin):
        pass
