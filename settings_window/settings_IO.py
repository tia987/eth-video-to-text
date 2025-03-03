import os, json

CONFIG_FILE = "cache/config.json"

def load_settings():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                # If the config file is corrupted, return default settings.
                pass
    # Default settings
    return {"font_size": 12, "preferred_model": "tiny"}

def save_settings(settings):
    with open(CONFIG_FILE, "w") as f:
        json.dump(settings, f, indent=4)