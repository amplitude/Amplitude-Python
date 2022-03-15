from typing import Optional

from amplitude.config import Config
from amplitude.event import Revenue, BaseEvent, Identify, IdentifyEvent, GroupIdentifyEvent
from amplitude.plugin import AmplitudeDestinationPlugin
from amplitude.timeline import Timeline


class Amplitude:

    def __init__(self, api_key: Optional[str] = None, configuration=Config()):
        self.configuration = configuration
        self.configuration.api_key = api_key
        self.__timeline = Timeline(configuration)
        amplitude_destination = AmplitudeDestinationPlugin()
        self.add(amplitude_destination)
        amplitude_destination.setup(configuration)

    def track(self, event: BaseEvent):
        self.__timeline.process(event)

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
        self.__timeline.flush()

    def add(self, plugin):
        self.__timeline.add(plugin)
        return self

    def remove(self, plugin):
        self.__timeline.remove(plugin)
        return self
