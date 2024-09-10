from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from .config import Config
from .extensions import db, login_manager
from .routes.auth import auth_bp
from .routes.gallery import gallery_bp
from .routes.admin import admin_bp
from flask_swagger_ui import get_swaggerui_blueprint

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialisation des extensions
    db.init_app(app)
    login_manager.init_app(app)

    # Configuration de Swagger UI
    SWAGGER_URL = '/api/docs'  # L'URL où Swagger UI sera accessible
    API_URL = '/static/swagger.json'  # Le chemin vers le fichier swagger.json

       # Crée le blueprint pour Swagger UI
    swaggerui_blueprint = get_swaggerui_blueprint(
        SWAGGER_URL,
        API_URL,
        config={'app_name': "Gallery API"}
    )


    # Enregistrer les blueprints
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(gallery_bp, url_prefix='/gallery')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

     

    with app.app_context():
        db.create_all()

    return app
