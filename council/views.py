from django.views.generic import TemplateView
from django.template.defaulttags import register
from django.views.generic.edit import UpdateView
from django.urls import reverse_lazy
from django.contrib.auth import get_user_model
from django.shortcuts import render
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_http_methods
from django.conf import settings
from django.db.models import Count, Max
from django.core.paginator import Paginator

from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import action
from rest_framework.response import Response

from stream.models import NotificationType, RulesAdd, StreamImage, Notification, ClassData
from stream.serializers import NotificationSerializer
from council.models import Department, Profile, ClassType
from web_project import TemplateLayout
from .serializers import UserSerializer

from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


@register.filter
def get_item(dictionary, key):
    if dictionary is None:
        return None
    try:
        return dictionary.get(key)
    except AttributeError:
        return None


class CouncilView(TemplateView):
    template_name = "raporlar.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Initialize template layout first
        context = TemplateLayout.init(self, context)

        departments = Department.objects.all()
        notification_types = NotificationType.objects.filter(is_active=True)
        stream_images = StreamImage.objects.prefetch_related("detections").order_by("-id")

        context.update(
            {
                "stream_images": stream_images,
                "departments": departments,
                "notification_types": notification_types,
                "notification_choices": NotificationType.NOTIFICATION_CHOICES,
                "mapbox_access_token": settings.MAPBOX_ACCESS_TOKEN,  # Pass the token here
            }
        )

        return context


class DepartmanlarView(TemplateView):
    template_name = "departmanlar.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context = TemplateLayout.init(self, context)
        context.update(
            {
                "departments": Department.objects.all().order_by("-created_at"),
                "class_data": ClassData.objects.all(),
            }
        )
        return context


class EditDepartmentView(UpdateView):
    model = Department
    template_name = "edit_department.html"
    fields = ["name"]
    success_url = reverse_lazy("departmanlar")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context = TemplateLayout.init(self, context)
        return context


class KullanicilarView(TemplateView):
    template_name = "kullanicilar.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context = TemplateLayout.init(self, context)
        User = get_user_model()
        context.update({"users": User.objects.all().order_by("-date_joined"), "departments": Department.objects.all()})
        return context


