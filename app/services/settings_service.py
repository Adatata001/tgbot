"""
Runtime bot settings stored in a small local JSON file.
"""
import json
import copy
from pathlib import Path
from typing import Dict


class SettingsService:
    """Load and persist admin-editable settings."""

    DEFAULT_PLANS = {
        "1month": {"label": "1 Month", "stars": 400, "days": 30},
        "3months": {"label": "3 Months", "stars": 1080, "days": 90},
        "1year": {"label": "1 Year", "stars": 3600, "days": 365},
    }

    def __init__(self, path: str = "bot_settings.json"):
        self.path = Path(path)
        self._settings = self._load()

    def _load(self) -> dict:
        if not self.path.exists():
            return {"premium_plans": copy.deepcopy(self.DEFAULT_PLANS)}

        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            data = {}

        plans = copy.deepcopy(self.DEFAULT_PLANS)
        plans.update(data.get("premium_plans", {}))
        return {"premium_plans": plans}

    def save(self):
        self.path.write_text(json.dumps(self._settings, indent=2), encoding="utf-8")

    def get_premium_plans(self) -> Dict[str, dict]:
        return self._settings["premium_plans"]

    def set_plan_stars(self, plan_key: str, stars: int) -> dict | None:
        plans = self.get_premium_plans()
        if plan_key not in plans:
            return None

        plans[plan_key]["stars"] = stars
        self.save()
        return plans[plan_key]


settings_service = SettingsService()
