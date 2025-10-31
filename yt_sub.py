import subprocess
import json
import time
import requests
from datetime import datetime

# === CONFIGURATION ===
VIDEO_URL = "https://youtu.be/FSDw3jX2tvE"  # Replace this with your video URL
CHECK_INTERVAL = 1800  # 30 minutes
LOG_FILE = "subtitle_check_log.txt"

# === TELEGRAM SETUP ===
TELEGRAM_BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
TELEGRAM_CHAT_ID = "YOUR_CHAT_ID"


def send_telegram(message):
    """Send a Telegram message"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        requests.post(url, data=payload, timeout=10)
    except Exception as e:
        print(f"[!] Telegram error: {e}")


def log_event(message):
    """Save logs to file and print"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_message = f"[{timestamp}] {message}"
    print(log_message)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_message + "\n")


def check_english_subtitles():
    """Check if English subtitles exist using yt-dlp metadata only"""
    try:
        result = subprocess.run(
            ["yt-dlp", "-J", "--skip-download", VIDEO_URL],
            capture_output=True,
            text=True,
            timeout=60
        )

        info = json.loads(result.stdout)
        subs = info.get("subtitles", {})

        if "en" in subs:
            return True, "English subtitles found."
        else:
            return False, "No English subtitles yet."

    except Exception as e:
        return False, f"Error checking subtitles: {e}"


def monitor_subtitles():
    """Main loop: check periodically"""
    english_sub_notified = False

    log_event("🎬 Starting English subtitle monitor...")

    while True:
        exists, message = check_english_subtitles()
        log_event(message)

        if exists and not english_sub_notified:
            send_telegram("✅ English subtitles are now available!")
            english_sub_notified = True
        elif not exists:
            english_sub_notified = False  # Reset in case they are removed

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    monitor_subtitles()
