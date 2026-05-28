"""
Data models
"""
from datetime import datetime
from typing import Optional, List


class User:
    """User model"""
    
    def __init__(
        self,
        user_id: int,
        username: str,
        is_premium: bool = False,
        created_at: datetime = None
    ):
        self.user_id = user_id
        self.username = username
        self.is_premium = is_premium
        self.created_at = created_at or datetime.now()
        self.analyses_today = 0
        self.total_analyses = 0


class StrategyAnalysis:
    """Strategy analysis result model"""
    
    def __init__(
        self,
        user_id: int,
        strategy_text: str,
        analysis_result: dict,
        created_at: datetime = None
    ):
        self.user_id = user_id
        self.strategy_text = strategy_text
        self.analysis_result = analysis_result
        self.created_at = created_at or datetime.now()
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "user_id": self.user_id,
            "strategy": self.strategy_text,
            "analysis": self.analysis_result,
            "created_at": self.created_at.isoformat()
        }
