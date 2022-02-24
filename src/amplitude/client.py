from amplitude import config
from amplitude.exception import InvalidEventError
from amplitude.timeline import Timeline
from amplitude import utils
from amplitude import worker


class Amplitude:

    def __init__(self, api_key, configuration=config.DEFAULT_CONFIG):
        self.configuration = configuration
        self.timeline = Timeline()
        self.api_key = api_key
        self.workers = worker.create_workers_pool()
        self.options = None

    def track(self, event):
        self.timeline.process(event)

    def identify(self, identify_obj):
        pass

    def group_identify(self, identify_obj):
        pass

    def revenue(self, revenue_obj):
        pass

    def flush(self):
        pass

    def add(self, plugin):
        self.timeline.add(plugin)
        return self

    def remove(self, plugin):
        self.timeline.remove(plugin)
        return self
