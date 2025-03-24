import redis
import json

redis_client = redis.Redis(host="localhost", port=6379, db=0)


def cache_video_frames(video_id, frames_data):
    """Cache video frames in Redis"""
    key = f"video_frames_{video_id}"
    redis_client.set(key, json.dumps(frames_data), ex=3600)  # 1 hour expiry


def get_cached_frames(video_id):
    """Get cached frames from Redis"""
    key = f"video_frames_{video_id}"
    data = redis_client.get(key)
    return json.loads(data) if data else None
