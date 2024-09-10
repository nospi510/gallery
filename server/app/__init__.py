from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from .config import Config
from .extensions import db, login_manager
from .routes.auth import auth_bp
from .routes.gallery import gallery_bp
from .routes.admin import admin_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialisation des extensions
    db.init_app(app)
    login_manager.init_app(app)

    # Enregistrer les blueprints
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(gallery_bp, url_prefix='/gallery')
    app.register_blueprint(admin_bp, url_prefix='/admin')

    with app.app_context():
        db.create_all()

    return app
