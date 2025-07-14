import requests
import json
import time
import os

APIFY_API_TOKEN = os.getenv("apify_api_token")
if not APIFY_API_TOKEN:
    raise Exception("❌ apify_api_token environment variable not set!")

APIFY_API_URL = (
    "https://api.apify.com/v2/acts/muhammetakkurtt~gmgn-copytrade-wallet-scraper/"
    f"run-sync-get-dataset-items?token={APIFY_API_TOKEN}"
)

WALLET_FILE = "tracked_wallets.json"
FETCH_INTERVAL_HOURS = 24
LAST_FETCH_FILE = "last_fetch_time.txt"


def should_fetch():
    if not os.path.exists(LAST_FETCH_FILE):
        return True
    with open(LAST_FETCH_FILE, "r") as f:
        last_fetch_time = float(f.read())
    return (time.time() - last_fetch_time) > (FETCH_INTERVAL_HOURS * 3600)


def fetch_and_save_wallets():
    print("📡 Fetching top wallets from Apify...")
    response = requests.get(APIFY_API_URL)
    response.raise_for_status()
    wallet_data = response.json()

    with open(WALLET_FILE, "w") as f:
        json.dump(wallet_data, f, indent=4)

    with open(LAST_FETCH_FILE, "w") as f:
        f.write(str(time.time()))

    print(f"✅ {len(wallet_data)} wallets saved to {WALLET_FILE}")


def update_wallet_list():
    if should_fetch():
        fetch_and_save_wallets()
    else:
        print("⏰ Using cached wallet list (within 24h).")
