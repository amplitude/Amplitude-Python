import abc
from amplitude import constants
from amplitude.client import Amplitude
from amplitude.storage import Storage
from amplitude.timeline import Timeline
from amplitude.event import BaseEvent


class Plugin(abc.ABC):

    def __init__(self, plugin_type):
        self.plugin_type = plugin_type
        self.enable = True

    @abc.abstractmethod
    def execute(self, event):
        pass


class DestinationPlugin(Plugin):

    def __init__(self, storage: Storage = None, ):
        super().__init__(constants.DESTINATION_PLUGIN_TYPE)
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
        self.storage.push_to_buffer(event, 0)

    def start(self):
        pass
