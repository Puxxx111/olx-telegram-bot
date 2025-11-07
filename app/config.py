import os
from dataclasses import dataclass
from dotenv import load_dotenv


@dataclass
class Config:
    bot_token: str
    filters_file: str = "filters.json"
    seen_file: str = "seen_ads.json"


def load_config() -> Config:
    load_dotenv()
    # Fallback: hardcode your token below if you don't want to use .env
    DEFAULT_BOT_TOKEN = ""  # e.g. "123456:ABC..." (leave empty to require env)
    token = os.getenv("BOT_TOKEN") or DEFAULT_BOT_TOKEN
    if not token:
        raise RuntimeError("BOT_TOKEN env variable is required")
    return Config(bot_token=token)


