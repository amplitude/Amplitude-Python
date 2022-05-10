import json
import requests

from amplitude import Amplitude, DestinationPlugin, PluginType, BaseEvent


class MyDestinationPlugin(DestinationPlugin):

    def __init__(self):
        self.plugin_type = PluginType.DESTINATION
        self.configuration = None
        self.url = "https://postman-echo.com/post"

    def setup(self, client: Amplitude):
        super().setup(client)
        self.configuration = client.configuration

    def execute(self, event: BaseEvent) -> None:
        event = self.timeline.process(event)
        r = requests.post(self.url, data=json.dumps(event.get_event_body()))
        print(r.text)


amp_client = Amplitude("YOUR API KEY")
amp_client.add(MyDestinationPlugin())
amp_client.track(BaseEvent("plugin_example_event", user_id="example_user"))
amp_client.shutdown()
