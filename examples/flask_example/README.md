# Flask Amplitude example

A simple flask app that has one page. Send a 'Page Loaded' event to Amplitude when the app page was opened.

### To run this example

First install flask:

`pip install flask`

Then:

`FLASK_APP=flaskapp flask run`

In your browser open link http://localhost:5000/ to see the app page and a 'Page Loaded' event will be sent.