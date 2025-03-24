import json
import os
import base64
import cv2
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.conf import settings
from ultralytics import YOLO


class VideoConsumer(AsyncWebsocketConsumer):
    # Load YOLO models once at class level for better performance
    belediye_model = None
    general_model = None

    @classmethod
    async def get_models(cls):
        if cls.belediye_model is None:
            # Use database_sync_to_async to avoid blocking
            cls.belediye_model = await database_sync_to_async(YOLO)("belediye.pt")

        if cls.general_model is None:
            cls.general_model = await database_sync_to_async(YOLO)("yolov8n.pt")

    async def connect(self):
        await self.accept()
        print("WebSocket connected")
        # Load models on first connection
        await self.get_models()

    async def disconnect(self, close_code):
        print(f"WebSocket disconnected with code: {close_code}")

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            frame_data = await self.get_frame(data["video_id"], data["frame_number"])
            await self.send(text_data=json.dumps(frame_data))
        except Exception as e:
            await self.send(text_data=json.dumps({"type": "frame", "status": "error", "message": str(e)}))

    @database_sync_to_async
    def get_frame(self, video_id, frame_number):
        from .models import OfflineMode, ClassData

        try:
            video = OfflineMode.objects.get(id=video_id)
            video_path = os.path.join(settings.MEDIA_ROOT, str(video.video_file))

            cap = cv2.VideoCapture(video_path)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)

            # Get the original width and height of the video
            original_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            original_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

            print(f"Video dimensions: {original_width}x{original_height}")

            if 0 <= frame_number < total_frames:
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
                ret, frame = cap.read()

                if ret:
                    detections = []

                    # Only run object detection if we have models loaded
                    if self.__class__.belediye_model:
                        # Run belediye model
                        belediye_results = self.__class__.belediye_model(frame)
                        for result in belediye_results:
                            for box in result.boxes:
                                x1, y1, x2, y2 = map(float, box.xyxy[0])
                                conf = float(box.conf[0])
                                cls = int(box.cls[0])
                                cls_name = result.names[cls]

                                # Try to get Turkish name from ClassData
                                turkish_name = cls_name
                                try:
                                    class_obj = ClassData.objects.filter(Name=cls_name).first()
                                    if class_obj:
                                        turkish_name = class_obj.Turkish or cls_name
                                except:
                                    pass

                                detections.append(
                                    {
                                        "x_min": x1,
                                        "y_min": y1,
                                        "x_max": x2,
                                        "y_max": y2,
                                        "confidence": conf,
                                        "class_name": cls_name,
                                        "turkish_name": turkish_name,
                                        "source": "belediye",
                                    }
                                )

                    # Run general YOLOv8 model
                    if self.__class__.general_model:
                        general_results = self.__class__.general_model(frame)
                        for result in general_results:
                            for box in result.boxes:
                                x1, y1, x2, y2 = map(float, box.xyxy[0])
                                conf = float(box.conf[0])
                                cls = int(box.cls[0])
                                cls_name = result.names[cls]

                                detections.append(
                                    {
                                        "x_min": x1,
                                        "y_min": y1,
                                        "x_max": x2,
                                        "y_max": y2,
                                        "confidence": conf,
                                        "class_name": cls_name,
                                        "turkish_name": cls_name,
                                        "source": "general",
                                    }
                                )

                    # Encode the frame as base64
                    _, buffer = cv2.imencode(".jpg", frame)
                    frame_b64 = base64.b64encode(buffer).decode("utf-8")

                    return {
                        "type": "frame",
                        "status": "success",
                        "frame": frame_b64,
                        "frame_number": frame_number,
                        "total_frames": total_frames,
                        "fps": fps,
                        "detections": detections,
                        "original_width": original_width,
                        "original_height": original_height,
                    }

            return {"type": "frame", "status": "error", "message": "Frame not found"}
        except Exception as e:
            return {"type": "frame", "status": "error", "message": str(e)}
        finally:
            if "cap" in locals():
                cap.release()