class UserViewSet(viewsets.ModelViewSet):
    queryset = get_user_model().objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()

        # Ensure council profile exists
        council_profile, created = Profile.objects.get_or_create(user=instance)

        # Update department if specified
        department_id = request.data.get("department_id")
        if department_id:
            try:
                department = Department.objects.get(id=department_id)
                council_profile.department = department
            except Department.DoesNotExist:
                return Response({"error": "Department not found"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            council_profile.department = None

        council_profile.save()

        # Update other user fields
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def toggle_status(self, request, pk=None):
        user = self.get_object()
        user.is_active = not user.is_active
        user.save()
        return Response({"status": "success"})


def department_list(request):
    departments = Department.objects.all()
    class_types = ClassType.objects.all()
    class_data = ClassData.objects.all()
    return render(
        request,
        "departmanlar.html",
        {
            "departments": departments,
            "class_types": class_types,
            "class_data": class_data,
        },
    )


@method_decorator(csrf_exempt, name="dispatch")
class UpdateDepartmentView(View):
    def put(self, request, pk):
        try:
            import json

            data = json.loads(request.body)
            department = Department.objects.get(pk=pk)
            department.name = data["name"]

            # Update class names
            class_names = data["class_names"]
            department.class_names.clear()
            for class_name in class_names:
                class_type, _ = ClassType.objects.get_or_create(name=class_name)
                department.class_names.add(class_type)

            department.save()
            return JsonResponse({"status": "success"})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)


# In your user update view
def update_user(request, user_id):
    user = User.objects.get(id=user_id)
    department_id = request.data.get("department_id")

    if department_id:
        department = Department.objects.get(id=department_id)
        user.profile.department = department
    else:
        user.profile.department = None

    user.profile.save()
    # ... rest of your update logic


class ReportsView(TemplateView):
    template_name = "raporlar.html"  # Update template name if needed

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context = TemplateLayout.init(self, context)

        # Get query parameters
        page = self.request.GET.get("page", 1)
        page_size = self.request.GET.get("page_size", 10)
        class_name = self.request.GET.get("class_name")  # Changed from detection_type

        # Get stream images with filters
        stream_images = StreamImage.objects.prefetch_related("detections").filter(detections__isnull=False)

        # Apply class name filter if provided
        if class_name:
            stream_images = stream_images.filter(detections__class_name=class_name)

        # Make queryset distinct and order by timestamp
        stream_images = stream_images.distinct().order_by("-timestamp")

        # Add pagination
        paginator = Paginator(stream_images, per_page=int(page_size))
        paginated_images = paginator.get_page(page)

        # Get class data for dropdown
        class_data = ClassData.objects.all().order_by("Turkish")

        context.update(
            {
                "stream_images": paginated_images,
                "departments": Department.objects.all(),
                "notification_types": NotificationType.objects.filter(is_active=True),
                "notification_choices": NotificationType.NOTIFICATION_CHOICES,
                "mapbox_access_token": settings.MAPBOX_ACCESS_TOKEN,
                "class_data": class_data,
                # Add selected filters to context
                "selected_class_name": class_name,  # Changed from selected_detection_type
            }
        )

        return context

    def get(self, request, *args, **kwargs):
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            try:
                # Get filter parameters
                start_date = request.GET.get("start_date")
                end_date = request.GET.get("end_date")
                department = request.GET.get("department")
                detection_types = request.GET.getlist("detection_types[]")

                # Start with images that have detections
                queryset = (
                    StreamImage.objects.prefetch_related("detections").filter(detections__isnull=False).distinct()
                )

                # Apply other filters
                if start_date and end_date:
                    try:
                        start = datetime.strptime(start_date, "%Y-%m-%dT%H:%M:%S.%fZ")
                        end = datetime.strptime(end_date, "%Y-%m-%dT%H:%M:%S.%fZ")
                        queryset = queryset.filter(timestamp__range=(start, end))
                    except ValueError:
                        return JsonResponse({"status": "error", "message": "Invalid date format"})

                if department:
                    queryset = queryset.filter(detections__notification__department_id=department)

                if detection_types:
                    queryset = queryset.filter(detections__class_name__in=detection_types)

                # Remove duplicates and order by timestamp
                queryset = queryset.distinct().order_by("-timestamp")

                # Update markers_data creation
                markers_data = []
                for image in queryset:
                    if image.lang and image.long:
                        detections = image.detections.all()
                        if detections:
                            markers_data.append(
                                {
                                    "id": image.id,
                                    "lat": image.lang,
                                    "lng": image.long,
                                    "timestamp": image.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                                    "fulladdress": image.fulladdress,
                                    "image_url": image.image.url,
                                    "detection_classes": [
                                        {
                                            "class_name": d.class_name,
                                            "icon_url": f"/static/belediyeicons/{d.class_name.lower().replace(' ', '-')}.svg",
                                        }
                                        for d in detections
                                    ],
                                    "department_id": image.detections.first().notification.department_id
                                    if image.detections.exists() and image.detections.first().notification
                                    else None,
                                }
                            )

                return JsonResponse({"status": "success", "markers": markers_data})

            except Exception as e:
                logger.error(f"Error in AJAX request: {str(e)}", exc_info=True)
                return JsonResponse({"status": "error", "message": str(e)}, status=500)

        return super().get(request, *args, **kwargs)


class NotificationViewSet(viewsets.ModelViewSet):
    permission_classes = [AllowAny]  # Tüm isteklere izin ver
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer

    def create(self, request, *args, **kwargs):
        try:
            # Log incoming data for debugging
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


@require_http_methods(["GET"])
def get_department_class_names(request, department_id):
    try:
        department = Department.objects.get(id=department_id)
        class_names = list(department.class_names.values_list("name", flat=True))
        return JsonResponse({"success": True, "class_names": class_names})
    except Department.DoesNotExist:
        return JsonResponse({"success": False, "error": "Department not found"}, status=404)
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@require_http_methods(["GET"])
def check_notification_rule(request, class_name):
    try:
        rule_exists = Notification.objects.filter(class_name=class_name).exists()
        return JsonResponse({"success": True, "hasRule": rule_exists})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)


