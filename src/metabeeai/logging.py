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
        # Determine logs directory from environment (fallback to data_dir/logs)
        logs_dir = os.environ.get("METABEEAI_LOGS_DIR")
        if not logs_dir:
            data_dir = os.environ.get("METABEEAI_DATA_DIR", "data")
            logs_dir = os.path.join(data_dir, "logs")
        Path(logs_dir).mkdir(parents=True, exist_ok=True)

        log_file = os.path.join(logs_dir, "metabeeai.log")
        handlers = [logging.StreamHandler(sys.stdout), TimedRotatingFileHandler(log_file, when="d", interval=1, backupCount=7)]
        formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s", "%Y-%m-%d %H:%M:%S")
        for handler in handlers:
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        # Set log level from environment (default INFO)
        level = os.environ.get("METABEEAI_LOG_LEVEL", "INFO").upper()
        logger.setLevel(level)
    return logger
