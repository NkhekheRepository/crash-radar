import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

class ColoredFormatter(logging.Formatter):
    COLORS = {
        "DEBUG": "\033[36m",
        "INFO": "\033[32m",
        "WARNING": "\033[33m",
        "ERROR": "\033[31m",
        "CRITICAL": "\033[35m",
    }
    RESET = "\033[0m"

    def format(self, record):
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.RESET}"
        return super().format(record)

def setup_logger(name: str = "crash_radar", level: str = "INFO") -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(getattr(logging, level.upper()))
        
        formatter = ColoredFormatter(
            fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger

def log_signal(score: int, signal_type: str, details: dict):
    logger = logging.getLogger("crash_radar.signals")
    logger.info(f"Signal: {signal_type} | Score: {score}/6 | BTC: ${details.get('btc_price', 'N/A')}")

def log_error(source: str, error: Exception):
    logger = logging.getLogger("crash_radar.errors")
    logger.error(f"{source}: {type(error).__name__} - {str(error)}")

def log_airbyte_sync(source: str, status: str, rows: int = 0):
    logger = logging.getLogger("crash_radar.sync")
    logger.info(f"Airbyte sync [{source}]: {status} ({rows} rows)")

logger = setup_logger()
