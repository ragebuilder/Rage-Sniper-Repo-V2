import json
import time
import sqlite3
import requests
import csv
import os
from datetime import datetime
from solana.rpc.api import Client
from solders.pubkey import Pubkey
from telegram import Bot

# Config with hardcoded Helius API Key
config = {
    "telegram_bot_token": os.getenv("telegram_bot_token"),
    "telegram_chat_id": os.getenv("telegram_chat_id"),
    "solana_rpc": os.getenv("solana_rpc"),
    "buy_amount_sol": float(os.getenv("buy_amount_sol", 0.01)),
    "discord_webhook": os.getenv("discord_webhook"),
    "helius_api_key": "f76a874c-43d3-4801-bbe8-aa36e5ea2349"
}

bot = Bot(token=config['telegram_bot_token'])
client = Client(config['solana_rpc'])

# CSV logging setup
CSV_FILE = 'alerts_log.csv'
if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["timestamp", "name", "mint", "gmgn_count", "gmgn_score", "liquidity", "volume", "txns_1h", "rugcheck_status", "top_10_pct"])

# Database setup
conn = sqlite3.connect('sniper.db')
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS alerted (mint TEXT PRIMARY KEY)''')
conn.commit()

# Bundle Check Cache
bundle_cache = {}

RECENT_MINT_WINDOW_SECONDS = 86400
MULTI_MINT_THRESHOLD = 2

def send_discord(message):
    if config['discord_webhook']:
        requests.post(config['discord_webhook'], json={"content": message})

def send_alert(message):
    bot.send_message(chat_id=config['telegram_chat_id'], text=message)
    send_discord(message)

def check_bundle(creator_wallet):
    if creator_wallet in bundle_cache:
        return bundle_cache[creator_wallet]

    print(f"Checking bundle risk for creator: {creator_wallet}")
    url = f"https://api.helius.xyz/v0/addresses/{creator_wallet}/transactions?api-key={config['helius_api_key']}&limit=100"

    try:
        res = requests.get(url)
        res.raise_for_status()
        txs = res.json()
        now = time.time()
        recent_mints = []

        for tx in txs:
            if tx.get('type') in ['NFT_MINT', 'TOKEN_MINT']:
                timestamp = tx.get('timestamp', 0)
                if now - timestamp <= RECENT_MINT_WINDOW_SECONDS:
                    recent_mints.append(tx)

        if len(recent_mints) >= MULTI_MINT_THRESHOLD:
            alert_msg = f"🚨 Bundle Detected ({len(recent_mints)} recent mints) from creator {creator_wallet}"
            print(alert_msg)
            send_alert(alert_msg)
            bundle_cache[creator_wallet] = True
            return True
        else:
            print(f"✅ No Bundle Risk for {creator_wallet}")
            bundle_cache[creator_wallet] = False
            return False

    except Exception as e:
        print(f"Bundle check failed for {creator_wallet}: {e}")
        bundle_cache[creator_wallet] = False
        return False

def fetch_dexscreener():
    return requests.get("https://api.dexscreener.com/latest/dex/pairs/solana").json().get("pairs", [])

def check_rug(mint):
    try:
        res = requests.get(f"https://api.rugcheck.xyz/v1/tokens/{mint}/report")
        return res.ok and res.json().get("status", "").upper() == "GOOD"
    except:
        return False

def get_top_holders_percent(mint):
    try:
        pubkey = Pubkey.from_string(mint)
        res = client.get_token_largest_accounts(pubkey)
        accounts = res.value
        total = sum([int(a.amount) for a in accounts])
        top10 = sum([int(a.amount) for a in accounts[:10]])
        return top10 / total if total else 1.0
    except:
        return 1.0

def process_token(token):
    mint = token.get("pairAddress")
    name = token.get("baseToken", {}).get("symbol", "Unknown")
    volume = float(token.get("volumeUsd", 0))
    liquidity = float(token.get("liquidity", 0))
    fdv = float(token.get("fdv", 0))
    mcap = float(token.get("marketCap", 0))
    age = (time.time() - int(token.get("pairCreatedAt", 0)) / 1000) / 3600
    buys = int(token.get("txns", {}).get("buys", 0))
    sells = int(token.get("txns", {}).get("sells", 0))
    txns_1h = int(token.get("txns", {}).get("h1", {}).get("buys", 0)) + int(token.get("txns", {}).get("h1", {}).get("sells", 0))
    tags = token.get("tags", [])

    creator_wallet = token.get("baseToken", {}).get("address", None)
    if not creator_wallet:
        print(f"No creator wallet found for token {mint}. Skipping bundle check.")
        return

    if liquidity < 10000 or fdv > 900000 or mcap < 350000 or age > 48:
        return
    if buys < 100 or sells < 70 or txns_1h < 100:
        return
    if "boosted" not in tags and "ads" not in tags:
        return
    if not check_rug(mint):
        return
    if get_top_holders_percent(mint) > 0.20:
        return
    if check_bundle(creator_wallet):
        print(f"⛔ Skipping {mint} due to bundle risk.")
        return

    cursor.execute("SELECT mint FROM alerted WHERE mint = ?", (mint,))
    if cursor.fetchone():
        return

    cursor.execute("INSERT INTO alerted (mint) VALUES (?)", (mint,))
    conn.commit()

    message = f"""🚀 FasolBot Snipe Alert!

Token: ${name}
Mint: `{mint}`

/buy SOL {mint} {config['buy_amount_sol']} --tp 2x --sl 30%

Rugcheck: GOOD
Liquidity: ${liquidity:,.0f}
Volume: ${volume:,.0f}
Txns (1h): {txns_1h}
"""

    send_alert(message)

    with open(CSV_FILE, 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([datetime.utcnow().isoformat(), name, mint, 0, 0, liquidity, volume, txns_1h, 'GOOD', 0])

def run_sniper():
    while True:
        try:
            pairs = fetch_dexscreener()
            for token in pairs:
                process_token(token)
            time.sleep(300)
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(60)

if __name__ == "__main__":
    run_sniper()