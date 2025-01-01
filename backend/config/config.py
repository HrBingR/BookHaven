import os
from dotenv import load_dotenv

# Load environment variables from a .env file, if it exists
load_dotenv()

class Config:
    # Provide a default value for BASE_DIRECTORY
    BASE_DIRECTORY = os.getenv('BASE_DIRECTORY', '/ebooks')
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
    if not os.getenv('GOOGLE_BOOKS_API_KEY'):
        raise ValueError(
            "Missing required Google Books API Key in environment variables"
        )
    GOOGLE_BOOKS_API_KEY = os.getenv('GOOGLE_BOOKS_API_KEY')

    valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    if LOG_LEVEL not in valid_levels:
        print(f"Invalid log level '{LOG_LEVEL}', defaulting to INFO")
        LOG_LEVEL = "INFO"

config = Config()