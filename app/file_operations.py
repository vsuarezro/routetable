import os
import re
import logging

logger = logging.getLogger(__name__)

ALLOWED_CHARACTERS = re.compile(r"^[a-zA-Z0-9\s\.,:-_\(\)\[\]#=\r\n]+$")  # Adjust as needed
MAX_FILE_SIZE = 1024 * 1024 * 200  # 200 MB limit

def load_file(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        if os.path.getsize(filename) > MAX_FILE_SIZE:
            raise ValueError("File exceeds maximum size")

        contents = f.read()
        # match = ALLOWED_CHARACTERS.match(contents, re.IGNORECASE | re.MULTILINE)
        # logger.debug(f"File contains invalid characters: {match}")
        # if not match:
        #     # ALLOWED_CHARACTERS.match(contents, re.IGNORECASE | re.MULTILINE)
        #     raise ValueError(f"File contains invalid characters {match}")

        return contents  # Proceed to process the sanitized content