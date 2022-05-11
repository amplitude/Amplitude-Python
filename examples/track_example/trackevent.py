"""A very simple example of using Amplitude Python SDK to track  events"""

from amplitude import Amplitude, BaseEvent, Identify, EventOptions, Revenue


def callback_fun(e, code, message):
    """A callback function"""
    print(e)
    print(code, message)


# Initialize a Amplitude client instance
amp_client = Amplitude(api_key="YOUR API KEY")
# Config a callback function
amp_client.configuration.callback = callback_fun

# Create a BaseEvent instance
event = BaseEvent(event_type="Test python SDK", user_id="test_user_id", device_id="test_devece_id")
# Set event properties
event["event_properties"] = {
    "keywords": ["amplitude", "python"],
    "likes": True
}
amp_client.track(event)

# Track a IdentifyEvent using identify() method
identify_obj = Identify()
identify_obj.set("age", 99)
amp_client.identify(identify_obj, EventOptions(user_id="example_user"))

# Track a GroupIdentifyEvent using group_identify() method
identify_obj = Identify()
identify_obj.set("member", 16)
amp_client.group_identify("Eng Team", "Infra", identify_obj)

# Put a user into a group use set_group method
amp_client.set_group("Eng Team", "Infra", EventOptions(user_id="example_user"))

# Track a revenue event using revenue() method
revenue_obj = Revenue(price=9.99, quantity=5, product_id="100A")
amp_client.revenue(revenue_obj, EventOptions(user_id="example_user"))

# Flush the event buffer
amp_client.flush()

# Shutdown the client
amp_client.shutdown()
