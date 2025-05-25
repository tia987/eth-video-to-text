import os
import sys

def get_cache_base_dir(app_name="eth-video-to-text"):
    """
    Determine a platform-appropriate cache directory for the given application.
    """
    home = os.path.expanduser("~")
    if sys.platform.startswith("darwin"):
        # macOS
        base = os.path.join(home, "Library", "Caches", app_name)
    elif sys.platform.startswith("win"):
        # Windows: prefer LOCALAPPDATA, fallback to APPDATA or home
        local = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA") or home
        base = os.path.join(local, app_name, "Cache")
    else:
        # Assume Linux/Unix: follow XDG spec, fallback to ~/.cache
        xdg = os.environ.get("XDG_CACHE_HOME", os.path.join(home, ".cache"))
        base = os.path.join(xdg, app_name)
    return base

CACHE_DIR = get_cache_base_dir() + "/"

AUDIO_DIR = CACHE_DIR + "audios/"
CONFIG_FILE = CACHE_DIR + "config.json"
RSS_DIR = CACHE_DIR + "rss/"
VIDEO_DIR = CACHE_DIR + "videos/"
URL_DIR = CACHE_DIR + "url/"
TRANSCRIPT_DIR = CACHE_DIR + "transcript/"