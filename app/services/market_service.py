"""
Market Data Service for crypto market information
"""
import aiohttp
from datetime import datetime
from config import Config


class MarketService:
    """Service for market data and analysis"""
    
    def __init__(self):
        self.coingecko_base_url = (
            "https://pro-api.coingecko.com/api/v3"
            if Config.COINGECKO_API_TIER == "pro"
            else "https://api.coingecko.com/api/v3"
        )
        self.binance_base_url = "https://api.binance.com/api/v3"

    def _headers(self) -> dict:
        """Build CoinGecko auth headers without exposing the API key."""
        if not Config.COINGECKO_API_KEY:
            return {}

        header_name = "x-cg-pro-api-key" if Config.COINGECKO_API_TIER == "pro" else "x-cg-demo-api-key"
        return {header_name: Config.COINGECKO_API_KEY}
    
    async def get_price_data(self, symbol: str = "BTC") -> dict:
        """
        Get current price data for a symbol
        
        Args:
            symbol: Symbol like BTC, ETH, SOL
            
        Returns:
            Price data
        """
        try:
            coin_id = self._symbol_to_coingecko_id(symbol)
            url = f"{self.coingecko_base_url}/simple/price"
            params = {
                "ids": coin_id,
                "vs_currencies": "usd",
                "include_market_cap": "true",
                "include_24hr_vol": "true",
                "include_24hr_change": "true",
                "include_last_updated_at": "true"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, headers=self._headers()) as response:
                    if response.status == 200:
                        data = await response.json()
                        price_info = data.get(coin_id, {})
                        return {
                            "symbol": symbol,
                            "price": price_info.get("usd", 0),
                            "market_cap": price_info.get("usd_market_cap"),
                            "volume_24h": price_info.get("usd_24h_vol"),
                            "change_24h": price_info.get("usd_24h_change"),
                            "last_updated_at": price_info.get("last_updated_at"),
                            "timestamp": datetime.now().isoformat()
                        }
                    error_text = await response.text()
                    return {"error": f"CoinGecko error {response.status}: {error_text[:200]}"}
            return {"error": "Failed to fetch price data"}
        except Exception as e:
            return {"error": str(e)}
    
    async def get_market_chart(self, symbol: str = "BTC", days: int = 7) -> dict:
        """
        Get market chart data for a symbol
        
        Args:
            symbol: Symbol like BTC, ETH
            days: Number of days to retrieve
            
        Returns:
            Chart data with prices and volumes
        """
        try:
            coin_id = self._symbol_to_coingecko_id(symbol)
            url = f"{self.coingecko_base_url}/coins/{coin_id}/market_chart"
            params = {
                "vs_currency": "usd",
                "days": days,
                "interval": "daily"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, headers=self._headers()) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "symbol": symbol,
                            "prices": data.get("prices", []),
                            "volumes": data.get("volumes", []),
                            "market_caps": data.get("market_caps", [])
                        }
            return {"error": "Failed to fetch chart data"}
        except Exception as e:
            return {"error": str(e)}
    
    async def get_multiple_prices(self, symbols: list) -> dict:
        """
        Get prices for multiple symbols at once
        
        Args:
            symbols: List of symbols
            
        Returns:
            Dict with prices for each symbol
        """
        try:
            coin_ids = [self._symbol_to_coingecko_id(s) for s in symbols]
            url = f"{self.coingecko_base_url}/simple/price"
            params = {
                "ids": ",".join(coin_ids),
                "vs_currencies": "usd",
                "include_market_cap": "true",
                "include_24hr_vol": "true",
                "include_24hr_change": "true",
                "include_last_updated_at": "true"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, headers=self._headers()) as response:
                    if response.status == 200:
                        data = await response.json()
                        result = {}
                        for idx, symbol in enumerate(symbols):
                            coin_id = coin_ids[idx]
                            if coin_id in data:
                                result[symbol] = data[coin_id]
                        return result
                    error_text = await response.text()
                    return {"error": f"CoinGecko error {response.status}: {error_text[:200]}"}
            return {"error": "Failed to fetch price data"}
        except Exception as e:
            return {"error": str(e)}
    
    def _symbol_to_coingecko_id(self, symbol: str) -> str:
        """Convert symbol to CoinGecko ID"""
        symbol_map = {
            "BTC": "bitcoin",
            "ETH": "ethereum",
            "SOL": "solana",
            "XRP": "ripple",
            "ADA": "cardano",
            "DOGE": "dogecoin",
            "LINK": "chainlink",
            "AVAX": "avalanche-2",
            "MATIC": "matic-network",
            "ARB": "arbitrum"
        }
        return symbol_map.get(symbol.upper(), symbol.lower())
