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
        self.BASE_URL = os.getenv('BASE_URL', "").strip()
        self.SECRET_KEY = os.getenv('SECRET_KEY', "").strip()
        self.ADMIN_PASS = os.getenv('ADMIN_PASS')
        self.ADMIN_EMAIL = os.getenv('ADMIN_EMAIL')
        self.ADMIN_RESET = str_to_bool(os.getenv('ADMIN_RESET', "false"))
        self.CF_ACCESS_AUTH = str_to_bool(os.getenv('CF_ACCESS_AUTH', "false"))
        self.ALLOW_UNAUTHENTICATED = str_to_bool(os.getenv('ALLOW_UNAUTHENTICATED', "false"))

        self.OIDC_ENABLED = str_to_bool(os.getenv('OIDC_ENABLED', "false"))
        self.OIDC_CLIENT_ID = os.getenv('OIDC_CLIENT_ID', None)
        self.OIDC_CLIENT_SECRET = os.getenv('OIDC_CLIENT_SECRET', None)
        self.OIDC_PROVIDER = os.getenv('OIDC_PROVIDER', None)
        self.OIDC_METADATA_ENDPOINT = os.getenv('OIDC_METADATA_ENDPOINT', None)
        self.OIDC_AUTO_REGISTER_USER = str_to_bool(os.getenv('OIDC_AUTO_REGISTER_USER', 'false'))
        self.OIDC_AUTO_LINK_USER = str_to_bool(os.getenv('OIDC_AUTO_LINK_USER', 'false'))

        self.REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
        self.REDIS_PORT = os.getenv('REDIS_PORT', '6379')
        self.REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', "").strip()
        self.REDIS_LIMITER_DB = os.getenv('REDIS_LIMITER_DB', 0)
        self.REDIS_SCHEDULER_DB = os.getenv('REDIS_SCHEDULER_DB', 5)

        self.RATE_LIMITER_ENABLED = str_to_bool(os.getenv('RATE_LIMITER_ENABLED', True))
        self.SCHEDULER_ENABLED = str_to_bool(os.getenv('SCHEDULER_ENABLED', True))

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

config = Config()
