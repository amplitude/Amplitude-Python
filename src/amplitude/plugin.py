import abc
from enum import Enum
from typing import Optional

from amplitude.client import Amplitude
from amplitude.storage import Storage
from amplitude.timeline import Timeline
from amplitude.event import BaseEvent, GroupIdentifyEvent, IdentifyEvent, RevenueEvent
from amplitude import utils
from amplitude.exception import InvalidEventError
from amplitude import constants
from amplitude.client import Amplitude
from amplitude.storage import Storage
from amplitude.timeline import Timeline
from amplitude.event import BaseEvent


class PluginType(Enum):
    BEFORE = 0
    ENRICHMENT = 1
    DESTINATION = 2
    OBSERVE = 3


class Plugin(abc.ABC):

    def __init__(self, plugin_type: PluginType):
        self.plugin_type: PluginType = plugin_type
        self.__amplitude_client = None

    def setup(self, client: Amplitude):
        self.__amplitude_client = client

    @abc.abstractmethod
    def execute(self, event: BaseEvent):
        pass


class EventPlugin(Plugin):

    def __init__(self, plugin_type: PluginType):
        super().__init__(plugin_type)

    def execute(self, event: BaseEvent) -> Optional[BaseEvent]:
        if isinstance(event, GroupIdentifyEvent):
            return self.group_identify(event)
        if isinstance(event, IdentifyEvent):
            return self.identify(event)
        if isinstance(event, RevenueEvent):
            return self.revenue(event)
        return self.track(event)

    def group_identify(self, event: GroupIdentifyEvent) -> Optional[GroupIdentifyEvent]:
        return event

    def identify(self, event: IdentifyEvent) -> Optional[IdentifyEvent]:
        return event

    def revenue(self, event: RevenueEvent) -> Optional[RevenueEvent]:
        return event

    def track(self, event: BaseEvent) -> Optional[BaseEvent]:
        return event


class DestinationPlugin(EventPlugin):

    def __init__(self, storage: Storage = None, ):
        super().__init__(PluginType.DESTINATION)
        self.__timeline = Timeline()
        self.__amplitude_client = None
        self.workers = None
        self.storage = storage

    @property
    def timeline(self):
        return self.__timeline

    def setup(self, client: Amplitude):
        self.__amplitude_client = client
        self.__timeline.__amplitude_client = client

    def set_storage(self, storage: Storage):
        self.storage = storage

    def add(self, plugin):
        self.__timeline.add(plugin)
        return self

    def remove(self, plugin):
        self.__timeline.remove(plugin)
        return self

    def execute(self, event: BaseEvent) -> None:
        event = self.timeline.process(event)
        if not utils.verify_event(event):
            raise InvalidEventError("Invalid event.")
        self.storage.push_to_buffer(event)

    def start(self):
        pass
