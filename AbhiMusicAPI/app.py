import os
import time
import threading
import requests
from datetime import datetime
from flask import Flask, request, jsonify
import yt_dlp

# App
app = Flask(__name__)

# Config (set these via environment variables)
API_KEY = os.getenv("API_KEY", "abhi_super_secret_key_change_me")
BOT_TOKEN = os.getenv("BOT_TOKEN", "8377129159:AAHnmvZRF1NAfNd3xfbeeE3daxaxsEABV9k")             # set before run
CHANNEL_ID = os.getenv("CHANNEL_ID", "-1003156795901")           # set before run
COOKIE_FILE = os.getenv("COOKIE_FILE", "cookies/youtube.txt")
REFRESH_INTERVAL_HOURS = int(os.getenv("COOKIE_REFRESH_HOURS", "168"))  # 7 days

# Telegram logger (safe: will do nothing if BOT_TOKEN or CHANNEL_ID not set)
def log_to_telegram(message: str):
    if not BOT_TOKEN or not CHANNEL_ID:
        print("[TG-LOG] skipping (BOT_TOKEN/CHANNEL_ID not set):", message)
        return
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {"chat_id": CHANNEL_ID, "text": message, "parse_mode": "HTML"}
        resp = requests.post(url, data=payload, timeout=10)
        if resp.status_code != 200:
            print("[TG-LOG] Telegram responded:", resp.status_code, resp.text)
    except Exception as e:
        print("[TG-LOG] error:", e)

# Background cookie refresher: uses yt-dlp option to import cookies from browser
def refresh_cookies_loop():
    while True:
        try:
            print("[COOKIE] Refresh run:", datetime.utcnow().isoformat())
            # This command attempts to produce/refresh a cookies file.
            # The exact command depends on yt-dlp & browser installed on the machine.
            # We call --cookies-from-browser to export cookies to our cookie file.
            # NOTE: Adjust browser name (chrome, firefox) if needed.
            cmd = f'yt-dlp --cookies-from-browser chrome --cookies "{COOKIE_FILE}" --skip-download --print-traffic'
            os.system(cmd)
            log_to_telegram("🍪 Cookies refreshed on server.")
        except Exception as e:
            log_to_telegram(f"⚠️ Cookie refresh failed: {e}")
        time.sleep(REFRESH_INTERVAL_HOURS * 3600)

# Start refresh thread only if cookie file path exists (directory exists)
if os.path.isdir(os.path.dirname(COOKIE_FILE)) and os.access(os.path.dirname(COOKIE_FILE), os.W_OK):
    t = threading.Thread(target=refresh_cookies_loop, daemon=True)
    t.start()
else:
    print("[COOKIE] cookies folder not writable or missing. Auto-refresh disabled.")

@app.route("/health")
def health():
    return jsonify({"ok": True, "service": "AbhiSMusic-API", "ts": int(time.time())})

@app.route("/api/v1/youtube", methods=["GET"])
def youtube_search():
    query = request.args.get("query")
    key = request.args.get("api_key") or request.headers.get("X-Api-Key")
    tg_user = request.args.get("tg_user") or request.headers.get("X-Tg-User")

    if key != API_KEY:
        return jsonify({"error": "Invalid API key", "status": False}), 403

    if not query:
        return jsonify({"error": "Missing query parameter", "status": False}), 400

    log_to_telegram(f"🎧 New Request: <b>{query}</b>\nUser: {tg_user or 'unknown'}")

    ydl_opts = {
        "quiet": True,
        "format": "bestaudio/best",
        "noplaylist": True,
        "cookiefile": COOKIE_FILE,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch1:{query}", download=False)
            if "entries" in info:
                info = info["entries"][0]

        return jsonify({
            "status": True,
            "title": info.get("title"),
            "duration": info.get("duration"),
            "thumbnail": info.get("thumbnail"),
            "audio_url": info.get("url"),
            "webpage_url": info.get("webpage_url"),
            "video_id": info.get("id")
        })
    except Exception as e:
        log_to_telegram(f"❌ Extraction error for <b>{query}</b>\n<code>{e}</code>")
        return jsonify({"error": str(e), "status": False}), 500

@app.route("/api/v1/details", methods=["GET"])
def youtube_details():
    url = request.args.get("url")
    key = request.args.get("api_key") or request.headers.get("X-Api-Key")

    if key != API_KEY:
        return jsonify({"error": "Invalid API key", "status": False}), 403

    if not url:
        return jsonify({"error": "Missing url parameter", "status": False}), 400

    ydl_opts = {
        "quiet": True,
        "format": "bestaudio/best",
        "cookiefile": COOKIE_FILE,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        return jsonify({
            "status": True,
            "title": info.get("title"),
            "duration": info.get("duration"),
            "thumbnail": info.get("thumbnail"),
            "audio_url": info.get("url"),
            "webpage_url": info.get("webpage_url"),
            "video_id": info.get("id")
        })
    except Exception as e:
        log_to_telegram(f"❌ Details error for <b>{url}</b>\n<code>{e}</code>")
        return jsonify({"error": str(e), "status": False}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
