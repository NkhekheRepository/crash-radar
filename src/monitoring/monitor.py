"""
Monitoring & Logging Module
Logs Airbyte syncs, Signal Engine runs, Telegram alerts, errors
"""
import os
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from ..utils.db import db
from ..utils.logger import logger

class SystemMonitor:
    LOG_TABLE = "system_logs"
    
    def __init__(self):
        self.log_file = "/home/ubuntu/crash_radar/logs/system.log"
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
        
    def log_event(self, event_type: str, component: str, status: str, message: str = "", details: dict = None):
        """Log a system event to database"""
        try:
            db.insert_one("system_logs", {
                "event_type": event_type,
                "component": component,
                "status": status,
                "message": message,
                "details": json.dumps(details) if details else None,
                "timestamp": datetime.now()
            })
        except Exception as e:
            logger.error(f"Failed to log event: {e}")
    
    def get_recent_events(self, hours: int = 24, event_type: str = None) -> List[dict]:
        """Get recent system events"""
        query = """
            SELECT * FROM system_logs 
            WHERE timestamp > NOW() - INTERVAL '%s hours'
        """
        params = (hours,)
        
        if event_type:
            query += " AND event_type = %s"
            params = (hours, event_type)
        
        query += " ORDER BY timestamp DESC LIMIT 100"
        
        return db.execute(query, params)
    
    def get_error_summary(self, days: int = 7) -> Dict:
        """Get error summary for specified days"""
        errors = db.execute("""
            SELECT event_type, component, status, COUNT(*) as count
            FROM system_logs
            WHERE timestamp > NOW() - INTERVAL '%s days'
            AND status IN ('error', 'failed')
            GROUP BY event_type, component, status
        """, (days,))
        
        total = db.execute_one("""
            SELECT COUNT(*) as cnt FROM system_logs
            WHERE timestamp > NOW() - INTERVAL '%s days'
            AND status IN ('error', 'failed')
        """, (days,))
        
        return {
            "total_errors": total["cnt"] if total else 0,
            "by_component": errors
        }
    
    def get_uptime_stats(self) -> Dict:
        """Get system uptime statistics"""
        pipeline_runs = db.execute_one("""
            SELECT COUNT(*) as total, 
                   MAX(timestamp) as last_run
            FROM system_logs
            WHERE event_type = 'pipeline' AND status = 'success'
        """)
        
        alerts_sent = db.execute_one("""
            SELECT COUNT(*) as total
            FROM system_logs
            WHERE event_type = 'alert' AND status = 'sent'
        """)
        
        return {
            "total_runs": pipeline_runs["total"] if pipeline_runs else 0,
            "last_run": pipeline_runs["last_run"].isoformat() if pipeline_runs and pipeline_runs.get("last_run") else None,
            "total_alerts": alerts_sent["total"] if alerts_sent else 0
        }
    
    def check_health(self) -> Dict:
        """Check system health status"""
        health = {
            "status": "healthy",
            "checks": {}
        }
        
        try:
            latest_signal = db.execute_one("SELECT created_at FROM signals ORDER BY created_at DESC LIMIT 1")
            if latest_signal:
                age = (datetime.now() - latest_signal["created_at"]).total_seconds()
                health["checks"]["signal_freshness"] = "ok" if age < 86400 else "stale"
            else:
                health["checks"]["signal_freshness"] = "no_data"
                health["status"] = "warning"
        except Exception as e:
            health["checks"]["database"] = "error"
            health["status"] = "unhealthy"
        
        return health
    
    def generate_report(self) -> str:
        """Generate daily system report"""
        errors = self.get_error_summary(1)
        uptime = self.get_uptime_stats()
        health = self.check_health()
        
        report = f"""
=== Crash Radar Daily Report ===
Generated: {datetime.now().isoformat()}

Status: {health['status'].upper()}

Uptime Stats:
- Total Pipeline Runs: {uptime['total_runs']}
- Total Alerts Sent: {uptime['total_alerts']}
- Last Run: {uptime['last_run'] or 'Never'}

Health Checks:
- Signal Freshness: {health['checks'].get('signal_freshness', 'unknown')}
- Database: {health['checks'].get('database', 'ok')}

Errors (Last 24h):
- Total: {errors['total_errors']}
"""
        return report


def log_pipeline_run(status: str, details: dict = None):
    """Log pipeline execution"""
    monitor = SystemMonitor()
    monitor.log_event("pipeline", "main", status, details=details)


def log_alert(status: str, details: dict = None):
    """Log alert sent"""
    monitor = SystemMonitor()
    monitor.log_event("alert", "telegram", status, details=details)


def log_error(component: str, error: str, details: dict = None):
    """Log error"""
    monitor = SystemMonitor()
    monitor.log_event("error", component, "error", error, details)


if __name__ == "__main__":
    monitor = SystemMonitor()
    
    print("System Monitor")
    print("=" * 40)
    
    print(monitor.generate_report())
