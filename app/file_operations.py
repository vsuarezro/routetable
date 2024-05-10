
import re

ALLOWED_CHARACTERS = re.compile(r"^[a-zA-Z0-9\s.,]+$")  # Adjust as needed
MAX_FILE_SIZE = 1024 * 1024 * 200  # 200 MB limit

def load_file(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        if os.path.getsize(filename) > MAX_FILE_SIZE:
            raise ValueError("File exceeds maximum size")

        contents = f.read()
        if not ALLOWED_CHARACTERS.match(contents):
            raise ValueError("File contains invalid characters")

        return contents  # Proceed to process the sanitized content