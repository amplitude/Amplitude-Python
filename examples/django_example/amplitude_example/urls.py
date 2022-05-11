from django.urls import path
from . import views


urlpatterns = [
    path('pageloaded', views.track_page_load, name='Track Page Load Event'),
    path('identify', views.set_age, name='Identify Event'),
    path('groupidentify', views.set_group_member, name='Group Identify Event'),
    path('setgroup', views.set_user_group, name='Set User Group'),
    path('revenue', views.track_revenue, name='Track Revenue Event'),
    path('flush', views.flush_event, name='Flush Events'),
]
