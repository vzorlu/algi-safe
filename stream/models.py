from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import FileExtensionValidator

User = get_user_model()


class NotificationType(models.Model):
    NOTIFICATION_CHOICES = [
        ("EMAIL", "E-posta"),
        ("SMS", "SMS"),
        ("PUSH", "Push Bildirim"),
        ("TELEGRAM", "Telegram"),
        ("WHATSAPP", "WhatsApp"),
    ]

    name = models.CharField(max_length=100, choices=NOTIFICATION_CHOICES)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.get_name_display()


class StreamImage(models.Model):
    image = models.ImageField(upload_to="stream_images/")
    timestamp = models.DateTimeField(auto_now_add=True)
    processed = models.BooleanField(default=False)
    lang = models.FloatField(null=True, blank=True)
    long = models.FloatField(null=True, blank=True)
    fulladdress = models.TextField(null=True, blank=True)
    area = models.CharField(max_length=255, null=True, blank=True)
    deviceuuid = models.CharField(max_length=255, null=True, blank=True)
    speech = models.TextField(null=True, blank=True)  # Make sure this field exists

    def __str__(self):
        return self.deviceuuid


class Notification(models.Model):
    SEVERITY_CHOICES = [("LOW", "Düşük"), ("MEDIUM", "Orta"), ("HIGH", "Yüksek")]

    FREQUENCY_CHOICES = [("immediate", "Anında"), ("daily", "Günlük"), ("weekly", "Haftalık"), ("monthly", "Aylık")]

    detection = models.ForeignKey("Detection", on_delete=models.CASCADE, related_name="notifications")
    class_name = models.CharField(max_length=100)
    rule_name = models.CharField(max_length=255)
    message = models.TextField()
    department = models.ForeignKey("council.Department", on_delete=models.CASCADE)
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES, default="MEDIUM")
    notification_type = models.ManyToManyField(NotificationType)
    frequency = models.CharField(max_length=10, choices=FREQUENCY_CHOICES, default="immediate")
    send_time = models.TimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    create_task = models.BooleanField(default=False)
    tasks = models.ManyToManyField("Task", blank=True, related_name="notifications")

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.rule_name} - {self.class_name}"

    def create_related_task(self, task_data):
        """
        Bildirimle ilişkili yeni görev oluşturur
        """
        task = Task.objects.create(
            title=f"Tespit: {self.rule_name}",
            description=task_data.get("description", self.message),
            task_type=task_data.get("task_type", "INSPECTION"),
            priority=task_data.get("priority", "MEDIUM"),
            assigned_to=self.department,
            created_by=task_data.get("created_by"),
            due_date=task_data.get("due_date"),
        )
        self.tasks.add(task)
        return task


class Detection(models.Model):
    image = models.ForeignKey(StreamImage, related_name="detections", on_delete=models.CASCADE)
    class_name = models.CharField(max_length=100)
    x_min = models.FloatField(default=0.0)
    y_min = models.FloatField(default=0.0)
    x_max = models.FloatField(default=0.0)
    y_max = models.FloatField(default=0.0)
    confidence = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)
    notification = models.ForeignKey(
        Notification, on_delete=models.SET_NULL, null=True, blank=True, related_name="detections"
    )

    def __str__(self):
        return self.class_name


class VideoUpload(models.Model):
    video = models.FileField(
        upload_to="videos/", validators=[FileExtensionValidator(allowed_extensions=["mp4", "avi", "mov"])]
    )
    json_file = models.FileField(
        upload_to="json_files/", validators=[FileExtensionValidator(allowed_extensions=["json"])]
    )
    device_id = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.device_id} - {self.timestamp}"


class Task(models.Model):
    TASK_STATUS_CHOICES = [
        ("PENDING", "Beklemede"),
        ("IN_PROGRESS", "Devam Ediyor"),
        ("COMPLETED", "Tamamlandı"),
        ("CANCELLED", "İptal Edildi"),
    ]

    TASK_TYPE_CHOICES = [("INSPECTION", "Saha Denetimi"), ("INVESTIGATION", "İnceleme"), ("ENFORCEMENT", "Yaptırım")]

    PRIORITY_CHOICES = [("LOW", "Düşük"), ("MEDIUM", "Orta"), ("HIGH", "Yüksek")]

    title = models.CharField(max_length=255)
    description = models.TextField()
    task_type = models.CharField(max_length=20, choices=TASK_TYPE_CHOICES)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default="MEDIUM")
    status = models.CharField(max_length=20, choices=TASK_STATUS_CHOICES, default="PENDING")
    assigned_to = models.ForeignKey("council.Department", on_delete=models.CASCADE, related_name="assigned_tasks")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="created_tasks")
    due_date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} - {self.get_status_display()}"


class ClassData(models.Model):
    """Model to store object detection class data instead of using static JSON data"""

    id = models.AutoField(primary_key=True)
    Name = models.CharField(max_length=100, unique=True)
    Turkish = models.CharField(max_length=100)
    Speech = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        verbose_name = "Class Data"
        verbose_name_plural = "Class Data"
        ordering = ["id"]

    def __str__(self):
        return f"{self.Name} - {self.Turkish}"


class OfflineMode(models.Model):
    video_file = models.FileField(
        upload_to="offline_videos/",
        validators=[FileExtensionValidator(allowed_extensions=["mp4", "avi", "mov"])],
        verbose_name="Video Dosyası",
    )

    device_name = models.CharField(max_length=255, verbose_name="Cihaz Adı")

    area = models.CharField(max_length=255, verbose_name="Bölge", null=True, blank=True)

    processed = models.BooleanField(default=False, verbose_name="İşlem Durumu")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma Tarihi")

    updated_at = models.DateTimeField(auto_now=True, verbose_name="Güncellenme Tarihi")

    class Meta:
        verbose_name = "Çevrimdışı Video"
        verbose_name_plural = "Çevrimdışı Videolar"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.device_name} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"


class RulesAdd(models.Model):
    detection = models.ForeignKey("Detection", on_delete=models.CASCADE, related_name="rules")
    class_name = models.CharField(max_length=100)
    rule_name = models.CharField(max_length=255)
    rule_scope = models.CharField(max_length=10, choices=[("single", "Tek Tespit"), ("all", "Tüm Tespitler")])
    department = models.ForeignKey("council.Department", on_delete=models.CASCADE)

    # Task fields
    create_task = models.BooleanField(default=False)
    task_type = models.CharField(max_length=50, null=True, blank=True)
    task_description = models.TextField(null=True, blank=True)
    task_due_date = models.DateTimeField(null=True, blank=True)

    # Notification fields
    create_notification = models.BooleanField(default=False)
    notification_types = models.ManyToManyField("NotificationType", blank=True)
    message = models.TextField(null=True, blank=True)
    frequency = models.CharField(max_length=20, null=True, blank=True)
    send_time = models.TimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Kural"
        verbose_name_plural = "Kurallar"

    def __str__(self):
        return f"{self.rule_name} - {self.class_name}"
