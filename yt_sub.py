import subprocess
import json
import time
import hashlib
import os
from datetime import datetime
import requests
from flask import Flask
import threading

# ======================================================
# 🔧 CONFIGURATION
# ======================================================
VIDEO_URL = "https://youtu.be/FSDw3jX2tvE"  # YouTube video to monitor
CHECK_INTERVAL = 60 * 60  # Check every 1 hour (in seconds)
LOG_FILE = "subtitle_update_log.txt"

# Telegram setup (from Render environment variables)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# ======================================================
# 💬 TELEGRAM FUNCTION
# ======================================================
def send_telegram(message):
    """Send a message to your Telegram bot."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Missing Telegram credentials.")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}

    try:
        response = requests.post(url, data=payload)
        if response.status_code != 200:
            print(f"⚠️ Telegram failed: {response.text}")
    except Exception as e:
        print(f"Telegram error: {e}")

# ======================================================
# 🎬 FETCH SUBTITLE HASH
# ======================================================
def get_subtitle_hash():
    """Fetch subtitle info and compute a hash."""
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

# ======================================================
# 🧾 LOGGING
# ======================================================
def log_event(message):
    """Write message to log file and console."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {message}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")

# ======================================================
# 👀 MONITORING LOOP
# ======================================================
def monitor_subtitles():
    """Continuously check for subtitle updates."""
    log_event("🚀 Starting subtitle monitor...")
    send_telegram("✅ Subtitle monitor started on Render!")

    last_hash = None

    while True:
        current_hash, error = get_subtitle_hash()

        if error:
            log_event(f"❌ Check failed: {error}")
        elif last_hash is None:
            last_hash = current_hash
            log_event("Initial subtitle hash recorded.")
        elif current_hash != last_hash:
            log_event("🔔 Subtitle updated!")
            send_telegram("🔔 Subtitle updated on YouTube video!")
            last_hash = current_hash
        else:
            log_event("No subtitle change detected.")

        time.sleep(CHECK_INTERVAL)

# ======================================================
# 🌐 FLASK APP (keeps Render service alive)
# ======================================================
app = Flask(__name__)

@app.route("/")
def home():
    return "✅ Subtitle Monitor is running on Render!"

# ======================================================
# 🚀 MAIN ENTRY POINT
# ======================================================
if __name__ == "__main__":
    # Run the monitor in a background thread
    thread = threading.Thread(target=monitor_subtitles, daemon=True)
    thread.start()

    # Keep the web service running
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)))
