import abc
from amplitude import constants
from amplitude.storage import Storage
from amplitude.timeline import Timeline


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
        self.timeline = None
        self.amplitude = None
        self.workers = None
        self.storage = storage

    def set_timeline(self, timeline: Timeline):
        self.timeline = timeline
        self.amplitude = timeline.amplitude
        self.workers = self.amplitude.workers

    def set_storage(self, storage: Storage):
        self.storage = storage

    def execute(self, event: BaseEvent):
        self.storage.push_to_buffer(event, 0)

    def start(self):
        pass
