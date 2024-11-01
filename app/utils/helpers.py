# app/utils/helpers.py
from werkzeug.security import generate_password_hash, check_password_hash
import re

def hash_password(password):
    return generate_password_hash(password)

def check_password(hashed_password, password):
    return check_password_hash(hashed_password, password)

def validate_email(email):
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """
    Password harus minimal 8 karakter dan mengandung huruf & angka
    """
    if len(password) < 8:
        return False
    if not re.search(r'[A-Za-z]', password) or not re.search(r'\d', password):
        return False
    return True