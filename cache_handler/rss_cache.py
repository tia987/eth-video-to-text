import os, json

from .video_hash import *  # Import hash function

CACHE_DIR = "cache/rss/"  # Directory to store cached RSS
os.makedirs(CACHE_DIR, exist_ok=True)  # Ensure the cache directory existss

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
    # Iterate over entries and extract the video URL.
    # print(feed_data.get("guid", []))

    # for entry in feed_data.get("guid", []):
    #     # First try to use the "link" key.
    #     if "link" in entry:
    #         urls.append(entry["link"])
    #     # If no direct link exists, check for an enclosure.
    #     elif "enclosures" in entry and entry["enclosures"]:
    #         urls.append(entry["enclosures"][0].get("href"))
    
    # return urls