import time
import logging
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound, NoTranscriptAvailable

# === Setup logging ===
logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(message)s")

# === Replace this with your video ID ===
VIDEO_ID = "FSDw3jX2tvE"  # Example only

def check_english_subs(video_id):
    """Check if English subtitles exist."""
    try:
        transcripts = YouTubeTranscriptApi.list_transcripts(video_id)
        for t in transcripts:
            if 'en' in t.language_code:
                logging.info("✅ English subtitles are available!")
                return True
        logging.info("❌ No English subtitles yet.")
        return False

    except TranscriptsDisabled:
        logging.info("⚠️ Subtitles are disabled for this video.")
    except NoTranscriptFound:
        logging.info("❌ No English subtitles found.")
    except NoTranscriptAvailable:
        logging.info("❌ Subtitles are not available at all.")
    except Exception as e:
        logging.warning(f"⚠️ Error checking subtitles: {e}")
    return False


if __name__ == "__main__":
    logging.info("🎬 Starting English subtitle monitor...")
    while True:
        check_english_subs(VIDEO_ID)
        time.sleep(300)  # check every 5 minutes
