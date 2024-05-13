import os
import re
import logging

logger = logging.getLogger(__name__)

MAX_FILE_SIZE = 1024 * 1024 * 200  # 200 MB limit

def load_file_content(filename: str):
    logger.debug("load_file_content")

    if not os.path.exists(filename):
        logger.error(f"File {filename} does not exist")
        raise FileNotFoundError("File {filename} does not exist")

    if os.path.getsize(filename) > MAX_FILE_SIZE:
        logger.error(f"File {filename} exceeds maximum size")
        raise ValueError(f"File {filename} exceeds maximum size")
        return

    with open(filename, "r", encoding="utf-8") as f:
        content = f.read()

    logger.debug(f"File {filename} loaded successfully")
    return content
