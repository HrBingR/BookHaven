import binascii
import sys
from functions.utils import check_admin_user, reset_admin_user_password, check_required_envs
from config.config import config
from config.logger import logger
import base64

def init_rate_limit(app):
    if config.ENVIRONMENT != "test":
        app.config["RATELIMIT_ENABLED"] = config.RATE_LIMITER_ENABLED
    else:
        app.config["RATELIMIT_ENABLED"] = False

def init_env():
    try:
        result, message = check_required_envs(config.SECRET_KEY, config.BASE_URL)
        if not result:
            logger.error(message)
            sys.exit(1)
        else:
            logger.debug("Required environment variables checked successfully.")
    except Exception as e:
        logger.exception("Failed to check required environment variables: %s", str(e))
        sys.exit(1)

def init_admin_user():
    if config.ENVIRONMENT != "test":
        try:
            result, message = check_admin_user(config.ADMIN_PASS, config.ADMIN_EMAIL)
            if not result:
                logger.error("Failed to initialize admin user: %s", message)
                sys.exit(1)
            else:
                logger.info("Admin user initialized successfully.")
        except Exception as e:
            logger.exception("Failed to initialize admin user: %s", str(e))
            sys.exit(1)
    else:
        logger.debug("TEST ENVIRONMENT")

def init_admin_password_reset():
    if config.ADMIN_RESET:
        try:
            result, message = reset_admin_user_password(config.ADMIN_PASS)
            if not result:
                logger.error("Failed to reset admin user password: %s", message)
                sys.exit(1)
        except Exception as e:
            logger.exception("Failed to reset admin user password: %s", str(e))

def init_encryption(app):
    key_bytes = binascii.unhexlify(config.SECRET_KEY)
    fernet_key = base64.urlsafe_b64encode(key_bytes)
    app.config["FERNET_KEY"] = fernet_key