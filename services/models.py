from django.db import models
from django.contrib.auth.models import User
from ultralytics import YOLO
import cv2
import tempfile
import os
from django.core.files.base import ContentFile
from council.models import Department
from stream.models import Notification


# Model for managing uploaded AI models
class Models(models.Model):
    TYPE_CHOICES = [
        ("YOLOV8", "YOLOv8"),
        ("TENSORRT", "TensorRT"),
        ("OPENVINO", "OpenVINO"),
    ]

    title = models.CharField(max_length=255)
    file = models.FileField(upload_to="models/")  # File upload field
    type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    sample_image = models.ImageField(upload_to="images/", blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    class_item = models.JSONField(blank=True, null=True)  # JSON field to store class items

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.pk:  # For new instances only
            super().save(*args, **kwargs)  # Save the file to make it accessible
            try:
                # Load model with YOLO
                yolo_model = YOLO(self.file.path)
                names_dict = yolo_model.model.names
                self.class_item = list(names_dict.values()) if isinstance(names_dict, dict) else list(names_dict)
            except Exception as e:
                print(f"Error loading model: {e}")
                self.class_item = []  # Fallback
            finally:
                super().save(*args, **kwargs)
        else:
            super().save(*args, **kwargs)


class Location(models.Model):
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    city = models.CharField(max_length=255)
    district = models.CharField(max_length=255)
    neighborhood = models.CharField(max_length=255)
    street = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.city}, {self.district}, {self.neighborhood}, {self.street}"


# Model for rules
class RulesList(models.Model):
    title = models.CharField(max_length=255)
    level = models.IntegerField()
    icon = models.ImageField(upload_to="rules/icons/", blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    value = models.CharField(max_length=255)

    def __str__(self):
        return self.title


# Model for services
class Services(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    models = models.ManyToManyField(Models, blank=True, related_name="services")

    def __str__(self):
        return self.name


class Reports(models.Model):
    LEVEL_CHOICES = [
        ("LOW", "Low"),
        ("MEDIUM", "Medium"),
        ("HIGH", "High"),
    ]

    STATUS_CHOICES = [
        ("OPEN", "Open"),
        ("IN_PROGRESS", "In Progress"),
        ("CLOSED", "Closed"),
    ]

    title = models.CharField(max_length=255)
    level = models.CharField(max_length=50, choices=LEVEL_CHOICES)
    assigned_to = models.ManyToManyField(User, related_name="assigned_reports", blank=True)
    departments = models.ManyToManyField(Department, related_name="reports", blank=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES)
    status_changed_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="status_changed_reports"
    )
    sources = models.ForeignKey("Sources", on_delete=models.CASCADE, related_name="reports")
    notification = models.ForeignKey(
        Notification, on_delete=models.CASCADE, related_name="reports", null=True, blank=True
    )
    captured_image = models.ImageField(upload_to="reports/images/", null=True, blank=True)
    video_clip = models.FileField(upload_to="reports/videos/", null=True, blank=True)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if self.pk is not None:
            old_report = Reports.objects.get(pk=self.pk)
            if old_report.status != self.status:
                self.status_changed_by = kwargs.pop("user", None)
        super().save(*args, **kwargs)


# Model for video sources
class Sources(models.Model):
    title = models.CharField(max_length=255)
    location = models.CharField(max_length=255, blank=True, null=True)
    url = models.CharField(max_length=255, default="RTSP://")
    type = models.CharField(max_length=255)
    addtype = models.CharField(max_length=255, blank=True, null=True)
    fps = models.IntegerField(blank=True, null=True)
    image = models.ImageField(upload_to="images/", blank=True, null=True)
    status = models.CharField(max_length=50, default="0", blank=True, null=True)
    resolution = models.CharField(max_length=50, blank=True, null=True)
    width = models.IntegerField(blank=True, null=True)
    height = models.IntegerField(blank=True, null=True)
    is_mobile = models.BooleanField(default=False)
    is_record = models.BooleanField(default=False)
    record_folder = models.CharField(max_length=255, blank=True, null=True)
    inlocation = models.ManyToManyField(Location, blank=True, related_name="sources")
    codec = models.CharField(max_length=10, null=True, blank=True)
    total_frames = models.IntegerField(null=True, blank=True)
    polygons = models.JSONField(
        null=True,
        blank=True,
        help_text="Store polygon data as list of objects: [{coordinates: [[x1,y1], [x2,y2],...], label: 'string', color: 'string', transition_lines: [[[x1,y1], [x2,y2]], ...], crossing_direction: ['left-to-right', ...]}]",
    )

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # Save the instance first to get the ID
        super(Sources, self).save(*args, **kwargs)

        # If URL is provided, get video properties
        resolution, width, height, status, fps, image_file, codec, total_frames = get_video_properties(self.url)

        # Ensure fps is a number
        if isinstance(fps, (int, float)):
            self.fps = fps
        else:
            self.fps = None  # or some default value

        self.resolution = resolution
        self.width = width
        self.height = height
        self.status = "1" if status else "0"
        self.codec = codec
        self.total_frames = total_frames

        if image_file:
            filename = os.path.basename(image_file.name)
            self.image.save(filename, ContentFile(image_file.read()), save=False)
        else:
            self.image = None

        super(Sources, self).save(*args, **kwargs)


def get_video_properties(url):
    cap = cv2.VideoCapture(url)
    if not cap.isOpened():
        return None, None, None, False, None, None, None, None

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    codec_int = int(cap.get(cv2.CAP_PROP_FOURCC))
    # Codec bilgisini dört karakterli stringe dönüştür
    codec = "".join([chr((codec_int >> 8 * i) & 0xFF) for i in range(4)])
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    ret, frame = cap.read()
    cap.release()

    if not ret:
        return None, width, height, False, fps, None, codec, total_frames

    # Frame'i geçici bir dosyaya kaydet
    temp_file = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
    cv2.imwrite(temp_file.name, frame)

    return f"{width}x{height}", width, height, True, fps, temp_file, codec, total_frames
