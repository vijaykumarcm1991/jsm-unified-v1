import logging
import sys

def setup_logger():
    logger = logging.getLogger("app")

    # duplicate handlers (IMPORTANT)
    if logger.hasHandlers():
        return logger

    logger.setLevel(logging.INFO)

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