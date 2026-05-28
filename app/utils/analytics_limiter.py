"""
Analytics limiter for free tier users
"""
from config import Config
from app.utils.user_manager import UserManager


class AnalyticsLimiter:
    """Manage API rate limits for users."""

    @staticmethod
    def can_analyze(user_id: int, user_data: dict) -> bool:
        """Check if user can perform analysis."""
        if AnalyticsLimiter._is_premium_active(user_data):
            return True

        return AnalyticsLimiter._analysis_count_today(user_data) < Config.FREE_ANALYSES_PER_DAY

    @staticmethod
    def get_remaining_analyses(user_data: dict) -> int:
        """Get remaining analyses for the day."""
        if AnalyticsLimiter._is_premium_active(user_data):
            return float("inf")

        remaining = Config.FREE_ANALYSES_PER_DAY - AnalyticsLimiter._analysis_count_today(user_data)
        return max(0, remaining)

    @staticmethod
    def format_limit_message(user_data: dict) -> str:
        """Format a message about current limits."""
        if AnalyticsLimiter._is_premium_active(user_data):
            return "Premium active: unlimited analyses."

        remaining = AnalyticsLimiter.get_remaining_analyses(user_data)
        limit = Config.FREE_ANALYSES_PER_DAY

        if remaining == 0:
            return f"You have reached your daily limit ({limit} analyses). Upgrade to Premium for unlimited access."

        return f"{remaining}/{limit} analyses remaining today."

    @staticmethod
    def _analysis_count_today(user_data: dict) -> int:
        return user_data.get("analysis_count_today") or user_data.get("analyses_today") or 0

    @staticmethod
    def _is_premium_active(user_data: dict) -> bool:
        if not user_data.get("is_premium"):
            return False

        premium_until = UserManager.parse_datetime(user_data.get("premium_until"))
        return premium_until is None or premium_until > UserManager._now()
