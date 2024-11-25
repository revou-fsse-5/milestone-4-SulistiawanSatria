from flask import Blueprint, render_template, redirect, url_for
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from app.models.user import User

home_bp = Blueprint('home', __name__)

@home_bp.route('/')
@home_bp.route('/home')
def index():
    is_authenticated = False
    user = None
    
    try:
        verify_jwt_in_request()
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        if user:
            is_authenticated = True
            return redirect(url_for('dashboard.index'))
    except:
        pass

    return render_template('home.html', 
                         is_authenticated=is_authenticated,
                         user=user)

@home_bp.errorhandler(404)
def not_found_error(error):
    return render_template('error/404.html'), 404

@home_bp.errorhandler(500) 
def internal_error(error):
    return render_template('error/500.html'), 500
