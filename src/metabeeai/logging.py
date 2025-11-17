import logging
import os
import sys
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path


def setup_logger(name: str = None):
    """
    Set up a logger with console and file handlers.

    Args:
        name: Logger name (optional)

    Returns:
        Logger instance
    """
    logger = logging.getLogger(name)
    if not logger.handlers:  # Prevent duplicate handlers in multi-import scenarios
        # Determine logs directory: METABEEAI_LOGS_DIR env var, or {DATA_DIR}/logs, or "data/logs"
        logs_dir = os.getenv("METABEEAI_LOGS_DIR") or os.path.join(os.getenv("METABEEAI_DATA_DIR", "data"), "logs")
        Path(logs_dir).mkdir(parents=True, exist_ok=True)

        log_file = os.path.join(logs_dir, "metabeeai.log")
        handlers = [logging.StreamHandler(sys.stdout), TimedRotatingFileHandler(log_file, when="d", interval=1, backupCount=7)]
        formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s", "%Y-%m-%d %H:%M:%S")
        for handler in handlers:
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        # Set log level from environment variable or default to INFO
        logger.setLevel(os.getenv("METABEEAI_LOG_LEVEL", "INFO").upper())
    return logger
