import subprocess
import json
import time
import requests
import os
from datetime import datetime

# ==========================
# 🔧 CONFIGURATION
# ==========================
VIDEO_URL = "https://www.youtube.com/watch?v=JdvzWjXWBHc&list=PLJGupZvqQHAs2MoSYfxdgjYIj2MPqMfQ1"  # YouTube video to monitor
CHECK_INTERVAL = 60  # check every 30 minutes (in seconds)
LOG_FILE = "subtitle_update_log.txt"

# 🧩 Load secret variables (from Replit/Render secrets)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# ==========================
# ⚙️ CORE FUNCTIONS
# ==========================
def send_telegram(message: str):
    """Send message to Telegram bot."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Telegram variables missing — set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID.")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        requests.post(url, data=payload, timeout=10)
    except Exception as e:
        print(f"Telegram error: {e}")


def log_event(message: str):
    """Write log message to file with timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {message}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def check_english_subtitles():
    """Return True if English subtitles exist, False if not."""
    try:
        # Only get video info, no downloading
        result = subprocess.run(
            ["yt-dlp", "-J", VIDEO_URL],
            capture_output=True, text=True, check=True
        )

        info = json.loads(result.stdout)
        subtitles = info.get("subtitles", {})

        if "en" in subtitles:
            return True, "✅ English subtitles found."
        else:
            return False, "❌ No English subtitles yet."

    except subprocess.CalledProcessError as e:
        return None, f"yt-dlp error: {e.stderr.strip()}"
    except Exception as e:
        return None, f"Unexpected error: {str(e)}"


# ==========================
# 🚀 MAIN MONITOR LOOP
# ==========================
def monitor_subtitles():
    log_event("🎬 Starting English subtitle monitor...")
    last_state = None  # Track last subtitle existence (to detect changes)

    while True:
        has_subs, message = check_english_subtitles()

        if has_subs is None:
            log_event(f"⚠️ Check failed: {message}")
        else:
            log_event(message)

            # Notify only when a change happens (True → False or False → True)
            if has_subs != last_state:
                if has_subs:
                    send_telegram("🎉 English subtitles are now available!")
                else:
                    send_telegram("⚠️ English subtitles are missing or removed.")
                last_state = has_subs

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    monitor_subtitles()
