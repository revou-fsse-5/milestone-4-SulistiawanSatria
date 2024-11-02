from flask import Blueprint, request, jsonify, render_template, redirect, url_for, make_response, flash, current_app
from flask_jwt_extended import create_access_token, verify_jwt_in_request, get_jwt_identity
from werkzeug.security import check_password_hash
from app.models.user import User
from app.extensions import db
from datetime import timedelta
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired, Email, Length, ValidationError
import logging

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
        # Gunakan try-except untuk menangani potential database errors
        try:
            user = User.query.filter_by(email=field.data).first()
            if user:
                raise ValidationError('Email already registered.')
        except Exception as e:
            logger.error(f"Database error during email validation: {str(e)}")
            raise ValidationError('Error checking email. Please try again.')

    def validate_username(self, field):
        try:
            user = User.query.filter_by(username=field.data).first()
            if user:
                raise ValidationError('Username already taken.')
        except Exception as e:
            logger.error(f"Database error during username validation: {str(e)}")
            raise ValidationError('Error checking username. Please try again.')

@auth_bp.route('/register', methods=['GET'])
def register_page():
    # Pisahkan GET request untuk menampilkan form
    try:
        verify_jwt_in_request()
        return redirect(url_for('dashboard.index'))
    except:
        form = RegistrationForm()
        return render_template('auth/register.html', form=form)

@auth_bp.route('/register', methods=['POST'])
def register():
    form = RegistrationForm()
    
    try:
        if form.validate_on_submit():
            # Bungkus operasi database dalam try-except
            try:
                user = User(
                    username=form.username.data,
                    email=form.email.data
                )
                user.set_password(form.password.data)
                
                db.session.add(user)
                db.session.commit()
                
                logger.info(f"New user registered: {user.email}")
                flash('Registration successful! Please login.', 'success')
                return redirect(url_for('auth.login_page'))
                
            except Exception as e:
                db.session.rollback()
                logger.error(f"Database error during registration: {str(e)}")
                flash('An error occurred during registration. Please try again.', 'error')
                
        # Jika validasi gagal, tampilkan error
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{field.title()}: {error}", 'error')
                
    except Exception as e:
        logger.error(f"Error during registration process: {str(e)}")
        flash('An unexpected error occurred. Please try again.', 'error')
    
    return render_template('auth/register.html', form=form)

@auth_bp.route('/login', methods=['GET'])
def login_page():
    # Pisahkan GET request untuk menampilkan form
    form = LoginForm()
    return render_template('auth/login.html', form=form)

@auth_bp.route('/login', methods=['POST'])
def login():
    form = LoginForm()
    
    try:
        if form.validate_on_submit():
            try:
                user = User.query.filter_by(email=form.email.data).first()
                
                if user and user.check_password(form.password.data):
                    access_token = create_access_token(
                        identity=user.id,
                        fresh=True,
                        expires_delta=timedelta(hours=1)
                    )
                    
                    response = make_response(redirect(url_for('dashboard.index')))
                    response.set_cookie(
                        'access_token_cookie',
                        value=access_token,
                        max_age=3600,
                        httponly=True,
                        secure=False,
                        samesite='Lax'
                    )
                    
                    logger.info(f"User logged in: {user.email}")
                    flash('Login successful!', 'success')
                    return response
                
                flash('Invalid email or password', 'error')
                
            except Exception as e:
                logger.error(f"Database error during login: {str(e)}")
                flash('An error occurred during login. Please try again.', 'error')
                
        # Jika validasi gagal, tampilkan error
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{field.title()}: {error}", 'error')
                
    except Exception as e:
        logger.error(f"Error during login process: {str(e)}")
        flash('An unexpected error occurred. Please try again.', 'error')
    
    return render_template('auth/login.html', form=form)

@auth_bp.route('/logout', methods=['GET', 'POST'])
def logout():
    try:
        response = make_response(redirect(url_for('auth.login_page')))
        response.delete_cookie('access_token_cookie')
        flash('Successfully logged out', 'success')
        return response
    except Exception as e:
        logger.error(f"Error during logout: {str(e)}")
        flash('An error occurred during logout', 'error')
        return redirect(url_for('auth.login_page'))

@auth_bp.route('/verify-token', methods=['POST'])
def verify_token():
    try:
        verify_jwt_in_request()
        current_user_id = get_jwt_identity()
        
        user = User.query.get(current_user_id)
        if not user:
            logger.warning(f"Invalid token attempt for user ID: {current_user_id}")
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

# Error handlers
@auth_bp.errorhandler(401)
def unauthorized_error(error):
    return jsonify({
        'status': 'error',
        'message': 'Unauthorized access'
    }), 401

@auth_bp.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({
        'status': 'error',
        'message': 'Internal server error'
    }), 500