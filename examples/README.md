# Amplitude Python SDK

There are some example apps of using Amplitude Python SDK.

## Usage

### Setup before execution

1. Install Amplitude Python SDK
   1. `pip install amplitude-analytics`
2. Replace `YOUR API KEY` in example code with your amplitude project api key.

### Run trackevent.py

This example initialized a amplitude client and tracked an event, then triggered a call back function.

`python trackevent.py`

### Run flask example app

This example have a simple flask app in flask_example/flaskapp.py and send a 'Page Loaded' event to Amplitude when the app page was opened.

To run this example app first install flask:

`pip install flask`

In flask_example directory:

`FLASK_APP=flaskapp flask run`

In your browser open link http://localhost:5000/ to see the app page and a 'Page Loaded' event will be sent.

### Run Django example app

This example Django projects contains a app called 'amplitude_example'. The app has one view in django_example/amplitude_example/views.py

To run this example first install Django:

`pip install django`

In django_example directory:

`python manage.py runserver`

In your browser open link http://127.0.0.1:8000/amplitude/ to see the view page in the example and a 'Page Loaded' event will be sent.

## Project structure

* README.md - you are here *
* [trackevent.py](trackevent.py) - The track event example
* [flask_example](flask_example) - The flask app example
  * flaskapp.py
* [django_example](django_example) - The django project example
  * manage.py
  * django_example
    * settings.py - Project settings
    * urls.py - Project url mapping
    * ...
  * amplitude_example
    * views.py - app event tracking views
    * urls.py - app url mapping
    * ...