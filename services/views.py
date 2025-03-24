import cv2
import uuid
import time
import logging
import base64
import asyncio
from django.shortcuts import render, get_object_or_404
from django.views.generic import TemplateView
from django.views.decorators.http import require_http_methods, require_POST
from django.http import JsonResponse
from config import TemplateLayout  # Update this import
from .forms import SourcesForm
from .models import Sources
import json
import os
from django.conf import settings
from channels.generic.websocket import AsyncWebsocketConsumer

os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "protocol_whitelist;file,rtp,udp,tcp"


class ServicesView(TemplateView):
    template_name = "sources.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        TemplateLayout.init(self, context)
        context["sources"] = Sources.objects.all()
        context["form"] = SourcesForm()
        return context


class ServicesAddView(TemplateView):
    template_name = "task-add.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        TemplateLayout.init(self, context)
        source_id = self.request.GET.get("source_id")
        if source_id:
            source = get_object_or_404(Sources, id=source_id)
            # Ensure polygons is a list or default to empty list
            source.polygons = source.polygons if isinstance(source.polygons, list) else []
            context["sources"] = source
        context["form"] = SourcesForm()
        return context


def add_source(request):
    if request.method == "POST":
        form = SourcesForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return JsonResponse({"success": True})
        else:
            return JsonResponse({"success": False, "error": form.errors})
    else:
        form = SourcesForm()

    sources = Sources.objects.all()
    return render(request, "sources.html", {"form": form, "sources": sources})


@require_http_methods(["PUT"])
def update_source(request, source_id):
    try:
        source = Sources.objects.get(id=source_id)
        data = json.loads(request.body)

        # Update polygons if provided
        if "polygons" in data:
            # Get existing polygons or initialize empty list
            existing_polygons = source.polygons or []
            if not isinstance(existing_polygons, list):
                existing_polygons = []

            # Merge existing polygons with new ones
            new_polygons = data["polygons"]
            merged_polygons = existing_polygons + new_polygons

            # Update source with merged polygons
            source.polygons = merged_polygons
            ###print(f"Merged polygons: {merged_polygons}")  # Debug ###print

        # Update other fields if needed
        if "name" in data:
            source.name = data["name"]
        if "url" in data:
            source.url = data["url"]

        source.save()
        return JsonResponse(
            {
                "status": "success",
                "message": "Source updated successfully",
                "polygons": source.polygons,  # Return updated polygons
            }
        )
    except Sources.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Source not found"}, status=404)
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


@require_http_methods(["DELETE"])
def delete_source(request, source_id):
    try:
        source = Sources.objects.get(id=source_id)
        source.delete()
        return JsonResponse({"status": "success", "message": "Source deleted successfully"})
    except Sources.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Source not found"}, status=404)
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


@require_POST
def refresh_source_image(request, source_id):
    try:
        source = get_object_or_404(Sources, id=source_id)

        # Updated codec configurations with more fallback options
        codec_configs = [
            {"codec": None},  # Try default first
            {"codec": "h264"},  # Software H264
            {"codec": "hevc"},  # Software HEVC
            {"codec": "libx264"},  # Alternative H264
            {"codec": "h264_videotoolbox"},  # macOS Hardware acceleration
            {"codec": "h264_qsv"},  # Intel Quick Sync
            {"codec": "hevc_qsv"},  # Intel Quick Sync HEVC
        ]

        valid_frame = None
        for config in codec_configs:
            try:
                cap = cv2.VideoCapture()
                if config["codec"]:
                    logging.info(f"Trying codec: {config['codec']}")
                    os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = f"video_codec|{config['codec']}"

                # Set additional options for better compatibility
                cap.set(cv2.CAP_PROP_BUFFERSIZE, 5)

                if not cap.open(source.url, cv2.CAP_FFMPEG):
                    logging.warning(f"Failed to open stream with codec {config['codec']}")
                    continue

                # Quick read attempt
                ret, frame = cap.read()
                if ret and frame is not None and frame.size > 0 and not all(frame.ravel() == 0):
                    valid_frame = frame
                    logging.info(f"Successfully captured frame with codec {config['codec']}")
                    break

                cap.release()
                time.sleep(0.5)  # Short delay between attempts

            except cv2.error as e:
                logging.error(f"OpenCV error with codec {config['codec']}: {str(e)}")
                continue
            except Exception as e:
                logging.error(f"Unexpected error with codec {config['codec']}: {str(e)}")
                continue
            finally:
                if cap.isOpened():
                    cap.release()

        if valid_frame is None:
            return JsonResponse(
                {"status": "error", "message": "Failed to capture valid frame with any codec configuration"}, status=400
            )

        # Save the captured frame
        img_dir = os.path.join(settings.MEDIA_ROOT, "images")
        os.makedirs(img_dir, exist_ok=True)
        img_filename = f"img-{uuid.uuid4()}.jpg"
        img_path = os.path.join(img_dir, img_filename)

        # Ensure the frame is in BGR format before saving
        if len(valid_frame.shape) == 2:  # If grayscale
            valid_frame = cv2.cvtColor(valid_frame, cv2.COLOR_GRAY2BGR)

        if not cv2.imwrite(img_path, valid_frame):
            return JsonResponse({"status": "error", "message": "Failed to save captured frame"}, status=500)

        source.image = os.path.join("images", img_filename)
        source.save()
        return JsonResponse({"status": "success", "image_url": source.image.url})

    except Exception as e:
        logging.error(f"Unexpected error in refresh_source_image: {str(e)}")
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