class HaritaRaporlariView(TemplateView):
    template_name = "harita-raporlari.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context = TemplateLayout.init(self, context)

        # Son 90 günlük veriyi getir
        ninety_days_ago = datetime.now() - timedelta(days=90)

        # Get base queryset with detections
        base_queryset = (
            StreamImage.objects.prefetch_related("detections")
            .filter(detections__isnull=False, timestamp__gte=ninety_days_ago)
            .distinct()
        )

        # Format detection data to ensure proper decimal separator
        formatted_stream_images = []
        for image in base_queryset:
            formatted_detections = []
            for detection in image.detections.all():
                formatted_detections.append(
                    {
                        "class_name": detection.class_name,
                        "x_min": float(f"{detection.x_min:.6f}"),  # Format with 6 decimal places
                        "y_min": float(f"{detection.y_min:.6f}"),
                        "x_max": float(f"{detection.x_max:.6f}"),
                        "y_max": float(f"{detection.y_max:.6f}"),
                        "confidence": float(f"{detection.confidence:.6f}"),
                    }
                )
            formatted_stream_images.append(
                {
                    "id": image.id,
                    "lang": image.lang,
                    "long": image.long,
                    "detections": formatted_detections,
                    "timestamp": image.timestamp,
                    "fulladdress": image.fulladdress,
                }
            )

        context.update(
            {
                "stream_images": formatted_stream_images,
                # ...existing code...
                "departments": [
                    {
                        "id": item["detections__notification__department__id"],
                        "name": item["detections__notification__department__name"],
                        "count": item["count"],
                    }
                    for item in department_counts
                ],
                "addresses": [{"address": item["fulladdress"], "count": item["count"]} for item in address_counts],
                "class_data": class_data_with_counts,
                "total_detections": base_queryset.count(),
                "date_range": {"start": ninety_days_ago.isoformat(), "end": datetime.now().isoformat()},
                "mapbox_access_token": settings.MAPBOX_ACCESS_TOKEN,
            }
        )

        return context


@require_http_methods(["GET"])
def map_reports_data(request):
    """API endpoint to get map reports data"""
    try:
        # Get filter parameters
        start_date = request.GET.get("start_date")
        end_date = request.GET.get("end_date")
        department = request.GET.get("department")
        detection_types = request.GET.getlist("detection_types[]")

        # Start with images that have detections
        queryset = StreamImage.objects.prefetch_related("detections").filter(detections__isnull=False).distinct()

        # Apply date filters if provided
        if start_date and end_date:
            try:
                start = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
                end = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
                queryset = queryset.filter(timestamp__range=(start, end))
            except ValueError as e:
                return JsonResponse({"status": "error", "message": f"Invalid date format: {str(e)}"})

        # Apply department filter if provided
        if department:
            queryset = queryset.filter(detections__notification__department_id=department)

        # Apply detection type filter if provided
        if detection_types:
            class_names = [dt.strip() for dt in detection_types]
            queryset = queryset.filter(detections__class_name__in=class_names)

        # Prepare the response data
        markers_data = []
        for image in queryset:
            if image.lang and image.long:
                # Ensure lat and long are parsed correctly
                lat = float(str(image.lang).replace(",", "."))
                lng = float(str(image.long).replace(",", "."))
                detections = image.detections.all()
                if detections:
                    markers_data.append(
                        {
                            "id": image.id,
                            "lat": lat,
                            "lng": lng,
                            "timestamp": image.timestamp.isoformat(),
                            "fulladdress": image.fulladdress or "Adres bilgisi yok",
                            "image_url": image.image.url,
                            "detection_classes": [
                                {
                                    "class_name": d.class_name,
                                    "icon_url": f"/static/belediyeicons/{d.class_name.lower().replace(' ', '-')}.svg",
                                }
                                for d in detections
                            ],
                            "department_id": image.detections.first().notification.department_id
                            if image.detections.exists() and image.detections.first().notification
                            else None,
                        }
                    )

        return JsonResponse({"status": "success", "markers": markers_data})

    except Exception as e:
        logger.error(f"Error in map reports data: {str(e)}", exc_info=True)
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


