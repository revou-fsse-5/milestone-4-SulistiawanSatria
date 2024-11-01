from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_caching import Cache
from flask_wtf.csrf import CSRFProtect
from flask_cors import CORS
from datetime import timedelta
import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize extensions
db = SQLAlchemy()
jwt = JWTManager()
migrate = Migrate()
cache = Cache(config={'CACHE_TYPE': 'simple'})
csrf = CSRFProtect()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app():
    app = Flask(__name__)
    
    # Basic Configuration
    app.config.update(
        SECRET_KEY=os.getenv('SECRET_KEY', 'dev-secret-key'),
        JWT_SECRET_KEY=os.getenv('JWT_SECRET_KEY', 'dev-jwt-secret'),
        SQLALCHEMY_DATABASE_URI=os.getenv('DATABASE_URL', 'sqlite:///app.db'),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        
        # JWT Configuration
        JWT_ACCESS_TOKEN_EXPIRES=timedelta(hours=1),
        JWT_TOKEN_LOCATION=['cookies'],
        JWT_COOKIE_CSRF_PROTECT=True,
        JWT_CSRF_CHECK_FORM=True,
        JWT_COOKIE_SECURE=False,  # Set to True in production
        JWT_COOKIE_SAMESITE='Lax',
        
        # Session and Cookie Configuration
        SESSION_COOKIE_SECURE=False,  # Set to True in production
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
        PERMANENT_SESSION_LIFETIME=timedelta(days=7),
        
        # CSRF Configuration
        WTF_CSRF_ENABLED=True,
        WTF_CSRF_SECRET_KEY=os.getenv('CSRF_SECRET_KEY', 'dev-csrf-secret'),
        
        # Cache Configuration
        CACHE_TYPE='simple',
        CACHE_DEFAULT_TIMEOUT=300,
        
        # File Upload Configuration
        MAX_CONTENT_LENGTH=16 * 1024 * 1024  # 16MB max file size
    )

    # Initialize extensions with app
    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)
    cache.init_app(app)
    csrf.init_app(app)
    CORS(app, supports_credentials=True)

    with app.app_context():
        # Import models
        from app.models import user, account, transaction, budget, bill
        
        # Import and register blueprints
        from app.routes import (
            home, auth, dashboard, accounts,
            transactions, users, investments,
            budgets, bills
        )

        app.register_blueprint(home.home_bp)
        app.register_blueprint(auth.auth_bp)
        app.register_blueprint(dashboard.dashboard_bp)
        app.register_blueprint(accounts.accounts_bp)
        app.register_blueprint(transactions.transactions_bp)
        app.register_blueprint(users.users_bp)
        app.register_blueprint(investments.investments_bp)
        app.register_blueprint(budgets.budgets_bp)
        app.register_blueprint(bills.bills_bp)

        # Create database tables
        db.create_all()
        logger.info("Database tables created successfully!")

    return app


# JWT error handlers
@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return redirect(url_for('auth.login_page'))

@jwt.invalid_token_loader
def invalid_token_callback(error):
    return redirect(url_for('auth.login_page'))

@jwt.unauthorized_loader
def missing_token_callback(error):
    return redirect(url_for('auth.login_page'))

# Authentication blueprint routes and forms
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, make_response, flash
from flask_jwt_extended import create_access_token, verify_jwt_in_request, get_jwt_identity
from werkzeug.security import check_password_hash
from app.models.user import User
from datetime import timedelta
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired, Email, Length, ValidationError

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=50)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered.')

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('Username already taken.')

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/register', methods=['GET'])
def register_page():
    try:
        verify_jwt_in_request()
        return redirect(url_for('dashboard.index'))
    except:
        form = RegistrationForm()
        return render_template('auth/register.html', form=form)

@auth_bp.route('/login', methods=['GET'], endpoint='login_page')
def login_page():
    form = LoginForm()
    
    if form.validate_on_submit():
        try:
            user = User.query.filter_by(email=form.email.data).first()
            
            if user and check_password_hash(user.password_hash, form.password.data):
                access_token = create_access_token(
                    identity=user.id,
                    expires_delta=timedelta(hours=1)
                )
                
                response = make_response(redirect(url_for('dashboard.index')))
                response.set_cookie(
                    'access_token_cookie',
                    access_token,
                    httponly=True,
                    secure=False,
                    samesite='Lax',
                    max_age=3600
                )
                
                flash('Login successful!', 'success')
                return response
            
            flash('Invalid email or password', 'error')
            return redirect(url_for('auth.login_page'))

        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            flash('An error occurred during login', 'error')
            return redirect(url_for('auth.login_page'))
    
    for field, errors in form.errors.items():
        for error in errors:
            flash(f"{field.title()}: {error}", 'error')
    
    return render_template('auth/login.html', form=form)

@auth_bp.route('/register', methods=['POST'])
def register():
    form = RegistrationForm()
    
    if form.validate_on_submit():
        try:
            user = User(
                username=form.username.data,
                email=form.email.data,
                password=form.password.data
            )
            
            db.session.add(user)
            db.session.commit()

            logger.info(f"New user registered: {form.email.data}")
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('auth.login_page'))

        except Exception as e:
            logger.error(f"Register error: {str(e)}")
            db.session.rollback()
            flash('An error occurred during registration', 'error')
            return render_template('auth/register.html', form=form)
    
    for field, errors in form.errors.items():
        for error in errors:
            flash(f"{field.title()}: {error}", 'error')
    
    return render_template('auth/register.html', form=form)

@auth_bp.route('/logout', methods=['POST', 'GET'])
def logout():
    try:
        response = make_response(redirect(url_for('auth.login_page')))
        response.delete_cookie('access_token_cookie')
        flash('Successfully logged out', 'success')
        return response
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        flash('Error during logout', 'error')
        return redirect(url_for('auth.login_page'))

@auth_bp.route('/verify-token', methods=['POST'])
def verify_token():
    try:
        verify_jwt_in_request()
        current_user_id = get_jwt_identity()
        
        user = User.query.get(current_user_id)
        if not user:
            return jsonify({
                'status': 'error',
                'message': 'Invalid token'
            }), 401
            
        return jsonify({
            'status': 'success',
            'data': {
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'username': user.username
                }
            }
        }), 200
            
    except Exception as e:
        logger.error(f"Token verification error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Invalid token'
        }), 401

# Error handlers untuk auth blueprint
@auth_bp.errorhandler(401)
def unauthorized_error(error):
    return jsonify({
        'status': 'error',
        'message': 'Unauthorized access'
    }), 401

@auth_bp.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({
        'status': 'error',
        'message': 'Internal server error'
    }), 500