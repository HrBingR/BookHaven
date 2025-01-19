from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS
from config.config import config

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["60 per minute"]
)

def setup_limiter(app):
    limiter.init_app(app)
    return limiter

def setup_cors(app):
    allowed_origin = config.BASE_URL
    CORS(app, resources={
        r"/api/*": {"origins": allowed_origin},  # API modules: authors, books, users, etc.
        r"/stream/*": {"origins": allowed_origin},  # Media streaming endpoints
        r"/files/*": {"origins": allowed_origin},  # File-serving routes
        r"/download/*": {"origins": allowed_origin},  # File download endpoints
        r"/login*": {"origins": allowed_origin},  # Authentication: login, OTP handling
        r"/api/admin/*": {"origins": allowed_origin},  # Admin-related endpoints
    })