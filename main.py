# Folder: rage-sniper

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

# Load config from environment variables
config = {
    "telegram_bot_token": os.getenv("telegram_bot_token"),
    "telegram_chat_id": os.getenv("telegram_chat_id"),
    "solana_rpc": os.getenv("solana_rpc"),
    "buy_amount_sol": float(os.getenv("buy_amount_sol", 0.01)),
    "discord_webhook": os.getenv("discord_webhook")
}

bot = Bot(token=config['telegram_bot_token'])
client = Client(config['solana_rpc'])

# CSV file setup
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
    except: return False

def get_top_holders_percent(mint):
    try:
        pubkey = Pubkey.from_string(mint)
        res = client.get_token_largest_accounts(pubkey)
        accounts = res.value
        total = sum([int(a.amount) for a in accounts])
        top10 = sum([int(a.amount) for a in accounts[:10]])
        return top10 / total if total else 1.0
    except: return 1.0

def process_token(token):
    mint = token.get("pairAddress")
    name = token.get("baseToken", {}).get("symbol", "Unknown")
    volume = float(token.get("volumeUsd", 0))
    liquidity = float(token.get("liquidity", 0))
    fdv = float(token.get("fdv", 0))
    mcap = float(token.get("marketCap", 0))
    age = (time.time() - int(token.get("pairCreatedAt", 0))/1000) / 3600
    buys = int(token.get("txns", {}).get("buys", 0))
    sells = int(token.get("txns", {}).get("sells", 0))
    txns_1h = int(token.get("txns", {}).get("h1", {}).get("buys", 0)) + int(token.get("txns", {}).get("h1", {}).get("sells", 0))
    tags = token.get("tags", [])

    if liquidity < 10000 or fdv > 900000 or mcap < 350000 or age > 48: return
    if buys < 100 or sells < 70 or txns_1h < 100: return
    if "boosted" not in tags and "ads" not in tags: return

    if not check_rug(mint): return
    if get_top_holders_percent(mint) > 0.20: return

    cursor.execute("SELECT mint FROM alerted WHERE mint = ?", (mint,))
    if cursor.fetchone(): return  # already alerted

    cursor.execute("INSERT INTO alerted (mint) VALUES (?)", (mint,))
    conn.commit()

    message = f"\ud83d\ude80 FasolBot Snipe Alert!\n\nToken: ${name}\nMint: `{mint}`\n\n/buy SOL {mint} {config['buy_amount_sol']} --tp 2x --sl 30%\n\nRugcheck: GOOD\nLiquidity: ${liquidity:,.0f}\nVolume: ${volume:,.0f}\nTxns (1h): {txns_1h}"

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
            time.sleep(300)  # 5 minutes
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(60)

if __name__ == "__main__":
    run_sniper()

# File: requirements.txt
requests
python-telegram-bot
solana
solders

# File: .env.example
telegram_bot_token=8090955789:AAHJDfyhF-1rJ1V2K1-GTzF2jXDQKc9jIcg
telegram_chat_id=https://t.me/POTRageBot
solana_rpc=https://api.mainnet-beta.solana.com
buy_amount_sol=0.01
discord_webhook=https://discordapp.com/api/webhooks/1394217215858839633/AQhR5w2NJxBzcCg8C5ro45Am_YVHMTT_XvlYDs-2tQtgvf_SpmtDP_FVbtxem17Nqru7

# File: README.md
# Rage Sniper Bot

Solana Memecoin Sniper Bot powered by Dexscreener, GMGN, Rugcheck, and Telegram + Discord alerts.

## Deployment

1. Create a free account on Render.com
2. Connect your GitHub repository (this repo)
3. Set Environment Variables using `.env.example`
4. Use `python main.py` as the start command

## Features

- FasolBot-ready sniper alerts
- Discord + Telegram notifications
- CSV logging of all detected tokens
- Rugcheck audit filter
- Top holders distribution check

## Notes

- Alerts are formatted for manual execution via FasolBot.
- This bot is signal-only, not executing trades directly.

# File: alerts_log.csv
# (Auto-generated at runtime)
