"""
Scheduled market announcements
"""
import asyncio
import logging
from aiogram import Bot
from config import Config
from app.services.market_service import MarketService
from app.services.openai_service import OpenAIService
from app.services.supabase_service import supabase_service
from app.utils.user_manager import UserManager

logger = logging.getLogger(__name__)


class MarketAnnouncementService:
    """Build and send scheduled market announcements."""

    def __init__(self):
        self.market_service = MarketService()
        self.ai_service = OpenAIService()

    async def build_message(self) -> str:
        assets = Config.MARKET_ANNOUNCEMENT_ASSETS or ["BTC", "ETH", "SOL"]
        prices_data = await self.market_service.get_multiple_prices(assets)
        if prices_data.get("error"):
            return f"Market update unavailable: {prices_data['error']}"

        summary = await self.ai_service.get_market_summary(assets, prices_data)

        lines = [
            "Market Announcement",
            "",
        ]

        for symbol in assets:
            info = prices_data.get(symbol, {})
            price = info.get("usd")
            change = info.get("usd_24h_change")
            price_text = f"${float(price):,.2f}" if price is not None else "N/A"
            change_text = f"{float(change):+.2f}%" if change is not None else "N/A"
            lines.append(f"{symbol}: {price_text} ({change_text} 24h)")

        lines.extend([
            "",
            summary,
            "",
            "Data source: CoinGecko. Analysis is not financial advice.",
        ])
        return "\n".join(lines)

    async def get_recipients(self) -> list[int]:
        if supabase_service.is_connected():
            users = await supabase_service.list_users(limit=10000)
        else:
            users = list(UserManager.users.values())

        recipients = []
        for user in users:
            user_id = user.get("user_id")
            if user_id:
                recipients.append(int(user_id))
        return recipients

    async def send_now(self, bot: Bot) -> tuple[int, int]:
        message = await self.build_message()
        recipients = await self.get_recipients()
        sent = 0
        failed = 0

        for chat_id in recipients:
            try:
                await bot.send_message(chat_id=chat_id, text=message)
                sent += 1
            except Exception:
                failed += 1

        return sent, failed

    async def run_forever(self, bot: Bot):
        interval_seconds = max(5, Config.MARKET_ANNOUNCEMENT_INTERVAL_MINUTES) * 60
        while True:
            await asyncio.sleep(interval_seconds)
            try:
                sent, failed = await self.send_now(bot)
                logger.info("Market announcement sent. sent=%s failed=%s", sent, failed)
            except asyncio.CancelledError:
                raise
            except Exception as e:
                logger.error("Market announcement failed: %s", e)


market_announcement_service = MarketAnnouncementService()
