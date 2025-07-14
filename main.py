# File: main.py

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
from bs4 import BeautifulSoup

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
        writer.writerow(["timestamp", "name", "mint", "gmgn_flag", "liquidity", "volume", "txns_1h", "rugcheck_status", "top_10_pct"])

conn = sqlite3.connect('sniper.db')
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS alerted (mint TEXT PRIMARY KEY)''')
conn.commit()

# GMGN Scraper
GMGN_WALLETS = set()

def update_gmgn_wallets():
    print("🔍 Scraping GMGN for top wallets...")
    url = "https://gmgn.ai/trade/5w8cdvu6?chain=sol"
    try:
        resp = requests.get(url)
        soup = BeautifulSoup(resp.text, 'html.parser')
        data_text = soup.find("script", {"id": "__NEXT_DATA__"})
        if not data_text:
            print("GMGN scrape failed: No data script tag found")
            return
        data_json = json.loads(data_text.text)
        entries = json.dumps(data_json).split("walletAddress")
        wallets = set()
        for entry in entries:
            if len(entry) > 20:
                wallet = entry.split('"')[2]
                if len(wallet) > 30:
                    wallets.add(wallet)
        if wallets:
            GMGN_WALLETS.clear()
            GMGN_WALLETS.update(wallets)
            print(f"✅ GMGN wallets updated: {len(GMGN_WALLETS)} wallets tracked.")
        else:
            print("⚠️ GMGN scrape returned no wallets.")
    except Exception as e:
        print(f"GMGN scrape failed: {e}")

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
    liquidity = float(token.get("liquidity", 0))
    txns_1h = int(token.get("txns", {}).get("h1", {}).get("buys", 0)) + int(token.get("txns", {}).get("h1", {}).get("sells", 0))
    creator_wallet = token.get("baseToken", {}).get("address", None)
    gmgn_flag = False

    print(f"Checking {name} | Mint: {mint}")

    if creator_wallet in GMGN_WALLETS:
        print(f"⚡ GMGN wallet detected: {creator_wallet}")
        gmgn_flag = True
        send_alert(f"⚡ GMGN Top Wallet Detected!\nToken: ${name}\nMint: `{mint}`")

    if liquidity < 10000:
        return
    if not check_rug(mint):
        return
    if get_top_holders_percent(mint) > 0.20:
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

Liquidity: ${liquidity:,.0f}
Txns (1h): {txns_1h}
{'⚡ GMGN Wallet Detected!' if gmgn_flag else ''}
"""
    send_alert(message)

    with open(CSV_FILE, 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([datetime.utcnow().isoformat(), name, mint, gmgn_flag, liquidity, 0, txns_1h, 'GOOD', 0])

def run_sniper():
    print("🚀 Rage Sniper with GMGN Starting...")
    while True:
        try:
            update_gmgn_wallets()
            pairs = fetch_dexscreener()
            for token in pairs:
                process_token(token)
            time.sleep(300)
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(60)

if __name__ == "__main__":
    run_sniper()
