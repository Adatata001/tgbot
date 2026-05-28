"""
Keyboard layouts for the bot
"""
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton


def get_main_keyboard(is_admin: bool = False) -> ReplyKeyboardMarkup:
    """Get main menu keyboard."""
    keyboard = [
        [KeyboardButton(text="Analyze Strategy")],
        [KeyboardButton(text="Market Summary")],
        [KeyboardButton(text="Risk Calculator")],
        [KeyboardButton(text="Trade Journal"), KeyboardButton(text="Upload Analysis")],
        [KeyboardButton(text="Premium"), KeyboardButton(text="Help")]
    ]

    if is_admin:
        keyboard.append([KeyboardButton(text="Admin")])

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True
    )


def get_analyze_keyboard() -> InlineKeyboardMarkup:
    """Get analyze menu keyboard."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Text Strategy", callback_data="analyze_text")],
            [InlineKeyboardButton(text="With Rules", callback_data="analyze_rules")],
            [InlineKeyboardButton(text="Back", callback_data="back_main")]
        ]
    )


def get_market_keyboard() -> InlineKeyboardMarkup:
    """Get market menu keyboard."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="BTC", callback_data="market_BTC")],
            [InlineKeyboardButton(text="ETH", callback_data="market_ETH")],
            [InlineKeyboardButton(text="SOL", callback_data="market_SOL")],
            [InlineKeyboardButton(text="Multi Assets", callback_data="market_multi")],
            [InlineKeyboardButton(text="Back", callback_data="back_main")]
        ]
    )


def get_premium_keyboard() -> InlineKeyboardMarkup:
    """Get premium upgrade keyboard."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="7 Days", callback_data="premium_7")],
            [InlineKeyboardButton(text="30 Days", callback_data="premium_30")],
            [InlineKeyboardButton(text="Back", callback_data="back_main")]
        ]
    )


def get_upload_keyboard() -> ReplyKeyboardMarkup:
    """Get upload analysis keyboard."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Analyze Screenshot")],
            [KeyboardButton(text="Analyze Strategy Document")],
            [KeyboardButton(text="Analyze Video")],
            [KeyboardButton(text="Back")]
        ],
        resize_keyboard=True
    )
