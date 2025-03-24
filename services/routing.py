from django.urls import re_path
from . import views

websocket_urlpatterns = [
    re_path(r'^ws/video/(?P<source_id>\d+)/$', views.VideoStreamConsumer.as_asgi()),
]
