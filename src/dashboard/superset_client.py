"""
Superset Dashboard Module
Queries PostgreSQL for historical signals and provides dashboard data
"""
import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from ..utils.db import db
from ..utils.logger import logger
from ..utils.config import config

class SupersetClient:
    def __init__(self):
        self.host = config.superset_host
        self.port = config.superset_port
        self.base_url = f"http://{self.host}:{self.port}"

    def get_signals_history(self, days: int = 30) -> List[dict]:
        """Get historical signals for dashboard"""
        query = """
            SELECT * FROM signals 
            WHERE created_at > NOW() - INTERVAL '%s days'
            ORDER BY created_at DESC
        """
        results = db.execute(query, (days,))
        return results

    def get_latest_signal(self) -> Optional[dict]:
        """Get the most recent signal"""
        return db.execute_one("SELECT * FROM signals ORDER BY created_at DESC LIMIT 1")

    def get_signal_summary(self) -> dict:
        """Get signal summary statistics"""
        total = db.execute_one("SELECT COUNT(*) as cnt FROM signals")
        risk_off = db.execute_one("SELECT COUNT(*) as cnt FROM signals WHERE signal_type = 'RISK OFF'")
        watch = db.execute_one("SELECT COUNT(*) as cnt FROM signals WHERE signal_type = 'WATCH'")
        buy = db.execute_one("SELECT COUNT(*) as cnt FROM signals WHERE signal_type = 'BUY'")
        
        return {
            "total_signals": total["cnt"] if total else 0,
            "risk_off_count": risk_off["cnt"] if risk_off else 0,
            "watch_count": watch["cnt"] if watch else 0,
            "buy_count": buy["cnt"] if buy else 0
        }

    def get_weekly_aggregates(self) -> List[dict]:
        """Get weekly signal aggregations"""
        query = """
            SELECT 
                DATE_TRUNC('week', created_at) as week,
                signal_type,
                COUNT(*) as count,
                AVG(score) as avg_score
            FROM signals
            WHERE created_at > NOW() - INTERVAL '12 weeks'
            GROUP BY DATE_TRUNC('week', created_at), signal_type
            ORDER BY week DESC
        """
        return db.execute(query)

    def get_metrics_trend(self, metric: str = "fear_index", days: int = 30) -> List[dict]:
        """Get trend data for a specific metric"""
        if metric == "fear_index":
            table = "normalized_sentiment"
            col = "fear_greed_index"
        elif metric == "rsi":
            table = "normalized_prices"
            col = "rsi_24h"
        elif metric == "oi_change":
            table = "normalized_leverage"
            col = "oi_change_pct"
        else:
            return []
        
        query = f"""
            SELECT {col}, timestamp 
            FROM {table}
            WHERE timestamp > NOW() - INTERVAL '{days} days'
            ORDER BY timestamp DESC
        """
        return db.execute(query)

    def export_dashboard_json(self, filepath: str = "/home/ubuntu/crash_radar/dashboard_data.json"):
        """Export dashboard data to JSON for Superset import"""
        data = {
            "export_date": datetime.now().isoformat(),
            "summary": self.get_signal_summary(),
            "latest_signal": self.get_latest_signal(),
            "history_30d": self.get_signals_history(30),
            "weekly_aggregates": self.get_weekly_aggregates(),
            "metrics": {
                "fear_index_trend": self.get_metrics_trend("fear_index", 30),
                "rsi_trend": self.get_metrics_trend("rsi", 30),
                "oi_change_trend": self.get_metrics_trend("oi_change", 30)
            }
        }
        
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2, default=str)
        
        logger.info(f"Dashboard data exported to {filepath}")
        return filepath

    def get_dashboard_data(self) -> dict:
        """Get all dashboard data in one call"""
        return {
            "summary": self.get_signal_summary(),
            "latest": self.get_latest_signal(),
            "history": self.get_signals_history(7),
            "weekly": self.get_weekly_aggregates()
        }


def generate_superset_sql():
    """Generate SQL queries for Superset charts"""
    queries = {
        "signal_history": """
            SELECT 
                DATE(created_at) as date,
                signal_type,
                score,
                btc_price,
                fear_index
            FROM signals
            ORDER BY created_at DESC
            LIMIT 1000
        """,
        "signal_distribution": """
            SELECT 
                signal_type,
                COUNT(*) as count,
                AVG(score) as avg_score
            FROM signals
            GROUP BY signal_type
        """,
        "metrics_over_time": """
            SELECT 
                np.timestamp,
                np.rsi_24h,
                nl.oi_change_pct,
                ns.fear_greed_index
            FROM normalized_prices np
            LEFT JOIN normalized_leverage nl ON np.symbol = nl.symbol
            LEFT JOIN normalized_sentiment ns ON np.timestamp = ns.timestamp
            ORDER BY np.timestamp DESC
            LIMIT 500
        """,
        "daily_alerts": """
            SELECT 
                DATE(created_at) as date,
                COUNT(*) as alert_count,
                SUM(CASE WHEN signal_type = 'RISK OFF' THEN 1 ELSE 0 END) as risk_off_count
            FROM signals
            GROUP BY DATE(created_at)
            ORDER BY date DESC
        """
    }
    
    output_file = "/home/ubuntu/crash_radar/superset_queries.sql"
    with open(output_file, "w") as f:
        for name, query in queries.items():
            f.write(f"-- {name}\n")
            f.write(query.strip() + "\n\n")
    
    logger.info(f"Superset SQL queries saved to {output_file}")
    return output_file


def run_dashboard_export():
    """Standalone dashboard data export"""
    client = SupersetClient()
    client.export_dashboard_json()


if __name__ == "__main__":
    client = SupersetClient()
    print(json.dumps(client.get_dashboard_data(), indent=2, default=str))
