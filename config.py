import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    bot_token: str = os.getenv("BOT_TOKEN", "")
    youtube_api_key: str = os.getenv("YOUTUBE_API_KEY", "")
    database_url: str = os.getenv(
        "DATABASE_URL", "sqlite+aiosqlite:///./recipe_puzzle.db"
    )
    cache_ttl_seconds: int = int(os.getenv("CACHE_TTL_SECONDS", "900"))
    # Необязательно, например socks5://127.0.0.1:10808
    proxy_url: str = os.getenv("PROXY_URL", "")


settings = Settings()


def validate_settings() -> None:
    missing = []
    if not settings.bot_token:
        missing.append("BOT_TOKEN")
    if not settings.youtube_api_key:
        missing.append("YOUTUBE_API_KEY")
    if missing:
        raise RuntimeError(
            "Не заполнены переменные в .env: " + ", ".join(missing)
        )