@require_http_methods(["GET"])
def detection_counts(request):
    """API endpoint to get detection counts by type"""
    try:
        # Get filter parameters
        start_date = request.GET.get("start_date")
        end_date = request.GET.get("end_date")
        department = request.GET.get("department")

        # Base queryset filtering by detections
        queryset = StreamImage.objects.prefetch_related("detections").filter(detections__isnull=False).distinct()

        # Apply date filters if provided
        if start_date and end_date:
            try:
                start = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
                end = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
                queryset = queryset.filter(timestamp__range=(start, end))
            except ValueError as e:
                return JsonResponse({"status": "error", "message": f"Invalid date format: {str(e)}"})

        # Apply department filter if provided
        if department:
            queryset = queryset.filter(detections__notification__department_id=department)

        # Get counts by detection class
        from django.db.models import Count

        detection_counts = (
            queryset.values("detections__class_name").annotate(count=Count("detections__class_name")).order_by("-count")
        )

        # Format results
        results = [
            {
                "class_name": item["detections__class_name"],
                "count": item["count"],
            }
            for item in detection_counts
            if item["detections__class_name"] is not None
        ]

        return JsonResponse({"status": "success", "counts": results})

    except Exception as e:
        logger.error(f"Error in detection counts: {str(e)}", exc_info=True)
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


