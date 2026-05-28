"""
Persistent trading journal analytics
"""
from datetime import datetime
from typing import Dict, List
import statistics
from app.services.supabase_service import supabase_service


def to_float(value, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def parse_datetime(value) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return datetime.now()
    return datetime.now()


class AdvancedAnalytics:
    """Advanced trading analytics and performance tracking."""

    def __init__(self):
        self.trade_journal = []

    async def log_trade(
        self,
        user_id: int,
        symbol: str,
        entry_price: float,
        exit_price: float,
        position_size: float,
        trade_type: str = "LONG",
        entry_time: datetime = None,
        exit_time: datetime = None,
        emotions: str = "",
        notes: str = ""
    ) -> dict:
        """Log a completed trade and persist it when Supabase is available."""
        entry_time = entry_time or datetime.now()
        exit_time = exit_time or datetime.now()
        trade_type = trade_type.upper()

        price_difference = exit_price - entry_price
        pnl = (-price_difference if trade_type == "SHORT" else price_difference) * position_size
        pnl_percent = ((-price_difference if trade_type == "SHORT" else price_difference) / entry_price) * 100

        trade_record = {
            "user_id": user_id,
            "symbol": symbol.upper(),
            "entry_price": entry_price,
            "exit_price": exit_price,
            "position_size": position_size,
            "trade_type": trade_type,
            "pnl": pnl,
            "pnl_percent": pnl_percent,
            "entry_time": entry_time,
            "exit_time": exit_time,
            "duration": exit_time - entry_time,
            "emotions": emotions,
            "notes": notes,
            "logged_at": datetime.now(),
            "status": "closed",
        }

        self.trade_journal.append(trade_record)

        if supabase_service.is_connected():
            await supabase_service.log_trade(
                user_id=user_id,
                symbol=symbol.upper(),
                entry_price=entry_price,
                exit_price=exit_price,
                position_size=position_size,
                pnl=pnl,
                pnl_percent=pnl_percent,
                emotions=emotions,
                notes=notes,
                trade_type=trade_type,
                entry_time=entry_time,
                exit_time=exit_time,
            )

        return {
            "status": "success",
            "pnl": pnl,
            "pnl_percent": pnl_percent,
            "trade_type": trade_type,
            "symbol": symbol.upper()
        }

    async def _get_trades(self, user_id: int, limit: int = 1000) -> List[Dict]:
        if supabase_service.is_connected():
            return await supabase_service.get_user_trades(user_id, limit=limit)
        return [t for t in self.trade_journal if t["user_id"] == user_id]

    async def get_performance_summary(self, user_id: int) -> dict:
        """Get performance summary for a user."""
        trades = await self._get_trades(user_id)
        closed = [t for t in trades if t.get("status", "closed") == "closed"]

        if not closed:
            return {
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "win_rate": 0,
                "avg_win": 0,
                "avg_loss": 0,
                "profit_factor": 0,
                "total_pnl": 0,
                "best_trade": 0,
                "worst_trade": 0,
            }

        pnl_values = [to_float(t.get("pnl")) for t in closed]
        winning = [p for p in pnl_values if p > 0]
        losing = [p for p in pnl_values if p < 0]
        total_wins = sum(winning)
        total_losses = abs(sum(losing))

        return {
            "total_trades": len(closed),
            "winning_trades": len(winning),
            "losing_trades": len(losing),
            "win_rate": round((len(winning) / len(closed)) * 100, 2),
            "avg_win": round(statistics.mean(winning), 2) if winning else 0,
            "avg_loss": round(abs(statistics.mean(losing)), 2) if losing else 0,
            "profit_factor": round(total_wins / total_losses, 2) if total_losses else 0,
            "total_pnl": round(sum(pnl_values), 2),
            "best_trade": round(max(pnl_values), 2),
            "worst_trade": round(min(pnl_values), 2),
        }

    async def analyze_trade_patterns(self, user_id: int) -> dict:
        """Analyze performance patterns."""
        trades = await self._get_trades(user_id)
        if not trades:
            return {"status": "no_data"}

        trades_by_hour = {}
        trades_by_symbol = {}
        for trade in trades:
            entry_time = parse_datetime(trade.get("entry_time") or trade.get("created_at"))
            hour = entry_time.hour
            trades_by_hour.setdefault(hour, []).append(to_float(trade.get("pnl")))

            symbol = trade.get("symbol", "UNKNOWN")
            trades_by_symbol.setdefault(symbol, []).append(trade)

        best_hours = sorted(
            trades_by_hour.items(),
            key=lambda item: statistics.mean(item[1]),
            reverse=True
        )[:3]
        worst_hours = sorted(
            trades_by_hour.items(),
            key=lambda item: statistics.mean(item[1])
        )[:3]

        symbol_performance = {}
        for symbol, symbol_trades in trades_by_symbol.items():
            pnl_values = [to_float(t.get("pnl")) for t in symbol_trades]
            wins = len([p for p in pnl_values if p > 0])
            total = len(symbol_trades)
            symbol_performance[symbol] = {
                "trades": total,
                "win_rate": round((wins / total * 100), 2) if total else 0,
                "total_pnl": round(sum(pnl_values), 2),
            }

        return {
            "status": "success",
            "best_trading_hours": best_hours,
            "worst_trading_hours": worst_hours,
            "symbol_performance": symbol_performance,
            "total_trades_analyzed": len(trades)
        }

    async def get_emotion_analysis(self, user_id: int) -> dict:
        """Analyze performance by emotional state."""
        trades = [t for t in await self._get_trades(user_id) if t.get("emotions")]
        if not trades:
            return {"status": "no_emotion_data"}

        grouped = {}
        for trade in trades:
            emotion = str(trade.get("emotions", "")).strip().lower()
            if not emotion:
                continue
            grouped.setdefault(emotion, []).append(to_float(trade.get("pnl")))

        results = {}
        for emotion, pnl_values in grouped.items():
            results[emotion] = {
                "average_pnl": round(statistics.mean(pnl_values), 2),
                "trade_count": len(pnl_values),
                "win_rate": round((len([p for p in pnl_values if p > 0]) / len(pnl_values)) * 100, 2),
            }

        return {
            "status": "success",
            "emotion_analysis": results
        }


advanced_analytics = AdvancedAnalytics()
