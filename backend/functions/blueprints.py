from routes.books import books_bp
from routes.media import media_bp
from routes.authors import authors_bp
from routes.auth import auth_bp
from routes.admin import admin_bp
from routes.users import users_bp
from routes.react import react_bp
from routes.scan import scan_bp

def register_blueprints(app):
    app.register_blueprint(books_bp)
    app.register_blueprint(media_bp)
    app.register_blueprint(authors_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(react_bp)
    app.register_blueprint(scan_bp)