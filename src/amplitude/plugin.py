"""Amplutide plugin module. Provide base class to implement customized plugin

Classes:
    Plugin: Base class of all plugins.
    EventPlugin: Base class to implement plugins that modify and enrich events.
    DestinationPlugin: Base class to implement plugins that send events to customized destinations.
    AmplitudeDestinationPlugin: Default Amplitude Destination plugin that send events to Amplitude.
    ContextPlugin: A default plugin that add library info to event. Also set event default timestamp and insert_id
        if not set elsewhere.

Methods:
    verify_event(event): Perform basic validation before AmplitudeDestinationPlugin send the event to storage.
"""

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
    """The abstract base class of plugins

    Args:
        plugin_type (constants.PluginType): The plugin type.
    """

    def __init__(self, plugin_type: constants.PluginType):
        """The constructor of Plugin class"""
        self.plugin_type: constants.PluginType = plugin_type

    def setup(self, client):
        """Setup plugins with client instance parameter"""
        pass

    @abc.abstractmethod
    def execute(self, event: BaseEvent):
        """Process event with plugin instance"""
        pass


class EventPlugin(Plugin):
    """Plugins that modify and enrich events. Used as base class of event plugins.

    Args:
        plugin_type (constants.PluginType): The plugin type.

    Methods:
        setup(client): Setup plugin using Amplitude client instance.
        execute(event): Method to override to process event. Return modified event or None. Return None will stop the
            Amplitude client sending the event and callback will not be triggered.
        track(event): Can be override to process BaseEvent if execute method not overrided.
        revenue(event): Can be override to process RevenueEvent if execute method not overrided.
        identify(event): Can be override to process IdentifyEvent if execute method not overrided.
        group_identify(event): Can be override to process GroupIdentifyEvent if execute method not overrided.
    """

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
    """Plugins that send events to a destination like Amplitude.

    Methods:
        setup(client): Setup plugin using Amplitude client instance.
        execute(event): Method to override to send out events.
        add(plugin): Add additional processing ability by plugins to modify events before sending out.
        remove(plugin): Remove a plugin instance from destination plugin.
        shutdown(): Method to override to handle closure of client like flushing events,
            closing threads and connections. Triggered by client.shutdown()
    """

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
    """The Amplitude destination plugin. Added to client by default. Send events to Amplitude.

    Methods:
        setup(client): Setup plugin instance and storage and workers instance of the destination plugin.
        execute(event): Process event with plugins added to the destination plugin. Then pushed the event to storage
            waiting to be sent.
        flush(): Flush all event in storage instance.
        shutdown(): Shutdown plugins and works of the destination plugin.
    """

    def __init__(self):
        """The constructor of AmplitudeDestinationPlugin class"""
        super().__init__()
        self.workers = Workers()
        self.storage = None
        self.configuration = None

    def setup(self, client):
        """Setup plugin instance and storage and workers instance of the destination plugin.

        Args:
            client: The Amplitude client that holds the destination plugin.
        """
        super().setup(client)
        self.configuration = client.configuration
        self.storage = client.configuration.get_storage()
        self.workers.setup(client.configuration, self.storage)
        self.storage.setup(client.configuration, self.workers)

    def execute(self, event: BaseEvent) -> None:
        """Process event with plugins added to the destination plugin. Then pushed the event to storage
            waiting to be sent.

        Args:
            event (BaseEvent): The event to be sent.
        """
        event = self.timeline.process(event)
        if not verify_event(event):
            raise InvalidEventError("Invalid event.")
        self.storage.push(event)

    def flush(self):
        """Flush all event in storage instance."""
        return self.workers.flush()

    def shutdown(self):
        """Shutdown plugins and works of the destination plugin."""
        self.timeline.shutdown()
        self.workers.stop()


class ContextPlugin(Plugin):
    """Amplitude Context plugin. Default added to client. Add library info to event.
        Also set event default timestamp and insert_id if not set elsewhere.

    Methods:
        apply_context_data(event): Add SDK name and version to event.library.
        execute(event): Set event default timestamp and insert_id if not set elsewhere.
            Add SDK name and version to event.library.
    """

    def __init__(self):
        """The constructor of ContextPlugin class"""
        super().__init__(constants.PluginType.BEFORE)
        self.context_string = f"{constants.SDK_LIBRARY}/{constants.SDK_VERSION}"
        self.configuration = None

    def setup(self, client):
        self.configuration = client.configuration

    def apply_context_data(self, event: BaseEvent):
        """Add SDK name and version to event.library.

        Args:
            event (BaseEvent): The event to be processed.
        """
        event.library = self.context_string

    def execute(self, event: BaseEvent) -> BaseEvent:
        """Set event default timestamp and insert_id if not set elsewhere. Add SDK name and version to event.library.

        Args:
            event (BaseEvent): The event to be processed.
        """
        if not event.time:
            event["time"] = utils.current_milliseconds()
        if not event.insert_id:
            event["insert_id"] = str(uuid.uuid4())
        if self.configuration.plan and (not event.plan):
            event["plan"] = self.configuration.plan
        self.apply_context_data(event)
        return event


def verify_event(event):
    """Perform basic validation before AmplitudeDestinationPlugin send the event to storage.

    Args:
        event (BaseEvent): the event to be verified.

    Returns:
        True is event is valid, False otherwise.
    """
    if isinstance(event, GroupIdentifyEvent):
        return True
    if (not isinstance(event, BaseEvent)) or \
            (not event["event_type"]) or \
            (not event["user_id"] and not event["device_id"]):
        return False
    return True
