import os
import requests

# Load environment variables (ensure secrets set in Fly.io or .env)
TELEGRAM_BOT_TOKEN = os.getenv("telegram_bot_token")
TELEGRAM_CHAT_ID = os.getenv("telegram_chat_id")

def send_telegram_message(message):
    """
    Send a message via Telegram using the bot token and chat ID.
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("[ERROR] Missing Telegram token or chat ID environment variables.")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message
    }

    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            print("[INFO] Telegram message sent successfully.")
        else:
            print(f"[ERROR] Telegram API error: {response.text}")

    except Exception as e:
        print(f"[ERROR] Telegram alert exception: {e}")
