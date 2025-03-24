from django.urls import path
from django.contrib.auth.decorators import login_required
from .views import JobssView

urlpatterns = [
    path(
        "jobs",
        login_required(JobssView.as_view(template_name="jobs.html")),
        name="jobs",
    )
]