@require_http_methods(["GET"])
def chronological_detections(request):
    """API endpoint to get chronologically ordered detections"""
    try:
        # Get filter parameters for regular listing
        start_date = request.GET.get("start_date")
        end_date = request.GET.get("end_date")
        department = request.GET.get("department")
        detection_types = request.GET.getlist("detection_types[]")
        sort_by = request.GET.get("sort_by", "timestamp")  # Default sort by timestamp

        # New parameters for relative navigation
        reference_timestamp = request.GET.get("reference_timestamp")
        direction = request.GET.get("direction")  # 'prev' or 'next'

        # Start with images that have detections
        queryset = StreamImage.objects.prefetch_related("detections").filter(detections__isnull=False).distinct()

        # Apply date filters if provided
        if start_date and end_date:
            try:
                start = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
                end = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
                queryset = queryset.filter(timestamp__range=(start, end))
            except ValueError as e:
                return JsonResponse({"status": "error", "message": f"Invalid date format: {str(e)}"})

        # Apply department filter if provided
        if department:
            queryset = queryset.filter(detections__notification__department_id=department)

        # Apply detection type filter if provided
        if detection_types:
            class_names = [dt.strip() for dt in detection_types if dt.strip()]
            if class_names:
                queryset = queryset.filter(detections__class_name__in=class_names)

        # Set default navigation status
        navigation_status = {
            "has_previous": False,
            "has_next": False,
            "total_count": queryset.count(),
            "current_position": 0,
        }

        # Handle relative navigation if reference timestamp is provided
        if reference_timestamp and direction:
            try:
                ref_time = datetime.fromisoformat(reference_timestamp.replace("Z", "+00:00"))

                # Save original queryset for determining navigation status
                original_queryset = queryset

                if direction == "prev":
                    # Get the previous detection (earlier than reference)
                    queryset = queryset.filter(timestamp__lt=ref_time).order_by("-timestamp")

                    # Check if there are any previous items
                    has_prev_items = queryset.exists()

                    # Limit to 1 to get just the previous detection
                    queryset = queryset[:1]

                    # Check if there are any next items after the reference
                    has_next_items = original_queryset.filter(timestamp__gt=ref_time).exists()

                    # Update navigation status
                    navigation_status["has_previous"] = (
                        queryset.count() > 0 and original_queryset.filter(timestamp__lt=queryset[0].timestamp).exists()
                        if queryset
                        else False
                    )
                    navigation_status["has_next"] = True  # Since we're going back, there's at least the current one

                elif direction == "next":
                    # Get the next detection (later than reference)
                    queryset = queryset.filter(timestamp__gt=ref_time).order_by("timestamp")

                    # Check if there are any next items
                    has_next_items = queryset.exists()

                    # Limit to 1 to get just the next detection
                    queryset = queryset[:1]

                    # Check if there are any previous items before the reference
                    has_prev_items = original_queryset.filter(timestamp__lt=ref_time).exists()

                    # Update navigation status
                    navigation_status["has_previous"] = (
                        True  # Since we're going forward, there's at least the current one
                    )
                    navigation_status["has_next"] = (
                        queryset.count() > 0 and original_queryset.filter(timestamp__gt=queryset[0].timestamp).exists()
                        if queryset
                        else False
                    )
            except ValueError as e:
                return JsonResponse({"status": "error", "message": f"Invalid timestamp format: {str(e)}"})
        else:
            # Order by timestamp for regular chronological listing
            queryset = queryset.order_by("timestamp")

            # Update navigation status for full listing
            if queryset.exists():
                navigation_status["has_previous"] = False
                navigation_status["has_next"] = queryset.count() > 1

        # Format the results
        detections = []
        for image in queryset:
            if image.lang and image.long:
                detection_list = []
                for d in image.detections.all():
                    # DEBUG: Print raw values from database
                    print(
                        f"DB Detection coordinates: class={d.class_name}, x_min={d.x_min}, y_min={d.y_min}, x_max={d.x_max}, y_max={d.y_max}"
                    )

                    # Handle potential None values or empty strings and ensure decimal point (not comma)
                    try:
                        x_min = None if d.x_min is None or d.x_min == "" else float(str(d.x_min).replace(",", "."))
                        y_min = None if d.y_min is None or d.y_min == "" else float(str(d.y_min).replace(",", "."))
                        x_max = None if d.x_max is None or d.x_max == "" else float(str(d.x_max).replace(",", "."))
                        y_max = None if d.y_max is None or d.y_max == "" else float(str(d.y_max).replace(",", "."))
                        confidence = float(str(d.confidence).replace(",", ".")) if d.confidence is not None else 0.0
                    except (ValueError, TypeError):
                        # If conversion fails, set to None
                        x_min, y_min, x_max, y_max = None, None, None, None
                        confidence = 0.0

                    detection_list.append(
                        {
                            "class_name": d.class_name,
                            "confidence": confidence,
                            "x_min": x_min,
                            "y_min": y_min,
                            "x_max": x_max,
                            "y_max": y_max,
                        }
                    )

                # Only include if we have detections
                if detection_list:
                    try:
                        # Ensure lat/lng use periods as decimal separators
                        lat = float(str(image.lang).replace(",", "."))
                        lng = float(str(image.long).replace(",", "."))
                    except (ValueError, TypeError):
                        # Use defaults if conversion fails
                        lat, lng = 0.0, 0.0

                    detections.append(
                        {
                            "id": image.id,
                            "timestamp": image.timestamp.isoformat(),
                            "fulladdress": image.fulladdress or "Adres bilgisi yok",
                            "image_url": image.image.url,
                            "all_detections": detection_list,
                            "detection_classes": detection_list,  # Ensure both fields have the same data
                            "lat": lat,
                            "lng": lng,
                        }
                    )

        return JsonResponse({"status": "success", "detections": detections, "navigation_status": navigation_status})

    except Exception as e:
        logger.error(f"Error in chronological detections: {str(e)}", exc_info=True)
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


