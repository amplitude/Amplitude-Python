import abc
import json
import logging
from enum import Enum
from typing import Optional

from amplitude.event import BaseEvent, GroupIdentifyEvent, IdentifyEvent, RevenueEvent
from amplitude import constants
from amplitude.client import Amplitude
from amplitude.timeline import Timeline
from amplitude import utils
from amplitude.exception import InvalidEventError
from amplitude.worker import Workers


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

    def __init__(self):
        super().__init__(PluginType.DESTINATION)
        self.__timeline = Timeline()
        self.__workers = Workers(self)
        self.__amplitude_client = None
        self._endpoint = None
        self.storage = None

    @property
    def timeline(self):
        return self.__timeline

    @property
    def workers(self):
        return self.__workers

    @property
    def endpoint(self):
        if self._endpoint:
            return self._endpoint
        if self.__amplitude_client:
            return self.__amplitude_client.endpoint
        return constants.HTTP_API_URL

    @endpoint.setter
    def endpoint(self, url: str):
        self._endpoint = url

    @property
    def logger(self):
        if self.__amplitude_client:
            return self.__amplitude_client.logger
        return logging.getLogger(__name__)

    @property
    def api_key(self) -> str:
        if self.__amplitude_client:
            return self.__amplitude_client.api_key
        self.logger.error("Missing API key for destination plugin")
        return ""

    @property
    def batch_size(self):
        if self.__amplitude_client:
            return self.__amplitude_client.configuration.batch_size
        return constants.BATCH_SIZE

    def setup(self, client: Amplitude):
        self.__amplitude_client = client
        self.storage = client.configuration.get_storage(self)
        self.timeline.setup(client)
        self.workers.setup(client)
        self.storage.setup(client)

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
        self.storage.push(event)

    def start(self):
        self.workers.start()

    def stop(self):
        self.workers.stop()

    def flush(self):
        self.workers.flush()

    def get_payload(self, events) -> bytes:
        payload_body = {
            "api_key": self.api_key,
            "events": events
        }
        if self.__amplitude_client.options:
            payload_body["options"] = self.__amplitude_client.options
        return json.dumps(payload_body).encode('utf8')
