import logging
import os
import sys
from logging.handlers import TimedRotatingFileHandler


def setup_logger(name: str = None):
    logger = logging.getLogger(name)
    if not logger.handlers:  # Prevent duplicate handlers in multi-import scenarios
        handlers = [logging.StreamHandler(sys.stdout), TimedRotatingFileHandler("app.log", when="d", interval=1, backupCount=7)]
        formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s", "%Y-%m-%d %H:%M:%S")
        for handler in handlers:
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        # Set log level from environment variable or default to INFO
        logger.setLevel(os.getenv("METABEEAI_LOG_LEVEL", "INFO").upper())
    return logger
