"""
Signal Engine Module - Computes Crash Radar scores
"""
from datetime import datetime
from typing import Optional

from ..utils.db import db
from ..utils.config import config
from ..utils.logger import logger, log_signal

class SignalEngine:
    def __init__(self):
        self.rsi_oversold = config.rsi_oversold
        self.oi_drop_critical = config.oi_drop_critical
        self.fear_greed_critical = config.fear_greed_critical

    def _get_latest_data(self) -> dict:
        data = {}
        
        price = db.execute_one("SELECT * FROM normalized_prices ORDER BY timestamp DESC LIMIT 1")
        data["price"] = price
        
        leverage = db.execute_one("SELECT * FROM normalized_leverage ORDER BY timestamp DESC LIMIT 1")
        data["leverage"] = leverage
        
        sentiment = db.execute_one("SELECT * FROM normalized_sentiment ORDER BY timestamp DESC LIMIT 1")
        data["sentiment"] = sentiment
        
        macro = db.execute_one("SELECT * FROM normalized_macro ORDER BY timestamp DESC LIMIT 1")
        data["macro"] = macro
        
        regulation = db.execute_one("SELECT * FROM normalized_regulation ORDER BY timestamp DESC LIMIT 1")
        data["regulation"] = regulation
        
        cycle = db.execute_one("SELECT * FROM normalized_cycle ORDER BY timestamp DESC LIMIT 1")
        data["cycle"] = cycle
        
        return data

    def _score_price_layer(self, rsi: Optional[float]) -> int:
        if rsi and rsi < self.rsi_oversold:
            return 1
        return 0

    def _score_leverage_layer(self, oi_change: Optional[float], funding: Optional[float]) -> int:
        if oi_change and oi_change < -self.oi_drop_critical:
            return 1
        if funding and funding < 0:
            return 1
        return 0

    def _score_sentiment_layer(self, fear_index: Optional[int]) -> int:
        if fear_index and fear_index < self.fear_greed_critical:
            return 1
        return 0

    def _score_cycle_layer(self, phase: Optional[str]) -> int:
        if phase in ("Accumulation", "Run-Up"):
            return 1
        return 0

    def _score_regulation_layer(self, threat_level: Optional[str]) -> int:
        if threat_level in (None, "none", "low"):
            return 1
        return 0

    def _score_macro_layer(self, cpi: Optional[float], dxy: Optional[float], prev_cpi: Optional[float], prev_dxy: Optional[float]) -> int:
        improving = 0
        if cpi and prev_cpi and cpi < prev_cpi:
            improving += 1
        if dxy and prev_dxy and dxy < prev_dxy:
            improving += 1
        return 1 if improving >= 1 else 0

    def compute_score(self) -> dict:
        data = self._get_latest_data()
        
        price = data.get("price", {})
        leverage = data.get("leverage", {})
        sentiment = data.get("sentiment", {})
        macro = data.get("macro", {})
        regulation = data.get("regulation", {})
        cycle = data.get("cycle", {})
        
        rsi = float(price.get("rsi_24h")) if price and price.get("rsi_24h") else None
        oi_change = float(leverage.get("oi_change_pct")) if leverage and leverage.get("oi_change_pct") else None
        funding = float(leverage.get("funding_rate")) if leverage and leverage.get("funding_rate") else None
        fear_index = int(sentiment.get("fear_greed_index")) if sentiment and sentiment.get("fear_greed_index") else None
        cpi = float(macro.get("cpi")) if macro and macro.get("cpi") else None
        dxy = float(macro.get("dxy")) if macro and macro.get("dxy") else None
        threat_level = regulation.get("threat_level") if regulation else None
        cycle_phase = cycle.get("phase") if cycle else None
        
        prev_macro = db.execute_one("SELECT cpi, dxy FROM normalized_macro ORDER BY timestamp DESC LIMIT 1 OFFSET 1")
        prev_cpi = float(prev_macro["cpi"]) if prev_macro and prev_macro.get("cpi") else None
        prev_dxy = float(prev_macro["dxy"]) if prev_macro and prev_macro.get("dxy") else None
        
        score = 0
        score += self._score_price_layer(rsi)
        score += self._score_leverage_layer(oi_change, funding)
        score += self._score_sentiment_layer(fear_index)
        score += self._score_cycle_layer(cycle_phase)
        score += self._score_regulation_layer(threat_level)
        score += self._score_macro_layer(cpi, dxy, prev_cpi, prev_dxy)
        
        if score >= config.alert_score:
            signal_type = "RISK OFF"
        elif score >= 3:
            signal_type = "WATCH"
        else:
            signal_type = "BUY"
        
        btc_price = float(price.get("price")) if price and price.get("price") else 0.0
        
        macro_indicator = "improving" if (cpi and prev_cpi and cpi < prev_cpi) or (dxy and prev_dxy and dxy < prev_dxy) else "neutral"
        
        result = {
            "score": score,
            "signal_type": signal_type,
            "btc_price": btc_price,
            "rsi": rsi,
            "oi_pct": oi_change,
            "fear_index": fear_index,
            "cycle_phase": cycle_phase,
            "macro_indicator": macro_indicator,
            "regulation_status": threat_level or "unknown"
        }
        
        signal_id = db.insert_one("signals", {
            "score": score,
            "signal_type": signal_type,
            "btc_price": btc_price,
            "rsi": rsi,
            "oi_pct": oi_change,
            "fear_index": fear_index,
            "cycle_phase": cycle_phase,
            "macro_indicator": macro_indicator,
            "regulation_status": threat_level or "unknown",
            "created_at": datetime.now()
        })
        
        log_signal(score, signal_type, {"btc_price": btc_price, "rsi": rsi, "fear_index": fear_index})
        
        return result

def compute_signals() -> dict:
    """Compute crash radar signals"""
    engine = SignalEngine()
    result = engine.compute_score()
    logger.info(f"Signal computed: {result['signal_type']} ({result['score']}/6)")
    return result
