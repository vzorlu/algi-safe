from django.contrib import admin
from .models import Profile, Customer


class ProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "customer",
        "is_verified",
        "created_at",
    )


class CustomerAdmin(admin.ModelAdmin):
    list_display = ("name", "created_at", "updated_at")


admin.site.register(Profile, ProfileAdmin)
admin.site.register(Customer, CustomerAdmin)
