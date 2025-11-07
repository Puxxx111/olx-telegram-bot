# OLX Telegram Bot (aiogram + selenium)

## Quick start

1. Create venv and install deps:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Export bot token:
```bash
export BOT_TOKEN=YOUR_TELEGRAM_BOT_TOKEN
```
or
open .env file and paste your bot token

3. Run bot:
```bash
python -m app.bot
```

## Features
- Manage filters (name -> OLX URL) stored in `filters.json`
- Start/stop tracking new ads for a selected filter
- Headless Selenium parser checks every 60s
- Sends nicely formatted messages with photo, title, price, location/date, size, link
- Deduplicates ads using ad `id` per filter (`seen_ads.json`)

## Files
- `app/bot.py` – bot and handlers
- `app/parser.py` – Selenium scraper for OLX listing grid
- `app/filters_storage.py` – JSON storage for filters
- `app/seen_storage.py` – JSON storage for seen ad ids
- `app/keyboards.py` – menus
- `app/config.py` – env config

## Notes
- Chrome/Chromedriver is auto-managed via `webdriver-manager`.
- Ensure the machine has Google Chrome or Chromium available.

