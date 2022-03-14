from amplitude import config
from amplitude.event import Revenue, BaseEvent, Identify
from amplitude.timeline import Timeline
from amplitude import worker


class Amplitude:

    def __init__(self, api_key, configuration=config.DEFAULT_CONFIG):
        self.configuration = configuration
        self.__timeline = Timeline()
        self.api_key = api_key
        self.__workers = worker.create_workers_pool()
        self.options = None

    @property
    def timeline(self):
        return self.__timeline

    @property
    def workers(self):
        return self.__workers

    def track(self, event: BaseEvent):
        self.timeline.process(event)

    def identify(self, identify_obj: Identify):
        pass

    def group_identify(self, identify_obj: Identify):
        pass

    def revenue(self, revenue_obj: Revenue):
        if not revenue_obj.is_valid():
            self.logger.error("Misssing price for revenue event")
        else:
            self.track(revenue_obj.to_revenue_event())

    def flush(self):
        pass

    def add(self, plugin):
        self.timeline.add(plugin)
        return self

    def remove(self, plugin):
        self.timeline.remove(plugin)
        return self
