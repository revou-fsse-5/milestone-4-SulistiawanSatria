from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.transaction_category import TransactionCategory
from app.extensions import db
import logging

category_bp = Blueprint('categories', __name__)

@category_bp.route('/categories')
@jwt_required()
def list_categories():
    categories = TransactionCategory.query.all()
    return render_template('dashboard/categories/index.html', categories=categories)

@category_bp.route('/categories/new', methods=['GET', 'POST'])
@jwt_required()
def create_category():
    if request.method == 'POST':
        try:
            category = TransactionCategory(
                name=request.form['name'],
                description=request.form.get('description', ''),
                icon=request.form.get('icon', 'default-icon')
            )
            db.session.add(category)
            db.session.commit()
            flash('Category created successfully', 'success')
            return redirect(url_for('categories.list_categories'))
        except Exception as e:
            db.session.rollback()
            flash('Error creating category', 'error')
            return redirect(url_for('categories.create_category'))
    
    return render_template('dashboard/categories/create.html')

@category_bp.route('/categories/<int:id>', methods=['PUT'])
@jwt_required()
def update_category(id):
    category = TransactionCategory.query.get_or_404(id)
    data = request.get_json()
    
    try:
        category.name = data.get('name', category.name)
        category.description = data.get('description', category.description)
        category.icon = data.get('icon', category.icon)
        db.session.commit()
        return jsonify({'message': 'Category updated successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@category_bp.route('/categories/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_category(id):
    category = TransactionCategory.query.get_or_404(id)
    try:
        db.session.delete(category)
        db.session.commit()
        return jsonify({'message': 'Category deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@category_bp.route('/categories/default', methods=['POST'])
@jwt_required()
def create_default_categories():
    try:
        default_categories = TransactionCategory.get_default_categories()
        for cat_name in default_categories:
            if not TransactionCategory.query.filter_by(name=cat_name).first():
                category = TransactionCategory(name=cat_name)
                db.session.add(category)
        db.session.commit()
        return jsonify({'message': 'Default categories created successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400
