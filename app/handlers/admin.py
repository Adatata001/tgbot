"""
Admin command handlers
"""
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from config import Config
from app.services.supabase_service import supabase_service
from app.services.announcement_service import market_announcement_service
from app.services.settings_service import settings_service
from app.utils import UserManager
from app.keyboards import get_main_keyboard

router = Router()


def admin_only(func):
    async def wrapper(message: Message, *args, **kwargs):
        if not Config.is_admin(message.from_user):
            await message.answer("Admin access required.")
            return
        return await func(message)

    return wrapper


def text_has(label: str):
    from aiogram import F
    return F.text.func(lambda text: isinstance(text, str) and label.lower() == text.strip().lower())


async def resolve_user(identifier: str) -> dict | None:
    """Resolve a user by numeric Telegram ID or @username."""
    identifier = identifier.strip()
    if identifier.lstrip("@").isdigit():
        return await UserManager.get_user(int(identifier.lstrip("@")))

    username = identifier.lstrip("@")
    if supabase_service.is_connected():
        return await supabase_service.get_user_by_username(username)

    for user in UserManager.users.values():
        if (user.get("username") or "").lower() == username.lower():
            return user

    return None


def format_user(user: dict) -> str:
    premium_until = UserManager.parse_datetime(user.get("premium_until"))
    premium_text = premium_until.strftime("%Y-%m-%d") if premium_until else "no expiry"
    return (
        f"User ID: {user.get('user_id')}\n"
        f"Username: @{user.get('username') or 'none'}\n"
        f"Name: {(user.get('first_name') or '').strip()} {(user.get('last_name') or '').strip()}\n"
        f"Premium: {'yes' if user.get('is_premium') else 'no'} ({premium_text})\n"
        f"Analyses today: {user.get('analysis_count_today') or 0}\n"
        f"Total analyses: {user.get('total_analyses') or 0}\n"
        f"Total PnL: {user.get('total_pnl') or 0}"
    )


@router.message(text_has("Admin"))
@router.message(Command("admin", "adminpanel"))
@admin_only
async def admin_menu(message: Message):
    await message.answer(
        "Admin Panel\n\n"
        "Stats:\n"
        "/adminstats\n\n"
        "Users:\n"
        "/user <id|@username>\n"
        "/grantpremium <id|@username> <days>\n"
        "/revokepremium <id|@username>\n\n"
        "Premium pricing:\n"
        "/plans\n"
        "/setstars <1month|3months|1year> <stars>\n\n"
        "Broadcasts:\n"
        "/broadcast <message>\n"
        "/announce_now",
        reply_markup=get_main_keyboard(is_admin=True)
    )


@router.message(Command("adminstats"))
@admin_only
async def admin_stats(message: Message):
    if supabase_service.is_connected():
        stats = await supabase_service.get_admin_stats()
    else:
        users = list(UserManager.users.values())
        stats = {
            "users": len(users),
            "premium_users": len([u for u in users if u.get("is_premium")]),
            "analyses": sum([u.get("total_analyses") or 0 for u in users]),
            "payments": 0,
            "stars": 0,
            "trades": 0,
        }

    await message.answer(
        "Bot Stats\n\n"
        f"Users: {stats.get('users', 0)}\n"
        f"Premium users: {stats.get('premium_users', 0)}\n"
        f"Free users: {max(0, stats.get('users', 0) - stats.get('premium_users', 0))}\n"
        f"Analyses saved: {stats.get('analyses', 0)}\n"
        f"Analyses today: {stats.get('analyses_today', 0)}\n"
        f"Payments: {stats.get('payments', 0)}\n"
        f"Stars collected: {stats.get('stars', 0)}\n"
        f"Trades logged: {stats.get('trades', 0)}\n"
        f"Users registered today: {stats.get('users_today', 0)}"
    )


@router.message(Command("user"))
@admin_only
async def admin_user_lookup(message: Message):
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Usage: /user <telegram_id|@username>")
        return

    user = await resolve_user(parts[1])
    if not user:
        await message.answer("User not found.")
        return

    await message.answer(format_user(user))


@router.message(Command("grantpremium"))
@admin_only
async def grant_premium(message: Message):
    parts = (message.text or "").split(maxsplit=2)
    if len(parts) < 3:
        await message.answer("Usage: /grantpremium <telegram_id|@username> <days>")
        return

    user = await resolve_user(parts[1])
    if not user:
        await message.answer("User not found.")
        return

    try:
        days = int(parts[2])
    except ValueError:
        await message.answer("Days must be a number.")
        return

    expiry = await UserManager.upgrade_to_premium(int(user["user_id"]), days=days)
    await message.answer(
        f"Premium granted to {user.get('username') or user.get('user_id')} until "
        f"{expiry.strftime('%Y-%m-%d') if expiry else 'unknown'}."
    )


@router.message(Command("revokepremium"))
@admin_only
async def revoke_premium(message: Message):
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Usage: /revokepremium <telegram_id|@username>")
        return

    user = await resolve_user(parts[1])
    if not user:
        await message.answer("User not found.")
        return

    ok = await UserManager.update_user(
        int(user["user_id"]),
        {
            "is_premium": False,
            "premium_until": None,
        }
    )

    await message.answer("Premium revoked." if ok else "Could not revoke premium.")


@router.message(Command("broadcast"))
@admin_only
async def broadcast(message: Message):
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Usage: /broadcast <message>")
        return

    users = await supabase_service.list_users(limit=10000) if supabase_service.is_connected() else list(UserManager.users.values())
    sent = 0
    failed = 0

    progress = await message.answer(f"Broadcasting to {len(users)} users...")
    for user in users:
        chat_id = user.get("user_id")
        if not chat_id:
            continue
        try:
            await message.bot.send_message(chat_id=int(chat_id), text=parts[1])
            sent += 1
        except Exception:
            failed += 1

    await progress.edit_text(f"Broadcast complete.\nSent: {sent}\nFailed: {failed}")


@router.message(Command("plans"))
@admin_only
async def show_plans(message: Message):
    plans = settings_service.get_premium_plans()
    text = "Premium Stars Pricing\n\n"
    for key, plan in plans.items():
        text += f"{key}: {plan['label']} - {plan['stars']} Stars ({plan['days']} days)\n"
    text += "\nEdit with: /setstars <plan> <stars>\nExample: /setstars 1month 400"
    await message.answer(text)


@router.message(Command("setstars"))
@admin_only
async def set_stars(message: Message):
    parts = (message.text or "").split(maxsplit=2)
    if len(parts) < 3:
        await message.answer("Usage: /setstars <1month|3months|1year> <stars>")
        return

    plan_key = parts[1].strip()
    try:
        stars = int(parts[2])
    except ValueError:
        await message.answer("Stars must be a number.")
        return

    if stars < 1:
        await message.answer("Stars must be at least 1.")
        return

    plan = settings_service.set_plan_stars(plan_key, stars)
    if not plan:
        await message.answer("Unknown plan. Use /plans to see valid plans.")
        return

    await message.answer(f"{plan['label']} is now {plan['stars']} Stars.")


@router.message(Command("announce_now"))
@admin_only
async def announce_now(message: Message):
    progress = await message.answer("Sending market announcement now...")
    sent, failed = await market_announcement_service.send_now(message.bot)
    await progress.edit_text(f"Market announcement complete.\nSent: {sent}\nFailed: {failed}")
