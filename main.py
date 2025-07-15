import os
import time
import sqlite3
import requests
import csv
from datetime import datetime
from telegram import Bot
from apify_wallet_fetcher import fetch_wallets

# Load config from environment variables
config = {
    "telegram_bot_token": os.getenv("telegram_bot_token"),
    "telegram_chat_id": os.getenv("telegram_chat_id"),
    "solana_rpc": os.getenv("solana_rpc"),
    "buy_amount_sol": float(os.getenv("buy_amount_sol", 0.01)),
    "discord_webhook": os.getenv("discord_webhook"),
}

bot = Bot(token=config["telegram_bot_token"])

# CSV log setup
CSV_FILE = 'alerts_log.csv'
if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["timestamp", "event", "detail"])

# SQLite DB setup
conn = sqlite3.connect('sniper.db')
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS alerted (mint TEXT PRIMARY KEY)''')
conn.commit()


def send_alert(message):
    """Send alerts to Telegram and Discord."""
    print(f"[ALERT] {message}")
    if config["telegram_chat_id"] and config["telegram_bot_token"]:
        try:
            bot.send_message(chat_id=config["telegram_chat_id"], text=message)
        except Exception as e:
            print(f"[ERROR] Telegram alert failed: {e}")

    if config["discord_webhook"]:
        try:
            requests.post(config["discord_webhook"], json={"content": message})
        except Exception as e:
            print(f"[ERROR] Discord alert failed: {e}")


def log_event(event, detail):
    """Log important events to CSV."""
    with open(CSV_FILE, 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([datetime.utcnow().isoformat(), event, detail])


def process_wallets(wallets):
    """Placeholder: Token scanning and monitoring logic."""
    for wallet in wallets:
        # TODO: Replace with actual token monitoring
        print(f"[INFO] Monitoring wallet: {wallet}")


def main():
    """Main bot loop."""
    try:
        wallets = fetch_wallets()
        if not wallets:
            print("[WARNING] No wallets fetched from Apify.")
            send_alert("⚠️ No wallets fetched. Bot running idle.")
        else:
            print(f"[INFO] Fetched {len(wallets)} wallets.")
            send_alert(f"✅ Sniper Bot Started | Monitoring {len(wallets)} wallets.")

        while True:
            process_wallets(wallets)
            log_event("heartbeat", f"Monitoring {len(wallets)} wallets")
            time.sleep(300)  # Check every 5 minutes

    except Exception as e:
        send_alert(f"❌ Sniper Bot crashed: {e}")
        log_event("fatal_error", str(e))


if __name__ == "__main__":
    main()
