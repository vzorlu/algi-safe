from django.db import models
from django.contrib.auth import get_user_model
from django.apps import apps

User = get_user_model()


class Customer(models.Model):
    name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    company_name = models.CharField(max_length=255, blank=True, null=True)  # Şirket ismi
    tax_number = models.CharField(max_length=50, blank=True, null=True)  # Vergi numarası
    note = models.TextField(blank=True, null=True)  # Not
    package = models.ForeignKey("Package", on_delete=models.SET_NULL, null=True, blank=True)  # Relationship to Package
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    services = models.ManyToManyField("services.Services", related_name="customers", blank=True)

    def __str__(self):
        return self.name

    def get_services(self):
        Service = apps.get_model("services", "Service")
        return Service


class Package(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration_days = models.IntegerField()  # Duration of the package in days
    max_model = models.IntegerField(default=0)  # Maximum number of models
    max_camera = models.IntegerField(default=0)  # Maximum number of cameras
    max_device = models.IntegerField(default=0)  # Maximum number of devices

    def __str__(self):
        return self.name


class Devices(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name
