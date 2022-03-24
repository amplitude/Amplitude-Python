from typing import Optional

from amplitude.config import Config
from amplitude.event import Revenue, BaseEvent, Identify, IdentifyEvent, GroupIdentifyEvent, EventOptions
from amplitude.plugin import AmplitudeDestinationPlugin, ContextPlugin
from amplitude.timeline import Timeline


class Amplitude:

    def __init__(self, api_key: Optional[str] = None, configuration=Config()):
        self.configuration = configuration
        self.configuration.api_key = api_key
        self.__timeline = Timeline()
        self.__timeline.setup(self)
        self.add(AmplitudeDestinationPlugin())
        self.add(ContextPlugin())

    def track(self, event: BaseEvent):
        self.__timeline.process(event)

    def identify(self, identify_obj: Identify, event_properties: Optional[dict] = None,
                 event_options: Optional[EventOptions] = None):
        if not identify_obj.is_valid():
            self.configuration.logger.error("Empty identify properties")
        else:
            event = IdentifyEvent(event_properties=event_properties,
                                  user_properties=identify_obj.user_properties)
            event.load_event_options(event_options)
            self.track(event)

    def group_identify(self, group_type: str, group_name: str, identify_obj: Identify, event_properties=None,
                       user_properties=None, event_options: Optional[EventOptions] = None):
        if not identify_obj.is_valid():
            self.configuration.logger.error("Empty group identify properties")
        else:
            event = GroupIdentifyEvent(event_properties=event_properties,
                                       user_properties=user_properties,
                                       groups={group_type: group_name},
                                       group_properties=identify_obj.user_properties)
            event.load_event_options(event_options)
            self.track(event)

    def revenue(self, revenue_obj: Revenue, event_options: Optional[EventOptions] = None):
        if not revenue_obj.is_valid():
            self.configuration.logger.error("Missing price for revenue event")
        else:
            event = revenue_obj.to_revenue_event()
            event.load_event_options(event_options)
            self.track(event)

    def flush(self):
        self.__timeline.flush()

    def add(self, plugin):
        self.__timeline.add(plugin)
        plugin.setup(self)
        return self

    def remove(self, plugin):
        self.__timeline.remove(plugin)
        return self
