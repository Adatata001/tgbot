"""
Market data and summary handler
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.exceptions import TelegramBadRequest
from config import Config
from app.services import OpenAIService, MarketService
from app.services.supabase_service import supabase_service
from app.keyboards import get_main_keyboard, get_market_keyboard

router = Router()


def text_has(label: str):
    return F.text.func(lambda text: isinstance(text, str) and label.lower() in text.lower())


def format_money(value, decimals: int = 2) -> str:
    if value is None:
        return "N/A"
    try:
        return f"${float(value):,.{decimals}f}"
    except (TypeError, ValueError):
        return "N/A"


def format_percent(value) -> str:
    if value is None:
        return "N/A"
    try:
        return f"{float(value):+.2f}%"
    except (TypeError, ValueError):
        return "N/A"


@router.message(text_has("Market Summary"))
@router.message(Command("market"))
async def market_handler(message: Message):
    """Handle market button and command."""
    await message.answer(
        "Which assets would you like to analyze?",
        reply_markup=get_market_keyboard()
    )


@router.callback_query(F.data.startswith("market_"))
async def market_callback(callback: CallbackQuery):
    """Handle market selection."""
    try:
        await callback.answer()
    except TelegramBadRequest:
        pass
    asset_choice = callback.data.replace("market_", "")

    try:
        await callback.message.edit_text("Fetching market data...")
    except Exception:
        pass

    try:
        market_service = MarketService()
        ai_service = OpenAIService()
        assets = ["BTC", "ETH", "SOL"] if asset_choice == "multi" else [asset_choice]

        prices_data = await market_service.get_multiple_prices(assets)
        if prices_data.get("error"):
            await callback.message.answer(
                f"Error fetching market data: {prices_data['error']}",
                reply_markup=get_main_keyboard(Config.is_admin(callback.from_user))
            )
            return

        summary = await ai_service.get_market_summary(assets, prices_data)

        lines = [
            "Market Summary",
            "",
            f"Assets: {', '.join(assets)}",
            "",
            "Current Prices:",
        ]

        for symbol in assets:
            price_info = prices_data.get(symbol, {})
            price = price_info.get("usd")
            change = price_info.get("usd_24h_change")
            market_cap = price_info.get("usd_market_cap")
            volume = price_info.get("usd_24h_vol")
            direction = "up" if isinstance(change, (int, float)) and change > 0 else "down"

            lines.extend([
                "",
                f"{symbol}: {format_money(price)} ({format_percent(change)} 24h, {direction})",
                f"Market cap: {format_money(market_cap, 0)}",
                f"24h volume: {format_money(volume, 0)}",
            ])

            if supabase_service.is_connected() and price is not None:
                await supabase_service.cache_market_data(
                    symbol=symbol,
                    price=float(price),
                    market_cap=float(market_cap or 0),
                    volume_24h=float(volume or 0),
                    change_24h=float(change or 0),
                )

        lines.extend([
            "",
            "AI Market Read:",
            summary,
            "",
            "Data source: CoinGecko.",
        ])

        await callback.message.answer("\n".join(lines), reply_markup=get_main_keyboard(Config.is_admin(callback.from_user)))

    except Exception as e:
        await callback.message.answer(
            f"Error fetching market data: {str(e)}",
            reply_markup=get_main_keyboard(Config.is_admin(callback.from_user))
        )


@router.callback_query(F.data == "back_main")
async def back_to_main(callback: CallbackQuery):
    """Go back to main menu."""
    try:
        await callback.answer()
    except TelegramBadRequest:
        pass
    try:
        await callback.message.edit_text("Back to main menu.")
    except Exception:
        pass
    await callback.message.answer("Choose an option:", reply_markup=get_main_keyboard(Config.is_admin(callback.from_user)))
