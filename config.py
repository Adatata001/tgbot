"""
Configuration module for the Trading Bot
"""
import os
from dotenv import load_dotenv

load_dotenv()


def _split_csv(value: str) -> list[str]:
    """Split comma-separated env values while ignoring blanks."""
    return [item.strip() for item in value.split(",") if item.strip()]


def _parse_admins(value: str) -> tuple[list[int], list[str]]:
    """Support numeric Telegram IDs and @usernames in admin env config."""
    admin_ids: list[int] = []
    admin_usernames: list[str] = []

    for item in _split_csv(value):
        normalized = item.lstrip("@").strip()
        if normalized.isdigit():
            admin_ids.append(int(normalized))
        elif normalized:
            admin_usernames.append(normalized.lower())

    return admin_ids, admin_usernames


class Config:
    """Main configuration class"""
    
    # Telegram
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    
    # OpenAI
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    OPENAI_VISION_MODEL = os.getenv("OPENAI_VISION_MODEL", "gpt-4o-mini")

    # OpenRouter. When set, this overrides OpenAI for analysis calls.
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
    OPENROUTER_VISION_MODEL = os.getenv("OPENROUTER_VISION_MODEL", "openai/gpt-4o-mini")
    OPENROUTER_SITE_URL = os.getenv("OPENROUTER_SITE_URL", "")
    OPENROUTER_APP_NAME = os.getenv("OPENROUTER_APP_NAME", "Trading Bot Pro")
    
    # Database
    SUPABASE_URL = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
    SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

    # CoinGecko
    COINGECKO_API_KEY = os.getenv("COINGECKO_API_KEY", "")
    COINGECKO_API_TIER = os.getenv("COINGECKO_API_TIER", "demo").lower()
    
    # Binance
    BINANCE_API_KEY = os.getenv("BINANCE_API_KEY", "")
    BINANCE_SECRET_KEY = os.getenv("BINANCE_SECRET_KEY", "")
    
    # Admin. ADMIN_IDS accepts numeric IDs and @usernames for convenience.
    ADMIN_IDS, ADMIN_USERNAMES = _parse_admins(
        ",".join(
            [
                os.getenv("ADMIN_IDS", ""),
                os.getenv("ADMIN_USERNAMES", ""),
            ]
        )
    )
    
    # Features
    ENABLE_PREMIUM = os.getenv("ENABLE_PREMIUM", "true").lower() == "true"
    FREE_ANALYSES_PER_DAY = int(os.getenv("FREE_ANALYSES_PER_DAY", "5"))

    # Uploads
    VIDEO_FRAME_LIMIT = int(os.getenv("VIDEO_FRAME_LIMIT", "3"))

    # Market announcements
    MARKET_ANNOUNCEMENTS_ENABLED = os.getenv("MARKET_ANNOUNCEMENTS_ENABLED", "false").lower() == "true"
    MARKET_ANNOUNCEMENT_INTERVAL_MINUTES = int(os.getenv("MARKET_ANNOUNCEMENT_INTERVAL_MINUTES", "360"))
    MARKET_ANNOUNCEMENT_ASSETS = _split_csv(os.getenv("MARKET_ANNOUNCEMENT_ASSETS", "BTC,ETH,SOL"))
    
    # Validators
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        if not cls.TELEGRAM_BOT_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN is not set")
        if not cls.OPENAI_API_KEY and not cls.OPENROUTER_API_KEY:
            raise ValueError("OPENAI_API_KEY or OPENROUTER_API_KEY is not set")
        return True

    @classmethod
    def is_admin(cls, telegram_user) -> bool:
        """Return whether a Telegram user can use admin commands."""
        if not telegram_user:
            return False

        if telegram_user.id in cls.ADMIN_IDS:
            return True

        username = (telegram_user.username or "").lstrip("@").lower()
        return bool(username and username in cls.ADMIN_USERNAMES)


# Validate config on import
Config.validate()
