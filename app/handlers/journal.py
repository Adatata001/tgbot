"""
Trading journal handler
"""
import statistics
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from app.services.advanced_analytics import advanced_analytics
from app.keyboards import get_main_keyboard
from config import Config

router = Router()


class JournalStates(StatesGroup):
    waiting_for_symbol = State()
    waiting_for_trade_type = State()
    waiting_for_entry_price = State()
    waiting_for_exit_price = State()
    waiting_for_size = State()
    waiting_for_emotions = State()
    waiting_for_notes = State()


def text_has(label: str):
    return F.text.func(lambda text: isinstance(text, str) and label.lower() in text.lower())


async def cancel_if_requested(message: Message, state: FSMContext) -> bool:
    if (message.text or "").strip().lower() == "/cancel":
        await state.clear()
        await message.answer("Operation cancelled.", reply_markup=get_main_keyboard(Config.is_admin(message.from_user)))
        return True
    return False


@router.message(text_has("Trade Journal"))
@router.message(Command("journal"))
async def journal_menu(message: Message):
    """Show trade journal menu."""
    await message.answer(
        "Trade Journal\n\n"
        "Log and analyze your trades to improve performance.\n\n"
        "Options:\n"
        "/log - Log a completed trade\n"
        "/summary - View performance summary\n"
        "/patterns - Analyze trading patterns\n"
        "/emotions - Emotional analysis\n\n"
        "Journal data is persisted to Supabase when connected.",
        reply_markup=get_main_keyboard(Config.is_admin(message.from_user))
    )


@router.message(Command("log"))
async def start_trade_logging(message: Message, state: FSMContext):
    """Start trade logging flow."""
    await message.answer(
        "Let's log your trade.\n\n"
        "What symbol were you trading?\n"
        "Example: BTCUSD, ETHUSD, EURUSD\n\n"
        "Send /cancel to go back."
    )
    await state.set_state(JournalStates.waiting_for_symbol)


@router.message(JournalStates.waiting_for_symbol)
async def get_symbol(message: Message, state: FSMContext):
    """Get trading symbol."""
    if await cancel_if_requested(message, state):
        return

    symbol = (message.text or "").upper().strip()
    if not symbol:
        await message.answer("Please send a symbol, or /cancel.")
        return

    await state.update_data(symbol=symbol)
    await message.answer("Was this trade LONG or SHORT? Send LONG, SHORT, or SKIP for LONG.")
    await state.set_state(JournalStates.waiting_for_trade_type)


@router.message(JournalStates.waiting_for_trade_type)
async def get_trade_type(message: Message, state: FSMContext):
    """Get trade direction."""
    if await cancel_if_requested(message, state):
        return

    text = (message.text or "").upper().strip()
    if text == "SKIP":
        trade_type = "LONG"
    elif text in {"LONG", "SHORT"}:
        trade_type = text
    else:
        await message.answer("Please send LONG, SHORT, SKIP, or /cancel.")
        return

    await state.update_data(trade_type=trade_type)
    await message.answer("What was your entry price?")
    await state.set_state(JournalStates.waiting_for_entry_price)


@router.message(JournalStates.waiting_for_entry_price)
async def get_entry_price(message: Message, state: FSMContext):
    """Get entry price."""
    if await cancel_if_requested(message, state):
        return

    try:
        entry_price = float(message.text)
    except (TypeError, ValueError):
        await message.answer("Please enter a valid number.")
        return

    await state.update_data(entry_price=entry_price)
    await message.answer("What was your exit price?")
    await state.set_state(JournalStates.waiting_for_exit_price)


@router.message(JournalStates.waiting_for_exit_price)
async def get_exit_price(message: Message, state: FSMContext):
    """Get exit price."""
    if await cancel_if_requested(message, state):
        return

    try:
        exit_price = float(message.text)
    except (TypeError, ValueError):
        await message.answer("Please enter a valid number.")
        return

    await state.update_data(exit_price=exit_price)
    await message.answer("What was your position size or quantity?")
    await state.set_state(JournalStates.waiting_for_size)


@router.message(JournalStates.waiting_for_size)
async def get_position_size(message: Message, state: FSMContext):
    """Get position size."""
    if await cancel_if_requested(message, state):
        return

    try:
        size = float(message.text)
    except (TypeError, ValueError):
        await message.answer("Please enter a valid number.")
        return

    await state.update_data(position_size=size)
    await message.answer(
        "How were you feeling during this trade?\n\n"
        "Examples: confident, nervous, greedy, fearful, excited\n"
        "Send SKIP if you do not want to add emotions."
    )
    await state.set_state(JournalStates.waiting_for_emotions)


@router.message(JournalStates.waiting_for_emotions)
async def get_emotions(message: Message, state: FSMContext):
    """Get emotional state."""
    if await cancel_if_requested(message, state):
        return

    text = message.text or ""
    emotions = "" if text.strip().upper() == "SKIP" else text.strip()
    await state.update_data(emotions=emotions)
    await message.answer("Any additional notes about this trade? Send SKIP if none.")
    await state.set_state(JournalStates.waiting_for_notes)


