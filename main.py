import os
import time
from telegram import Bot
import requests
from apify_wallet_fetcher import fetch_wallets

# Load config from environment variables
config = {
    "telegram_bot_token": os.getenv("telegram_bot_token"),
    "telegram_chat_id": os.getenv("telegram_chat_id"),
    "discord_webhook": os.getenv("discord_webhook"),
    "buy_amount_sol": float(os.getenv("buy_amount_sol", 0.01)),
    "solana_rpc": os.getenv("solana_rpc"),
    "apify_api_token": os.getenv("apify_api_token")
}

bot = Bot(token=config["telegram_bot_token"])

def send_telegram(message: str):
    try:
        bot.send_message(chat_id=config["telegram_chat_id"], text=message)
    except Exception as e:
        print(f"[ERROR] Telegram alert exception: {e}")

def send_discord(message: str):
    try:
        requests.post(config["discord_webhook"], json={"content": message})
    except Exception as e:
        print(f"[ERROR] Discord alert exception: {e}")

def main():
    while True:
        wallets = fetch_wallets()
        if not wallets:
            print("[ALERT] ⚠️ No wallets fetched. Bot running idle.")
            send_discord("⚠️ No wallets fetched. Bot running idle.")
            send_telegram("⚠️ No wallets fetched. Bot running idle.")
        else:
            print(f"[INFO] Bot running with {len(wallets)} wallets.")
            send_discord(f"✅ Bot running with {len(wallets)} wallets.")
            send_telegram(f"✅ Bot running with {len(wallets)} wallets.")

        time.sleep(60 * 60 * 24)  # Run every 24 hours

if __name__ == "__main__":
    main()
