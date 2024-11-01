from flask import Blueprint, request, jsonify, render_template, redirect, url_for, make_response, flash
from flask_jwt_extended import create_access_token, verify_jwt_in_request, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from app.models.user import User
from datetime import timedelta
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired, Email, Length, ValidationError
from app import db
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
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered.')

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('Username already taken.')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register_page():
    form = RegistrationForm()
    
    if request.method == 'POST' and form.validate_on_submit():
        try:
            user = User(
                username=form.username.data,
                email=form.email.data,
                password=form.password.data
            )
            db.session.add(user)
            db.session.commit()
            
            flash('Registration successful!', 'success')
            return redirect(url_for('auth.login_page'))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Register error: {str(e)}")
            flash('Registration failed', 'error')
            
    return render_template('auth/register.html', form=form)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login_page():
    form = LoginForm()
    
    if request.method == 'POST' and form.validate_on_submit():
        try:
            user = User.query.filter_by(email=form.email.data).first()
            
            if user and user.check_password(form.password.data):
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
            
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            flash('Login failed', 'error')
            
    return render_template('auth/login.html', form=form)

@auth_bp.route('/logout')
def logout():
    response = make_response(redirect(url_for('auth.login_page')))
    response.delete_cookie('access_token_cookie')
    flash('Successfully logged out', 'success')
    return response

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