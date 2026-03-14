"""
Data Ingestion Module - Validates Airbyte sync status
"""
from datetime import datetime
from typing import Optional

from ..utils.db import db
from ..utils.logger import logger, log_airbyte_sync

RAW_TABLES = [
    "raw_coingecko",
    "raw_coinglass", 
    "raw_alternative_me",
    "raw_fred",
    "raw_news"
]

def validate_airbyte_sync() -> dict:
    """Validate Airbyte sync status for all sources"""
    results = {}
    
    for table in RAW_TABLES:
        try:
            if not db.table_exists(table):
                log_airbyte_sync(table, "TABLE_MISSING", 0)
                results[table] = {"status": "missing", "rows": 0}
                continue
            
            result = db.execute_one(f"SELECT COUNT(*) as cnt, MAX(timestamp) as last_sync FROM {table}")
            row_count = result["cnt"] if result else 0
            last_sync = result["last_sync"] if result and result.get("last_sync") else None
            
            status = "ok" if row_count > 0 else "empty"
            log_airbyte_sync(table, status, row_count)
            results[table] = {"status": status, "rows": row_count, "last_sync": last_sync}
            
        except Exception as e:
            log_airbyte_sync(table, f"ERROR: {e}", 0)
            results[table] = {"status": "error", "error": str(e), "rows": 0}
    
    all_ok = all(r.get("status") == "ok" for r in results.values())
    logger.info(f"Airbyte sync validation: {'PASSED' if all_ok else 'FAILED'}")
    
    return results
