from django.urls import path, include
from . import views
from django.contrib.auth.decorators import login_required
from rest_framework.routers import DefaultRouter
from .views import DevicesView

# API yönlendirmeleri için router oluşturun
router = DefaultRouter()

urlpatterns = [
    path("api/register_device/", views.register_device, name="register_device"),
    path("api/web_activate_device/", views.web_activate_device, name="web_activate_device"),  # Web Aktivasyonu
    path("api/sh_activate_device/", views.sh_activate_device, name="sh_activate_device"),  # SH Aktivasyonu
    path("api/post_device_data/", views.post_device_data, name="post_device_data"),
    path("api/verify_license/", views.verify_license, name="verify_license"),
    path("api/device_list/", views.device_list, name="device_list"),
    path(
        "devices/device_list/", views.device_list, name="device_list"
    ),  # device_list view'i için doğru URL tanımlaması
    path(
        "devices/list",
        login_required(DevicesView.as_view(template_name="devices.html")),
        name="devices-list",
    ),
    path(
        "devices/map",
        login_required(DevicesView.as_view(template_name="device_map.html")),
        name="device-map",
    ),
    path("devices/add/", views.register_device, name="register_device"),
    # Notification API'lerini dahil edin
    path("api/", include(router.urls)),  # router URL'lerini ekleyin
]
