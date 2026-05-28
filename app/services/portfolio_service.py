"""
Portfolio Tracking Service for Phase 4
"""
from datetime import datetime
from typing import List, Dict, Optional


class Portfolio:
    """User portfolio tracker"""
    
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.positions = {}  # {symbol: {"quantity": 100, "entry_price": 42000, "entry_time": datetime}}
        self.closed_positions = []
        self.portfolio_value_history = []
    
    def open_position(
        self,
        symbol: str,
        quantity: float,
        entry_price: float,
        position_type: str = "LONG"
    ) -> dict:
        """Open a new position"""
        if symbol in self.positions:
            # Add to existing position
            existing = self.positions[symbol]
            total_quantity = existing["quantity"] + quantity
            avg_price = (
                (existing["quantity"] * existing["entry_price"] + quantity * entry_price) /
                total_quantity
            )
            self.positions[symbol] = {
                "quantity": total_quantity,
                "entry_price": avg_price,
                "entry_time": datetime.now(),
                "type": position_type
            }
        else:
            self.positions[symbol] = {
                "quantity": quantity,
                "entry_price": entry_price,
                "entry_time": datetime.now(),
                "type": position_type
            }
        
        return {
            "status": "success",
            "symbol": symbol,
            "quantity": self.positions[symbol]["quantity"],
            "entry_price": self.positions[symbol]["entry_price"]
        }
    
    def close_position(self, symbol: str, quantity: Optional[float] = None, exit_price: float = None) -> dict:
        """Close a position (full or partial)"""
        if symbol not in self.positions:
            return {"status": "error", "message": "No position found"}
        
        position = self.positions[symbol]
        close_quantity = quantity or position["quantity"]
        
        if close_quantity > position["quantity"]:
            return {"status": "error", "message": "Cannot close more than position size"}
        
        # Calculate PnL
        entry_cost = position["entry_price"] * close_quantity
        exit_value = exit_price * close_quantity if exit_price else 0
        pnl = exit_value - entry_cost
        pnl_percent = (pnl / entry_cost * 100) if entry_cost > 0 else 0
        
        # Record closed position
        closed = {
            "symbol": symbol,
            "quantity": close_quantity,
            "entry_price": position["entry_price"],
            "exit_price": exit_price,
            "entry_time": position["entry_time"],
            "close_time": datetime.now(),
            "pnl": pnl,
            "pnl_percent": pnl_percent,
            "type": position["type"]
        }
        self.closed_positions.append(closed)
        
        # Update position
        if close_quantity == position["quantity"]:
            del self.positions[symbol]
        else:
            position["quantity"] -= close_quantity
        
        return {
            "status": "success",
            "symbol": symbol,
            "closed_quantity": close_quantity,
            "pnl": pnl,
            "pnl_percent": pnl_percent
        }
    
    def get_portfolio_value(self, current_prices: Dict[str, float]) -> dict:
        """Calculate current portfolio value"""
        total_value = 0
        total_entry_value = 0
        positions_detail = {}
        
        for symbol, position in self.positions.items():
            current_price = current_prices.get(symbol, position["entry_price"])
            quantity = position["quantity"]
            
            entry_value = position["entry_price"] * quantity
            current_value = current_price * quantity
            pnl = current_value - entry_value
            pnl_percent = (pnl / entry_value * 100) if entry_value > 0 else 0
            
            positions_detail[symbol] = {
                "quantity": quantity,
                "entry_price": position["entry_price"],
                "current_price": current_price,
                "entry_value": entry_value,
                "current_value": current_value,
                "pnl": pnl,
                "pnl_percent": pnl_percent,
                "type": position["type"]
            }
            
            total_value += current_value
            total_entry_value += entry_value
        
        total_pnl = total_value - total_entry_value
        total_pnl_percent = (total_pnl / total_entry_value * 100) if total_entry_value > 0 else 0
        
        portfolio_snapshot = {
            "timestamp": datetime.now(),
            "total_value": total_value,
            "total_entry_value": total_entry_value,
            "total_pnl": total_pnl,
            "total_pnl_percent": total_pnl_percent,
            "positions": len(self.positions),
            "positions_detail": positions_detail
        }
        
        self.portfolio_value_history.append(portfolio_snapshot)
        
        return portfolio_snapshot
    
    def get_risk_exposure(self) -> dict:
        """Analyze portfolio risk exposure"""
        total_exposure = sum([
            p["quantity"] * p["entry_price"] for p in self.positions.values()
        ])
        
        exposure_by_symbol = {}
        for symbol, position in self.positions.items():
            exposure = position["quantity"] * position["entry_price"]
            exposure_percent = (exposure / total_exposure * 100) if total_exposure > 0 else 0
            exposure_by_symbol[symbol] = {
                "exposure": exposure,
                "exposure_percent": exposure_percent,
                "quantity": position["quantity"],
                "type": position["type"]
            }
        
        # Calculate diversification
        long_positions = len([p for p in self.positions.values() if p["type"] == "LONG"])
        short_positions = len([p for p in self.positions.values() if p["type"] == "SHORT"])
        
        return {
            "total_exposure": total_exposure,
            "exposure_by_symbol": exposure_by_symbol,
            "long_positions": long_positions,
            "short_positions": short_positions,
            "diversification_score": min(100, len(self.positions) * 10)  # Simple diversification metric
        }


class PortfolioManager:
    """Manage multiple user portfolios"""
    
    def __init__(self):
        self.portfolios = {}  # {user_id: Portfolio}
    
    def get_or_create_portfolio(self, user_id: int) -> Portfolio:
        """Get or create portfolio for user"""
        if user_id not in self.portfolios:
            self.portfolios[user_id] = Portfolio(user_id)
        return self.portfolios[user_id]
    
    def get_portfolio_summary(self, user_id: int, current_prices: Dict[str, float]) -> dict:
        """Get portfolio summary for user"""
        portfolio = self.get_or_create_portfolio(user_id)
        value = portfolio.get_portfolio_value(current_prices)
        risk = portfolio.get_risk_exposure()
        
        return {
            "portfolio_value": value,
            "risk_exposure": risk,
            "open_positions": len(portfolio.positions),
            "closed_positions": len(portfolio.closed_positions)
        }


# Global portfolio manager
portfolio_manager = PortfolioManager()
