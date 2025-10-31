import subprocess
import json
import time
import hashlib
import os
from datetime import datetime
import requests

# === CONFIGURATION ===
VIDEO_URL = "https://youtu.be/FSDw3jX2tvE"  # Replace with the video you want to monitor
CHECK_INTERVAL = 3600  # seconds (1 hour)
LOG_FILE = "subtitle_update_log.txt"

# Telegram setup (you’ll add these as environment variables on Render/Replit)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# === FUNCTIONS ===

def send_telegram(message):
    """Send a message to your Telegram bot."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Telegram credentials missing. Skipping notification.")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}

    try:
        response = requests.post(url, data=payload)
        if response.status_code != 200:
            print(f"Telegram API error: {response.text}")
    except Exception as e:
        print(f"Telegram error: {e}")


def get_subtitle_hash():
    """Downloads the subtitle metadata and returns an MD5 hash."""
    try:
        # Use --impersonate chrome to avoid YouTube rate limiting
        result = subprocess.run(
            [
                "python", "-m", "yt_dlp",
                "--skip-download",
                "--write-sub",
                "--print-json",
                "--impersonate", "chrome",
                VIDEO_URL
            ],
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
    """Logs a message with timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {message}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def monitor_subtitles():
    """Continuously monitors the subtitles and sends alerts when updated."""
    log_event("🎬 Starting subtitle monitor...")
    last_hash = None

    while True:
        current_hash, error = get_subtitle_hash()

        if error:
            log_event(f"❌ Check failed: {error}")
        elif last_hash is None:
            last_hash = current_hash
            log_event("✅ Initial subtitle hash recorded.")
            send_telegram("✅ Subtitle found and monitoring started.")
        elif current_hash != last_hash:
            log_event("🔔 Subtitle updated!")
            send_telegram("🔔 Subtitle updated on the video!")
            last_hash = current_hash
        else:
            log_event("⏳ No subtitle change detected.")

        # Wait before next check
        time.sleep(CHECK_INTERVAL)


# === ENTRY POINT ===
if __name__ == "__main__":
    log_event("Initializing environment...")
    monitor_subtitles()
