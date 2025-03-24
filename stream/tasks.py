from celery import shared_task
import cv2
import base64
from .cache import cache_video_frames


@shared_task
def process_video_frames(video_id, video_path):
    """Process video frames in background"""
    frames_data = []
    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)

    try:
        for frame_number in range(total_frames):
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            ret, frame = cap.read()
            if ret:
                _, buffer = cv2.imencode(".jpg", frame)
                frame_b64 = base64.b64encode(buffer).decode("utf-8")
                frames_data.append({"frame": frame_b64, "frame_number": frame_number})

            # Cache every 30 frames (1 second of video)
            if frame_number % 30 == 0:
                cache_video_frames(video_id, {"frames": frames_data, "total_frames": total_frames, "fps": fps})
    finally:
        cap.release()

    return {"total_frames": total_frames, "fps": fps}
