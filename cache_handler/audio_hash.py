import hashlib

def get_audio_hash(audio_path):
    """Generate a hash of the audio file to use as a cache key."""
    hasher = hashlib.md5()
    with open(audio_path, "rb") as f:
        while chunk := f.read(8192):
            hasher.update(chunk)
    return hasher.hexdigest()