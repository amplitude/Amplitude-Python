import abc
from enum import Enum
from amplitude.client import Amplitude
from amplitude.storage import Storage
from amplitude.timeline import Timeline
from amplitude.event import BaseEvent
from amplitude import utils
from amplitude.exception import InvalidEventError


class PluginType(Enum):
    BEFORE = 0
    ENRICHMENT = 1
    DESTINATION = 2


class Plugin(abc.ABC):

    def __init__(self, plugin_type: PluginType):
        self.plugin_type: PluginType = plugin_type
        self.enable = True

    @abc.abstractmethod
    def execute(self, event):
        pass


class DestinationPlugin(Plugin):

    def __init__(self, storage: Storage = None, ):
        super().__init__(PluginType.DESTINATION)
        self.timeline = Timeline()
        self.amplitude = None
        self.workers = None
        self.storage = storage

    def setup(self, client: Amplitude):
        self.amplitude = client
        self.workers = self.amplitude.workers

    def set_storage(self, storage: Storage):
        self.storage = storage

    def add(self, plugin):
        self.timeline.add(plugin)
        return self

    def remove(self, plugin):
        self.timeline.remove(plugin)
        return self

    def execute(self, event: BaseEvent):
        event = self.timeline.process(event)
        if not utils.verify_event(event):
            raise InvalidEventError("Invalid event.")
        self.storage.push_to_buffer(event)

    def start(self):
        pass