@router.message(JournalStates.waiting_for_notes)
async def get_notes_and_save(message: Message, state: FSMContext):
    """Get notes and save trade."""
    if await cancel_if_requested(message, state):
        return

    notes = "" if (message.text or "").strip().upper() == "SKIP" else (message.text or "").strip()
    data = await state.get_data()
    user_id = message.from_user.id

    try:
        result = await advanced_analytics.log_trade(
            user_id=user_id,
            symbol=data["symbol"],
            trade_type=data.get("trade_type", "LONG"),
            entry_price=data["entry_price"],
            exit_price=data["exit_price"],
            position_size=data["position_size"],
            emotions=data.get("emotions", ""),
            notes=notes
        )

        pnl = result["pnl"]
        pnl_percent = result["pnl_percent"]
        direction = "profit" if pnl > 0 else "loss" if pnl < 0 else "flat"

        response = (
            "Trade Logged Successfully\n\n"
            f"Symbol: {data['symbol']}\n"
            f"Type: {data.get('trade_type', 'LONG')}\n"
            f"Entry: ${data['entry_price']:,.2f}\n"
            f"Exit: ${data['exit_price']:,.2f}\n"
            f"Size: {data['position_size']}\n\n"
            f"PnL: ${pnl:,.2f} ({direction})\n"
            f"Return: {pnl_percent:.2f}%\n"
            f"Emotions: {data.get('emotions') or 'N/A'}\n\n"
            "Use /summary, /patterns, or /emotions to review performance."
        )

        await message.answer(response, reply_markup=get_main_keyboard(Config.is_admin(message.from_user)))
        await state.clear()

    except Exception as e:
        await message.answer(f"Error logging trade: {str(e)}", reply_markup=get_main_keyboard(Config.is_admin(message.from_user)))
        await state.clear()


@router.message(Command("summary"))
async def show_performance_summary(message: Message):
    """Show performance summary."""
    user_id = message.from_user.id
    summary = await advanced_analytics.get_performance_summary(user_id)

    if summary["total_trades"] == 0:
        await message.answer(
            "No trades logged yet.\n\nStart logging trades with /log.",
            reply_markup=get_main_keyboard(Config.is_admin(message.from_user))
        )
        return

    response = (
        "Performance Summary\n\n"
        f"Total trades: {summary['total_trades']}\n"
        f"Winning: {summary['winning_trades']} ({summary['win_rate']}%)\n"
        f"Losing: {summary['losing_trades']}\n\n"
        f"Total PnL: ${summary['total_pnl']:,.2f}\n"
        f"Best trade: ${summary['best_trade']:,.2f}\n"
        f"Worst trade: ${summary['worst_trade']:,.2f}\n"
        f"Average win: ${summary['avg_win']:,.2f}\n"
        f"Average loss: ${summary['avg_loss']:,.2f}\n"
        f"Profit factor: {summary['profit_factor']:.2f}"
    )

    await message.answer(response, reply_markup=get_main_keyboard(Config.is_admin(message.from_user)))


@router.message(Command("patterns"))
async def analyze_patterns(message: Message):
    """Analyze trading patterns."""
    user_id = message.from_user.id
    patterns = await advanced_analytics.analyze_trade_patterns(user_id)

    if patterns.get("status") == "no_data":
        await message.answer("No trade data yet. Start logging trades with /log.", reply_markup=get_main_keyboard(Config.is_admin(message.from_user)))
        return

    response = "Trading Patterns Analysis\n\n"

    if patterns["best_trading_hours"]:
        response += "Best hours:\n"
        for hour, pnl_values in patterns["best_trading_hours"]:
            response += f"- {hour}:00 avg PnL ${statistics.mean(pnl_values):,.2f}\n"
        response += "\n"

    if patterns["worst_trading_hours"]:
        response += "Worst hours:\n"
        for hour, pnl_values in patterns["worst_trading_hours"]:
            response += f"- {hour}:00 avg PnL ${statistics.mean(pnl_values):,.2f}\n"
        response += "\n"

    response += "Performance by symbol:\n"
    for symbol, perf in patterns["symbol_performance"].items():
        response += f"- {symbol}: {perf['win_rate']}% WR | ${perf['total_pnl']:,.2f} PnL\n"

    await message.answer(response, reply_markup=get_main_keyboard(Config.is_admin(message.from_user)))


@router.message(Command("emotions"))
async def analyze_emotions(message: Message):
    """Analyze emotional impact on trading."""
    user_id = message.from_user.id
    emotion_data = await advanced_analytics.get_emotion_analysis(user_id)

    if emotion_data.get("status") == "no_emotion_data":
        await message.answer(
            "No emotion data yet.\n\nWhen logging trades with /log, share how you were feeling.",
            reply_markup=get_main_keyboard(Config.is_admin(message.from_user))
        )
        return

    response = "Emotional Trading Analysis\n\n"
    for emotion, data in emotion_data["emotion_analysis"].items():
        response += (
            f"{emotion.title()}:\n"
            f"- Avg PnL: ${data['average_pnl']:,.2f}\n"
            f"- Win rate: {data['win_rate']}%\n"
            f"- Trades: {data['trade_count']}\n\n"
        )

    await message.answer(response, reply_markup=get_main_keyboard(Config.is_admin(message.from_user)))
