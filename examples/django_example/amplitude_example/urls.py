from django.urls import path
from . import views


urlpatterns = [
    path('pageloaded', views.track_page_load, name='Track Page Load Event'),
    path('identify', views.set_age, name='Track Page Load Event'),
    path('groupidentify', views.set_group_member, name='Track Page Load Event'),
    path('setgroup', views.set_user_group, name='Track Page Load Event'),
    path('revenue', views.track_revenue, name='Track Page Load Event'),
    path('flush', views.flush_event, name='Track Page Load Event'),
]
