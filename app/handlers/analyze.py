"""
Strategy analysis handler
"""
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from app.services import OpenAIService
from app.services.supabase_service import supabase_service
from app.utils import UserManager, AnalyticsLimiter
from app.keyboards import get_main_keyboard
from config import Config

router = Router()


class AnalyzeStates(StatesGroup):
    waiting_for_strategy = State()


def text_has(label: str):
    return F.text.func(lambda text: isinstance(text, str) and label.lower() in text.lower())


async def ask_for_strategy(message: Message, state: FSMContext):
    await message.answer(
        "Please describe your trading strategy.\n\n"
        "Include entry conditions, exit conditions, indicators, timeframe, and risk rules if you have them.\n\n"
        "Example: RSI oversold bounce - buy when RSI < 30 on the 4h chart, exit when RSI > 70.\n\n"
        "Send /cancel to go back."
    )
    await state.set_state(AnalyzeStates.waiting_for_strategy)


@router.message(text_has("Analyze Strategy"))
async def analyze_button_handler(message: Message, state: FSMContext):
    """Handle analyze button."""
    await ask_for_strategy(message, state)


@router.message(Command("analyze"))
async def analyze_command_handler(message: Message, state: FSMContext):
    """Handle /analyze command."""
    await ask_for_strategy(message, state)


@router.message(AnalyzeStates.waiting_for_strategy)
async def strategy_received(message: Message, state: FSMContext):
    """Analyze the strategy after the user sends it."""
    if not message.text:
        await message.answer("Please send your strategy as text, or send /cancel.")
        return

    if message.text.strip().lower() == "/cancel":
        await state.clear()
        await message.answer("Operation cancelled.", reply_markup=get_main_keyboard(Config.is_admin(message.from_user)))
        return

    user_id = message.from_user.id
    user_data = await UserManager.get_or_create_user(
        user_id=user_id,
        username=message.from_user.username or "",
        first_name=message.from_user.first_name or "",
        last_name=message.from_user.last_name or "",
    )

    if not AnalyticsLimiter.can_analyze(user_id, user_data):
        await message.answer(
            f"{AnalyticsLimiter.format_limit_message(user_data)}\n\n"
            "Upgrade to Premium for unlimited analyses.",
            reply_markup=get_main_keyboard(Config.is_admin(message.from_user))
        )
        await state.clear()
        return

    strategy_text = message.text.strip()
    processing_msg = await message.answer("Analyzing your strategy. This may take a moment...")

    try:
        ai_service = OpenAIService()
        analysis_result = await ai_service.analyze_strategy(strategy_text=strategy_text)

        if analysis_result["status"] != "success":
            try:
                await processing_msg.delete()
            except Exception:
                pass
            await message.answer(
                f"Analysis failed: {analysis_result.get('error', 'Unknown error')}",
                reply_markup=get_main_keyboard(Config.is_admin(message.from_user))
            )
            await state.clear()
            return

        analysis_text = analysis_result["analysis"]
        await UserManager.increment_analysis_count(user_id)
        user_data = await UserManager.get_or_create_user(user_id)

        if supabase_service.is_connected():
            await supabase_service.save_analysis(
                user_id=user_id,
                strategy=strategy_text,
                analysis=analysis_text,
                tokens_used=analysis_result.get("tokens_used", 0),
            )

        response = (
            "Strategy Analysis Complete\n\n"
            f"{analysis_text}\n\n"
            f"{AnalyticsLimiter.format_limit_message(user_data)}"
        )

        try:
            await processing_msg.delete()
        except Exception:
            pass

        await message.answer(response, reply_markup=get_main_keyboard(Config.is_admin(message.from_user)))
        await state.clear()

    except Exception as e:
        try:
            await processing_msg.delete()
        except Exception:
            pass

        await message.answer(
            f"Error during analysis: {str(e)}\n\nPlease try again.",
            reply_markup=get_main_keyboard(Config.is_admin(message.from_user))
        )
        await state.clear()


@router.message(Command("cancel"))
async def cancel_handler(message: Message, state: FSMContext):
    """Handle cancel command."""
    await state.clear()
    await message.answer("Operation cancelled.", reply_markup=get_main_keyboard(Config.is_admin(message.from_user)))
