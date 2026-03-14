"""
Normalization Module - Transforms raw data to normalized tables
"""
from datetime import datetime
from typing import Optional
from decimal import Decimal

from ..utils.db import db
from ..utils.logger import logger

class Normalizer:
    @staticmethod
    def _get_latest_timestamp(table: str, col: str = "timestamp") -> Optional[datetime]:
        result = db.execute_one(f"SELECT MAX({col}) as ts FROM {table}")
        return result["ts"] if result else None

    @staticmethod
    def _compute_cycle_phase(rsi: float, oi_change: float) -> str:
        if rsi < 30 and oi_change < -5:
            return "Accumulation"
        elif rsi > 70 and oi_change > 5:
            return "Distribution"
        elif 30 <= rsi <= 50:
            return "Run-Up"
        elif 50 < rsi <= 70:
            return "Run-Down"
        return "Neutral"

    def normalize_prices(self) -> int:
        last_ts = self._get_latest_timestamp("normalized_prices")
        query = "SELECT * FROM raw_coingecko"
        if last_ts:
            query += f" WHERE timestamp > '{last_ts}'"
        
        rows = db.execute(query)
        inserted = 0
        
        for row in rows:
            db.insert_one("normalized_prices", {
                "symbol": row["symbol"],
                "price": row.get("price"),
                "rsi_24h": row.get("rsi_24h"),
                "timestamp": row.get("timestamp", datetime.now())
            })
            inserted += 1
        
        logger.info(f"Normalized {inserted} price records")
        return inserted

    def normalize_leverage(self) -> int:
        last_ts = self._get_latest_timestamp("normalized_leverage")
        query = "SELECT * FROM raw_coinglass"
        if last_ts:
            query += f" WHERE timestamp > '{last_ts}'"
        
        rows = db.execute(query)
        inserted = 0
        
        for row in rows:
            db.insert_one("normalized_leverage", {
                "symbol": row["symbol"],
                "open_interest": row.get("open_interest"),
                "oi_change_pct": row.get("oi_change_pct"),
                "funding_rate": row.get("funding_rate"),
                "funding_change": row.get("funding_change"),
                "timestamp": row.get("timestamp", datetime.now())
            })
            inserted += 1
        
        logger.info(f"Normalized {inserted} leverage records")
        return inserted

    def normalize_sentiment(self) -> int:
        last_ts = self._get_latest_timestamp("normalized_sentiment")
        query = "SELECT * FROM raw_alternative_me"
        if last_ts:
            query += f" WHERE timestamp > '{last_ts}'"
        
        rows = db.execute(query)
        inserted = 0
        
        news_result = db.execute_one("SELECT COUNT(*) as cnt FROM raw_news WHERE timestamp > %s", 
                                       (last_ts,)) if last_ts else db.execute_one("SELECT COUNT(*) as cnt FROM raw_news")
        news_count = news_result["cnt"] if news_result else 0
        
        for row in rows:
            db.insert_one("normalized_sentiment", {
                "fear_greed_index": row.get("fear_greed_index"),
                "news_count": news_count,
                "timestamp": row.get("timestamp", datetime.now())
            })
            inserted += 1
        
        logger.info(f"Normalized {inserted} sentiment records")
        return inserted

    def normalize_macro(self) -> int:
        last_ts = self._get_latest_timestamp("normalized_macro")
        query = "SELECT * FROM raw_fred"
        if last_ts:
            query += f" WHERE timestamp > '{last_ts}'"
        
        rows = db.execute(query)
        inserted = 0
        
        for row in rows:
            db.insert_one("normalized_macro", {
                "cpi": row.get("cpi"),
                "dxy": row.get("dxy"),
                "interest_rate": row.get("interest_rate"),
                "timestamp": row.get("timestamp", datetime.now())
            })
            inserted += 1
        
        logger.info(f"Normalized {inserted} macro records")
        return inserted

    def normalize_regulation(self) -> int:
        rows = db.execute("SELECT DISTINCT source, MAX(timestamp) as ts FROM raw_news GROUP BY source")
        inserted = 0
        
        if not rows:
            db.insert_one("normalized_regulation", {
                "threat_level": "none",
                "source": "default",
                "description": "No regulatory news detected - default to safe",
                "timestamp": datetime.now()
            })
            inserted = 1
        else:
            for row in rows:
                db.insert_one("normalized_regulation", {
                    "threat_level": "none",
                    "source": row["source"],
                    "description": "No regulatory threat detected",
                    "timestamp": row.get("ts", datetime.now())
                })
                inserted += 1
        
        logger.info(f"Normalized {inserted} regulation records")
        return inserted

    def normalize_cycle(self) -> int:
        prices = db.execute_one("SELECT rsi_24h FROM normalized_prices ORDER BY timestamp DESC LIMIT 1")
        leverage = db.execute_one("SELECT oi_change_pct FROM normalized_leverage ORDER BY timestamp DESC LIMIT 1")
        
        rsi = float(prices["rsi_24h"]) if prices and prices.get("rsi_24h") else 50.0
        oi_change = float(leverage["oi_change_pct"]) if leverage and leverage.get("oi_change_pct") else 0.0
        
        phase = self._compute_cycle_phase(rsi, oi_change)
        
        db.insert_one("normalized_cycle", {
            "phase": phase,
            "confidence": 0.75,
            "timestamp": datetime.now()
        })
        
        logger.info(f"Computed cycle phase: {phase}")
        return 1

def normalize_all() -> dict:
    """Run all normalizations"""
    normalizer = Normalizer()
    results = {
        "prices": normalizer.normalize_prices(),
        "leverage": normalizer.normalize_leverage(),
        "sentiment": normalizer.normalize_sentiment(),
        "macro": normalizer.normalize_macro(),
        "regulation": normalizer.normalize_regulation(),
        "cycle": normalizer.normalize_cycle()
    }
    logger.info(f"Normalization complete: {results}")
    return results
