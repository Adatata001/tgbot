"""
AI service for analysis via OpenRouter-compatible APIs
"""
from openai import AsyncOpenAI
from config import Config


class OpenRouterService:
    """Service for interacting with OpenRouter-compatible chat APIs."""
    
    def __init__(self):
        if Config.OPENROUTER_API_KEY:
            headers = {}
            if Config.OPENROUTER_SITE_URL:
                headers["HTTP-Referer"] = Config.OPENROUTER_SITE_URL
            if Config.OPENROUTER_APP_NAME:
                headers["X-Title"] = Config.OPENROUTER_APP_NAME

            self.client = AsyncOpenAI(
                api_key=Config.OPENROUTER_API_KEY,
                base_url=Config.OPENROUTER_BASE_URL,
                default_headers=headers or None,
            )
            self.model = Config.OPENROUTER_MODEL
            self.vision_model = Config.OPENROUTER_VISION_MODEL
            self.provider = "OpenRouter"
        else:
            self.client = AsyncOpenAI(
                api_key=Config.OPENAI_API_KEY,
                base_url=Config.OPENAI_BASE_URL,
            )
            self.model = Config.OPENAI_MODEL
            self.vision_model = Config.OPENAI_VISION_MODEL
            self.provider = "OpenAI"
    
    async def analyze_strategy(self, strategy_text: str, rules: str = "", market_conditions: str = "") -> dict:
        """
        Analyze a trading strategy using AI
        
        Args:
            strategy_text: Description of the strategy
            rules: Trading rules and parameters
            market_conditions: Current market conditions
            
        Returns:
            dict with analysis results
        """
        prompt = self._create_analysis_prompt(strategy_text, rules, market_conditions)
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional trading analyst. Provide insightful, data-driven analysis of trading strategies. Be concise but thorough. Focus on risk management and market suitability."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=1500
            )
            
            analysis_text = response.choices[0].message.content
            return {
                "status": "success",
                "analysis": analysis_text,
                "tokens_used": response.usage.total_tokens
            }
        except Exception as e:
            return {
                "status": "error",
                "error": self._format_error(e)
            }
    
    async def get_market_summary(self, assets: list = None, market_data: dict = None) -> str:
        """
        Generate market summary for specified assets
        
        Args:
            assets: List of assets (e.g., ['BTC', 'ETH', 'SOL'])
            
        Returns:
            Market summary text
        """
        if not assets:
            assets = ["BTC", "ETH"]
        
        market_lines = []
        if market_data:
            for symbol in assets:
                info = market_data.get(symbol, {})
                market_lines.append(
                    f"{symbol}: price={info.get('usd')}, "
                    f"24h_change={info.get('usd_24h_change')}%, "
                    f"market_cap={info.get('usd_market_cap')}, "
                    f"volume_24h={info.get('usd_24h_vol')}"
                )

        prompt = f"""Provide a brief market summary for these assets: {', '.join(assets)}

Live CoinGecko data:
{chr(10).join(market_lines) if market_lines else "No live price data supplied."}
        
Include:
- Current market sentiment
- Key support/resistance levels (if you can estimate)
- Notable trading patterns
- Risk considerations

Keep it to 3-4 sentences, professional tone."""
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional market analyst. Provide concise, actionable market insights."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            return response.choices[0].message.content
        except Exception as e:
            return f"Error generating market summary with {self.provider}: {self._format_error(e)}"
    
    async def analyze_risk(self, trade_setup: str, position_size: float = None, leverage: float = 1.0) -> dict:
        """
        Analyze risk parameters of a trade setup
        
        Args:
            trade_setup: Description of the trade setup
            position_size: Position size in quote currency
            leverage: Leverage being used
            
        Returns:
            Risk analysis with recommendations
        """
        prompt = self._create_risk_analysis_prompt(trade_setup, position_size, leverage)
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a risk management expert. Provide detailed risk analysis with specific recommendations for position sizing and stop losses."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.6,
                max_tokens=1000
            )
            
            return {
                "status": "success",
                "analysis": response.choices[0].message.content
            }
        except Exception as e:
            return {
                "status": "error",
                "error": self._format_error(e)
            }
    
    def _create_analysis_prompt(self, strategy_text: str, rules: str, market_conditions: str) -> str:
        """Create prompt for strategy analysis"""
        return f"""Analyze the following trading strategy:

STRATEGY DESCRIPTION:
{strategy_text}

TRADING RULES:
{rules if rules else "Not specified"}

CURRENT MARKET CONDITIONS:
{market_conditions if market_conditions else "General market analysis"}

Provide analysis on:
1. STRENGTHS - What works well about this strategy
2. WEAKNESSES - Potential issues or edge cases
3. RISK ASSESSMENT - Key risks and mitigation strategies
4. MARKET SUITABILITY - Which market conditions favor this strategy
5. RECOMMENDATION - Overall rating (1-5 stars) and key improvements

Be professional, analytical, and trader-focused."""
    
    def _create_risk_analysis_prompt(self, trade_setup: str, position_size: float, leverage: float) -> str:
        """Create prompt for risk analysis"""
        return f"""Analyze the risk of this trade setup:

TRADE SETUP:
{trade_setup}

POSITION SIZE: {position_size if position_size else "Not specified"}
LEVERAGE: {leverage}x

Provide:
1. Recommended stop loss levels
2. Appropriate position sizing (% of account)
3. Risk-to-reward ratio assessment
4. Leverage suitability
5. Key risk factors
6. Portfolio exposure considerations

Be specific and practical."""

    async def analyze_with_vision(self, image_base64: str, prompt: str, mime_type: str = "image/jpeg") -> str:
        """
        Analyze image with GPT-4 Vision
        
        Args:
            image_base64: Base64 encoded image
            prompt: Analysis prompt
            
        Returns:
            Analysis text
        """
        try:
            response = await self.client.chat.completions.create(
                model=self.vision_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional trading analyst with expertise in technical analysis and chart reading. Provide actionable insights based on visual analysis."
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mime_type};base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=1024,
                temperature=0.7
            )
            
            return response.choices[0].message.content
        except Exception as e:
            return f"Vision analysis unavailable through {self.provider}: {self._format_error(e)}. Please provide text description instead."

    async def analyze_multiple_images(self, images: list[dict], prompt: str) -> str:
        """Analyze multiple image frames in one request."""
        try:
            content = [{"type": "text", "text": prompt}]
            for image in images:
                mime_type = image.get("mime_type", "image/jpeg")
                content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{mime_type};base64,{image['base64']}"
                    }
                })

            response = await self.client.chat.completions.create(
                model=self.vision_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional trading analyst. Compare chart frames and extract concise, actionable trading insights."
                    },
                    {
                        "role": "user",
                        "content": content
                    }
                ],
                max_tokens=1200,
                temperature=0.6
            )

            return response.choices[0].message.content
        except Exception as e:
            return f"Video frame analysis unavailable through {self.provider}: {self._format_error(e)}."

    def _format_error(self, error: Exception) -> str:
        message = str(error)
        if "insufficient_quota" in message or "exceeded your current quota" in message:
            return f"{self.provider} quota/billing is not available for this key."
        return message
