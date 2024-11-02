from flask import Blueprint, render_template
from flask_jwt_extended import verify_jwt_in_request

home_bp = Blueprint('home', __name__)

@home_bp.route('/')
@home_bp.route('/home')
def index():
    is_authenticated = False
    try:
        verify_jwt_in_request()
        is_authenticated = True
    except:
        pass
    return render_template('base.html', is_authenticated=is_authenticated)
