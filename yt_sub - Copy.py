import subprocess
import json
import time
import hashlib
import os
from datetime import datetime
import requests

# Configuration
VIDEO_URL = "https://youtu.be/FSDw3jX2tvE"  # Replace with a public video if needed
CHECK_INTERVAL = 60  # Check every hour (in seconds)
LOG_FILE = "subtitle_update_log.txt"

# Telegram setup
TELEGRAM_BOT_TOKEN = "8377884147:AAE9LVFcgWP0-A_94hbZAsLyLO7jpGXKbG8"
TELEGRAM_CHAT_ID = "6412296937"

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print(f"Telegram error: {e}")

def get_subtitle_hash():
    try:
        result = subprocess.run(
            ["python", "-m", "yt_dlp", "--skip-download", "--write-sub", "--print-json", VIDEO_URL],
            capture_output=True, text=True, check=True
        )
        info = json.loads(result.stdout)
        subs = info.get("subtitles", {})
        if not subs:
            return None, "No subtitles found."

        sub_data = json.dumps(subs, sort_keys=True)
        hash_val = hashlib.md5(sub_data.encode()).hexdigest()
        return hash_val, None
    except subprocess.CalledProcessError as e:
        return None, f"yt-dlp error: {e.stderr.strip()}"
    except Exception as e:
        return None, f"Unexpected error: {str(e)}"

def log_event(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")
    print(f"[{timestamp}] {message}")

def monitor_subtitles():
    log_event("Starting subtitle monitor...")
    last_hash = None

    while True:
        current_hash, error = get_subtitle_hash()
        if error:
            log_event(f"Check failed: {error}")
        elif last_hash is None:
            last_hash = current_hash
            log_event("Initial subtitle hash recorded.")
            send_telegram("✅ Subtitle found and monitoring started.")
        elif current_hash != last_hash:
            log_event("🔔 Subtitle updated!")
            send_telegram("🔔 Subtitle updated on the video!")
            last_hash = current_hash
        else:
            log_event("No subtitle change detected.")

        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    os.chdir(r"F:\python projects\Yt eng sub update notification")
    monitor_subtitles()