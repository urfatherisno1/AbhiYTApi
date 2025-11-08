#!/usr/bin/env bash
source .venv/bin/activate
export API_KEY="${API_KEY:-abhi_super_secret_key_change_me}"
export BOT_TOKEN="${BOT_TOKEN:-}"
export CHANNEL_ID="${CHANNEL_ID:-}"
export COOKIE_FILE="${COOKIE_FILE:-cookies/youtube.txt}"
python3 app.py
