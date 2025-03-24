from django.urls import path
from .views import (
    DashboardsView
)
from django.contrib.auth.decorators import login_required

urlpatterns = [

    # Dashboard Sayfaları
    path(
        "",
        login_required(DashboardsView.as_view(template_name="dashboard_analytics.html")),
        name="index",
    ),
    path(
        "dashboard/crm/",
        login_required(DashboardsView.as_view(template_name="dashboard_crm.html")),
        name="dashboard-crm",
    ),
    path(
        "dashboard/ready-models/",
        login_required(DashboardsView.as_view(template_name="dashboard_models.html")),
        name="ready-models",
    ),
    path(
        "rules/",
        login_required(DashboardsView.as_view(template_name="rules.html")),
        name="rules",
    )
]
