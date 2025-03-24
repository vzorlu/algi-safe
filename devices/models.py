from django.db import models
from django.utils import timezone


class Device(models.Model):
    device_id = models.AutoField(primary_key=True)  # Otomatik artan ID
    name = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    license_key = models.ForeignKey("License", on_delete=models.SET_NULL, null=True, blank=True)
    registered_on = models.DateTimeField(auto_now_add=True)
    mac_address = models.CharField(max_length=100, unique=True, blank=True, null=True)
    ip_address = models.GenericIPAddressField(protocol="both", unpack_ipv4=True, null=True, blank=True)
    ssh_username = models.CharField(max_length=100, blank=True, null=True)
    ssh_password = models.CharField(max_length=100, blank=True, null=True)
    tunnel_info = models.JSONField(blank=True, null=True)
    cpu_info = models.CharField(max_length=255, blank=True, null=True)
    gpu_info = models.CharField(max_length=255, blank=True, null=True)

    DEVICE_TYPE_CHOICES = [
        ("NVIDIA_GPU", "NVIDIA GPU"),
        ("INTEL_CPU", "Intel CPU"),
        ("CPU", "CPU"),
        ("JETSON", "Jetson"),
    ]
    type = models.CharField(max_length=50, choices=DEVICE_TYPE_CHOICES, blank=True, null=True)

    INFRASTRUCTURE_CHOICES = [
        ("ON_PREMISE", "On-Premise"),
        ("CLOUD", "Cloud"),
    ]
    infrastructure = models.CharField(max_length=50, choices=INFRASTRUCTURE_CHOICES, blank=True, null=True)

    OPERATING_SYSTEM_CHOICES = [
        ("UBUNTU", "Ubuntu"),
        ("WINDOWS", "Windows"),
    ]
    operating_system = models.CharField(max_length=50, choices=OPERATING_SYSTEM_CHOICES, blank=True, null=True)

    def __str__(self):
        return self.name if self.name else f"Device {self.device_id}"


class License(models.Model):
    LICENSE_TYPE_CHOICES = [
        ("DEMO", "Demo"),
        ("TIMED", "Süreli"),
        ("UNLIMITED", "Süresiz"),
    ]
    license_key = models.CharField(max_length=100, unique=True)
    license_type = models.CharField(max_length=50, choices=LICENSE_TYPE_CHOICES)
    is_active = models.BooleanField(default=True)
    expiry_date = models.DateTimeField(null=True, blank=True)
    available_devices = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.license_key} ({self.license_type})"


class DeviceData(models.Model):
    device = models.ForeignKey(Device, on_delete=models.CASCADE)
    cpu_usage = models.FloatField()
    memory_usage = models.FloatField()
    disk_space = models.FloatField()
    timestamp = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.device.device_id} - {self.timestamp}"


class DeviceReport(models.Model):
    mac_address = models.CharField(max_length=100)
    data = models.JSONField()  # Cihaz verilerini JSON formatında tutar
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Report for {self.mac_address} at {self.created_at}"
