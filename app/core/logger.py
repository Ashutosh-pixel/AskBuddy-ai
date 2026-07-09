import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

# Create logs directory if it doesn't exist
log_dir = Path("app/logs")
log_dir.mkdir(exist_ok=True)

logger = logging.getLogger("fastapi-app")
logger.setLevel(logging.INFO)


formatter = logging.Formatter(
    "%(asctime)s | %(levelname)s | %(message)s"
)

# Console Handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)

# File Handler (10 MB per file, keep 5 backups)
file_handler = RotatingFileHandler(
    "app/logs/app.log",
    maxBytes=10 * 1024 * 1024,
    backupCount=5,
    encoding="utf-8"
)
file_handler.setFormatter(formatter)

logger.addHandler(console_handler)
logger.addHandler(file_handler)
