from flask import Blueprint, request, jsonify, render_template, redirect, url_for, make_response, flash, current_app
from flask_jwt_extended import create_access_token, verify_jwt_in_request, get_jwt_identity
from werkzeug.security import check_password_hash
from app.models.user import User
from datetime import timedelta
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired, Email, Length, ValidationError
from app import db
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

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

@auth_bp.route('/login', methods=['GET', 'POST'])
def login_page():
    form = LoginForm()
    
    if request.method == 'GET':
        return render_template('auth/login.html', form=form)
    
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

    # Tambahkan return statement di sini
    return render_template('auth/login.html', form=form)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register_page():
    if request.method == 'GET':
        try:
            verify_jwt_in_request()
            return redirect(url_for('dashboard.index'))
        except:
            form = RegistrationForm()
            return render_template('auth/register.html', form=form)

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
        
        with current_app.app_context():
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