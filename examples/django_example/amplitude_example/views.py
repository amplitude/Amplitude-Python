from django.http import HttpResponse
from amplitude import Amplitude, BaseEvent, Identify, EventOptions, Revenue

# Create your views here.


amp_client = Amplitude("44270dfba966dafe46554de66e088877")


def track_page_load(request):
    amp_client.track(BaseEvent("Page Loaded", user_id="django_example_user"))
    return HttpResponse("<p>Page Loaded event sent.</p>")


def set_age(request):
    user_id = request.GET.get("user_id", "django_example_user")
    identify_obj = Identify()
    identify_obj.set("age", 99)
    amp_client.identify(identify_obj, EventOptions(user_id=user_id))
    return HttpResponse(f"<p>Set age to 99 for {user_id}.</p>")


def set_group_member(request):
    group_type = request.GET.get("group_type", "default")
    group_name = request.GET.get("group_name", "default")
    identify_obj = Identify()
    identify_obj.set("member", 16)
    amp_client.group_identify(group_type, group_name, identify_obj=identify_obj)
    return HttpResponse(f"<p>Set group {group_name} member to 16</p>")


def set_user_group(request):
    user_id = request.GET.get("user_id", "django_example_user")
    group_type = request.GET.get("group_type", "default")
    group_name = request.GET.get("group_name", "default")
    amp_client.set_group(group_type, group_name, EventOptions(user_id=user_id))
    return HttpResponse(f"<p>Put {user_id} to group {group_name}</p>")


def track_revenue(request):
    user_id = request.GET.get("user_id", "django_example_user")
    price = float(request.GET.get("price", "0"))
    quantity = int(request.GET.get("quantity", "1"))
    revenue_obj = Revenue(price, quantity)
    amp_client.revenue(revenue_obj, EventOptions(user_id=user_id))
    return HttpResponse(f"<p>Track revenue for {user_id}</p>")


def flush_event(request):
    amp_client.flush()
    return HttpResponse(f"<p>All events flushed</p>")
