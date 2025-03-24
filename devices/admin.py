# admin.py

from django.contrib import admin
from .models import Device, License, DeviceData, DeviceReport


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ("device_id", "name", "license_key", "registered_on", "mac_address")
    search_fields = ("device_id", "name", "mac_address")


@admin.register(License)
class LicenseAdmin(admin.ModelAdmin):
    list_display = ("license_key", "license_type", "is_active", "expiry_date", "available_devices")
    search_fields = ("license_key",)


@admin.register(DeviceData)
class DeviceDataAdmin(admin.ModelAdmin):
    list_display = ("device", "cpu_usage", "memory_usage", "disk_space", "timestamp")
    search_fields = ("device__device_id",)


@admin.register(DeviceReport)
class DeviceReportAdmin(admin.ModelAdmin):
    list_display = ("mac_address", "created_at")
    search_fields = ("mac_address",)
