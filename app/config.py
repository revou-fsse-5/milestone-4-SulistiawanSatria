# config.py
import os
from datetime import timedelta

# config.py
class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    WTF_CSRF_SECRET_KEY = os.getenv('WTF_CSRF_SECRET_KEY', 'csrf-secret-key')
    WTF_CSRF_ENABLED = True
    
    # Database config
    MYSQL_DATABASE = os.getenv('MYSQL_DATABASE', 'railway')
    MYSQL_HOST = os.getenv('MYSQL_HOST', 'mysql.railway.internal')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD')
    MYSQL_PORT = os.getenv('MYSQL_PORT', '3306')
    MYSQL_USER = os.getenv('MYSQL_USER', 'root')
    
    # Construct Database URL
    if os.getenv('FLASK_ENV') == 'production':
        SQLALCHEMY_DATABASE_URI = os.getenv('MYSQL_URL').replace('mysql://', 'mysql+pymysql://')
    else:
        SQLALCHEMY_DATABASE_URI = os.getenv('MYSQL_PUBLIC_URL').replace('mysql://', 'mysql+pymysql://')
    
    # SQLAlchemy config
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 300,
        'pool_timeout': 20,
        'pool_pre_ping': True
    }
    
    # JWT config
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_TOKEN_LOCATION = ['headers', 'cookies']
    JWT_COOKIE_CSRF_PROTECT = False
    JWT_COOKIE_SECURE = False  # Set True di production
    JWT_ACCESS_COOKIE_NAME = 'access_token_cookie'
    JWT_REFRESH_COOKIE_NAME = 'refresh_token_cookie'
    JWT_ACCESS_COOKIE_PATH = '/'
    JWT_COOKIE_SAMESITE = 'Lax'
    
    # Additional config
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    WTF_CSRF_ENABLED = True