@require_http_methods(["GET"])
def filtered_detections(request):
    """API endpoint to get filtered detections"""
    try:
        # Get filter parameters with proper fallbacks
        detection_types = request.GET.getlist("detection_types[]", [])
        address = request.GET.get("address", "").strip()
        department = request.GET.get("department")
        date_range = request.GET.get("dateRange", "")

        # Base queryset with prefetched detections
        queryset = StreamImage.objects.prefetch_related("detections")

        # Handle date range parameter
        if date_range:
            try:
                # Handle different date formats
                date_range = date_range.replace("undefined", "")
                if " - " in date_range:
                    start_str, end_str = date_range.split(" - ")
                elif " ile " in date_range:
                    start_str, end_str = date_range.split(" ile ")
                else:
                    start_str = end_str = date_range

                # Parse dates with multiple format attempts
                date_formats = ["%Y-%m-%d", "%d.%m.%Y", "%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%d %H:%M:%S"]

                start_date = None
                end_date = None

                for date_format in date_formats:
                    try:
                        start_date = datetime.strptime(start_str.strip(), date_format)
                        end_date = datetime.strptime(end_str.strip(), date_format)
                        break
                    except ValueError:
                        continue

                if start_date and end_date:
                    # Ensure end date includes the entire day
                    end_date = end_date.replace(hour=23, minute=59, second=59)
                    queryset = queryset.filter(timestamp__range=(start_date, end_date))

            except (ValueError, IndexError) as e:
                logger.warning(f"Date parsing error: {str(e)} for date_range: {date_range}")
                # Continue without date filter if parsing fails

        # Apply other filters
        if detection_types:
            valid_types = [t for t in detection_types if t and t.strip()]
            if valid_types:
                queryset = queryset.filter(detections__class_name__in=valid_types)

        if address:
            queryset = queryset.filter(fulladdress__icontains=address)

        if department:
            try:
                department_id = int(department)
                queryset = queryset.filter(detections__notification__department_id=department_id)
            except (ValueError, TypeError):
                pass

        # Always filter for non-null detections and coordinates
        queryset = queryset.filter(detections__isnull=False, lang__isnull=False, long__isnull=False).distinct()

        # Order by timestamp descending
        queryset = queryset.order_by("-timestamp")

        # Prepare results
        results = []
        for image in queryset:
            try:
                lat = float(str(image.lang).replace(",", "."))
                lng = float(str(image.long).replace(",", "."))

                if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
                    continue  # Skip invalid coordinates

                detections = []
                for d in image.detections.all():
                    try:
                        # Ensure all numeric values use periods as decimal separators
                        confidence = float(str(d.confidence).replace(",", "."))
                        x_min = float(str(d.x_min).replace(",", ".")) if d.x_min else None
                        y_min = float(str(d.y_min).replace(",", ".")) if d.y_min else None
                        x_max = float(str(d.x_max).replace(",", ".")) if d.x_max else None
                        y_max = float(str(d.y_max).replace(",", ".")) if d.y_max else None
                    except (ValueError, TypeError):
                        # Use safe defaults if conversion fails
                        confidence = 0.0
                        x_min, y_min, x_max, y_max = None, None, None, None

                    detections.append(
                        {
                            "class_name": d.class_name,
                            "confidence": confidence,
                            "x_min": x_min,
                            "y_min": y_min,
                            "x_max": x_max,
                            "y_max": y_max,
                        }
                    )

                if detections:
                    results.append(
                        {
                            "id": image.id,
                            "lat": lat,
                            "lng": lng,
                            "timestamp": image.timestamp.isoformat(),
                            "fulladdress": image.fulladdress or "Adres bilgisi yok",
                            "image_url": image.image.url if image.image else None,
                            "detection_classes": detections,
                        }
                    )
            except (ValueError, TypeError, AttributeError) as e:
                logger.warning(f"Error processing image {image.id}: {str(e)}")
                continue

        return JsonResponse(
            {
                "success": True,
                "results": results,
                "stats": {"total": len(results), "filtered_types": detection_types, "date_range": date_range},
            }
        )

    except Exception as e:
        logger.error(f"Error in filtered_detections: {str(e)}", exc_info=True)
        return JsonResponse(
            {"success": False, "message": "Internal server error occurred", "error": str(e)}, status=500
        )


