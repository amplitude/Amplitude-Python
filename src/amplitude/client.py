"""Amplitude client module that provide client class with public interface and configuration attributes

Classes:
    Amplitude: the Amplitude client class
"""

from typing import Optional, Union, List

from amplitude.config import Config
from amplitude.event import Revenue, BaseEvent, Identify, IdentifyEvent, GroupIdentifyEvent, EventOptions
from amplitude.plugin import AmplitudeDestinationPlugin, ContextPlugin, Plugin
from amplitude.timeline import Timeline


class Amplitude:
    """Amplitude client used to store configurations and track events

    Args:
        api_key (str): The api key of amplitude project. Must be set properly before tracking events.
        configuration (amplitude.config.Config, optional): The configuration of client instance. A new instance
            with default config value will be used by default.

    Attributes:
        configuration (amplitude.config.Config): the configuration of client instance

    Methods:
        track(event): Process and send event
        identify(identify_obj, event_properties, event_options): Send an identify event to update user properties
        group_identify(group_type, group_name, identify_obj, event_options, event_properties, user_properties): Send
            a group identify event to update group properties
        revenue(revenue_obj, event_options): Send a revenue event with revenue info in event_properties
        flush(): Flush all event waiting to be sent in the buffer
        add(plugin): Add the plugin object to client instance.
        remove(plugin): Remove the plugin object from client instance
        shutdown(): Shutdown the client instance
    """

    def __init__(self, api_key: str, configuration: Config = Config()):
        """The constructor for the Amplitude class

        Args:
            api_key (str): The api key of amplitude project. Must be set properly before tracking events.
            configuration (amplitude.config.Config, optional): The configuration of client instance. A new instance
                with default config value will be used by default.
        """
        self.configuration: Config = configuration
        self.configuration.api_key = api_key
        self.__timeline = Timeline()
        self.__timeline.setup(self)
        self.add(AmplitudeDestinationPlugin())
        self.add(ContextPlugin())

    def track(self, event: BaseEvent):
        """Process and send the given event object.

        Args:
            event (amplitude.event.BaseEvent): The event that we want to track
        """
        self.__timeline.process(event)

    def identify(self, identify_obj: Identify, event_options: EventOptions, event_properties: Optional[dict] = None):
        """Send an identify event to update user properties

        Args:
            identify_obj (amplitude.event.Identify): Identify object contain operations of updating user properties
            event_options (amplitude.event.EventOptions): Provide additional information to identify event.
            event_properties (dict, optional): A dictionary of event properties.
        """
        if not identify_obj.is_valid():
            self.configuration.logger.error("Empty identify properties")
        else:
            event = IdentifyEvent(event_properties=event_properties,
                                  user_properties=identify_obj.user_properties)
            event.load_event_options(event_options)
            self.track(event)

    def group_identify(self, group_type: str, group_name: str, identify_obj: Identify,
                       event_options: Optional[EventOptions] = None,
                       event_properties: Optional[dict] = None,
                       user_properties: Optional[dict] = None):
        """Send a group identify event to update group properties

        Args:
            group_type (str): The group type e.g. "sport"
            group_name (str): The group name e.g. "soccer"
            identify_obj (amplitude.event.Identify): Identify object contain operations of updating group properties
            event_options (amplitude.event.EventOptions, optional): Provide additional information to
                group identify event like user_id.
            event_properties (dict, optional): A dictionary of event properties. Defaults to None.
            user_properties (dict, optional): A dictionary of user properties. Defaults to None.
        """
        if not identify_obj.is_valid():
            self.configuration.logger.error("Empty group identify properties")
        else:
            event = GroupIdentifyEvent(event_properties=event_properties,
                                       user_properties=user_properties,
                                       groups={group_type: group_name},
                                       group_properties=identify_obj.user_properties)
            event.load_event_options(event_options)
            self.track(event)

    def revenue(self, revenue_obj: Revenue, event_options: EventOptions):
        """Send a revenue event with revenue info in event_properties

        Args:
            revenue_obj (amplitude.event.Revenue): A revenue object that contains information like price,
                quantity, receipt,  revenue_type
            event_options (amplitude.event.EventOptions): Provide additional information to revenue event
                like user_id.
        """
        if not revenue_obj.is_valid():
            self.configuration.logger.error("Invalid price for revenue event")
        else:
            event = revenue_obj.to_revenue_event()
            event.load_event_options(event_options)
            self.track(event)

    def set_group(self, group_type: str, group_name: Union[str, List[str]], event_options: EventOptions):
        """Sending an identify event to put a user in group(s) by setting group type and group name as
            user property for a user.

        Args:
            group_type (str): The group type e.g. "sport"
            group_name (str): The group name e.g. "soccer"
            event_options (amplitude.event.EventOptions): Provide additional information for event
                like user_id.
        """
        event = IdentifyEvent(groups={group_type: group_name})
        event.load_event_options(event_options)
        self.track(event)

    def flush(self):
        """Flush all event waiting to be sent in the buffer

        Returns:
            A list of Future objects for all destination plugins
        """
        return self.__timeline.flush()

    def add(self, plugin: Plugin):
        """Add the plugin object to client instance. Events tracked by this client instance will be
            processed by instance's plugins.

        Args:
            plugin (amplitude.plugin.Plugin): the plugin object to be added to the client instance

        Returns:
            Amplitude: the client instance itself
        """
        self.__timeline.add(plugin)
        plugin.setup(self)
        return self

    def remove(self, plugin: Plugin):
        """Remove the plugin object from client instance

        Args:
            plugin (amplitude.plugin.Plugin): the plugin object to be removed from the client instance

        Returns:
            Amplitude: the client instance itself
        """
        self.__timeline.remove(plugin)
        return self

    def shutdown(self):
        """Shutdown the client instance, not accepting new events, flush all events in buffer"""
        self.configuration.opt_out = True
        self.__timeline.shutdown()
