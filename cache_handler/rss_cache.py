import os, json

from .video_hash import *  # Import hash function

CACHE_DIR = "cache/rss/"  # Directory to store cached RSS
CACHE_URL_DIR = "cache/url/"  # Directory to store cached RSS
os.makedirs(CACHE_DIR, exist_ok=True)  # Ensure the cache directory existss
os.makedirs(CACHE_URL_DIR, exist_ok=True)  # Ensure the cache directory existss

def set_rss_cache(feed_rss, url_rss):
    """Set rss feed in cache"""
    rss_cache_file_path = CACHE_DIR+url_rss
    with open(f"{rss_cache_file_path}.json", "w") as f:
        json.dump(feed_rss, f, ensure_ascii=False, indent=4)

def get_rss_cache(url_rss):
    """Get rss feed in cache"""
    # Construct the file path; note: you may want to use a hash or other sanitization
    # in a real-world scenario to avoid filename issues.
    cache_file_path = os.path.join(CACHE_DIR, url_rss + ".json")
    
    if not os.path.exists(cache_file_path):
        return []
    
    with open(cache_file_path, "r", encoding="utf-8") as f:
        feed_data = json.load(f)
    
    urls = []

def set_rss_url_cache(feed_rss, url_rss):
    """Set rss furl eed in cache"""
    rss_cache_file_path = CACHE_URL_DIR+url_rss
    with open(f"{rss_cache_file_path}.json", "w") as f:
        json.dump(feed_rss, f, ensure_ascii=False, indent=4)

def get_rss_url_cache(url_rss):
    """Get rss feed in cache"""
    # Construct the file path; note: you may want to use a hash or other sanitization
    # in a real-world scenario to avoid filename issues.
    cache_file_path = os.path.join(CACHE_URL_DIR, url_rss + ".json")
    
    if not os.path.exists(cache_file_path):
        return []
    
    with open(cache_file_path, "r", encoding="utf-8") as f:
        feed_data = json.load(f)
    
    urls = []
    return 