import abc
from amplitude import constants


class Plugin(abc.ABC):

    def __init__(self, plugin_type):
        self.plugin_type = plugin_type
        self.enable = True

    @abc.abstractmethod
    def execute(self, event):
        pass


class DestinationPlugin(Plugin):

    def __init__(self, timeline):
        super().__init__(constants.DESTINATION_PLUGIN_TYPE)
        self.timeline = timeline
        self.amplitude = timeline.amplitude
        self.workers = self.amplitude.workers
        self.storage = self.amplitude.storage
        self.logger = self.amplitude.logger

    def execute(self, event):
        self.storage.push_to_buffer(event, 0)

    def start(self):
        pass
    