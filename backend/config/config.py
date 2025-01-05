import os
from dotenv import load_dotenv

# Load environment variables from a .env file, if it exists
load_dotenv()

class Config:
    # Provide a default value for BASE_DIRECTORY
    BASE_DIRECTORY = os.getenv('BASE_DIRECTORY', '/ebooks')
    print(f"Using base directory: {BASE_DIRECTORY}")
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
    BASE_URL = os.getenv('BASE_URL')
    if not BASE_URL:
        raise ValueError(
            "Missing required BASE_URL in environment variables."
        )

    valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    if LOG_LEVEL not in valid_levels:
        print(f"Invalid log level '{LOG_LEVEL}', defaulting to INFO")
        LOG_LEVEL = "INFO"

    DB_TYPE = os.getenv('DB_TYPE', 'sqlite').lower()  # Default to SQLite
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = os.getenv('DB_PORT')  # Optional; fallback to DB_TYPE defaults
    DB_NAME = os.getenv('DB_NAME', 'epub_library')  # Default DB name
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', None)

    @staticmethod
    def get_database_url():
        """
        Construct the SQLAlchemy database URL based on the configuration.
        """
        if Config.DB_TYPE == 'sqlite':
            # Use SQLite's specific URL format (file-based)
            return f"sqlite:///{Config.DB_NAME}.db"
        elif Config.DB_TYPE == 'mysql':
            # MySQL URL: mysql+pymysql://username:password@host[:port]/dbname
            return f"mysql+pymysql://{Config.DB_USER}:{Config.DB_PASSWORD}@{Config.DB_HOST}:{Config.DB_PORT or 3306}/{Config.DB_NAME}"
        elif Config.DB_TYPE == 'postgres':
            # Postgres URL: postgresql://username:password@host[:port]/dbname
            return f"postgresql://{Config.DB_USER}:{Config.DB_PASSWORD}@{Config.DB_HOST}:{Config.DB_PORT or 5432}/{Config.DB_NAME}"
        else:
            raise ValueError(f"Unsupported DB_TYPE: {Config.DB_TYPE}")

config = Config()