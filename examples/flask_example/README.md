# Flask Amplitude example

A simple flask app that provided apis to demo Amplitude client functions.

### Setup before execution

All examples require installing the Amplitude Python SDK and setting your API key.

1. Install Amplitude Python SDK
   1. `pip install amplitude-analytics`
2. Replace `YOUR API KEY` in example code with your amplitude project api key.

### To run this example

First install flask:

`pip install flask`

Then:

`FLASK_APP=flaskapp flask run`

In your browser

1. Open http://127.0.0.1:5000/pageloaded to see the app page and a 'Page Loaded' event will be sent.
2. Open http://127.0.0.1:5000/identify/flask_example_user to send an identify event for flask_example_user
3. Open http://127.0.0.1:5000/groupidentify?group_type=team&group_name=SDE to send a group identify event
4. Open http://127.0.0.1:5000/setgroup/flask_example_user?group_type=team&group_name=SDE to put flask_example_user into SDE team
5. Open http://127.0.0.1:5000/revenue/flask_example_user?price=20&quantity=4 to track a revenue order
6. Open http://127.0.0.1:5000/flush to flush events in buffer