
import os
from .audio_hash import *  # Import hash function

CACHE_DIR = "cache"  # Directory to store cached transcriptions
os.makedirs(CACHE_DIR, exist_ok=True)  # Ensure the cache directory exists

def get_cache_path(audio_path, model_name):
    """Generate the cache filename based on the audio hash and model name."""
    audio_hash = get_audio_hash(audio_path)
    return os.path.join(CACHE_DIR, f"{audio_hash}_{model_name}.json")