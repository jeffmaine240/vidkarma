import os
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from app.core.config import Config

try:
    import orjson  # Optional: for fast JSON logs
    USE_JSON_LOGS = True
except ImportError:
    USE_JSON_LOGS = False


# === Configuration === #
LOG_DIR = Path("logs")
LOG_FILE = LOG_DIR / "app.log"
LOG_LEVEL = Config.LOG_LEVEL.upper()
MAX_LOG_SIZE = 10 * 1024 * 1024  # 10 MB
BACKUP_COUNT = 5


# === Ensure log directory exists === #
LOG_DIR.mkdir(parents=True, exist_ok=True)


# === JSON Formatter (optional) === #
class JSONLogFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        return orjson.dumps(log_record).decode()


# === Standard Formatter === #
standard_formatter = logging.Formatter(
    fmt="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


# Rotating File Handler
file_handler = RotatingFileHandler(
    LOG_FILE, maxBytes=MAX_LOG_SIZE, backupCount=BACKUP_COUNT, encoding="utf-8"
)
file_handler.setLevel(LOG_LEVEL)
file_handler.setFormatter(JSONLogFormatter() if USE_JSON_LOGS else standard_formatter)

# Stream Handler (console)
console_handler = logging.StreamHandler()
console_handler.setLevel(LOG_LEVEL)
console_handler.setFormatter(standard_formatter)

# === Root Logger Configuration === #
root_logger = logging.getLogger()
root_logger.setLevel(LOG_LEVEL)
root_logger.addHandler(file_handler)
root_logger.addHandler(console_handler)
root_logger.propagate = False


# === Get Logger Function === #
def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
