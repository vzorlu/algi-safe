from django.urls import path, include
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from .views import (
    CouncilView,
    DepartmanlarView,
    EditDepartmentView,
    KullanicilarView,
    UpdateDepartmentView,
    ReportsView,
    chronological_detections,
    get_department_class_names,
    map_reports_data,
    detection_counts,
    filtered_detections,
    council_filters,  # Add this import
    get_recent_addresses,
)
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, NotificationViewSet, check_notification_rule, RulesView
from stream.views import address_suggestions

router = DefaultRouter()
router.register(r"users", UserViewSet)

urlpatterns = [
    path(
        "raporlar/",
        ReportsView.as_view(),  # Update view
        name="raporlar",  # This is the name used in url reversing
    ),
    path(
        "rules-add/",
        RulesView.as_view(),
        name="rules-add",  # Keep this name as is
    ),
    path(
        "rules/add/",
        RulesView.as_view(),
        name="rules-add",
    ),
    path(
        "harita-raporlari/",
        login_required(CouncilView.as_view(template_name="harita-raporlari.html")),
        name="harita-raporlari",
    ),
    path("departmanlar/", DepartmanlarView.as_view(), name="departmanlar"),
    path("departmanlar/<int:pk>/edit/", EditDepartmentView.as_view(), name="edit_department"),
    path("departmanlar/<int:pk>/update/", UpdateDepartmentView.as_view(), name="update_department"),
    path("kullanicilar/", login_required(KullanicilarView.as_view()), name="kullanicilar"),
    path("api/", include(router.urls)),
    path(
        "api/stream/notifications/",
        csrf_exempt(NotificationViewSet.as_view({"post": "create", "get": "list"})),
        name="notification-list",
    ),
    path(
        "api/stream/notifications/<int:pk>/",
        csrf_exempt(NotificationViewSet.as_view({"delete": "destroy", "put": "update", "patch": "partial_update"})),
        name="notification-detail",
    ),
    path("api/departments/<int:department_id>/class-names/", get_department_class_names, name="department-class-names"),
    path("api/notifications/check/<str:class_name>/", check_notification_rule, name="check_notification_rule"),
    path("map-reports/data/", map_reports_data, name="map_reports_data"),  # Add new URL pattern
    path("api/stream/detection-counts/", detection_counts, name="detection_counts"),  # Add new URL pattern
    path(
        "api/stream/chronological-detections/", chronological_detections, name="chronological_detections"
    ),  # Add new URL pattern
    path("api/stream/filtered-detections/", filtered_detections, name="filtered_detections"),  # Add new endpoint
    path("api/stream/council-filters/<str:filter_id>/", council_filters, name="council_filters"),  # Add new URL pattern
    path("api/address-suggestions/", address_suggestions, name="address_suggestions"),  # Add this line
    path("api/recent-addresses/", get_recent_addresses, name="recent_addresses"),  # Add this line
]
