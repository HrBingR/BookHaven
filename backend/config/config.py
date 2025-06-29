import os
from dotenv import load_dotenv

load_dotenv()

def str_to_bool(value):
    if isinstance(value, bool):
        return value
    if not value:
        return False
    if isinstance(value, int):
        if value == 1:
            return True
    if isinstance(value, str):
        value = value.lower()
        if value in ('true', 'yes', 't', 'y', '1'):
            return True
        if value in ('false', 'no', 'f', 'n', '0'):
            return False
    return False

class Config:
    def __init__(self):

        self.UI_BASE_COLOR = os.getenv("UI_BASE_COLOR", "green")

        self.ENVIRONMENT = "production"
        self.BASE_DIRECTORY = os.getenv('BASE_DIRECTORY', '/ebooks')
        self.UPLOADS_DIRECTORY = os.getenv('UPLOADS_DIRECTORY', '/uploads')
        self.UPLOADS_ENABLED = str_to_bool(os.getenv('UPLOADS_ENABLED', False))
        self.BASE_URL = os.getenv('BASE_URL', "").strip()
        self.SECRET_KEY = os.getenv('SECRET_KEY', "").strip()
        self.ADMIN_PASS = os.getenv('ADMIN_PASS')
        self.ADMIN_EMAIL = os.getenv('ADMIN_EMAIL')
        self.ADMIN_RESET = str_to_bool(os.getenv('ADMIN_RESET', False))
        self.CF_ACCESS_AUTH = str_to_bool(os.getenv('CF_ACCESS_AUTH', False))
        self.ALLOW_UNAUTHENTICATED = str_to_bool(os.getenv('ALLOW_UNAUTHENTICATED', False))
        self.WRITE_TO_EPUB = str_to_bool(os.getenv('WRITE_TO_EPUB', False))
        self.REQUESTS_ENABLED = str_to_bool(os.getenv('REQUESTS_ENABLED', True))

        self.OIDC_ENABLED = str_to_bool(os.getenv('OIDC_ENABLED', False))
        self.OIDC_CLIENT_ID = os.getenv('OIDC_CLIENT_ID', None)
        self.OIDC_CLIENT_SECRET = os.getenv('OIDC_CLIENT_SECRET', None)
        self.OIDC_PROVIDER = os.getenv('OIDC_PROVIDER', None)
        self.OIDC_METADATA_ENDPOINT = os.getenv('OIDC_METADATA_ENDPOINT', None)
        self.OIDC_AUTO_REGISTER_USER = str_to_bool(os.getenv('OIDC_AUTO_REGISTER_USER', False))
        self.OIDC_AUTO_LINK_USER = str_to_bool(os.getenv('OIDC_AUTO_LINK_USER', False))

        self.REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
        self.REDIS_PORT = os.getenv('REDIS_PORT', '6379')
        self.REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', "").strip()
        self.REDIS_LIMITER_DB = os.getenv('REDIS_LIMITER_DB', 0)
        self.REDIS_SCHEDULER_DB = os.getenv('REDIS_SCHEDULER_DB', 5)
        self.REDIS_LOCK_DB = os.getenv('REDIS_LOCK_DB', 6)
        self.REDIS_OPDS_DB = os.getenv('REDIS_OPDS_DB', 8)

        self.RATE_LIMITER_ENABLED = str_to_bool(os.getenv('RATE_LIMITER_ENABLED', True))
        self.BACKEND_RATE_LIMIT = os.getenv('BACKEND_RATE_LIMIT', 300)

        self.SCHEDULER_ENABLED = str_to_bool(os.getenv('SCHEDULER_ENABLED', True))
        self.OPDS_ENABLED = str_to_bool(os.getenv('OPDS_ENABLED', False))

        self.PERIODIC_SCAN_INTERVAL = os.getenv('PERIODIC_SCAN_INTERVAL', 10)

        self.DB_TYPE = os.getenv('DB_TYPE', 'sqlite').lower()
        self.DB_HOST = os.getenv('DB_HOST', 'localhost')
        self.DB_PORT = os.getenv('DB_PORT')
        self.DB_NAME = os.getenv('DB_NAME', 'epub_library')
        self.DB_USER = os.getenv('DB_USER', 'root')
        self.DB_PASSWORD = os.getenv('DB_PASSWORD', None)

    @property
    def RATE_LIMITER_URI(self):
        if not self.REDIS_PASSWORD:
            return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_LIMITER_DB}"
        return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_LIMITER_DB}"

    @property
    def CELERY_BROKER_URL(self):
        if not self.REDIS_PASSWORD:
            return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_SCHEDULER_DB}"
        return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_SCHEDULER_DB}"

    @property
    def CELERY_RESULT_BACKEND(self):
        if not self.REDIS_PASSWORD:
            return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_SCHEDULER_DB}"
        return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_SCHEDULER_DB}"

    @property
    def OPDS_REDIS_URI(self):
        if not self.REDIS_PASSWORD:
            return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_OPDS_DB}"
        return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_OPDS_DB}"

    @property
    def REDIS_LOCK_DB_URI(self):
        if not self.REDIS_PASSWORD:
            return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_LOCK_DB}"
        return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_LOCK_DB}"


config = Config()
