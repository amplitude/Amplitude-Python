from amplitude import Amplitude, EventPlugin, PluginType, BaseEvent, IdentifyEvent, GroupIdentifyEvent, RevenueEvent, \
    Identify, Revenue, EventOptions


class MyEventPlugin(EventPlugin):

    def __init__(self):
        self.plugin_type = PluginType.ENRICHMENT
        self.configuration = None

    def setup(self, client: Amplitude):
        self.configuration = client.configuration

    def execute(self, event: BaseEvent):
        """Add a description to event properties"""
        if isinstance(event, RevenueEvent):
            return self.add_description(event, "A revenue event")
        if isinstance(event, IdentifyEvent):
            return self.add_description(event, "A identify event")
        if isinstance(event, GroupIdentifyEvent):
            return self.add_description(event, "A group identify event")
        return self.add_description(event, "A base event")

    @staticmethod
    def add_description(event, desc: str):
        if not event["event_properties"]:
            event["event_properties"] = {}
        event["event_properties"]["description"] = desc
        return event


my_plugin = MyEventPlugin()
print(my_plugin.execute(BaseEvent("plugin_example_event", user_id="example_user")))
print(my_plugin.execute(IdentifyEvent(user_id="example_user")))
print(my_plugin.execute(GroupIdentifyEvent()))
print(my_plugin.execute(RevenueEvent(user_id="example_user")))

amp_client = Amplitude("YOUR API KEY")
amp_client.add(my_plugin)
amp_client.track(BaseEvent("plugin_example_event", user_id="example_user"))
identify_obj = Identify().set("example", "plugin")
amp_client.identify(identify_obj, EventOptions(user_id="example_user"))
amp_client.group_identify("fruit", "banana", identify_obj)
amp_client.revenue(Revenue(price=9.99, quantity=2), EventOptions(user_id="example_user"))
amp_client.shutdown()
