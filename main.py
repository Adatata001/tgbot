"""
Main bot application
"""
import logging
import asyncio
from typing import Any, Awaitable, Callable
from aiogram import BaseMiddleware, Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand, BotCommandScopeChat, ErrorEvent
from config import Config
from app.handlers import (
    start_router,
    analyze_router,
    market_router,
    help_router,
    payments_router,
    journal_router,
    upload_router,
    admin_router,
)
from app.services.supabase_service import supabase_service, init_supabase
from app.services.announcement_service import market_announcement_service
from app.utils.user_manager import UserManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class UserRegistrationMiddleware(BaseMiddleware):
    """Register/update Telegram users before handlers run."""

    async def __call__(
        self,
        handler: Callable[[types.TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: types.TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = data.get("event_from_user")
        if user and not user.is_bot:
            await UserManager.get_or_create_user(
                user_id=user.id,
                username=user.username or "",
                first_name=user.first_name or "",
                last_name=user.last_name or "",
            )

        return await handler(event, data)


class TradingBot:
    """Main bot class"""
    
    def __init__(self):
        self.bot = Bot(token=Config.TELEGRAM_BOT_TOKEN)
        self.storage = MemoryStorage()
        self.dp = Dispatcher(storage=self.storage)
        self.setup_handlers()
    
    def setup_handlers(self):
        """Setup all handlers and routers"""
        registration_middleware = UserRegistrationMiddleware()
        self.dp.message.middleware(registration_middleware)
        self.dp.callback_query.middleware(registration_middleware)
        self.dp.pre_checkout_query.middleware(registration_middleware)

        # Include routers
        self.dp.include_router(start_router)
        self.dp.include_router(analyze_router)
        self.dp.include_router(market_router)
        self.dp.include_router(help_router)
        self.dp.include_router(payments_router)
        self.dp.include_router(journal_router)
        self.dp.include_router(upload_router)
        self.dp.include_router(admin_router)
        
        # Add error handler
        self.dp.error.register(self.error_handler)
    
    async def error_handler(self, event: ErrorEvent):
        """Handle errors."""
        update = event.update
        exception = event.exception
        logger.error("Update %s caused error: %s", update.update_id if update else "unknown", exception)
        try:
            if update and update.message:
                await self.bot.send_message(
                    chat_id=update.message.chat.id,
                    text="An error occurred. Please try again or use /help"
                )
            elif update and update.callback_query and update.callback_query.message:
                await self.bot.send_message(
                    chat_id=update.callback_query.message.chat.id,
                    text="An error occurred. Please try again or use /help"
                )
        except Exception as e:
            logger.error(f"Failed to send error message: {e}")
    
    async def set_commands(self):
        """Set bot commands"""
        commands = [
            BotCommand(command="start", description="Start the bot"),
            BotCommand(command="analyze", description="Analyze a trading strategy"),
            BotCommand(command="market", description="Get market summary"),
            BotCommand(command="risk", description="Calculate trade risk"),
            BotCommand(command="journal", description="Trade journal & analytics"),
            BotCommand(command="upload", description="Analyze screenshots/documents/videos"),
            BotCommand(command="premium", description="Upgrade to premium"),
            BotCommand(command="paysupport", description="Premium payment support"),
            BotCommand(command="terms", description="Premium terms"),
            BotCommand(command="help", description="Show help message"),
        ]
        await self.bot.set_my_commands(commands)

        admin_commands = commands + [
            BotCommand(command="admin", description="Admin panel"),
        ]
        for admin_id in Config.ADMIN_IDS:
            await self.bot.set_my_commands(
                admin_commands,
                scope=BotCommandScopeChat(chat_id=admin_id),
            )
    
    async def start(self):
        """Start the bot"""
        try:
            logger.info("Starting Trading Bot Pro...")
            
            # Initialize Supabase
            await init_supabase()
            UserManager.set_supabase_service(supabase_service)
            
            if supabase_service.is_connected():
                logger.info("✅ Database connected - using persistent storage")
            else:
                logger.warning("⚠️ Using in-memory storage (Supabase not connected)")
            
            await self.set_commands()
            logger.info("Bot commands set")

            announcement_task = None
            if Config.MARKET_ANNOUNCEMENTS_ENABLED:
                announcement_task = asyncio.create_task(
                    market_announcement_service.run_forever(self.bot)
                )
                logger.info(
                    "Market announcements enabled every %s minutes",
                    Config.MARKET_ANNOUNCEMENT_INTERVAL_MINUTES,
                )
            
            # Start polling
            logger.info("Starting polling...")
            await self.dp.start_polling(self.bot, allowed_updates=self.dp.resolve_used_update_types())
        except Exception as e:
            logger.error(f"Error starting bot: {e}")
            raise
        finally:
            if "announcement_task" in locals() and announcement_task:
                announcement_task.cancel()
                try:
                    await announcement_task
                except asyncio.CancelledError:
                    pass
            await self.bot.session.close()


async def main():
    """Main entry point"""
    bot = TradingBot()
    await bot.start()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
