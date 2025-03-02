
import os
from .video_hash import *  # Import hash function

CACHE_DIR = "cache"  # Directory to store cached transcriptions
os.makedirs(CACHE_DIR, exist_ok=True)  # Ensure the cache directory exists

def get_cache_path(video_path, model_name):
    """Generate the cache filename based on the audio hash and model name."""
    video_hash = get_video_hash(video_path)
    return os.path.join(CACHE_DIR, f"{video_hash}_{model_name}.json")

def get_cache_video_path():
    return os.path.join(CACHE_DIR)