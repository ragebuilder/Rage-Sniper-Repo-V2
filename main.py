import time
import os
from apify_wallet_fetcher import fetch_wallets
from telegram_alert import send_telegram_message
from discord_alert import send_discord_message  # Assuming you have similar logic for Discord

def main():
    print("[INFO] Rage2Success Bot started.")

    while True:
        print("[INFO] Fetching wallets...")
        wallets = fetch_wallets()

        if not wallets:
            alert_msg = "⚠️ No wallets fetched. Bot running idle."
            print(f"[ALERT] {alert_msg}")
            send_discord_message(alert_msg)
            send_telegram_message(alert_msg)
        else:
            msg = f"✅ Bot running with {len(wallets)} wallets tracked."
            print(f"[INFO] {msg}")
            send_discord_message(msg)
            send_telegram_message(msg)

        print("[INFO] Sleeping for 24 hours before next fetch cycle...\n")
        time.sleep(86400)  # 24 hours in seconds

if __name__ == "__main__":
    main()
