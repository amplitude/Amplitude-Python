import abc
import uuid
from typing import Optional

from amplitude.event import BaseEvent, GroupIdentifyEvent, IdentifyEvent, RevenueEvent
from amplitude import constants
from amplitude.timeline import Timeline
from amplitude.exception import InvalidEventError
from amplitude import utils
from amplitude.worker import Workers


class Plugin(abc.ABC):

    def __init__(self, plugin_type: constants.PluginType):
        self.plugin_type: constants.PluginType = plugin_type

    def setup(self, client):
        pass

    @abc.abstractmethod
    def execute(self, event: BaseEvent):
        pass


class EventPlugin(Plugin):

    def __init__(self, plugin_type: constants.PluginType):
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
        super().__init__(constants.PluginType.DESTINATION)
        self.timeline = Timeline()

    def setup(self, client):
        self.timeline.setup(client)

    def add(self, plugin):
        self.timeline.add(plugin)
        return self

    def remove(self, plugin):
        self.timeline.remove(plugin)
        return self

    def execute(self, event: BaseEvent) -> None:
        event = self.timeline.process(event)
        super().execute(event)

    def shutdown(self):
        self.timeline.shutdown()


class AmplitudeDestinationPlugin(DestinationPlugin):

    def __init__(self):
        super().__init__()
        self.workers = Workers()
        self.storage = None
        self.configuration = None

    def setup(self, client):
        super().setup(client)
        self.configuration = client.configuration
        self.storage = client.configuration.get_storage()
        self.workers.setup(client.configuration, self.storage)
        self.storage.setup(client.configuration, self.workers)

    def execute(self, event: BaseEvent) -> None:
        event = self.timeline.process(event)
        if not verify_event(event):
            raise InvalidEventError("Invalid event.")
        self.storage.push(event)

    def flush(self):
        self.workers.flush()

    def shutdown(self):
        self.timeline.shutdown()
        self.workers.stop()


class ContextPlugin(Plugin):

    def __init__(self):
        super().__init__(constants.PluginType.BEFORE)
        self.context_string = f"{constants.SDK_LIBRARY}/{constants.SDK_VERSION}"

    def apply_context_data(self, event: BaseEvent):
        event.library = self.context_string

    def execute(self, event: BaseEvent) -> BaseEvent:
        if not event.time:
            event.time = utils.current_milliseconds()
        if not event.insert_id:
            event.insert_id = str(uuid.uuid4())
        self.apply_context_data(event)
        return event


def verify_event(event):
    if (not isinstance(event, BaseEvent)) or \
            (not event["event_type"]) or \
            (not event["user_id"] and not event["device_id"]):
        return False
    return True
