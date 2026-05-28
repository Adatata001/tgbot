"""
Supabase Database Integration Service
======================================

Handles all database operations for user management, trade logging,
and analytics data persistence.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, List, Any
from supabase import create_client, Client
import logging
from config import Config

logger = logging.getLogger(__name__)


class SupabaseService:
    """Service for managing Supabase database operations"""
    
    def __init__(self):
        """Initialize Supabase client"""
        self.url = Config.SUPABASE_URL
        self.key = Config.SUPABASE_SERVICE_ROLE_KEY or Config.SUPABASE_KEY
        self.using_service_role = bool(Config.SUPABASE_SERVICE_ROLE_KEY)
        self.writes_blocked = False
        
        if not self.url or not self.key:
            logger.warning("Supabase credentials not configured")
            self.client = None
            return
        
        try:
            self.client: Client = create_client(self.url, self.key)
            key_type = "service-role" if self.using_service_role else "anon/public"
            logger.info("Supabase connected successfully using %s key", key_type)
        except Exception as e:
            logger.error(f"Failed to connect to Supabase: {e}")
            self.client = None
    
    def is_connected(self) -> bool:
        """Check if Supabase is connected"""
        return self.client is not None

    def can_write(self) -> bool:
        """Check if write operations should be attempted."""
        return bool(self.client and not self.writes_blocked)

    def _handle_write_error(self, operation: str, error: Exception) -> None:
        """Log write failures and stop noisy retry loops when RLS blocks writes."""
        message = str(error)
        if "42501" in message or "row-level security" in message.lower() or "Unauthorized" in message:
            self.writes_blocked = True
            logger.error(
                "%s blocked by Supabase RLS. Add SUPABASE_SERVICE_ROLE_KEY to .env or create write policies.",
                operation,
            )
            return

        logger.error("%s failed: %s", operation, error)

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    @classmethod
    def _now_iso(cls) -> str:
        return cls._now().isoformat()

    @classmethod
    def _today_key(cls) -> str:
        return cls._now().date().isoformat()
    
    # ============ USER MANAGEMENT ============
    
    async def get_or_create_user(self, user_id: int, username: str, first_name: str = "", last_name: str = "") -> Dict[str, Any]:
        """Get or create user in database"""
        if not self.client:
            return {"user_id": user_id, "username": username}
        
        try:
            # Check if user exists
            response = self.client.table("users").select("*").eq("user_id", user_id).execute()
            
            if response.data:
                logger.info(f"User {user_id} found in database")
                return response.data[0]

            if not self.can_write():
                return None
            
            # Create new user
            new_user = {
                "user_id": user_id,
                "username": username,
                "first_name": first_name,
                "last_name": last_name,
                "is_premium": False,
                "profile": {"analysis_count_date": self._today_key()},
                "created_at": self._now_iso(),
                "updated_at": self._now_iso()
            }
            
            response = self.client.table("users").insert([new_user]).execute()
            logger.info(f"Created new user {user_id}")
            return response.data[0]
        
        except Exception as e:
            self._handle_write_error(f"Creating user {user_id}", e)
            return None
    
    async def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user from database"""
        if not self.client:
            return None
        
        try:
            response = self.client.table("users").select("*").eq("user_id", user_id).single().execute()
            return response.data
        except Exception as e:
            logger.error(f"Error getting user {user_id}: {e}")
            return None

    async def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user by Telegram username."""
        if not self.can_write():
            return None

        try:
            normalized = username.lstrip("@")
            response = self.client.table("users").select("*").ilike("username", normalized).limit(1).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error getting user by username {username}: {e}")
            return None

    async def list_users(self, limit: int = 1000) -> List[Dict[str, Any]]:
        """List users for admin/broadcast tasks."""
        if not self.client:
            return []

        try:
            response = self.client.table("users").select("*").order("created_at", desc=True).limit(limit).execute()
            return response.data or []
        except Exception as e:
            logger.error(f"Error listing users: {e}")
            return []

    async def get_admin_stats(self) -> Dict[str, Any]:
        """Return high-level bot stats for admins."""
        if not self.client:
            return {}

        try:
            users = await self.list_users(limit=10000)
            payments = self.client.table("payments").select("*").execute().data or []
            analyses = self.client.table("analyses").select("*").execute().data or []
            trades = self.client.table("trades").select("*").execute().data or []
            today = self._today_key()

            return {
                "users": len(users),
                "premium_users": len([u for u in users if u.get("is_premium")]),
                "analyses": len(analyses),
                "analyses_today": len([a for a in analyses if str(a.get("created_at", "")).startswith(today)]),
                "payments": len(payments),
                "stars": sum([p.get("amount_stars") or 0 for p in payments]),
                "trades": len(trades),
                "users_today": len([u for u in users if str(u.get("created_at", "")).startswith(today)]),
            }
        except Exception as e:
            logger.error(f"Error getting admin stats: {e}")
            return {}
    
    async def update_user(self, user_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update user in database"""
        if not self.can_write():
            return None
        
        try:
            data["updated_at"] = self._now_iso()
            response = self.client.table("users").update(data).eq("user_id", user_id).execute()
            logger.info(f"Updated user {user_id}")
            return response.data[0] if response.data else None
        except Exception as e:
            self._handle_write_error(f"Updating user {user_id}", e)
            return None
    
    async def upgrade_to_premium(self, user_id: int, months: int = 1) -> Optional[Dict[str, Any]]:
        """Upgrade user to premium"""
        if not self.can_write():
            return None
        
        try:
            premium_until = (self._now() + timedelta(days=30 * months)).isoformat()
            
            data = {
                "is_premium": True,
                "premium_until": premium_until,
                "updated_at": self._now_iso()
            }
            
            response = self.client.table("users").update(data).eq("user_id", user_id).execute()
            logger.info(f"Upgraded user {user_id} to premium until {premium_until}")
            return response.data[0] if response.data else None
        except Exception as e:
            self._handle_write_error(f"Upgrading user {user_id}", e)
            return None
    
    async def increment_analysis_count(self, user_id: int, profile: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Increment daily analysis count"""
        if not self.can_write():
            return None
        
        try:
            # Get current count
            user = await self.get_user(user_id)
            if not user:
                return None
            
            profile = profile or user.get("profile") or {}
            if not isinstance(profile, dict):
                profile = {}

            if profile.get("analysis_count_date") != self._today_key():
                current_count = 0
            else:
                current_count = user.get("analysis_count_today") or 0

            profile["analysis_count_date"] = self._today_key()
            count = current_count + 1
            total = (user.get("total_analyses") or 0) + 1
            
            data = {
                "analysis_count_today": count,
                "total_analyses": total,
                "profile": profile,
                "updated_at": self._now_iso()
            }
            
            response = self.client.table("users").update(data).eq("user_id", user_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            self._handle_write_error(f"Incrementing analysis count for {user_id}", e)
            return None
    
    # ============ TRADE MANAGEMENT ============
    
    async def log_trade(self, user_id: int, symbol: str, entry_price: float, exit_price: float,
                       position_size: float, pnl: float, pnl_percent: float, emotions: str = "",
                       notes: str = "", trade_type: str = "LONG",
                       entry_time: Optional[datetime] = None,
                       exit_time: Optional[datetime] = None) -> Optional[Dict[str, Any]]:
        """Log a trade in database"""
        if not self.can_write():
            return None
        
        try:
            trade = {
                "user_id": user_id,
                "symbol": symbol,
                "trade_type": trade_type,
                "entry_price": entry_price,
                "exit_price": exit_price,
                "position_size": position_size,
                "pnl": pnl,
                "pnl_percent": pnl_percent,
                "emotions": emotions,
                "notes": notes,
                "entry_time": (entry_time or self._now()).isoformat(),
                "exit_time": (exit_time or self._now()).isoformat(),
                "status": "closed",
                "created_at": self._now_iso()
            }
            
            response = self.client.table("trades").insert([trade]).execute()
            logger.info(f"Logged trade for user {user_id}: {symbol}")
            
            # Update user total PnL
            user = await self.get_user(user_id)
            if user:
                current_pnl = user.get("total_pnl") or 0
                await self.update_user(user_id, {"total_pnl": current_pnl + pnl})
            
            return response.data[0] if response.data else None
        except Exception as e:
            self._handle_write_error(f"Logging trade for {user_id}", e)
            return None
    
    async def get_user_trades(self, user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """Get user's trades from database"""
        if not self.client:
            return []
        
        try:
            response = self.client.table("trades").select("*").eq(
                "user_id", user_id
            ).order("created_at", desc=True).limit(limit).execute()
            
            return response.data or []
        except Exception as e:
            logger.error(f"Error getting trades for {user_id}: {e}")
            return []
    
    async def get_user_stats(self, user_id: int) -> Dict[str, Any]:
        """Get user's trading statistics"""
        if not self.client:
            return {
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "total_pnl": 0,
                "win_rate": 0,
                "avg_win": 0,
                "avg_loss": 0
            }
        
        try:
            trades = await self.get_user_trades(user_id, limit=1000)
            
            if not trades:
                return {
                    "total_trades": 0,
                    "winning_trades": 0,
                    "losing_trades": 0,
                    "total_pnl": 0,
                    "win_rate": 0,
                    "avg_win": 0,
                    "avg_loss": 0
                }
            
            closed_trades = [t for t in trades if t.get("status") == "closed"]
            
            total_pnl = sum([float(t["pnl"]) for t in closed_trades if t.get("pnl") is not None])
            winning = [t for t in closed_trades if t.get("pnl") is not None and float(t["pnl"]) > 0]
            losing = [t for t in closed_trades if t.get("pnl") is not None and float(t["pnl"]) < 0]
            
            avg_win = sum([float(t["pnl"]) for t in winning]) / len(winning) if winning else 0
            avg_loss = sum([abs(float(t["pnl"])) for t in losing]) / len(losing) if losing else 0
            total_wins = sum([float(t["pnl"]) for t in winning])
            total_losses = sum([abs(float(t["pnl"])) for t in losing])
            profit_factor = (total_wins / total_losses) if total_losses else 0
            
            return {
                "total_trades": len(closed_trades),
                "winning_trades": len(winning),
                "losing_trades": len(losing),
                "total_pnl": round(total_pnl, 2),
                "win_rate": round((len(winning) / len(closed_trades) * 100) if closed_trades else 0, 2),
                "avg_win": round(avg_win, 2),
                "avg_loss": round(avg_loss, 2),
                "profit_factor": round(profit_factor, 2),
                "best_trade": max([float(t["pnl"]) for t in closed_trades], default=0),
                "worst_trade": min([float(t["pnl"]) for t in closed_trades], default=0),
            }
        except Exception as e:
            logger.error(f"Error getting stats for {user_id}: {e}")
            return {}
    
    # ============ PAYMENT MANAGEMENT ============
    
    async def log_payment(self, user_id: int, amount_stars: int, plan_duration: int,
                         payment_id: str = "", transaction_id: str = "") -> Optional[Dict[str, Any]]:
        """Log a payment transaction"""
        if not self.can_write():
            return None
        
        try:
            expires_at = (self._now() + timedelta(days=plan_duration)).isoformat()
            
            payment = {
                "user_id": user_id,
                "amount_stars": amount_stars,
                "plan_duration": plan_duration,
                "payment_id": payment_id,
                "transaction_id": transaction_id,
                "status": "completed",
                "method": "telegram_stars",
                "created_at": self._now_iso(),
                "expires_at": expires_at
            }
            
            response = self.client.table("payments").insert([payment]).execute()
            logger.info(f"Logged payment for user {user_id}: {amount_stars} stars")
            return response.data[0] if response.data else None
        except Exception as e:
            self._handle_write_error(f"Logging payment for {user_id}", e)
            return None
    
    async def get_user_payments(self, user_id: int) -> List[Dict[str, Any]]:
        """Get user's payment history"""
        if not self.client:
            return []
        
        try:
            response = self.client.table("payments").select("*").eq(
                "user_id", user_id
            ).order("created_at", desc=True).execute()
            
            return response.data or []
        except Exception as e:
            logger.error(f"Error getting payments for {user_id}: {e}")
            return []
    
    # ============ ANALYSIS MANAGEMENT ============
    
    async def save_analysis(self, user_id: int, strategy: str, analysis: str,
                           market_context: str = "", tokens_used: int = 0) -> Optional[Dict[str, Any]]:
        """Save strategy analysis to database"""
        if not self.can_write():
            return None
        
        try:
            analysis_data = {
                "user_id": user_id,
                "strategy_description": strategy,
                "analysis_result": analysis,
                "market_conditions": market_context,
                "tokens_used": tokens_used,
                "created_at": self._now_iso()
            }
            
            response = self.client.table("analyses").insert([analysis_data]).execute()
            logger.info(f"Saved analysis for user {user_id}")
            return response.data[0] if response.data else None
        except Exception as e:
            self._handle_write_error(f"Saving analysis for {user_id}", e)
            return None
    
    async def get_user_analyses(self, user_id: int, limit: int = 20) -> List[Dict[str, Any]]:
        """Get user's past analyses"""
        if not self.client:
            return []
        
        try:
            response = self.client.table("analyses").select("*").eq(
                "user_id", user_id
            ).order("created_at", desc=True).limit(limit).execute()
            
            return response.data or []
        except Exception as e:
            logger.error(f"Error getting analyses for {user_id}: {e}")
            return []
    
    # ============ TRADINGVIEW SIGNALS ============
    
    async def save_tradingview_signal(self, user_id: int, symbol: str, action: str,
                                      price: float, timeframe: str = "", confidence: float = 0,
                                      analysis: str = "") -> Optional[Dict[str, Any]]:
        """Save TradingView signal to database"""
        if not self.can_write():
            return None
        
        try:
            signal = {
                "user_id": user_id,
                "symbol": symbol,
                "action": action,
                "price": price,
                "timeframe": timeframe,
                "confidence": confidence,
                "analysis": analysis,
                "acknowledged": False,
                "created_at": self._now_iso()
            }
            
            response = self.client.table("tradingview_signals").insert([signal]).execute()
            logger.info(f"Saved TradingView signal for {symbol}")
            return response.data[0] if response.data else None
        except Exception as e:
            self._handle_write_error("Saving TradingView signal", e)
            return None
    
    async def get_unacknowledged_signals(self, user_id: int) -> List[Dict[str, Any]]:
        """Get user's unacknowledged signals"""
        if not self.client:
            return []
        
        try:
            response = self.client.table("tradingview_signals").select("*").eq(
                "user_id", user_id
            ).eq("acknowledged", False).order("created_at", desc=True).execute()
            
            return response.data or []
        except Exception as e:
            logger.error(f"Error getting signals for {user_id}: {e}")
            return []
    
    # ============ MARKET DATA CACHE ============
    
    async def cache_market_data(self, symbol: str, price: float, market_cap: float = 0,
                               volume_24h: float = 0, change_24h: float = 0) -> Optional[Dict[str, Any]]:
        """Cache market data in database"""
        if not self.can_write():
            return None
        
        try:
            market_data = {
                "symbol": symbol,
                "price": price,
                "market_cap": market_cap,
                "volume_24h": volume_24h,
                "change_24h": change_24h,
                "updated_at": self._now_iso()
            }
            
            # Try to update existing record first
            response = self.client.table("market_data").upsert([market_data]).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            self._handle_write_error(f"Caching market data for {symbol}", e)
            return None

    async def save_file_upload(self, user_id: int, file_id: str, file_name: str = "",
                               file_type: str = "", file_size: int = 0,
                               upload_type: str = "", analysis_result: str = "") -> Optional[Dict[str, Any]]:
        """Save uploaded file metadata and analysis."""
        if not self.can_write():
            return None

        try:
            upload = {
                "user_id": user_id,
                "file_id": file_id,
                "file_name": file_name,
                "file_type": file_type,
                "file_size": file_size,
                "upload_type": upload_type,
                "analysis_result": analysis_result,
                "created_at": self._now_iso(),
            }
            response = self.client.table("file_uploads").insert([upload]).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            self._handle_write_error(f"Saving file upload for {user_id}", e)
            return None


# Global instance
supabase_service = SupabaseService()


async def init_supabase():
    """Initialize Supabase connection on bot startup"""
    if supabase_service.is_connected():
        if supabase_service.using_service_role:
            logger.info("Supabase service initialized with write-capable service-role key")
        else:
            logger.warning("Supabase initialized with anon/public key; writes may be blocked by RLS")
    else:
        logger.warning("Supabase not connected - using fallback (in-memory storage)")
