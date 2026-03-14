"""
Alerts Module - Telegram notifications
"""
import requests
from datetime import datetime
from typing import Optional

from ..utils.db import db
from ..utils.config import config
from ..utils.logger import logger

class AlertManager:
    def __init__(self):
        self.bot_token = config.telegram_bot_token
        self.chat_id = config.telegram_chat_id
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}"

    def _format_message(self, signal: dict) -> str:
        score = signal.get("score", 0)
        btc_price = signal.get("btc_price", 0)
        rsi = signal.get("rsi", 0)
        oi_pct = signal.get("oi_pct", 0)
        fear_index = signal.get("fear_index", 0)
        cycle_phase = signal.get("cycle_phase", "N/A")
        macro_indicator = signal.get("macro_indicator", "N/A")
        regulation_status = signal.get("regulation_status", "unknown")
        
        emoji = "🚨" if score >= 5 else "⚠️"
        
        rsi_str = f"{rsi:.2f}" if rsi else "N/A"
        oi_str = f"{oi_pct:+.2f}%" if oi_pct else "N/A"
        
        return f"""{emoji} CRASH RADAR ALERT {emoji}

🔴 {signal.get('signal_type', 'N/A')} - Score: {score}/6

📊 Metrics:
• BTC Price: ${btc_price:,.2f}
• RSI: {rsi_str}
• OI Change: {oi_str}
• Fear Index: {fear_index if fear_index else 'N/A'}

📈 Context:
• Cycle Phase: {cycle_phase}
• Macro: {macro_indicator}
• Regulation: {regulation_status}

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""

    def send_message(self, text: str) -> bool:
        if not self.bot_token or not self.chat_id:
            logger.warning("Telegram credentials not configured")
            return False
        
        url = f"{self.api_url}/sendMessage"
        data = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "Markdown"
        }
        
        try:
            response = requests.post(url, json=data, timeout=10)
            if response.status_code == 200:
                logger.info(f"Telegram alert sent: {text[:50]}...")
                return True
            else:
                logger.error(f"Telegram API error: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"Failed to send Telegram alert: {e}")
            return False

    def check_and_alert(self, signal: dict) -> bool:
        if signal.get("score", 0) >= config.alert_score:
            message = self._format_message(signal)
            return self.send_message(message)
        logger.debug(f"Alert threshold not met: {signal.get('score')}/{config.alert_score}")
        return False

def check_and_send_alerts() -> bool:
    """Check latest signal and send alert if needed"""
    latest = db.execute_one("SELECT * FROM signals ORDER BY created_at DESC LIMIT 1")
    if not latest:
        logger.warning("No signals found to alert")
        return False
    
    manager = AlertManager()
    return manager.check_and_alert(latest)
