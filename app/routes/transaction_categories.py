from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.transaction_category import TransactionCategory
from app.extensions import db
import logging

# Ubah prefix sesuai requirement
category_bp = Blueprint('transaction_categories', __name__, url_prefix='/transactions')
logger = logging.getLogger(__name__)

# Endpoint utama untuk mendapatkan kategori transaksi
@category_bp.route('/categories', methods=['GET'])
@jwt_required()
def get_categories():
    """Get all transaction categories"""
    try:
        categories = TransactionCategory.query.all()
        return jsonify({
            "status": "success",
            "categories": [{
                "id": category.id,
                "name": category.name,
                "description": category.description,
                "icon": category.icon
            } for category in categories]
        }), 200
    except Exception as e:
        logger.error(f"Error fetching categories: {str(e)}")
        return jsonify({
            "status": "error",
            "message": "Failed to fetch categories"
        }), 500

# Endpoint untuk membuat kategori baru
@category_bp.route('/categories', methods=['POST'])
@jwt_required()
def create_category():
    """Create a new transaction category"""
    try:
        data = request.get_json()
        
        # Validasi input
        if not data.get('name'):
            return jsonify({
                "status": "error",
                "message": "Category name is required"
            }), 400

        # Cek duplikasi
        existing_category = TransactionCategory.query.filter_by(name=data['name']).first()
        if existing_category:
            return jsonify({
                "status": "error",
                "message": "Category with this name already exists"
            }), 400

        # Buat kategori baru
        category = TransactionCategory(
            name=data['name'],
            description=data.get('description', ''),
            icon=data.get('icon', 'default-icon')
        )
        
        db.session.add(category)
        db.session.commit()

        return jsonify({
            "status": "success",
            "message": "Category created successfully",
            "category": {
                "id": category.id,
                "name": category.name,
                "description": category.description,
                "icon": category.icon
            }
        }), 201
    except Exception as e:
        logger.error(f"Error creating category: {str(e)}")
        db.session.rollback()
        return jsonify({
            "status": "error",
            "message": "Failed to create category"
        }), 500

# Endpoint untuk mengupdate kategori
@category_bp.route('/categories/<int:id>', methods=['PUT'])
@jwt_required()
def update_category(id):
    """Update an existing transaction category"""
    try:
        category = TransactionCategory.query.get(id)
        if not category:
            return jsonify({
                "status": "error",
                "message": "Category not found"
            }), 404

        data = request.get_json()
        
        # Update fields if provided
        if 'name' in data:
            # Cek duplikasi nama jika nama diubah
            existing = TransactionCategory.query.filter_by(name=data['name']).first()
            if existing and existing.id != id:
                return jsonify({
                    "status": "error",
                    "message": "Category with this name already exists"
                }), 400
            category.name = data['name']
            
        if 'description' in data:
            category.description = data['description']
        if 'icon' in data:
            category.icon = data['icon']

        db.session.commit()

        return jsonify({
            "status": "success",
            "message": "Category updated successfully",
            "category": {
                "id": category.id,
                "name": category.name,
                "description": category.description,
                "icon": category.icon
            }
        }), 200
    except Exception as e:
        logger.error(f"Error updating category: {str(e)}")
        db.session.rollback()
        return jsonify({
            "status": "error",
            "message": "Failed to update category"
        }), 500

# Endpoint untuk menghapus kategori
@category_bp.route('/categories/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_category(id):
    """Delete a transaction category"""
    try:
        category = TransactionCategory.query.get(id)
        if not category:
            return jsonify({
                "status": "error",
                "message": "Category not found"
            }), 404

        db.session.delete(category)
        db.session.commit()

        return jsonify({
            "status": "success",
            "message": "Category deleted successfully"
        }), 200
    except Exception as e:
        logger.error(f"Error deleting category: {str(e)}")
        db.session.rollback()
        return jsonify({
            "status": "error",
            "message": "Failed to delete category"
        }), 500

# Endpoint untuk membuat kategori default
@category_bp.route('/categories/default', methods=['POST'])
@jwt_required()
def create_default_categories():
    """Create default transaction categories"""
    try:
        default_categories = TransactionCategory.get_default_categories()
        created_categories = []

        for cat_name in default_categories:
            if not TransactionCategory.query.filter_by(name=cat_name).first():
                category = TransactionCategory(name=cat_name)
                db.session.add(category)
                created_categories.append(cat_name)

        if created_categories:
            db.session.commit()
            return jsonify({
                "status": "success",
                "message": "Default categories created successfully",
                "categories": created_categories
            }), 201
        else:
            return jsonify({
                "status": "success",
                "message": "Default categories already exist"
            }), 200
    except Exception as e:
        logger.error(f"Error creating default categories: {str(e)}")
        db.session.rollback()
        return jsonify({
            "status": "error",
            "message": "Failed to create default categories"
        }), 500