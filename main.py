"""
Crash Radar v1.0 - Main Orchestrator
Runs 3× daily to compute crash risk signals
"""
import sys
import argparse
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler

sys.path.insert(0, str(__file__).rsplit("/", 1)[0])

from src.utils import config, db, logger
from src.data_ingestion.validate_sync import validate_airbyte_sync
from src.normalization.normalize import normalize_all
from src.signal_engine.scorer import compute_signals
from src.alerts.alerter import check_and_send_alerts

def run_pipeline():
    """Execute full Crash Radar pipeline"""
    logger.info("=" * 50)
    logger.info("Starting Crash Radar Pipeline")
    start_time = datetime.now()
    
    try:
        db.initialize()
        logger.info("Database connection established")
        
        logger.info("Phase 1: Validating Airbyte sync...")
        sync_status = validate_airbyte_sync()
        
        logger.info("Phase 2: Normalizing data...")
        norm_results = normalize_all()
        
        logger.info("Phase 3: Computing signals...")
        signal = compute_signals()
        
        logger.info("Phase 4: Checking alerts...")
        alert_sent = check_and_send_alerts()
        
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info(f"Pipeline complete in {elapsed:.2f}s | Alert sent: {alert_sent}")
        logger.info("=" * 50)
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise
    finally:
        db.close()

def main():
    parser = argparse.ArgumentParser(description="Crash Radar v1.0")
    parser.add_argument("--once", action="store_true", help="Run once instead of scheduling")
    parser.add_argument("--validate-only", action="store_true", help="Only validate sync")
    args = parser.parse_args()
    
    if args.validate_only:
        db.initialize()
        validate_airbyte_sync()
        db.close()
        return
    
    if args.once:
        run_pipeline()
        return
    
    scheduler = BlockingScheduler()
    for time_str in config.run_times:
        hour, minute = map(int, time_str.split(":"))
        scheduler.add_job(run_pipeline, "cron", hour=hour, minute=minute, id=f"crash_radar_{time_str}")
    
    logger.info(f"Scheduler started. Running at: {config.run_times}")
    logger.info("Press Ctrl+C to exit")
    
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped")

if __name__ == "__main__":
    main()
