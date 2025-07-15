import os
import time
import requests
from telegram import Bot
from telegram.error import TelegramError
from apify_wallet_fetcher import fetch_wallets

# Load environment variables
config = {
    "telegram_bot_token": os.getenv("telegram_bot_token"),
    "telegram_chat_id": os.getenv("telegram_chat_id"),
    "discord_webhook": os.getenv("discord_webhook"),
    "buy_amount_sol": float(os.getenv("buy_amount_sol", 0.01))
}

# Initialize Telegram bot
bot = Bot(token=config["telegram_bot_token"])


def send_telegram_message(message):
    max_attempts = 3
    delay_seconds = 5

    for attempt in range(max_attempts):
        try:
            bot.send_message(chat_id=config["telegram_chat_id"], text=message, timeout=15)
            print("[INFO] Telegram message sent successfully.")
            return
        except TelegramError as e:
            print(f"[WARNING] Telegram send failed: {e}. Retrying {attempt+1}/{max_attempts}...")
            time.sleep(delay_seconds)
        except requests.exceptions.ReadTimeout:
            print(f"[WARNING] Telegram timeout. Retrying {attempt+1}/{max_attempts}...")
            time.sleep(delay_seconds)
        except Exception as e:
            print(f"[ERROR] Telegram alert exception: {e}")
            time.sleep(delay_seconds)

    print("[ALERT] Telegram message failed after retries.")


def send_discord_message(message):
    webhook = config.get("discord_webhook")
    if webhook:
        try:
            requests.post(webhook, json={"content": message}, timeout=10)
            print("[INFO] Discord message sent.")
        except Exception as e:
            print(f"[ERROR] Discord alert exception: {e}")


def alert_all(message):
    send_telegram_message(message)
    send_discord_message(message)


def main():
    while True:
        print("[INFO] Starting smart wallet fetch cycle...")

        wallets = fetch_wallets()

        if not wallets:
            print("[ALERT] ⚠️ No wallets fetched. Bot running idle.")
            alert_all("⚠️ No wallets fetched. Bot running idle.")
        else:
            msg = f"✅ Bot running with {len(wallets)} wallets tracked."
            print(msg)
            alert_all(msg)

        print("[INFO] Sleeping for 24 hours before next fetch cycle...")
        time.sleep(86400)  # 24 hours


if __name__ == "__main__":
    main()
