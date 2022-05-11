# Plugin example

### Setup before execution

All examples require installing the Amplitude Python SDK and setting your API key.

1. Install Amplitude Python SDK
   1. `pip install amplitude-analytics`
2. Replace `YOUR API KEY` in example code with your amplitude project api key.

### Event plugin example

An event plugin that add a description to events' event_properties

`python event_plugin.py`

### Destination plugin example

A customized destination plugin that post event to https://postman-echo.com/post and print the response

To run this example, first install requests if needed:

`pip install requests`

Then:

`python destination_plugin.py`
