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
VIDEO_URLS = [
    "https://youtu.be/fym9zf86c7Y",
    "https://youtu.be/EXAMPLE2",
    "https://youtu.be/EXAMPLE3"
]
CHECK_INTERVAL = 60  # seconds between checks
LOG_FILE = "subtitle_update_log.txt"

# Telegram credentials (secured as environment variables)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Dictionary to track last hashes for each video
last_hashes = {url: None for url in VIDEO_URLS}

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
        requests.post(url, data=payload, timeout=10)
    except Exception as e:
        print(f"Telegram error: {e}")

# ======================================================
# 🎬 FETCH SUBTITLE STATUS (manual only)
# ======================================================
def get_manual_subtitle_status(video_url):
    """Check if manually uploaded English subtitles exist and get title."""
    try:
        result = subprocess.run([
            "python", "-m", "yt_dlp", "--skip-download", "--print-json",
            "--no-warnings", "--no-check-certificate", video_url
        ],
                                capture_output=True,
                                text=True,
                                check=True)
        info = json.loads(result.stdout)

        # Get video title
        title = info.get("title", "Unknown Title")

        # Only manual subtitles
        manual_subs = info.get("subtitles", {})

        # Look for English subtitles
        en_keys = [k for k in manual_subs.keys() if k.startswith("en")]
        if not en_keys:
            return None, title, "No manually uploaded English subtitles found."

        # Hash to track changes
        en_sub_data = {k: manual_subs[k] for k in en_keys}
        sub_data = json.dumps(en_sub_data, sort_keys=True)
        hash_val = hashlib.md5(sub_data.encode()).hexdigest()
        return hash_val, title, None

    except subprocess.CalledProcessError as e:
        return None, None, f"yt-dlp error: {e.stderr.strip()}"
    except Exception as e:
        return None, None, f"Unexpected error: {str(e)}"

# ======================================================
# 🧾 LOGGING
# ======================================================
def log_event(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {message}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")

# ======================================================
# 👀 MONITORING LOOP
# ======================================================
def monitor_subtitles():
    log_event("🚀 Starting manual English subtitle monitor for multiple videos...")
    send_telegram("✅ Manual subtitle monitor started for multiple videos!")

    while True:
        for url in VIDEO_URLS:
            current_hash, title, error = get_manual_subtitle_status(url)

            if error:
                log_event(f"⚠️ [{title}] {error}")  # <-- use title here
            elif last_hashes[url] is None:
                last_hashes[url] = current_hash
                log_event(f"✅ [{title}] Manual subtitles detected. Monitoring started.")
                send_telegram(f"✅ [{title}] Manual subtitles detected. Monitoring started.")
            elif current_hash != last_hashes[url]:
                log_event(f"🔔 [{title}] Subtitle updated!")
                send_telegram(f"🔔 [{title}] Manually uploaded English subtitles have been updated!")
                last_hashes[url] = current_hash
            else:
                log_event(f"[{title}] No subtitle change detected.")

        time.sleep(CHECK_INTERVAL)


# ======================================================
# 🌐 FLASK APP (keeps Render service alive)
# ======================================================
app = Flask(__name__)

@app.route("/")
def home():
    return "✅ Manual English Subtitle Monitor is running on Render!"

# ======================================================
# 🚀 MAIN ENTRY POINT
# ======================================================
if __name__ == "__main__":
    thread = threading.Thread(target=monitor_subtitles, daemon=True)
    thread.start()
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
