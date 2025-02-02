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
        # Serve the requested file if it exists (e.g., JS, CSS, images)
        return send_from_directory(static_folder, path)
    else:
        # Serve React's index.html for unmatched paths
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

    react_config = {
        "UI_BASE_COLOR": color
    }
    return jsonify(react_config), 200