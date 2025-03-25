import os
import tempfile
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.decorators import api_view, action
from web_project import TemplateLayout
from config import settings
import logging

from .models import (
    NotificationType,
    StreamImage,
    Detection,
    VideoUpload,
    Notification,
    ClassData,
    OfflineMode,
    RulesAdd,
)
from .serializers import (
    StreamImageSerializer,
    DetectionSerializer,
    VideoUploadSerializer,
    NotificationSerializer,
    ClassDataSerializer,
    RulesAddSerializer,
)
from ultralytics import YOLO
from django.db.models import Count, Exists, OuterRef, Max
from rest_framework.filters import OrderingFilter
from rest_framework.test import APIRequestFactory
from django.views.generic import ListView, DetailView, TemplateView
from rest_framework.permissions import AllowAny
import cv2
import base64
from django.http import JsonResponse
from django.http import HttpResponse
import requests
from django.views.decorators.http import require_http_methods

logger = logging.getLogger(__name__)

# Initialize YOLO model at module level
yolo_model = YOLO("belediye.pt")

yolo11 = YOLO("yolov8n.pt")  # Standard model for common objects


# Replace static JSON data with database query
# Create a lookup dictionary for faster access
def get_class_speech_lookup():
    class_data = ClassData.objects.all()
    return {item.Name: item.Speech or "" for item in class_data}


# Function to refresh lookup data
def refresh_class_speech_lookup():
    global CLASS_SPEECH_LOOKUP
    CLASS_SPEECH_LOOKUP = get_class_speech_lookup()


# Initialize lookup on module load
CLASS_SPEECH_LOOKUP = {}  # Initialize as empty dict
refresh_class_speech_lookup()


def extract_area(address):
    parts = [part.strip() for part in address.split(",")]
    print(parts)
    for part in parts:
        if "Sokak" in part:
            return part
        elif "Caddesi" in part:
            print(part)
            return part

    # If no street/avenue found, return neighborhood
    for part in parts:
        if part and part not in ["", " "]:
            print(part)
            return part

    return None


