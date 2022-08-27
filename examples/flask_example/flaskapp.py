from flask import Flask, request
from amplitude import Amplitude, BaseEvent, Identify, EventOptions, Revenue

app = Flask(__name__)
amp_client = Amplitude("YOUR API KEY")


@app.route("/pageloaded")
def track_page_load():
    amp_client.track(BaseEvent("Page Loaded", user_id="flask_example_user"))
    return "<p>Page Loaded event sent.</p>"


@app.route("/identify/<user_id>")
def set_age(user_id):
    identify_obj = Identify()
    identify_obj.set("age", 99)
    amp_client.identify(identify_obj, EventOptions(user_id=user_id))
    return f"<p>Set age to 99 for {user_id}.</p>"


@app.route("/groupidentify")
def set_group_member():
    identify_obj = Identify()
    identify_obj.set("member", 16)
    amp_client.group_identify(group_type=request.args.get("group_type", "default"),
                              group_name=request.args.get("group_name", "default"),
                              identify_obj=identify_obj)
    return f"<p>Set group {request.args.get('group_name', 'default')} member to 16</p>"


@app.route("/setgroup/<user_id>")
def set_user_group(user_id):
    amp_client.set_group(group_type=request.args.get("group_type", "default"),
                         group_name=request.args.get("group_name", "default"),
                         event_options=EventOptions(user_id=user_id))
    return f"<p>Put {user_id} to group {request.args.get('group_name', 'default')}</p>"


@app.route("/revenue/<user_id>")
def track_revenue(user_id):
    revenue_obj = Revenue(price=request.args.get("price", 0, float),
                          quantity=request.args.get("quantity", 1, int))
    amp_client.revenue(revenue_obj, EventOptions(user_id=user_id))
    return f"<p>Track revenue for {user_id}</p>"


@app.route("/flush")
def flush_event():
    amp_client.flush()
    return "<p>All events flushed</p>"


if __name__ == "__main__":
    app.run()
