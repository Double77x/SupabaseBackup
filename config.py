import json
import os
import sys

# 1. Determine the correct path for settings.json (handles both script and .exe modes)
BASE_DIR = (
    os.path.dirname(os.path.abspath(sys.argv[0]))
    if getattr(sys, "frozen", False)
    else os.path.dirname(os.path.abspath(__file__))
)
SETTINGS_FILE = os.path.join(BASE_DIR, "settings.json")

# 2. Default values
MAX_BACKUPS_PER_PROJECT = 5
RETENTION_DAYS = 30
ALLOW_PERMANENT_TAGGING = True

# 3. Load from JSON if available
try:
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as f:
            data = json.load(f)
            MAX_BACKUPS_PER_PROJECT = data.get("max_backups", 5)
            RETENTION_DAYS = data.get("retention_days", 30)
except Exception as e:
    print(f"Warning: Could not load settings.json ({e}). Using defaults.")
