import logging
import os
import sys
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

from metabeeai.config import get_config_param


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
        # Determine logs directory from config (with fallback to data_dir/logs)
        logs_dir = get_config_param("logs_dir")
        if logs_dir is None:
            data_dir = get_config_param("data_dir")
            logs_dir = os.path.join(data_dir, "logs")
        Path(logs_dir).mkdir(parents=True, exist_ok=True)

        log_file = os.path.join(logs_dir, "metabeeai.log")
        handlers = [logging.StreamHandler(sys.stdout), TimedRotatingFileHandler(log_file, when="d", interval=1, backupCount=7)]
        formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s", "%Y-%m-%d %H:%M:%S")
        for handler in handlers:
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        # Set log level from config
        logger.setLevel(get_config_param("log_level").upper())
    return logger
