import os
import time
import sqlite3
import requests
import csv
from datetime import datetime
from apify_wallet_fetcher import fetch_wallets


# Load configuration from environment variables
config = {
    "telegram_bot_token": os.getenv("telegram_bot_token"),
    "telegram_chat_id": os.getenv("telegram_chat_id"),
    "solana_rpc": os.getenv("solana_rpc"),
    "buy_amount_sol": float(os.getenv("buy_amount_sol", 0.01)),
    "discord_webhook": os.getenv("discord_webhook"),
}


# CSV Log File Setup
CSV_FILE = 'alerts_log.csv'
if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["timestamp", "event", "detail"])


# Database Setup
conn = sqlite3.connect('sniper.db')
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS alerted (mint TEXT PRIMARY KEY)''')
conn.commit()


# Telegram + Discord Alert Function (REST-based)
def send_alert(message):
    """Send alerts to Telegram and Discord."""
    print(f"[ALERT] {message}")

    # Telegram Alert via REST API
    try:
        telegram_url = f"https://api.telegram.org/bot{config['telegram_bot_token']}/sendMessage"
        payload = {"chat_id": config["telegram_chat_id"], "text": message}

        response = requests.post(telegram_url, json=payload)
        if response.status_code != 200:
            print(f"[ERROR] Telegram failed: {response.text}")

    except Exception as e:
        print(f"[ERROR] Telegram alert exception: {e}")

    # Discord Alert
    if config["discord_webhook"]:
        try:
            requests.post(config["discord_webhook"], json={"content": message})
        except Exception as e:
            print(f"[ERROR] Discord alert exception: {e}")


# CSV Logger
def log_event(event, detail):
    with open(CSV_FILE, 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([datetime.utcnow().isoformat(), event, detail])


# Token Monitoring Placeholder
def process_wallets(wallets):
    """Token monitoring placeholder."""
    for wallet in wallets:
        print(f"[INFO] Watching wallet: {wallet}")
        # TODO: Add token monitoring logic here


# Main Loop
def main():
    try:
        wallets = fetch_wallets()

        if not wallets:
            send_alert("⚠️ No wallets fetched. Bot running idle.")
        else:
            send_alert(f"✅ Rage Sniper running | Monitoring {len(wallets)} wallets.")

        while True:
            process_wallets(wallets)
            log_event("heartbeat", f"Monitoring {len(wallets)} wallets")
            time.sleep(300)  # 5 minutes delay

    except Exception as e:
        send_alert(f"❌ Bot crashed: {e}")
        log_event("fatal_error", str(e))


if __name__ == "__main__":
    main()
