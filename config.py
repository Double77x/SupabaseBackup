# config.py

# RETENTION SETTINGS
# ------------------

# How many past backups to keep per project (excluding permanent ones)
MAX_BACKUPS_PER_PROJECT = 5

# Delete backups older than this many days (set to 0 to disable age-based deletion)
RETENTION_DAYS = 180

# UI SETTINGS
# -----------

# Show the option to mark a backup as "Permanent" (suffix _P)
# Permanent backups are ignored by the cleanup script.
ALLOW_PERMANENT_TAGGING = True
