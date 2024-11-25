from flask import jsonify, Flask
from flask_cors import CORS
from datetime import timedelta
from app.extensions import db, jwt, migrate, cache, csrf  
from flask_jwt_extended import verify_jwt_in_request
import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app():
    app = Flask(__name__)
    
    # Database Configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'mysql+pymysql://root:BPAEXeuAfVfdGQvPNqophcWioBlZNvaI@autorack.proxy.rlwy.net:36443/railway')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_timeout': 30,
        'max_overflow': 2
    }
    
    # Basic Configuration
    app.config.update(
        SECRET_KEY=os.getenv('SECRET_KEY', 'dev-secret-key'),
        JWT_SECRET_KEY=os.getenv('JWT_SECRET_KEY', 'dev-jwt-secret'),
        JWT_ACCESS_TOKEN_EXPIRES=timedelta(hours=1),
        JWT_TOKEN_LOCATION=['cookies', 'headers'],
        JWT_COOKIE_CSRF_PROTECT=False,
        JWT_COOKIE_SECURE=False,
        JWT_COOKIE_SAMESITE='Lax',
        SESSION_COOKIE_SECURE=False,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
        PERMANENT_SESSION_LIFETIME=timedelta(days=7),
        WTF_CSRF_ENABLED=True,
        WTF_CSRF_SECRET_KEY=os.getenv('CSRF_SECRET_KEY', 'dev-csrf-secret'),
        CACHE_TYPE='simple',
        CACHE_DEFAULT_TIMEOUT=300
    )

    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)
    cache.init_app(app)
    csrf.init_app(app)
    CORS(app, supports_credentials=True)

    # Register JWT handlers
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({
            "message": "token expired",
        }, 403)

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({
            "message": "invalid token",
        }, 403)

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({
            "message": "unauthorized",
        }, 403)

    @app.context_processor
    def inject_user():
        def is_authenticated():
            try:
                verify_jwt_in_request()
                return True
            except:
                return False
        return dict(is_authenticated=is_authenticated())

    with app.app_context():
        # Import models
        from app.models.user import User
        from app.models.account import Account

        # Import and register blueprints
        from app.routes.auth import auth_bp
        from app.routes.dashboard import dashboard_bp
        from app.routes.accounts import accounts_bp
        from app.routes.transactions import transactions_bp
        from app.routes.users import users_bp
        from app.routes.investments import investments_bp
        from app.routes.budgets import budgets_bp
        from app.routes.bills import bills_bp
        from app.routes.transaction_categories import category_bp
        from app.routes.home import home_bp

        app.register_blueprint(home_bp)
        app.register_blueprint(auth_bp)
        app.register_blueprint(dashboard_bp)
        app.register_blueprint(accounts_bp)
        app.register_blueprint(transactions_bp)
        app.register_blueprint(users_bp)
        app.register_blueprint(investments_bp)
        app.register_blueprint(budgets_bp)
        app.register_blueprint(bills_bp)
        app.register_blueprint(category_bp)
        
        # Create database tables
        db.create_all()
        logger.info("Database tables created successfully!")

    return app

