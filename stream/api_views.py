from rest_framework.decorators import api_view
from django.http import JsonResponse
from rest_framework.response import Response
from .models import ClassData, Detection, StreamImage
import logging

logger = logging.getLogger(__name__)


@api_view(["GET"])
def class_data_list(request):
    """API endpoint to get all ClassData entries"""
    try:
        classes = ClassData.objects.all().order_by("id")
        data = [{"id": c.id, "Name": c.Name, "Turkish": c.Turkish, "Speech": c.Speech} for c in classes]

        return JsonResponse({"success": True, "classes": data})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@api_view(["GET"])
def icon_mappings(request):
    """
    Return all icon mappings from ClassData model for use in frontend
    """
    class_data = ClassData.objects.all()

    # Convert to the format expected by the frontend
    mappings = {}
    whitelist = []

    for item in class_data:
        mappings[item.Name] = {"icon": f"{item.Name}.png", "turkish": item.Turkish}
        whitelist.append(item.Turkish)

    return Response({"mappings": mappings, "whitelist": whitelist})


@api_view(["GET"])
def council_filters(request, filter_id):
    """
    Return StreamImage entries that have Detection objects with class_name matching filter_id
    Focus on map-relevant data including coordinates
    """
    try:
        # Find the class data by name (which is passed as filter_id)
        class_data = ClassData.objects.filter(Name=filter_id).first()

        if not class_data:
            return JsonResponse({"success": False, "error": f"Filter not found: {filter_id}"}, status=404)

        # Get detections matching the filter_id
        detections = Detection.objects.filter(class_name__icontains=filter_id)

        # Get unique image IDs from these detections
        image_ids = detections.values_list("image_id", flat=True).distinct()

        # Fetch those images with their coordinates
        stream_images = StreamImage.objects.filter(id__in=image_ids)

        results = []
        for image in stream_images:
            # Only include images with location data
            if hasattr(image, "lang") and hasattr(image, "long") and image.lang and image.long:
                results.append(
                    {
                        "id": image.id,
                        "class_name": class_data.Name,
                        "location": {"lat": float(image.lang), "lng": float(image.long)},
                        "image_url": image.image.url if image.image else None,
                        "timestamp": image.timestamp.isoformat() if hasattr(image, "timestamp") else None,
                        "area": image.area if hasattr(image, "area") else None,
                        "fulladdress": image.fulladdress if hasattr(image, "fulladdress") else None,
                    }
                )

        return JsonResponse(
            {
                "success": True,
                "filter_name": class_data.Turkish,
                "count": len(results),
                "results": results,  # Changed from 'images' to 'results' to match other API patterns
            }
        )
    except Exception as e:
        logger.error(f"Error in council_filters: {str(e)}")
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@api_view(["GET"])
def map_reports_filter(request, filter_category):
    """
    Filter map reports by category and return geolocated items
    """
    logger.info(f"Filtering for2: {filter_category}")

    # For car/araba specifically, also check for std_car but exclude them from results
    if filter_category.lower() == "araba":
        # Only get araba detections, not std_car detections
        filtered_detections = Detection.objects.filter(
            class_name__icontains=filter_category, geolocation__isnull=False
        ).select_related("stream_image")
    else:
        # Standard filtering for other categories
        filtered_detections = Detection.objects.filter(
            class_name__icontains=filter_category, geolocation__isnull=False
        ).select_related("stream_image")

    # Format the response data
    result = []
    for detection in filtered_detections:
        # Explicitly exclude std_car entries
        if detection.class_name.lower() == "car":
            continue

        if detection.geolocation:
            try:
                # Some geolocation data might be stored with different separators
                if "," in detection.geolocation:
                    lat, lng = detection.geolocation.split(",")
                elif ";" in detection.geolocation:
                    lat, lng = detection.geolocation.split(";")
                else:
                    logger.warning(f"Unknown geolocation format: {detection.geolocation}")
                    continue

                # Clean and convert to float
                lat = lat.strip()
                lng = lng.strip()

                result.append(
                    {
                        "id": detection.id,
                        "class_name": detection.class_name,
                        "location": {"lat": float(lat), "lng": float(lng)},
                        "confidence": detection.confidence,
                        "image_url": detection.stream_image.image.url
                        if detection.stream_image and detection.stream_image.image
                        else None,
                        "timestamp": detection.created_at.isoformat(),
                    }
                )
            except ValueError as e:
                # Log the specific error with the problematic geolocation
                logger.warning(
                    f"Invalid geolocation data for detection {detection.id}: {detection.geolocation} - Error: {str(e)}"
                )
                continue
            except Exception as e:
                logger.error(f"Error processing detection {detection.id}: {str(e)}")
                continue

    logger.info(f"Found {len(result)} items for filter: {filter_category}")
    return JsonResponse({"results": result, "filter": filter_category, "count": len(result)})
