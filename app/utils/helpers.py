"""
Development utilities and helpers
"""


def format_analysis_response(analysis: str) -> str:
    """Format analysis response for better readability"""
    # Split by numbered sections
    lines = analysis.split('\n')
    formatted = []
    
    for line in lines:
        if line.strip():
            formatted.append(line)
    
    return '\n'.join(formatted)


def calculate_risk_reward_ratio(entry: float, stop_loss: float, take_profit: float) -> dict:
    """Calculate risk/reward ratio"""
    risk = abs(entry - stop_loss)
    reward = abs(take_profit - entry)
    
    if risk == 0:
        return {"error": "Stop loss equals entry"}
    
    ratio = reward / risk
    
    return {
        "risk": risk,
        "reward": reward,
        "ratio": ratio,
        "assessment": "Good" if ratio >= 1.5 else "Fair" if ratio >= 1.0 else "Poor"
    }


def validate_strategy_input(strategy_text: str) -> tuple:
    """Validate strategy input"""
    if not strategy_text or len(strategy_text) < 10:
        return False, "Strategy description too short. Please provide at least 10 characters."
    
    if len(strategy_text) > 5000:
        return False, "Strategy description too long. Maximum 5000 characters."
    
    return True, "Valid"


def format_price(price: float, decimal_places: int = 2) -> str:
    """Format price for display"""
    if price >= 1:
        return f"${price:,.{decimal_places}f}"
    else:
        return f"${price:.8f}".rstrip('0')