@require_http_methods(["GET"])
def council_filters(request, filter_id):
    """API endpoint to get filtered detections by class name"""
    try:
        # Start with images that have detections
        queryset = StreamImage.objects.prefetch_related("detections").filter(detections__isnull=False).distinct()

        # Apply date filters if provided
        start_date = request.GET.get("start_date")
        end_date = request.GET.get("end_date")
        if start_date and end_date:
            try:
                start = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
                end = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
                queryset = queryset.filter(timestamp__range=(start, end))
            except ValueError as e:
                return JsonResponse({"success": False, "message": f"Invalid date format: {str(e)}"})

        # Apply department filter if provided
        department = request.GET.get("department")
        if department:
            queryset = queryset.filter(detections__notification__department_id=department)

        # Filter by the specific class name provided in the URL
        if filter_id:
            queryset = queryset.filter(detections__class_name=filter_id)

        # Prepare the response data
        results = []
        for image in queryset:
            if image.lang and image.long:
                detections = []
                for d in image.detections.all():
                    if d.class_name == filter_id:
                        detections.append(
                            {
                                "class_name": d.class_name,
                                "confidence": d.confidence,
                                "x_min": d.x_min,
                                "y_min": d.y_min,
                                "x_max": d.x_max,
                                "y_max": d.y_max,
                            }
                        )

                if detections:
                    results.append(
                        {
                            "id": image.id,
                            "lat": image.lang,
                            "lng": image.long,
                            "timestamp": image.timestamp.isoformat(),
                            "fulladdress": image.fulladdress or "Adres bilgisi yok",
                            "image_url": image.image.url,
                            "detection_classes": detections,
                        }
                    )

        return JsonResponse({"success": True, "results": results})

    except Exception as e:
        logger.error(f"Error filtering detections: {str(e)}", exc_info=True)
        return JsonResponse({"success": False, "message": str(e)}, status=500)


@require_http_methods(["GET"])
def get_recent_addresses(request):
    """API endpoint to get recent addresses with search capability"""
    try:
        # Get search term from request
        search = request.GET.get("search", "").strip()

        # Base query for unique addresses
        addresses_query = (
            StreamImage.objects.exclude(fulladdress__isnull=True)
            .exclude(fulladdress__exact="")
            .values("fulladdress")
            .distinct()
        )

        # Apply search filter if provided
        if search:
            addresses_query = addresses_query.filter(fulladdress__icontains=search)

        # Get addresses with counts and last seen date
        addresses = (
            addresses_query.annotate(count=Count("id"), last_seen=Max("timestamp")).order_by("-last_seen")[
                :50
            ]  # Limit to 50 most recent
        )

        # Format suggestions with metadata
        suggestions = []
        for addr in addresses:
            if addr["fulladdress"]:
                # Split address into parts (mahalle, sokak, etc.)
                parts = addr["fulladdress"].split(",")
                area = parts[0].strip() if parts else ""

                suggestions.append(
                    {
                        "value": addr["fulladdress"],
                        "label": addr["fulladdress"],
                        "area": area,
                        "count": addr["count"],
                        "last_seen": addr["last_seen"].strftime("%d.%m.%Y %H:%M") if addr["last_seen"] else None,
                    }
                )

        return JsonResponse({"success": True, "suggestions": suggestions})
    except Exception as e:
        logger.error(f"Error getting addresses: {str(e)}", exc_info=True)
        return JsonResponse({"success": False, "error": str(e), "suggestions": []})


def index(request):
    stream_images = StreamImage.objects.prefetch_related("detections").filter(detections__isnull=False)

    for image in stream_images:
        for detection in image.detections.all():
            # Add debug print here
            print(
                f"Detection for image {image.id}:",
                {
                    "class_name": detection.class_name,
                    "confidence": detection.confidence,
                    "x_min": detection.x_min,
                    "y_min": detection.y_min,
                    "x_max": detection.x_max,
                    "y_max": detection.y_max,
                    "id": detection.id,
                    "timestamp": detection.timestamp,
                },
            )

    return render(request, "harita-raporlari.html", {"stream_images": stream_images})


class RulesView(TemplateView):
    template_name = "rules-add.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context = TemplateLayout.init(self, context)

        # Get query parameters
        page = self.request.GET.get("page", 1)
        page_size = self.request.GET.get("page_size", 10)
        class_name = self.request.GET.get("class_name")

        # Get rules with filters
        rules = RulesAdd.objects.all()

        # Apply class name filter if provided
        if class_name:
            rules = rules.filter(class_name=class_name)

        # Order by created_at
        rules = rules.order_by("-created_at")

        # Add pagination
        paginator = Paginator(rules, per_page=int(page_size))
        paginated_rules = paginator.get_page(page)

        context.update(
            {
                "rules": paginated_rules,
                "departments": Department.objects.all(),
                "notification_types": NotificationType.objects.filter(is_active=True),
                "selected_class_name": class_name,
            }
        )

        return context
