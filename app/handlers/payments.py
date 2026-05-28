"""
Telegram Stars payment system for Premium subscriptions
"""
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, LabeledPrice, PreCheckoutQuery
from aiogram.filters import Command
from aiogram.exceptions import TelegramBadRequest
from config import Config
from app.services.supabase_service import supabase_service
from app.services.settings_service import settings_service
from app.utils import UserManager
from app.keyboards import get_main_keyboard

router = Router()
logger = logging.getLogger(__name__)

def get_premium_plans():
    return settings_service.get_premium_plans()


def text_has(label: str):
    return F.text.func(lambda text: isinstance(text, str) and label.lower() in text.lower())


def format_expiry(value) -> str:
    expiry = UserManager.parse_datetime(value)
    return expiry.strftime("%B %d, %Y") if expiry else "Unlimited"


def premium_keyboard():
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    plans = get_premium_plans()

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"{plan['label']} ({plan['stars']} Stars)",
                    callback_data=f"pay_{plan_key}",
                )
            ]
            for plan_key, plan in plans.items()
        ] + [[InlineKeyboardButton(text="Back", callback_data="back_main")]]
    )


@router.message(text_has("Premium"))
@router.message(Command("premium"))
async def premium_menu(message: Message):
    """Show premium subscription options."""
    user_data = await UserManager.get_or_create_user(
        user_id=message.from_user.id,
        username=message.from_user.username or "",
        first_name=message.from_user.first_name or "",
        last_name=message.from_user.last_name or "",
    )

    premium_until = UserManager.parse_datetime(user_data.get("premium_until"))
    is_active = bool(user_data.get("is_premium") and (premium_until is None or premium_until > UserManager._now()))

    if is_active:
        premium_text = (
            "You are Premium.\n\n"
            f"Active until: {format_expiry(user_data.get('premium_until'))}\n\n"
            "Premium benefits:\n"
            "- Unlimited strategy analyses\n"
            "- Advanced risk calculations\n"
            "- Priority support\n"
            "- Portfolio analytics\n\n"
            "You can pay again to extend your access."
        )
    else:
        premium_text = (
            "Upgrade to Premium\n\n"
            "Current plan: Free (5 analyses/day)\n\n"
            "Premium benefits:\n"
            "- Unlimited strategy analyses\n"
            "- Advanced risk calculations\n"
            "- Priority support\n"
            "- Portfolio analytics\n\n"
            "Choose a Telegram Stars plan below."
        )

    await message.answer(premium_text, reply_markup=premium_keyboard())


@router.message(Command("paysupport"))
async def payment_support(message: Message):
    """Provide payment support details required for Stars purchases."""
    admin_contact = f"@{Config.ADMIN_USERNAMES[0]}" if Config.ADMIN_USERNAMES else "the bot admin"
    await message.answer(
        "Payment Support\n\n"
        f"For Premium payment issues, contact {admin_contact} with your Telegram username and purchase date.\n\n"
        "Telegram support cannot resolve purchases made inside this bot; payment support is handled by the bot owner.",
        reply_markup=get_main_keyboard(Config.is_admin(message.from_user))
    )


@router.message(Command("terms"))
async def payment_terms(message: Message):
    """Show basic purchase terms for Premium."""
    await message.answer(
        "Terms for Premium\n\n"
        "- Premium is a digital subscription inside this Telegram bot.\n"
        "- Payments are made with Telegram Stars (XTR).\n"
        "- Premium unlocks unlimited strategy analyses and advanced risk tools for the selected duration.\n"
        "- This bot provides trading analysis, not financial advice.\n"
        "- Contact /paysupport for payment issues.",
        reply_markup=get_main_keyboard(Config.is_admin(message.from_user))
    )


@router.callback_query(F.data.startswith("pay_"))
async def process_payment_selection(callback: CallbackQuery):
    """Send a Telegram Stars invoice for the selected plan."""
    try:
        await callback.answer()
    except TelegramBadRequest:
        pass
    plan_key = callback.data.replace("pay_", "")
    plan = get_premium_plans().get(plan_key)

    if not plan:
        await callback.message.answer("Invalid plan selected.", reply_markup=get_main_keyboard(Config.is_admin(callback.from_user)))
        return

    payload = f"premium:{plan_key}:{plan['days']}:{plan['stars']}"
    prices = [LabeledPrice(label=f"Premium - {plan['label']}", amount=plan["stars"])]

    await callback.message.bot.send_invoice(
        chat_id=callback.message.chat.id,
        title=f"Trading Bot Pro Premium - {plan['label']}",
        description=f"Premium access for {plan['days']} days.",
        payload=payload,
        provider_token="",
        currency="XTR",
        prices=prices,
    )


@router.pre_checkout_query()
async def process_pre_checkout_query(pre_checkout_query: PreCheckoutQuery):
    """Approve Telegram Stars checkout."""
    payload = pre_checkout_query.invoice_payload or ""
    if not payload.startswith("premium:"):
        await pre_checkout_query.answer(ok=False, error_message="Invalid payment payload.")
        return

    await pre_checkout_query.answer(ok=True)


@router.message(F.successful_payment)
async def process_successful_payment(message: Message):
    """Handle successful Telegram Stars payment."""
    user_id = message.from_user.id
    payment = message.successful_payment
    payload_parts = (payment.invoice_payload or "").split(":")

    try:
        plan_key = payload_parts[1]
        duration_days = int(payload_parts[2])
        plan = get_premium_plans()[plan_key]
    except (IndexError, ValueError, KeyError):
        plan_key = "1month"
        duration_days = get_premium_plans()[plan_key]["days"]
        plan = get_premium_plans()[plan_key]

    await UserManager.get_or_create_user(
        user_id=user_id,
        username=message.from_user.username or "",
        first_name=message.from_user.first_name or "",
        last_name=message.from_user.last_name or "",
    )

    new_expiry = await UserManager.upgrade_to_premium(user_id, days=duration_days)

    if supabase_service.is_connected():
        await supabase_service.log_payment(
            user_id=user_id,
            amount_stars=payment.total_amount,
            plan_duration=duration_days,
            payment_id=payment.telegram_payment_charge_id,
            transaction_id=payment.provider_payment_charge_id,
        )

    confirmation_text = (
        "Payment Successful\n\n"
        f"Plan: {plan['label']}\n"
        f"Amount: {payment.total_amount} Stars\n"
        f"Status: Active\n"
        f"Valid until: {format_expiry(new_expiry)}\n\n"
        "Premium is now unlocked:\n"
        "- Unlimited analyses\n"
        "- Advanced risk calculations\n"
        "- Priority support\n"
        "- Portfolio analytics\n\n"
        "Use /analyze to start."
    )

    await message.answer(confirmation_text, reply_markup=get_main_keyboard(Config.is_admin(message.from_user)))
    logger.info("Premium payment processed for user %s: %s Stars", user_id, payment.total_amount)
