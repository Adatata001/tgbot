"""
User management utilities
"""
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional


class UserManager:
    """Manage user data and subscriptions - supports both in-memory and Supabase"""

    # In-memory storage (fallback)
    users: Dict = {}
    supabase_service = None  # Will be set on bot startup

    @classmethod
    def set_supabase_service(cls, service):
        """Set Supabase service instance"""
        cls.supabase_service = service

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    @classmethod
    def _today_key(cls) -> str:
        return cls._now().date().isoformat()

    @staticmethod
    def _profile(user: dict) -> dict:
        profile = user.get("profile") or {}
        return profile if isinstance(profile, dict) else {}

    @classmethod
    def parse_datetime(cls, value) -> Optional[datetime]:
        """Parse Supabase/in-memory datetime values into aware datetimes."""
        if not value:
            return None
        if isinstance(value, datetime):
            return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
        if isinstance(value, str):
            try:
                parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
                return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
            except ValueError:
                return None
        return None

    @classmethod
    def _normalize_user(cls, user: Optional[dict]) -> Optional[dict]:
        """Normalize DB and in-memory users to one shape."""
        if not user:
            return user

        user["profile"] = cls._profile(user)

        if "analysis_count_today" not in user and "analyses_today" in user:
            user["analysis_count_today"] = user["analyses_today"]
        if "analyses_today" not in user and "analysis_count_today" in user:
            user["analyses_today"] = user["analysis_count_today"]

        premium_until = cls.parse_datetime(user.get("premium_until"))
        if user.get("is_premium") and premium_until and premium_until <= cls._now():
            user["is_premium"] = False

        return user

    @classmethod
    def _needs_daily_reset(cls, user: dict) -> bool:
        profile = cls._profile(user)
        count_date = profile.get("analysis_count_date")
        return bool(count_date and count_date != cls._today_key())

    @classmethod
    async def _reset_daily_if_needed(cls, user: dict) -> dict:
        user = cls._normalize_user(user)
        if not user:
            return user

        profile = cls._profile(user)
        today = cls._today_key()
        if profile.get("analysis_count_date") == today:
            return user

        profile["analysis_count_date"] = today
        data = {
            "analysis_count_today": 0,
            "profile": profile,
        }

        user.update(data)
        user["analyses_today"] = 0

        user_id = user.get("user_id")
        if user_id and cls.supabase_service and cls.supabase_service.is_connected():
            try:
                await cls.supabase_service.update_user(user_id, data.copy())
            except Exception as e:
                print(f"Supabase reset error: {e}")
        elif user_id in cls.users:
            cls.users[user_id].update(user)

        return user

    @classmethod
    def _default_user(cls, user_id: int, username: str = "", first_name: str = "", last_name: str = "") -> dict:
        now = cls._now()
        return {
            "user_id": user_id,
            "username": username,
            "first_name": first_name,
            "last_name": last_name,
            "is_premium": False,
            "premium_until": None,
            "created_at": now,
            "last_activity": now,
            "analysis_count_today": 0,
            "analyses_today": 0,
            "total_analyses": 0,
            "total_pnl": 0,
            "profile": {
                "trading_style": "",
                "experience_level": "",
                "favorite_assets": [],
                "analysis_count_date": cls._today_key()
            }
        }

    @classmethod
    async def get_or_create_user(cls, user_id: int, username: str = "", first_name: str = "", last_name: str = "") -> dict:
        """Get or create a user (tries Supabase first, falls back to in-memory)."""
        if cls.supabase_service and cls.supabase_service.is_connected():
            try:
                user = await cls.supabase_service.get_or_create_user(
                    user_id, username, first_name, last_name
                )
                if user:
                    return await cls._reset_daily_if_needed(user)
            except Exception as e:
                print(f"Supabase error: {e}, falling back to in-memory")

        if user_id not in cls.users:
            cls.users[user_id] = cls._default_user(user_id, username, first_name, last_name)
        else:
            cls.users[user_id].update({
                "username": username or cls.users[user_id].get("username", ""),
                "first_name": first_name or cls.users[user_id].get("first_name", ""),
                "last_name": last_name or cls.users[user_id].get("last_name", ""),
                "last_activity": cls._now(),
            })

        return await cls._reset_daily_if_needed(cls.users[user_id])

    @classmethod
    async def get_user(cls, user_id: int) -> Optional[dict]:
        """Get user data (tries Supabase first, falls back to in-memory)."""
        if cls.supabase_service and cls.supabase_service.is_connected():
            try:
                user = await cls.supabase_service.get_user(user_id)
                if user:
                    return await cls._reset_daily_if_needed(user)
            except Exception as e:
                print(f"Supabase error: {e}, falling back to in-memory")

        user = cls._normalize_user(cls.users.get(user_id))
        return await cls._reset_daily_if_needed(user) if user else None

    @classmethod
    async def update_user(cls, user_id: int, data: dict) -> bool:
        """Update user data (tries Supabase first, falls back to in-memory)."""
        if cls.supabase_service and cls.supabase_service.is_connected():
            try:
                result = await cls.supabase_service.update_user(user_id, data.copy())
                if result:
                    cls._normalize_user(result)
                    return True
            except Exception as e:
                print(f"Supabase error: {e}, falling back to in-memory")

        if user_id in cls.users:
            cls.users[user_id].update(data)
            cls._normalize_user(cls.users[user_id])
            return True

        return False

    @classmethod
    async def increment_analysis_count(cls, user_id: int) -> int:
        """Increment analysis count for today."""
        if cls.supabase_service and cls.supabase_service.is_connected():
            try:
                user = await cls.get_or_create_user(user_id)
                result = await cls.supabase_service.increment_analysis_count(user_id, cls._profile(user))
                if result:
                    return result.get("analysis_count_today") or result.get("analyses_today") or 0
            except Exception as e:
                print(f"Supabase error: {e}, falling back to in-memory")

        if user_id in cls.users:
            current_count = cls.users[user_id].get("analysis_count_today") or cls.users[user_id].get("analyses_today") or 0
            profile = cls._profile(cls.users[user_id])
            profile["analysis_count_date"] = cls._today_key()
            cls.users[user_id]["analysis_count_today"] = current_count + 1
            cls.users[user_id]["analyses_today"] = current_count + 1
            cls.users[user_id]["total_analyses"] = (cls.users[user_id].get("total_analyses") or 0) + 1
            cls.users[user_id]["profile"] = profile
            return cls.users[user_id]["analysis_count_today"]

        return 0

    @classmethod
    def reset_daily_analyses(cls, user_id: int) -> None:
        """Reset daily analysis count."""
        if user_id in cls.users:
            cls.users[user_id]["analysis_count_today"] = 0
            cls.users[user_id]["analyses_today"] = 0
            profile = cls._profile(cls.users[user_id])
            profile["analysis_count_date"] = cls._today_key()
            cls.users[user_id]["profile"] = profile

    @classmethod
    async def upgrade_to_premium(cls, user_id: int, days: int = 30) -> Optional[datetime]:
        """Upgrade or extend premium access and return the new expiry."""
        user = await cls.get_or_create_user(user_id)
        now = cls._now()
        current_expiry = cls.parse_datetime(user.get("premium_until"))
        base_date = current_expiry if user.get("is_premium") and current_expiry and current_expiry > now else now
        new_expiry = base_date + timedelta(days=days)

        data = {
            "is_premium": True,
            "premium_until": new_expiry.isoformat(),
        }

        if await cls.update_user(user_id, data):
            return new_expiry

        if user_id in cls.users:
            cls.users[user_id]["is_premium"] = True
            cls.users[user_id]["premium_until"] = new_expiry
            return new_expiry

        return None
