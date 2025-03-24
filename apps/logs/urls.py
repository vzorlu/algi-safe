from django.urls import path
from django.contrib.auth.decorators import login_required
from .views import LogsView

urlpatterns = [
    path(
            "logs",
            login_required(LogsView.as_view(template_name="index.html")),
            name="logs",
        ),
]
