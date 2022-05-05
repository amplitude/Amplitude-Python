"""A very simple example of using Amplitude Python SDK to track a event"""

from amplitude import Amplitude, BaseEvent


def callback_fun(event, code, message):
    print(event)
    print(code, message)


client = Amplitude(api_key="YOUR API KEY")
client.configuration.callback = callback_fun
event = BaseEvent(event_type="Test python SDK", user_id="test_user_id", device_id="test_devece_id")
event.event_properties = {
    "keywords": ["amplitude", "python"],
    "likes": True
}
client.track(event)
client.flush()
client.shutdown()
