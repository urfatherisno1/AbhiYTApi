AbhiMusicAPI — personal YouTube extractor + Telegram logger

1) Create a virtualenv and install:
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt

2) Create cookie folder and place your youtube cookie file:
   mkdir -p cookies
   # place cookies file as "cookies/youtube.txt" (Netscape format)

3) Export environment variables:
   export API_KEY="abhi_super_secret_key_change_me"
   export BOT_TOKEN="<your-bot-token>"
   export CHANNEL_ID="-1003156795901"
   export COOKIE_FILE="cookies/youtube.txt"

4) Run:
   ./start.sh

5) Test:
   curl "http://<YOUR_IP>:8000/health"
   curl "http://<YOUR_IP>:8000/api/v1/youtube?query=tere%20vaaste&api_key=YOUR_KEY"
