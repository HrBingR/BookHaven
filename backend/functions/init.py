import binascii
from flask import Flask
import sys
from functions.utils import check_admin_user, reset_admin_user_password, check_required_envs
from config.config import config
from config.logger import logger
import base64
import redis
from authlib.integrations.flask_client import OAuth, OAuthError
from typing import Optional
import os

class CustomFlask(Flask):
    oauth: OAuth
    redis: Optional[redis.StrictRedis]

def init_redis() -> Optional[redis.StrictRedis]:
    if config.OPDS_ENABLED:
        try:
            redis_client = redis.StrictRedis.from_url(config.OPDS_REDIS_URI, decode_responses=True)
            return redis_client
        except redis.RedisError as e:
            logger.exception(f"Could not connect to Redis: {e}")
            raise
    else:
        return None

def init_uploads(app):
    if not config.UPLOADS_ENABLED or not os.path.exists(config.UPLOADS_DIRECTORY):
        if not config.UPLOADS_ENABLED or not config.UPLOADS_DIRECTORY:
            reason = "Uploads feature disabled in config."
        else:
            reason = f"Uploads directory ({config.UPLOADS_DIRECTORY}) not mounted into container."
        logger.warning(f"{reason} Disabling uploads feature.")
        app.config["UPLOADS_ENABLED"] = False
        return
    link_path = os.path.join(config.BASE_DIRECTORY, "_uploads")
    try:
        if os.path.islink(link_path):
            if os.readlink(link_path) == config.UPLOADS_DIRECTORY:
                app.config["UPLOADS_ENABLED"] = True
                return
            else:
                raise FileExistsError(f"Incorrect symlink at {link_path}")
        elif os.path.exists(link_path):
            raise FileExistsError(f"File or directory exists at {link_path} and is not a symlink")
        os.symlink(config.UPLOADS_DIRECTORY, link_path)
        app.config["UPLOADS_ENABLED"] = True
    except (OSError, FileExistsError) as e:
        logger.warning(f"{e}. Disabling uploads feature.")
        app.config["UPLOADS_ENABLED"] = False

def init_rate_limit(app):
    if config.ENVIRONMENT != "test":
        app.config["RATELIMIT_ENABLED"] = config.RATE_LIMITER_ENABLED
    else:
        app.config["RATELIMIT_ENABLED"] = False

def init_env():
    try:
        result, message = check_required_envs(config.SECRET_KEY, config.BASE_URL, config.OIDC_ENABLED)
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

def init_oauth(app):
    if config.OIDC_ENABLED:
        try:
            oauth = OAuth(app)
            oauth.register(
                name=config.OIDC_PROVIDER,
                client_id=config.OIDC_CLIENT_ID,
                client_secret=config.OIDC_CLIENT_SECRET,
                server_metadata_url=config.OIDC_METADATA_ENDPOINT,
                client_kwargs={"scope": "openid email profile"}
            )
            return oauth
        except OAuthError as e:
            logger.exception(f"Could not instantiate OIDC configuration; Exception occurred: {e}")
        except Exception as e:
            logger.exception(f"Could not instantiate OIDC configuration; Exception occurred: {e}")
    return None