class StreamImageViewSet(viewsets.ModelViewSet):
    permission_classes = [AllowAny]  # Add this line
    queryset = StreamImage.objects.all()  # Add base queryset
    serializer_class = StreamImageSerializer
    parser_classes = (MultiPartParser, FormParser)
    filter_backends = [OrderingFilter]
    ordering_fields = ["timestamp", "processed", "area", "detection_count"]
    ordering = ["-timestamp"]  # Default sorting

    def get_queryset(self):
        base_queryset = StreamImage.objects.all()

        has_detections = self.request.query_params.get("has_detections", None)
        if has_detections == "true":
            # Use exists() subquery instead of annotation
            detections_exist = Detection.objects.filter(image=OuterRef("pk"))
            base_queryset = base_queryset.annotate(has_detections=Exists(detections_exist)).filter(has_detections=True)

        return base_queryset.prefetch_related("detections")

    def create(self, request, *args, **kwargs):
        # Refresh class lookup to ensure we have the latest data
        refresh_class_speech_lookup()

        logger.info("Step 1: Incoming data: %s", request.data)
        temp_file = None

        try:
            # Extract area from fulladdress
            fulladdress = request.data.get("fulladdress", [""])
            print("--fa", fulladdress)
            area = extract_area(fulladdress)

            # Update request data with area
            mutable_data = request.data.copy()
            mutable_data["area"] = area

            # Validate and save StreamImage
            serializer = self.get_serializer(data=mutable_data)
            serializer.is_valid(raise_exception=True)
            stream_image = serializer.save()
            logger.info("Step 2: Validated data, saved StreamImage")

            # Get image file
            image_file = request.FILES.get("image")
            if not image_file:
                return Response({"error": "No image file provided"}, status=status.HTTP_400_BAD_REQUEST)

            # Save image content to temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
            for chunk in image_file.chunks():
                temp_file.write(chunk)
            temp_file.close()

            # Process YOLO detections
            logger.info("Step 4: YOLO detection started")
            results = yolo_model.predict(source=temp_file.name)

            # Process standard YOLO detections for common objects
            logger.info("Step 4b: YOLOv8 standard detection started")
            standard_results = yolo11.predict(source=temp_file.name)

            # Track if any speech content was found
            speech_content = []

            # Create Detection objects from custom model
            for r in results[0].boxes.data:
                x1, y1, x2, y2, conf, cls = r.tolist()
                class_name = results[0].names[int(cls)]

                # Check if this class has speech content and add it
                speech_text = CLASS_SPEECH_LOOKUP.get(class_name, "")
                if speech_text:
                    speech_content.append(speech_text)

                # Create Detection object
                Detection.objects.create(
                    image=stream_image,
                    class_name=class_name,
                    x_min=float(x1),
                    y_min=float(y1),
                    x_max=float(x2),
                    y_max=float(y2),
                    confidence=float(conf),
                )

                # Trigger notification system
                try:
                    factory = APIRequestFactory()
                    request = factory.post("/api/notifications/send/", {"class_field": class_name}, format="json")
                except Exception as e:
                    logger.error(f"Error sending notification for {class_name}: {str(e)}")

            # Create Detection objects from standard model (person, car, etc.)
            for r in standard_results[0].boxes.data:
                x1, y1, x2, y2, conf, cls = r.tolist()
                class_name = standard_results[0].names[int(cls)]

                # Filter for only the specific classes we want from standard model
                wanted_classes = ["person", "car", "motorcycle", "trunck", "dog", "cat"]
                if (
                    class_name in wanted_classes and float(conf) > 0.45
                ):  # Higher confidence threshold for standard objects
                    # Check if this class has speech content and add it (prefixed with std_)
                    speech_text = CLASS_SPEECH_LOOKUP.get(class_name, "")
                    if speech_text:
                        speech_content.append(speech_text)

                    Detection.objects.create(
                        image=stream_image,
                        class_name=f"{class_name}",
                        x_min=float(x1),
                        y_min=float(y1),
                        x_max=float(x2),
                        y_max=float(y2),
                        confidence=float(conf),
                    )

            # Update the StreamImage with any speech content found
            if speech_content:
                stream_image.speech = " ".join(speech_content)
                stream_image.save()

            # Get the updated serializer data after saving all detections
            updated_serializer = self.get_serializer(stream_image)
            return Response(updated_serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Error in StreamImageViewSet.create: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        finally:
            # Cleanup temporary file
            if temp_file and os.path.exists(temp_file.name):
                os.unlink(temp_file.name)

    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @action(detail=False, methods=["get"])
    def with_detections(self, request):
        queryset = StreamImage.objects.annotate(detection_count=Count("detections")).filter(detection_count__gt=0)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class DetectionViewSet(viewsets.ModelViewSet):
    queryset = Detection.objects.all()
    serializer_class = DetectionSerializer
    filter_backends = [OrderingFilter]
    ordering_fields = ["timestamp", "confidence", "class_name"]
    ordering = ["-timestamp"]  # Default sorting


class NotificationViewSet(viewsets.ModelViewSet):
    permission_classes = [AllowAny]
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer

    def create(self, request, *args, **kwargs):
        try:
            logger.debug(f"Incoming notification data: {request.data}")

            # Prepare data for serializer
            data = {
                "detection_id": request.data.get("detection_id"),
                "class_name": request.data.get("class_name"),
                "rule_name": request.data.get("rule_name"),
                "message": request.data.get("message"),
                "department": request.data.get("department"),
                "severity": request.data.get("severity", "MEDIUM"),
                "notification_types": request.data.get("notification_types", []),
                "frequency": request.data.get("frequency", "immediate"),
                "send_time": request.data.get("send_time"),
            }

            serializer = self.get_serializer(data=data)

            if not serializer.is_valid():
                logger.error(f"Validation errors: {serializer.errors}")
                return Response(
                    {"status": "error", "message": "Validation error", "errors": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            self.perform_create(serializer)

            return Response(
                {"status": "success", "message": "Notification created successfully", "data": serializer.data},
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            logger.error(f"Error creating notification: {str(e)}", exc_info=True)
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class VideoUploadViewSet(viewsets.ModelViewSet):
    queryset = VideoUpload.objects.all()
    serializer_class = VideoUploadSerializer
    parser_classes = (MultiPartParser, FormParser)
    filter_backends = [OrderingFilter]
    ordering_fields = ["timestamp", "device_id"]
    ordering = ["-timestamp"]

    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


@api_view(["GET"])
def debug_view(request):
    logger.info(f"Headers: {request.headers}")
    logger.info(f"Method: {request.method}")
    logger.info(f"Data: {request.data}")
    return Response({"status": "debug info logged"})


@api_view(["GET"])
def device_locations(request):
    # Get latest location for each unique deviceuuid
    latest_locations = (
        StreamImage.objects.values("deviceuuid")
        .annotate(latest_timestamp=Max("timestamp"))
        .filter(lang__isnull=False, long__isnull=False)
    )

    # Get the full records for these latest locations
    devices = []
    for loc in latest_locations:
        device = StreamImage.objects.filter(deviceuuid=loc["deviceuuid"], timestamp=loc["latest_timestamp"]).first()
        if device:
            devices.append(
                {
                    "deviceuuid": device.deviceuuid,
                    "lang": device.lang,
                    "long": device.long,
                    "fulladdress": device.fulladdress,
                    "timestamp": device.timestamp,
                }
            )

    return Response(devices)


class NotificationListView(ListView):
    model = Notification
    template_name = "stream/notification_list.html"
    context_object_name = "notifications"
    ordering = ["-created_at"]


class NotificationDetailView(DetailView):
    model = Notification
    template_name = "stream/notification_detail.html"
    context_object_name = "notification"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["notification_types"] = NotificationType.objects.all()
        return context


class CouncilView(TemplateView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        notification_types = NotificationType.objects.filter(is_active=True).prefetch_related("notifications")
        context["notification_types"] = notification_types
        return context


class ClassDataViewSet(viewsets.ModelViewSet):
    queryset = ClassData.objects.all()
    serializer_class = ClassDataSerializer
    permission_classes = [AllowAny]

    @action(detail=False, methods=["post"])
    def refresh_lookup(self, request):
        refresh_class_speech_lookup()
        return Response({"status": "Class speech lookup refreshed"})


class MapReportsView(TemplateView):
    template_name = "stream/map_reports.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["GOOGLE_MAPS_API_KEY"] = settings.GOOGLE_MAPS_API_KEY
        return context


class VideoProcessView(TemplateView):
    template_name = "offline-mode.html"

    def get_context_data(self, **kwargs):
        try:
            context = super().get_context_data(**kwargs)
            context = TemplateLayout.init(self, context)
            context["videos"] = OfflineMode.objects.all().order_by("-created_at")
            context["MAPBOX_ACCESS_TOKEN"] = settings.MAPBOX_ACCESS_TOKEN
            return context
        except Exception as e:
            print(f"Error in VideoProcessView: {str(e)}")  # Debug print
            raise

    def get_frame(self, video_path, frame_number):
        try:
            cap = cv2.VideoCapture(video_path)
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            ret, frame = cap.read()
            if ret:
                # Convert frame to base64
                _, buffer = cv2.imencode(".jpg", frame)
                frame_b64 = base64.b64encode(buffer).decode("utf-8")
                total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                fps = cap.get(cv2.CAP_PROP_FPS)
                return {"frame": frame_b64, "total_frames": total_frames, "fps": fps, "status": "success"}
            return {"status": "error", "message": "Frame not found"}
        finally:
            if cap:
                cap.release()


@api_view(["GET"])
def get_frame(request):
    video_id = request.GET.get("video_id")
    frame_number = int(request.GET.get("frame", 0))

    try:
        video = OfflineMode.objects.get(id=video_id)
        video_path = os.path.join(settings.MEDIA_ROOT, str(video.video_file))

        cap = cv2.VideoCapture(video_path)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        ret, frame = cap.read()

        if ret:
            # Process frame with YOLOv8
            results = yolo11.predict(source=frame, conf=0.45)[0]

            # Draw detections on frame
            for box in results.boxes.data:
                x1, y1, x2, y2, conf, cls = box.tolist()
                class_name = results.names[int(cls)]

                # Draw rectangle and label
                cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
                cv2.putText(
                    frame,
                    f"{class_name} {conf:.2f}",
                    (int(x1), int(y1) - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.9,
                    (0, 255, 0),
                    2,
                )

            # Convert to base64
            _, buffer = cv2.imencode(".jpg", frame)
            frame_b64 = base64.b64encode(buffer).decode("utf-8")

            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)

            return JsonResponse(
                {
                    "status": "success",
                    "frame": frame_b64,
                    "total_frames": total_frames,
                    "fps": fps,
                    "detections": [
                        {
                            "class": results.names[int(box.cls)],
                            "confidence": float(box.conf),
                            "bbox": box.xyxy[0].tolist(),
                        }
                        for box in results.boxes
                    ],
                }
            )

    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)})
    finally:
        if "cap" in locals():
            cap.release()


def proxy_image(request):
    """Image proxy to handle CORS and authentication"""
    url = request.GET.get("url")
    if not url:
        return HttpResponse("No URL provided", status=400)

    try:
        # Handle relative URLs
        if not url.startswith("http"):
            url = f"{url}"

        response = requests.get(url, stream=True)
        return HttpResponse(response.content, content_type=response.headers.get("content-type", "image/jpeg"))
    except Exception as e:
        return HttpResponse(str(e), status=500)


@require_http_methods(["GET"])
def address_suggestions(request):
    """API endpoint to get address suggestions based on user input"""
    try:
        query = request.GET.get("query", "").strip()
        if len(query) < 2:
            return JsonResponse({"suggestions": []})

        # Query the StreamImage model for unique addresses
        addresses = (
            StreamImage.objects.filter(fulladdress__icontains(query))
            .values_list("fulladdress", flat=True)
            .distinct()
            .order_by("fulladdress")[:10]
        )

        # Format suggestions with area and full address
        suggestions = []
        for addr in addresses:
            if addr:
                parts = addr.split(",")
                area = parts[0].strip() if parts else ""
                suggestions.append({"value": addr, "area": area, "label": addr})

        return JsonResponse({"suggestions": suggestions})
    except Exception as e:
        logger.error(f"Error in address suggestions: {str(e)}", exc_info=True)
        return JsonResponse({"error": str(e)}, status=500)


class RulesViewSet(viewsets.ModelViewSet):
    queryset = RulesAdd.objects.all()
    serializer_class = RulesAddSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        try:
            data = request.data.copy()

            # Convert string 'false'/'true' to boolean
            data["create_task"] = str(data.get("create_task", "")).lower() == "true"
            data["create_notification"] = str(data.get("create_notification", "")).lower() == "true"

            # Remove empty strings
            for key in ["task_type", "task_description", "task_due_date", "message", "send_time"]:
                if key in data and data[key] == "":
                    data.pop(key)

            serializer = self.get_serializer(data=data)
            if not serializer.is_valid():
                return Response({"status": "error", "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

            rule = serializer.save()
            return Response(
                {"status": "success", "data": self.get_serializer(rule).data}, status=status.HTTP_201_CREATED
            )

        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)
