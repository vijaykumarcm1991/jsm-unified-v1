import logging
import sys
import os

def setup_logger():
    logger = logging.getLogger("app")

    # duplicate handlers (IMPORTANT)
    if logger.hasHandlers():
        return logger

    # ✅ Read log level from environment variable
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    logger.setLevel(getattr(logging, log_level, logging.INFO))

    file_handler = logging.FileHandler("logs.txt")
    stream_handler = logging.StreamHandler(sys.stdout)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s"
    )

    file_handler.setFormatter(formatter)
    stream_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    return logger


# ✅ THIS LINE IS MANDATORY
logger = setup_logger()