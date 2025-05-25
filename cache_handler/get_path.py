import os

from pathlib import Path

from .video_hash import *  # Import hash function
from .cache_directories import *  # Import hash function

os.makedirs(CACHE_DIR, exist_ok=True)  # Ensure the cache directory exists

def get_cache_path(video_path, model_name):
    video_path = Path(video_path).stem
    """Generate the cache filename based on the audio hash and model name."""
    # video_hash = get_video_hash(video_path) changed video_cache with video_path next
    return os.path.join(TRANSCRIPT_DIR, f"{video_path}_{model_name}.json")

def get_cache_video_path():
    return os.path.join(CACHE_DIR)