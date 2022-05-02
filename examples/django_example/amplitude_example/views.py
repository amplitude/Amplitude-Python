from django.http import HttpResponse
from amplitude import Amplitude, BaseEvent
# Create your views here.


client = Amplitude("API KEY")


def track_event(request):
    client.track(BaseEvent("Page Loaded", user_id="django_example_user"))
    return HttpResponse("<p>Page Loaded event sent.</p>")
