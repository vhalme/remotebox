import json
import os
from .config import STATE_FILE

def load_settings():
    if not os.path.exists(STATE_FILE):
        return {"vpn_enabled": False, "last_wifi": None}
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}

def save_settings(data):
    with open(STATE_FILE, "w") as f:
        json.dump(data, f, indent=2)
