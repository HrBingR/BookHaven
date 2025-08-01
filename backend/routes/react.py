import os
from flask import Blueprint, send_from_directory, current_app, jsonify
from config.config import config

react_bp = Blueprint("react", __name__, static_folder="../frontend/dist")

@react_bp.route("/", defaults={"path": ""})
@react_bp.route("/<path:path>")
def serve_react_app(path):
    """
    Serve the React app's index.html for all non-API routes.
    React will take over routing for SPA functionality.
    """
    static_folder = os.path.join(current_app.root_path, "../frontend/dist")
    if path != "" and os.path.exists(os.path.join(static_folder, path)):
        return send_from_directory(static_folder, path)
    else:
        return send_from_directory(static_folder, "index.html")

@react_bp.route("/api/react-init", methods=["GET"])
def react_frontend_config():
    color_variants = {
        'green': 'success',
        'blue': 'primary',
        'red': 'danger',
        'yellow': 'warning',
        'white': 'light',
        'black': 'dark',
        'pink': 'pink',
        'purple': 'purple',
        'orange': 'orange',
        'cyan': 'cyan'
    }
    color = color_variants.get(config.UI_BASE_COLOR, "success")
    cloudflare = config.CF_ACCESS_AUTH
    oidc = config.OIDC_ENABLED
    uploads_enabled = current_app.config["UPLOADS_ENABLED"]
    requests_enabled = config.REQUESTS_ENABLED
    react_config = {
        "UI_BASE_COLOR": color,
        "CF_ACCESS_AUTH": cloudflare,
        "OIDC_ENABLED": oidc,
        "UPLOADS_ENABLED": uploads_enabled,
        "REQUESTS_ENABLED": requests_enabled,
    }
    return jsonify(react_config), 200