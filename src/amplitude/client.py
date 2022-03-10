from amplitude.event import Revenue, BaseEvent, Identify, IdentifyEvent, GroupIdentifyEvent
from amplitude.config import Config
from amplitude.plugin import DestinationPlugin
from amplitude.timeline import Timeline


class Amplitude:

    def __init__(self, api_key, configuration=Config()):
        self.configuration = configuration
        self.api_key = api_key
        self.__timeline = Timeline(self)
        amplitude_destination = DestinationPlugin()
        amplitude_destination.setup(self)
        self.add(amplitude_destination)

    @property
    def logger(self):
        return self.configuration.logger

    @logger.setter
    def logger(self, logger):
        self.configuration.logger = logger

    def callback(self, event: BaseEvent, code: int, message: str):
        callback_func = self.configuration.callback
        event.callback(code, message)
        if callable(callback_func):
            try:
                callback_func(event, code, message)
            except Exception:
                self.logger.error(f"Client callback error for event {event}")

    def set_callback(self, callback):
        self.configuration.callback = callback

    @property
    def timeline(self):
        return self.__timeline

    @property
    def endpoint(self):
        if self.configuration.is_eu:
            if self.configuration.is_batch_mode:
                return self.configuration.batch_api_url_eu
            else:
                return self.configuration.batch_api_url
        else:
            if self.configuration.is_batch_mode:
                return self.configuration.api_url_eu
            else:
                return self.configuration.api_url

    @property
    def options(self):
        return self.configuration.options

    def track(self, event: BaseEvent):
        self.timeline.process(event)

    def identify(self, user_id: str, identify_obj: Identify):
        if identify_obj.is_valid():
            event = IdentifyEvent(user_id)
            event.user_properties = identify_obj.user_properties
            self.track(event)
        else:
            self.configuration.logger.error("Empty identify properties")

    def group_identify(self, user_id: str, group_type: str, group_name: str, identify_obj: Identify):
        if identify_obj.is_valid():
            event = GroupIdentifyEvent(user_id=user_id, groups={group_type: group_name})
            event.group_properties = identify_obj.user_properties
            self.track(event)
        else:
            self.configuration.logger.error("Empty group identify properties")

    def revenue(self, revenue_obj: Revenue):
        if not revenue_obj.is_valid():
            self.configuration.logger.error("Missing price for revenue event")
        else:
            self.track(revenue_obj.to_revenue_event())

    def flush(self):
        self.timeline.flush()

    def add(self, plugin):
        self.timeline.add(plugin)
        return self

    def remove(self, plugin):
        self.timeline.remove(plugin)
        return self
