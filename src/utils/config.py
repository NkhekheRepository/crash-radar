import os
import json
from pathlib import Path
from typing import Any, Optional
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")

class Config:
    _instance: Optional["Config"] = None
    _settings: dict = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load()
        return cls._instance

    def _load(self):
        settings_path = BASE_DIR / "settings.json"
        if settings_path.exists():
            with open(settings_path) as f:
                self._settings = json.load(f)

    @property
    def postgres_host(self) -> str:
        return os.getenv("POSTGRES_HOST", "localhost")

    @property
    def postgres_port(self) -> int:
        return int(os.getenv("POSTGRES_PORT", "5432"))

    @property
    def postgres_db(self) -> str:
        return os.getenv("POSTGRES_DB", "crash_radar")

    @property
    def postgres_user(self) -> str:
        return os.getenv("POSTGRES_USER", "postgres")

    @property
    def postgres_password(self) -> str:
        return os.getenv("POSTGRES_PASSWORD", "")

    @property
    def postgres_dsn(self) -> str:
        return f"host={self.postgres_host} port={self.postgres_port} dbname={self.postgres_db} user={self.postgres_user} password={self.postgres_password}"

    @property
    def telegram_bot_token(self) -> str:
        return os.getenv("TELEGRAM_BOT_TOKEN", "")

    @property
    def telegram_chat_id(self) -> str:
        return os.getenv("TELEGRAM_CHAT_ID", "")

    @property
    def run_times(self) -> list[str]:
        times = os.getenv("RUN_TIMES", "06:00,14:00,22:00")
        return [t.strip() for t in times.split(",")]

    @property
    def log_level(self) -> str:
        return os.getenv("LOG_LEVEL", "INFO")

    @property
    def rsi_oversold(self) -> float:
        return self._settings.get("signal_thresholds", {}).get("rsi_oversold", 30)

    @property
    def oi_drop_critical(self) -> float:
        return self._settings.get("signal_thresholds", {}).get("oi_drop_critical", 10)

    @property
    def fear_greed_critical(self) -> int:
        return self._settings.get("signal_thresholds", {}).get("fear_greed_critical", 25)

    @property
    def alert_score(self) -> int:
        return self._settings.get("signal_thresholds", {}).get("alert_score", 5)

    @property
    def airbyte_host(self) -> str:
        return os.getenv("AIRBYTE_HOST", "localhost")

    @property
    def airbyte_port(self) -> int:
        return int(os.getenv("AIRBYTE_PORT", "8000"))

    def get(self, key: str, default: Any = None) -> Any:
        return self._settings.get(key, default)

config = Config()
