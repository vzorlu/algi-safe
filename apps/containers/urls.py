from django.urls import path
from django.contrib.auth.decorators import login_required
from .views import ContainersView, start_web_call

urlpatterns = [
    path(
        "container",
        login_required(ContainersView.as_view(template_name="container.html")),
        name="container",
    ),
    path("start-web-call/", start_web_call, name="start_web_call"),
]
