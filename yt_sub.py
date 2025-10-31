import subprocess
import json
import time
import requests
from datetime import datetime

# === CONFIGURATION ===
VIDEO_URL = "https://youtu.be/FSDw3jX2tvE"  # Replace this with your target video
CHECK_INTERVAL = 1800  # 30 minutes

# === TELEGRAM SETUP ===
TELEGRAM_BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
TELEGRAM_CHAT_ID = "YOUR_TELEGRAM_CHAT_ID"


def send_telegram(message):
    """Send Telegram message"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
        requests.post(url, data=payload, timeout=10)
    except Exception as e:
        print(f"[!] Telegram error: {e}")


def log_event(message):
    """Print and save log with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")


def check_subtitles():
    """Check only subtitle metadata (no download)"""
    try:
        # Get metadata in JSON form (no actual download)
        result = subprocess.run(
            ["yt-dlp", "-J", "--skip-download", VIDEO_URL],
            capture_output=True,
            text=True,
            timeout=60
        )

        # Parse JSON
        info = json.loads(result.stdout)
        subs = info.get("subtitles", {})

        # Check for English subs
        if "en" in subs:
            return True
        else:
            return False

    except Exception as e:
        log_event(f"⚠️ Error checking subtitles: {e}")
        return None


def monitor():
    """Main loop: check periodically"""
    english_sub_available = False
    log_event("🎬 Starting English subtitle monitor...")

    while True:
        result = check_subtitles()

        if result is True:
            if not english_sub_available:
                english_sub_available = True
                msg = "✅ English subtitles are now available!"
                log_event(msg)
                send_telegram(msg)
            else:
                log_event("✅ English subtitles still available.")
        elif result is False:
            if english_sub_available:
                english_sub_available = False
                msg = "⚠️ English subtitles were removed!"
                log_event(msg)
                send_telegram(msg)
            else:
                log_event("❌ No English subtitles yet.")
        else:
            log_event("⚠️ Failed to check subtitles (connection or rate limit?)")

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    monitor()
