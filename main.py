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

CSV_FILE = 'alerts_log.csv'
if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["timestamp", "name", "mint", "gmgn_count", "gmgn_score", "liquidity", "volume", "txns_1h", "rugcheck_status", "top_10_pct"])

conn = sqlite3.connect('sniper.db')
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS alerted (mint TEXT PRIMARY KEY)''')
conn.commit()

def send_discord(message):
    if config['discord_webhook']:
        requests.post(config['discord_webhook'], json={"content": message})

def send_alert(message):
    bot.send_message(chat_id=config['telegram_chat_id'], text=message)
    send_discord(message)

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
    age = (time.time() - int(token.get("pairCreatedAt", 0)) / 1000) / 3600

    print(f"🛠️ Checking {name} | Mint: {mint} | Liquidity: {liquidity} | Volume: {volume} | Age: {age:.2f}h")

    if liquidity < 1000:
        print(f"❌ Skipped {name} due to low liquidity")
        return
    if age > 72:
        print(f"❌ Skipped {name} due to age over 72h")
        return
    if not check_rug(mint):
        print(f"❌ Skipped {name} - Rugcheck failed")
        return
    if get_top_holders_percent(mint) > 0.30:
        print(f"❌ Skipped {name} - Top holders exceed 30%")
        return

    # Forced Alert for Testing
    print(f"✅ TEST ALERT: {name} meets relaxed filters.")

    cursor.execute("SELECT mint FROM alerted WHERE mint = ?", (mint,))
    if cursor.fetchone():
        print(f"⏭️ Already alerted {mint}")
        return

    cursor.execute("INSERT INTO alerted (mint) VALUES (?)", (mint,))
    conn.commit()

    message = f"""🚨 TEST ALERT

Token: ${name}
Mint: `{mint}`

Simulated Buy:
/buy SOL {mint} {config['buy_amount_sol']} --tp 2x --sl 30%

Liquidity: ${liquidity:,.0f}
"""

    send_alert(message)

def run_sniper():
    print("🚀 TEST MODE: Sniper Bot Starting...")
    while True:
        try:
            pairs = fetch_dexscreener()
            print(f"🔍 Fetched {len(pairs)} tokens from Dexscreener")
            for token in pairs:
                process_token(token)
            time.sleep(120)  # Every 2 minutes
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(60)

if __name__ == "__main__":
    run_sniper()
