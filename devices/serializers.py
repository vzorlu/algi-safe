from rest_framework import serializers
from .models import Device, License, DeviceData, DeviceReport


class DeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = "__all__"  # Gerekli alanları kontrol edin


class LicenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = License
        fields = "__all__"


class DeviceDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceData
        fields = "__all__"


class DeviceReportSerializer(serializers.ModelSerializer):  # NEW: Added DeviceReportSerializer
    class Meta:
        model = DeviceReport
        fields = "__all__"
