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
- GMGN wallet detection and scoring
- Rugcheck audit filter
- Top holders distribution check

## Notes

- Alerts are formatted for manual execution via FasolBot.
- This bot is signal-only, not executing trades directly.
