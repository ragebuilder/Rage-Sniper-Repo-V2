import os
import asyncio
import requests
from telegram import Bot
from telegram.constants import ParseMode
from apify_wallet_fetcher import fetch_wallets

TELEGRAM_TOKEN = os.getenv("telegram_bot_token")
TELEGRAM_CHAT_ID = os.getenv("telegram_chat_id")
DISCORD_WEBHOOK = os.getenv("discord_webhook")

bot = Bot(token=TELEGRAM_TOKEN)

async def send_telegram(message):
    try:
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message, parse_mode=ParseMode.HTML)
        print("[INFO] Telegram message sent.")
    except Exception as e:
        print(f"[ERROR] Telegram alert exception: {e}")

def send_discord(message):
    try:
        requests.post(DISCORD_WEBHOOK, json={"content": message})
        print("[INFO] Discord message sent.")
    except Exception as e:
        print(f"[ERROR] Discord alert exception: {e}")

async def main_loop():
    while True:
        wallets = fetch_wallets()

        if not wallets:
            print("[ALERT] ⚠️ No wallets fetched. Bot running idle.")
            send_discord("⚠️ No wallets fetched. Bot running idle.")
            await send_telegram("⚠️ No wallets fetched. Bot running idle.")
        else:
            msg = f"✅ Bot running with {len(wallets)} wallets tracked."
            print(msg)
            send_discord(msg)
            await send_telegram(msg)

        print("[INFO] Sleeping for 24 hours before next fetch cycle...")
        await asyncio.sleep(60 * 60 * 24)

if __name__ == "__main__":
    asyncio.run(main_loop())
