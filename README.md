# OLX.ua Telegram Bot
[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

A **Telegram bot** for real-time monitoring of new listings on [OLX.ua](https://www.olx.ua). Users can create custom search filters using OLX search URLs, enable tracking, and receive instant notifications about new ads matching their criteria.

The bot uses **Selenium** for web scraping and **Aiogram** for Telegram integration. All state (filters, seen ads) is persisted in lightweight JSON files — no external database required. It runs in **headless Chrome**, checks for new listings every **60 seconds**, and sends rich notifications with title, price, location, size (if available), link, and image.

Designed for personal use — ideal for tracking apartments, cars, electronics, or any category on OLX.ua.

---

## Key Features

- **Custom Filters** – Save named OLX search URLs (e.g., `"Kyiv Apartments"` → `https://www.olx.ua/nedvizhimost/arenda-kvartir/kiev/?...`).
- **Real-Time Monitoring** – Tracks only **today’s listings** (containing "Сьогодні" in the date).
- **Rich Notifications** – Sends full ad cards with photo (if available), formatted HTML caption, and direct link.
- **Deduplication** – Prevents duplicates using `seen_ads.json` per filter.
- **Concurrency Control** – Up to **3 simultaneous trackers** globally (configurable, but impacts performance).
- **Interactive UI** – Inline and reply keyboards for seamless filter management.
- **Built-in Help** – `/help` command with full user guide.
- **Async & Thread-Safe** – Powered by `asyncio`, `ThreadPoolExecutor`, and `RLock`-protected storage.

---

## Requirements

- **Python**: 3.10+
- **Dependencies** (via `requirements.txt`):
  - `aiogram==3.13.1` – Telegram Bot API
  - `selenium==4.25.0` – Web scraping
  - `webdriver-manager==4.0.2` – Auto ChromeDriver management
  - `python-dotenv==1.0.1` – Environment config
- **Browser**: Google Chrome (headless mode used)
- **Telegram Bot Token** – Obtain from [@BotFather](https://t.me/BotFather)
- **OS**: Windows, Linux, macOS (headless Selenium works without GUI)

---

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/olx-telegram-bot.git
   cd olx-telegram-bot
   ```

2. **Set up a virtual environment** (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate   # Linux/macOS
   # or: venv\Scripts\activate  # Windows
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

   If `requirements.txt` is missing, create it:
   ```txt
   aiogram==3.13.1
   selenium==4.25.0
   webdriver-manager==4.0.2
   python-dotenv==1.0.1
   ```

4. **Configure the bot**:
   Create `.env` in the project root:
   ```env
   BOT_TOKEN=your_bot_token_here
   ```
   Optional (defaults shown):
   ```env
   filters_file=filters.json
   seen_file=seen_ads.json
   ```

---

## Running the Bot

### Local Development
```bash
python -m app.bot
# or
python app/bot.py
```
Logs are printed to console (`INFO` level).

### Production Deployment (Linux VPS)

Use `systemd` for auto-start and reliability:

```ini
# /etc/systemd/system/olx-bot.service
[Unit]
Description=OLX.ua Telegram Monitoring Bot
After=network.target

[Service]
User=youruser
WorkingDirectory=/path/to/olx-telegram-bot
Environment=PATH=/path/to/olx-telegram-bot/venv/bin
ExecStart=/path/to/olx-telegram-bot/venv/bin/python -m app.bot
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now olx-bot
```

---

## Usage Guide (In Telegram)

1. **Start the bot**:
   - Send `/start`
   - Main menu appears:  
     `My Filters` | `Track Filter` | (`Stop!` if active)

2. **Create a Filter**:
   - `My Filters` → `Create Filter`
   - Enter name: `Kyiv-Rent`
   - Paste OLX search URL:
     ```
     https://www.olx.ua/nedvizhimost/arenda-kvartir/kiev/?search[order]=created_at:desc&search[filter_float_price:from]=5000
     ```
   - Saved to `filters.json`

3. **Manage Filters**:
   - View list under `My Filters`
   - Click filter name → see URL
   - `Delete Filter` → remove permanently

4. **Start Tracking**:
   - `Track Filter` → select filter → `Start!`
   - Bot checks every **60 seconds**
   - New ads are sent immediately with photo + details

5. **Stop Tracking**:
   - Tap `Stop!` in main menu

6. **Help**:
   - Send `/help` for full in-bot instructions

---

## Important Notes

- **Rate Limits**: Max **3 concurrent trackers**. Increase `max_parallel` in `bot.py` if needed (may affect stability).
- **OLX Blocking**: Frequent scraping may trigger CAPTCHAs or IP bans. Use responsibly.
- **Data Persistence**:
  - Filters → `filters.json`
  - Seen ads → `seen_ads.json`
  - **Backup regularly**
- **Error Handling**: Check console logs. `webdriver-manager` auto-downloads ChromeDriver.
- **Security**: Never share your `BOT_TOKEN`. No user data is stored.

---

## Support the Author

If this bot saves you time and helps you find great deals — consider supporting the developer 🇺🇦:

- **ETH**: `0xf4acece1ac6270cad690c8b0edfccccf640290ab`
- **TON**: `UQBdwmdnD9jx9h_SaOUrcEV-89G3o9RR16TPG_7WYyQ0jopu`
- **Email**: `corvi11@proton.me`

---

## License

[MIT License](LICENSE) – Free to use, modify, and distribute.

---

## Contributing

Contributions are welcome!  
Ideas for improvement:
- Email/SMS alerts
- Multiple photos per ad
- Price change detection
- Docker support
- Web dashboard

Open an **issue** or submit a **pull request**!
