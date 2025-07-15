from datetime import timedelta
from sqlalchemy.pool import QueuePool
import secrets
from dotenv import load_dotenv
import os
from flask_sqlalchemy import SQLAlchemy

load_dotenv()


class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv('SQLALCHEMY_DATABASE_URI')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv('SECRET_KEY')  # Génération d'une clé secrète si non définie
    PERMANENT_SESSION_LIFETIME = timedelta(days=100)
    #SESSION_COOKIE_SECURE = True  # Les cookies de session sont transmis uniquement sur des connexions sécurisées (HTTPS)
    SESSION_COOKIE_HTTPONLY = True  # Empêche l'accès au cookie via JavaScript
    SESSION_COOKIE_SAMESITE = 'Lax'
    # Ajout de la configuration pour gérer les connexions inactives
    SQLALCHEMY_ENGINE_OPTIONS = {
    'poolclass': QueuePool,
    'pool_size': 10,
    'max_overflow': 20,
    'pool_recycle': 10,
    'pool_pre_ping': True,
}

    
