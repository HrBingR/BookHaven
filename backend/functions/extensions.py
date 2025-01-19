from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["60 per minute"]
)

def setup_limiter(app):
    limiter.init_app(app)
    return limiter

def setup_cors(app):
    CORS(app, resources={
    r"/api/*": {"origins": "*"},  # Allow all origins for API routes
    r"/stream/*": {"origins": "*"},  # Allow all origins for streaming routes
    r"/files/*": {"origins": "*"},  # Allow all origins for file-serving routes
    r"/download/*": {"origins": "*"},  # Allow all origins for file-serving routes
})