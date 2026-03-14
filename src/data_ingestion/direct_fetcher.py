"""
Direct API Fetcher - Alternative to Airbyte
Fetches data directly from APIs without Airbyte
"""
import requests
import json
from datetime import datetime
from typing import Optional
from ..utils.db import db
from ..utils.logger import logger

class DirectAPIFetcher:
    COINGECKO_URL = "https://api.coingecko.com/api/v3"
    FEAR_GREED_URL = "https://api.alternative.me/fng/"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/json"})

    def fetch_coingecko(self, coin: str = "bitcoin") -> Optional[dict]:
        """Fetch price and RSI from CoinGecko"""
        try:
            url = f"{self.COINGECKO_URL}/coins/{coin}"
            params = {
                "localization": "false",
                "tickers": "false",
                "community_data": "false",
                "developer_data": "false",
                "sparkline": "false"
            }
            response = self.session.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                market_data = data.get("market_data", {})
                
                result = {
                    "symbol": coin,
                    "price": market_data.get("current_price", {}).get("usd", 0),
                    "market_cap": market_data.get("market_cap", {}).get("usd", 0),
                    "volume": market_data.get("total_volume", {}).get("usd", 0),
                    "rsi_24h": None,  # CoinGecko doesn't provide RSI directly
                    "timestamp": datetime.now()
                }
                
                db.insert_one("raw_coingecko", result)
                logger.info(f"Fetched CoinGecko data for {coin}: ${result['price']}")
                return result
            else:
                logger.error(f"CoinGecko API error: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Error fetching CoinGecko: {e}")
            return None

    def fetch_fear_greed(self) -> Optional[dict]:
        """Fetch Fear & Greed Index"""
        try:
            response = self.session.get(self.FEAR_GREED_URL, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("data"):
                    fgi = data["data"][0]
                    result = {
                        "fear_greed_index": int(fgi.get("value", 50)),
                        "timestamp": datetime.now()
                    }
                    
                    db.insert_one("raw_alternative_me", result)
                    logger.info(f"Fetched Fear & Greed: {result['fear_greed_index']}")
                    return result
            logger.error(f"Alternative.me API error: {response.status_code}")
            return None
        except Exception as e:
            logger.error(f"Error fetching Fear & Greed: {e}")
            return None

    def fetch_coinglass(self) -> Optional[dict]:
        """Fetch Open Interest from Coinglass (requires API key)"""
        logger.warning("Coinglass requires API key - skipping")
        return None

    def fetch_fred(self, series_id: str = "CPIAUCSL") -> Optional[dict]:
        """Fetch FRED data (requires API key)"""
        logger.warning("FRED requires API key - skipping")
        return None

    def fetch_all(self) -> dict:
        """Fetch all available data"""
        results = {
            "coingecko": self.fetch_coingecko("bitcoin"),
            "fear_greed": self.fetch_fear_greed(),
            "coinglass": None,
            "fred": None
        }
        
        fetched_count = sum(1 for v in results.values() if v is not None)
        logger.info(f"Direct API fetch complete: {fetched_count}/4 sources")
        return results


def run_direct_fetch():
    """Run direct API fetch as standalone script"""
    db.initialize()
    fetcher = DirectAPIFetcher()
    results = fetcher.fetch_all()
    db.close()
    return results


if __name__ == "__main__":
    run_direct_fetch()
