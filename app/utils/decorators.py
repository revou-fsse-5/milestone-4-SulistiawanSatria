from functools import wraps
from flask import redirect, url_for, request, jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from app.models.account import Account
import logging

logger = logging.getLogger(__name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            verify_jwt_in_request()
            current_user_id = get_jwt_identity()
            if not current_user_id:
                return redirect(url_for('auth.login_page'))
            return f(*args, **kwargs)
        except:
            if request.is_json:
                return jsonify({
                    'status': 'error',
                    'message': 'Authentication required'
                }), 401
            return redirect(url_for('auth.login_page'))
    return decorated_function


def check_account_ownership(f):
    @wraps(f)
    def decorated_function(account_id, *args, **kwargs):
        try:
            verify_jwt_in_request()
            current_user_id = get_jwt_identity()
            account = Account.query.filter_by(id=account_id, user_id=current_user_id).first()
            
            if not account:
                if request.is_json:
                    return jsonify({
                        'status': 'error',
                        'message': 'Account not found or access denied'
                    }), 403
                return redirect(url_for('dashboard.index'))
                
            return f(account_id, *args, **kwargs)
        except Exception as e:
            logger.error(f"Account ownership check failed: {str(e)}")
            if request.is_json:
                return jsonify({
                    'status': 'error',
                    'message': 'Authentication required'
                }), 401
            return redirect(url_for('auth.login_page'))
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            verify_jwt_in_request()
            current_user_id = get_jwt_identity()
            from app.models.user import User
            
            user = User.query.get(current_user_id)
            if not user or not user.is_admin:
                if request.is_json:
                    return jsonify({
                        'status': 'error',
                        'message': 'Admin access required'
                    }), 403
                return redirect(url_for('dashboard.index'))
                
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"Admin check failed: {str(e)}")
            if request.is_json:
                return jsonify({
                    'status': 'error',
                    'message': 'Authentication required'
                }), 401
            return redirect(url_for('auth.login_page'))
    return decorated_function