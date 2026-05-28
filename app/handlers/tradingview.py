"""
TradingView Webhook Integration for Phase 4
Receives trading signals from TradingView alerts
"""
from fastapi import FastAPI, HTTPException, Header
from fastapi.responses import JSONResponse
from datetime import datetime
from typing import Optional
from pydantic import BaseModel
import hmac
import hashlib
import json
from app.services import OpenAIService
from app.utils import UserManager
import asyncio

# Initialize FastAPI app for webhooks
webhook_app = FastAPI()


class TradingViewSignal(BaseModel):
    """TradingView webhook signal format"""
    symbol: str
    action: str  # BUY, SELL, CLOSE
    price: float
    time: str
    analysis: Optional[str] = ""
    timeframe: Optional[str] = "4h"
    confidence: Optional[float] = 1.0


class TradingViewWebhook:
    """Handle TradingView webhook integration"""
    
    def __init__(self, webhook_secret: str = ""):
        self.webhook_secret = webhook_secret
        self.signal_history = []
    
    async def verify_signature(self, signature: str, body: str) -> bool:
        """Verify TradingView webhook signature"""
        if not self.webhook_secret:
            return True  # Skip verification if no secret set
        
        expected_signature = hmac.new(
            self.webhook_secret.encode(),
            body.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)
    
    async def process_signal(self, signal: TradingViewSignal, bot) -> dict:
        """
        Process TradingView signal
        
        Args:
            signal: TradingView signal data
            bot: Telegram bot instance
            
        Returns:
            Processing result
        """
        try:
            ai_service = OpenAIService()
            
            # Create analysis prompt
            analysis_prompt = f"""
A TradingView alert has triggered:

SYMBOL: {signal.symbol}
ACTION: {signal.action}
PRICE: ${signal.price}
TIMEFRAME: {signal.timeframe}
CONFIDENCE: {signal.confidence * 100}%
TIME: {signal.time}

Additional Analysis:
{signal.analysis if signal.analysis else "No additional notes"}

Provide a brief, professional trading analysis with:
1. Signal validation (is this a good entry/exit?)
2. Key support/resistance levels
3. Risk management recommendation
4. Market context
5. Next steps

Keep response under 200 words, trader-focused tone."""
            
            # Get AI analysis
            response = await ai_service.client.chat.completions.create(
                model="gpt-3.5-turbo",  # Cheaper model for quick analysis
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional trading analyst. Provide quick, actionable analysis for trading signals."
                    },
                    {
                        "role": "user",
                        "content": analysis_prompt
                    }
                ],
                temperature=0.7,
                max_tokens=300
            )
            
            analysis = response.choices[0].message.content
            
            # Store signal for tracking
            self.signal_history.append({
                "symbol": signal.symbol,
                "action": signal.action,
                "price": signal.price,
                "analysis": analysis,
                "timestamp": datetime.now()
            })
            
            return {
                "status": "success",
                "signal": signal.symbol,
                "analysis": analysis,
                "timestamp": datetime.now().isoformat()
            }
        
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def send_alert_to_user(self, user_id: int, signal: TradingViewSignal, analysis: str, bot) -> bool:
        """Send trading alert to user via Telegram"""
        try:
            alert_message = f"""
📊 **TradingView Signal Received**

🎯 {signal.symbol}
{'🟢 BUY' if signal.action == 'BUY' else '🔴 SELL' if signal.action == 'SELL' else '⚪ CLOSE'} Signal

📈 Price: ${signal.price}
⏱️ Timeframe: {signal.timeframe}
💯 Confidence: {signal.confidence * 100}%

**AI Analysis:**
{analysis}

Time: {signal.time}
"""
            
            await bot.send_message(
                chat_id=user_id,
                text=alert_message
            )
            return True
        except Exception as e:
            print(f"Error sending alert to user {user_id}: {str(e)}")
            return False


# Global webhook handler
tradingview_webhook = TradingViewWebhook()


@webhook_app.post("/webhook/tradingview")
async def handle_tradingview_webhook(
    signal: TradingViewSignal,
    x_signature: Optional[str] = Header(None)
):
    """
    TradingView webhook endpoint
    
    Expected POST from TradingView:
    {
        "symbol": "BTCUSD",
        "action": "BUY",
        "price": 42000,
        "time": "2024-01-01T12:00:00Z",
        "timeframe": "4h",
        "confidence": 0.95
    }
    """
    try:
        # Verify signature if provided
        # if x_signature:
        #     is_valid = await tradingview_webhook.verify_signature(x_signature, body)
        #     if not is_valid:
        #         raise HTTPException(status_code=401, detail="Invalid signature")
        
        # Process the signal
        result = await tradingview_webhook.process_signal(signal, None)
        
        if result["status"] == "success":
            return JSONResponse(
                status_code=200,
                content={
                    "status": "success",
                    "message": "Signal processed",
                    "analysis": result["analysis"]
                }
            )
        else:
            raise HTTPException(status_code=500, detail=result.get("error"))
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@webhook_app.get("/webhook/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "signals_processed": len(tradingview_webhook.signal_history)
    }