@require_POST
def save_polygon(request):
    try:
        data = json.loads(request.body)
        source_id = data.get("sourceId")
        points = data.get("points")

        source = get_object_or_404(Sources, id=source_id)

        # Save polygon data to your model
        polygon = Sources.polygons.objects.create(source=source, points=points)

        return JsonResponse({"status": "success", "message": "Polygon saved successfully", "id": polygon.id})
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


@require_http_methods(["DELETE"])
def delete_polygon(request, source_id, polygon_index):
    try:
        source = Sources.objects.get(id=source_id)

        # Get existing polygons
        polygons = source.polygons if isinstance(source.polygons, list) else []

        # Check if index is valid
        if 0 <= polygon_index < len(polygons):
            # Remove the polygon at the specified index
            removed_polygon = polygons.pop(polygon_index)

            # Update source with modified polygons list
            source.polygons = polygons
            source.save()

            return JsonResponse(
                {"status": "success", "message": "Polygon deleted successfully", "deleted_polygon": removed_polygon}
            )
        else:
            return JsonResponse({"status": "error", "message": "Invalid polygon index"}, status=400)

    except Sources.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Source not found"}, status=404)
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


@require_http_methods(["GET"])
def get_source(request, source_id):
    try:
        source = Sources.objects.get(id=source_id)
        return JsonResponse(
            {
                "success": True,
                "source": {
                    "id": source.id,
                    "title": source.title,
                    "url": source.url,
                    "image_url": source.image.url if source.image else None,
                },
            }
        )
    except Sources.DoesNotExist:
        return JsonResponse({"success": False, "error": "Source not found"}, status=404)


class VideoStreamConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.source_id = self.scope["url_route"]["kwargs"]["source_id"]
        self.stop_streaming = False
        await self.accept()
        asyncio.create_task(self.stream_video())

    async def disconnect(self, close_code):
        self.stop_streaming = True

    async def stream_video(self):
        try:
            source = await asyncio.to_thread(lambda: Sources.objects.get(id=self.source_id))

            cap = cv2.VideoCapture(source.url)
            if not cap.isOpened():
                await self.send(json.dumps({"error": "Could not open video stream"}))
                return

            while not self.stop_streaming:
                success, frame = await asyncio.to_thread(cap.read)
                if not success:
                    break

                # Resize frame if needed (optional)
                if hasattr(source, "resolution"):
                    try:
                        width = int(source.resolution.split("x")[0])
                        height = int(source.resolution.split("x")[1])
                        frame = cv2.resize(frame, (width, height))
                    except:
                        pass

                # Convert frame to JPEG
                ret, buffer = cv2.imencode(".jpg", frame)
                if not ret:
                    continue

                # Convert to base64
                frame_bytes = base64.b64encode(buffer).decode("utf-8")

                # Send frame
                await self.send(
                    json.dumps(
                        {"frame": frame_bytes, "polygons": source.polygons if hasattr(source, "polygons") else []}
                    )
                )

                # Add a small delay to control frame rate
                await asyncio.sleep(0.033)  # ~30 FPS

        except Exception as e:
            logging.error(f"Error in video streaming: {str(e)}")
            await self.send(json.dumps({"error": str(e)}))
        finally:
            if "cap" in locals():
                cap.release()
