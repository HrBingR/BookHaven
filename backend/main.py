from functions.blueprints import register_blueprints
from functions.extensions import setup_cors, setup_limiter
from functions.init import init_env, init_admin_user, init_admin_password_reset, init_rate_limit, init_encryption, init_oauth, CustomFlask
from config.config import config
from celery_app import celery

def create_app() -> CustomFlask:
    app = CustomFlask(__name__, static_folder="../frontend/dist", static_url_path="/static")
    app.secret_key = config.SECRET_KEY
    init_env()
    init_encryption(app)
    init_rate_limit(app)
    app.config["RATELIMIT_STORAGE_URI"] = config.RATE_LIMITER_URI
    setup_cors(app)
    setup_limiter(app)
    register_blueprints(app)
    app.celery = celery
    init_admin_user()
    init_admin_password_reset()
    app.oauth = init_oauth(app)
    return app

app = create_app()