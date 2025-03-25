from django.urls import path, include, re_path
from rest_framework.routers import DefaultRouter
from . import consumers, views
from .views import (
    StreamImageViewSet,
    DetectionViewSet,
    NotificationViewSet,
    VideoUploadViewSet,
    ClassDataViewSet,
    MapReportsView,
    RulesViewSet,  # Add this import
    get_frame,
    proxy_image,
    address_suggestions,
)
from .api_views import class_data_list, icon_mappings, council_filters, map_reports_filter
from council import views as vi
from services.views import ServicesView

router = DefaultRouter()
router.register(r"images", StreamImageViewSet)
router.register(r"detections", DetectionViewSet)
router.register(r"videos", VideoUploadViewSet)
router.register(r"notifications", NotificationViewSet)
router.register(r"classdata", ClassDataViewSet)
router.register(r"rules", RulesViewSet, basename="rules")  # Add this line

app_name = "stream"

urlpatterns = [
    # Change this line - remove the "api/" prefix since it's already in the main urls.py
    path("", include(router.urls)),
    # Update these paths to remove the duplicate "api/" prefix
    path("debug/", views.debug_view, name="debug"),
    path("device-locations/", views.device_locations, name="device_locations"),
    # Keep these as they are since they don't have the api/ prefix
    path("icon-mappings/", icon_mappings, name="icon_mappings"),
    path("class-data/", class_data_list, name="class_data_list"),
    path("notifications/", views.NotificationListView.as_view(), name="notifications"),
    path("notifications/<int:pk>/", views.NotificationDetailView.as_view(), name="notification-detail"),
    path("council-filters/<str:filter_id>/", council_filters, name="council_filters"),
    path("map-reports/filter/<str:filter_category>/", map_reports_filter, name="map_reports_filter"),
    path("map-reports/data/", vi.map_reports_data, name="map_reports_data"),
    path("map-reports/", MapReportsView.as_view(), name="map_reports"),
    path("get-frame/", get_frame, name="get_frame"),
    path("offline-mode/", views.VideoProcessView.as_view(), name="offline_mode"),
    path("proxy-image/", proxy_image, name="proxy_image"),
    path("address-suggestions/", address_suggestions, name="address_suggestions"),
    path("rules-add/", RulesViewSet.as_view({"get": "list", "post": "create"}), name="rules-add"),  # Modified this line
    path("sources/", ServicesView.as_view(), name="sources"),  # Fixed ServicesView call
    re_path(r"ws/video/$", consumers.VideoConsumer.as_asgi()),
    re_path(r"wss/video/$", consumers.VideoConsumer.as_asgi()),
]
