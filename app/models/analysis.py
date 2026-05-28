"""
Analysis data model
"""
from datetime import datetime


class StrategyAnalysis:
    """Represents a strategy analysis"""
    
    def __init__(
        self,
        user_id: int,
        strategy_description: str,
        analysis_result: str,
        market_conditions: str = "",
        timestamp: datetime = None
    ):
        self.user_id = user_id
        self.strategy_description = strategy_description
        self.analysis_result = analysis_result
        self.market_conditions = market_conditions
        self.timestamp = timestamp or datetime.now()
