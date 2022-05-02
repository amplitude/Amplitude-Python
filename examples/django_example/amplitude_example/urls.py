from django.urls import path
from . import views


urlpatterns = [
    path('', views.track_event, name='Track Page Load Event'),
]