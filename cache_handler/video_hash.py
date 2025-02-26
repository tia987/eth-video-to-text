import hashlib

def get_video_hash(video_path):
    """Generate a hash of the video file to use as a cache key."""
    hasher = hashlib.md5()
    with open(video_path, "rb") as f:
        while chunk := f.read(8192):
            hasher.update(chunk)
    return hasher.hexdigest()