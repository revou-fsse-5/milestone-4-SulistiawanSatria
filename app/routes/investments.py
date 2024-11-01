from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.investment import Investment
from app.models.user import User
from app.extensions import db

investments_bp = Blueprint('investments', __name__, url_prefix='/investments')

@investments_bp.route('', methods=['POST'])
@jwt_required()
def create_investment():
    # Logika untuk menambah investasi baru
    pass

@investments_bp.route('', methods=['GET'])
@jwt_required()
def get_investments():
    # Logika untuk mendapatkan daftar investasi pengguna
    pass

@investments_bp.route('/<int:id>', methods=['GET'])
@jwt_required()
def get_investment(id):
    # Logika untuk mendapatkan detail investasi spesifik
    pass

@investments_bp.route('/<int:id>', methods=['PUT'])
@jwt_required()
def update_investment(id):
    # Logika untuk memperbarui investasi
    pass

@investments_bp.route('/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_investment(id):
    # Logika untuk menghapus investasi
    pass
