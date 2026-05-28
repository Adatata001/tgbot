"""
Help and risk calculation handler
"""
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from app.services import OpenAIService
from app.keyboards import get_main_keyboard
from config import Config

router = Router()


class RiskStates(StatesGroup):
    waiting_for_setup = State()
    waiting_for_position_size = State()
    waiting_for_leverage = State()


def text_has(label: str):
    return F.text.func(lambda text: isinstance(text, str) and label.lower() in text.lower())


@router.message(text_has("Risk Calculator"))
@router.message(Command("risk"))
async def risk_handler(message: Message, state: FSMContext):
    """Handle risk calculator."""
    await message.answer(
        "Risk Calculator\n\n"
        "Describe your trade setup.\n\n"
        "Example: Long BTC at 42000, targeting 44000, support at 40500.\n\n"
        "Send /cancel to go back."
    )
    await state.set_state(RiskStates.waiting_for_setup)


@router.message(RiskStates.waiting_for_setup)
async def risk_setup_received(message: Message, state: FSMContext):
    """Process trade setup."""
    if message.text and message.text.strip().lower() == "/cancel":
        await state.clear()
        await message.answer("Operation cancelled.", reply_markup=get_main_keyboard(Config.is_admin(message.from_user)))
        return

    setup = message.text or ""
    if not setup.strip():
        await message.answer("Please send the trade setup as text, or send /cancel.")
        return

    await state.update_data(setup=setup.strip())

    await message.answer(
        "Position size in USD? Send a number or SKIP.\n\n"
        "Example: 1000"
    )
    await state.set_state(RiskStates.waiting_for_position_size)


@router.message(RiskStates.waiting_for_position_size)
async def risk_position_received(message: Message, state: FSMContext):
    """Process position size."""
    text = (message.text or "").strip().upper()

    if text == "/CANCEL":
        await state.clear()
        await message.answer("Operation cancelled.", reply_markup=get_main_keyboard(Config.is_admin(message.from_user)))
        return

    if text == "SKIP":
        position_size = None
    else:
        try:
            position_size = float(text)
        except ValueError:
            await message.answer("Please enter a valid number or SKIP.")
            return

    await state.update_data(position_size=position_size)

    await message.answer(
        "Leverage? Send a number or SKIP for 1x.\n\n"
        "Example: 5"
    )
    await state.set_state(RiskStates.waiting_for_leverage)


@router.message(RiskStates.waiting_for_leverage)
async def risk_analysis(message: Message, state: FSMContext):
    """Perform risk analysis."""
    text = (message.text or "").strip().upper()

    if text == "/CANCEL":
        await state.clear()
        await message.answer("Operation cancelled.", reply_markup=get_main_keyboard(Config.is_admin(message.from_user)))
        return

    if text == "SKIP":
        leverage = 1.0
    else:
        try:
            leverage = float(text)
        except ValueError:
            await message.answer("Please enter a valid number or SKIP.")
            return

    data = await state.get_data()
    setup = data.get("setup", "")
    position_size = data.get("position_size")
    processing_msg = await message.answer("Analyzing risk parameters...")

    try:
        ai_service = OpenAIService()
        analysis = await ai_service.analyze_risk(setup, position_size, leverage)

        try:
            await processing_msg.delete()
        except Exception:
            pass

        if analysis["status"] == "success":
            response = (
                "Risk Analysis\n\n"
                f"{analysis['analysis']}\n\n"
                "Reminder: Always use stop losses. This is analysis, not financial advice."
            )
            await message.answer(response, reply_markup=get_main_keyboard(Config.is_admin(message.from_user)))
        else:
            await message.answer(
                f"Analysis failed: {analysis.get('error')}",
                reply_markup=get_main_keyboard(Config.is_admin(message.from_user))
            )

        await state.clear()

    except Exception as e:
        try:
            await processing_msg.delete()
        except Exception:
            pass
        await message.answer(f"Error: {str(e)}", reply_markup=get_main_keyboard(Config.is_admin(message.from_user)))
        await state.clear()


@router.message(text_has("Help"))
async def help_button_handler(message: Message):
    """Show help."""
    help_text = """
How to Use Trading Bot Pro

Main Features:

Analyze Strategy - Get AI analysis of your trading strategy
Market Summary - Real-time CoinGecko crypto data with AI market read
Risk Calculator - Calculate position sizing and stop-loss considerations
Premium - Pay with Telegram Stars for unlimited analyses

Commands:
/start - Main menu
/analyze - Strategy analysis
/market - Market summary
/risk - Risk calculator
/premium - Premium plans
/help - Help message
"""
    await message.answer(help_text, reply_markup=get_main_keyboard(Config.is_admin(message.from_user)))
