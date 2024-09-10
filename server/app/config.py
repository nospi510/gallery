from datetime import timedelta
from sqlalchemy.pool import QueuePool
import secrets

class Config:
    SQLALCHEMY_DATABASE_URI = 'mysql+mysqlconnector://nick:passer@192.168.1.23:3307/gallery?charset=utf8mb4'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = secrets.token_hex(24)
    PERMANENT_SESSION_LIFETIME = timedelta(days=1)
    #SESSION_COOKIE_SECURE = True  # Les cookies de session sont transmis uniquement sur des connexions sécurisées (HTTPS)
    #SESSION_COOKIE_HTTPONLY = True  # Empêche l'accès au cookie via JavaScript
    SESSION_COOKIE_SAMESITE = 'Lax'
    # Ajout de la configuration pour gérer les connexions inactives
    SQLALCHEMY_ENGINE_OPTIONS = {
    'poolclass': QueuePool,
    'pool_size': 10,
    'max_overflow': 20,
    'pool_recycle': 10,
    'pool_pre_ping': True,
}

    
