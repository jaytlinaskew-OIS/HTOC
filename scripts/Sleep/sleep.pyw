import os
import time
import ctypes
import platform
import json
from datetime import datetime, timedelta

# Base directory for log file
BASE_DIR = r"C:\Users\jaskew\Documents\project_repository\scripts\Sleep"
# Path to your JSON log file
LOG_PATH = os.path.join(BASE_DIR, "SleepLogs.json")

# Ensure the directory exists
os.makedirs(BASE_DIR, exist_ok=True)


def read_log():
    """Read the JSON log, returning a list (empty if missing or invalid)."""
    try:
        with open(LOG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def write_log(entries):
    """Write the entire list of entries as pretty-printed JSON."""
    with open(LOG_PATH, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=True, indent=2)
        f.write("\n")


def log_event(message: str):
    """Append a new entry to the JSON log with pretty formatting."""
    entries = read_log()
    entries.append({
        "timestamp": datetime.now().isoformat(),
        "message": message
    })
    write_log(entries)


def purge_old_records(hours: float = 1.0):
    """Remove any JSON entries older than `hours` and rewrite the file."""
    cutoff = datetime.now() - timedelta(hours=hours)
    entries = read_log()
    new_entries = [e for e in entries if datetime.fromisoformat(e.get("timestamp", "")) >= cutoff]
    write_log(new_entries)


def poke_screen():
    """Reset Windows idle timer so system and display stay awake."""
    if platform.system() != "Windows":
        return
    ES_CONTINUOUS       = 0x80000000
    ES_SYSTEM_REQUIRED  = 0x00000001
    ES_DISPLAY_REQUIRED = 0x00000002
    ctypes.windll.kernel32.SetThreadExecutionState(
        ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED
    )


if __name__ == "__main__":
    # Initialize log on first run
    if not os.path.exists(LOG_PATH) or os.path.getsize(LOG_PATH) == 0:
        write_log([{"timestamp": datetime.now().isoformat(), "message": "Keep-alive script started"}])
        last_purge = datetime.now()
        last_log   = datetime.now() - timedelta(minutes=1)
    else:
        last_purge = datetime.now()
        last_log   = datetime.now() - timedelta(minutes=1)

    retry_count = 0
    max_retries = 3

    try:
        while True:
            try:
                poke_screen()

                now = datetime.now()
                # Purge once every hour
                if (now - last_purge) >= timedelta(hours=1):
                    purge_old_records(hours=1)
                    log_event("Purged records older than 1 hour")
                    last_purge = now

                # Only log poke if at least 1 minute has passed
                if (now - last_log) >= timedelta(minutes=1):
                    log_event("Screen poked")
                    last_log = now

                # Reset retry count on successful loop
                retry_count = 0

            except Exception as e:
                retry_count += 1
                log_event(f"Error in main loop: {e} (retry {retry_count}/{max_retries})")
                if retry_count >= max_retries:
                    log_event("Max retries reached, exiting")
                    break

            time.sleep(50)

    except KeyboardInterrupt:
        log_event("Interrupted by user, exiting")
