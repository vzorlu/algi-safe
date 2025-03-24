# ... (diğer importlar sabit kalabilir)
from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

User = get_user_model()

# models.py'da Way modeliniz zaten şu şekilde revize edilmiş olsun (daha önce konuştuğumuz gibi):


class Way(models.Model):
    base_type = models.CharField(max_length=50)
    way_id = models.IntegerField(unique=True)
    nodes = models.JSONField()
    destination = models.CharField(max_length=255, null=True, blank=True)
    highway = models.CharField(max_length=50)
    hist_ref = models.CharField(max_length=50, null=True, blank=True)
    loc_name = models.CharField(max_length=50, null=True, blank=True)
    maxspeed = models.CharField(max_length=10, null=True, blank=True)
    name = models.CharField(max_length=255)
    oneway = models.CharField(max_length=10)
    ref = models.CharField(max_length=50)
    lanes = models.CharField(max_length=10, null=True, blank=True)
    nat_ref = models.CharField(max_length=50, null=True, blank=True)
    toll = models.CharField(max_length=10, null=True, blank=True)
    tracker_id = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return self.name


class ClassType(models.Model):
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Sınıf Tipi"
        verbose_name_plural = "Sınıf Tipleri"


class Department(models.Model):
    name = models.CharField(max_length=255)
    class_names = models.ManyToManyField(ClassType, related_name="departments")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Departman"
        verbose_name_plural = "Departmanlar"


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="council_profile")
    department = models.ForeignKey("Department", on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.user.username}'s council profile"


@receiver(post_save, sender=User)
def create_council_profile(sender, instance, created, **kwargs):
    # Create profile if it doesn't exist, regardless of whether user is new or not
    Profile.objects.get_or_create(user=instance)


@receiver(post_save, sender=User)
def save_council_profile(sender, instance, **kwargs):
    try:
        instance.council_profile.save()
    except Profile.DoesNotExist:
        Profile.objects.create(user=instance)
