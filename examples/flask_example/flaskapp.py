from flask import Flask
from amplitude import Amplitude, BaseEvent

app = Flask(__name__)
amp_client = Amplitude("YOUR API KEY")


@app.route("/")
def amplitude_example_app():
    amp_client.track(BaseEvent("Page Loaded", user_id="flask_example_user"))
    return "<p>Page Loaded event sent.</p>"


if __name__ == "__main__":
    app.run()
