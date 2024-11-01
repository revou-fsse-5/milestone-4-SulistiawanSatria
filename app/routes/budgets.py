from flask import Blueprint, request, jsonify, render_template
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.budget import Budget
from app.extensions import db
from datetime import datetime
import logging

budgets_bp = Blueprint('budgets', __name__, url_prefix='/budgets')
logger = logging.getLogger(__name__)

@budgets_bp.route('/create', methods=['GET'])
@jwt_required()
def create_budget_page():
    return render_template('budgets/create.html')

@budgets_bp.route('/', methods=['GET'])
@jwt_required()
def list_budgets():
    budgets = Budget.query.filter_by(user_id=get_jwt_identity()).all()
    return render_template('budgets/list.html', budgets=budgets)

# API Endpoints
@budgets_bp.route('/api/create', methods=['POST'])
@jwt_required()
def create_budget():
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()

        required_fields = ['name', 'amount', 'start_date', 'end_date']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"{field} is required"}), 400

        budget = Budget(
            user_id=current_user_id,
            name=data['name'],
            amount=data['amount'],
            start_date=datetime.strptime(data['start_date'], '%Y-%m-%d').date(),
            end_date=datetime.strptime(data['end_date'], '%Y-%m-%d').date()
        )

        db.session.add(budget)
        db.session.commit()

        return jsonify({
            "message": "Budget created successfully",
            "budget": {
                "id": budget.id,
                "name": budget.name,
                "amount": float(budget.amount),
                "start_date": budget.start_date.isoformat(),
                "end_date": budget.end_date.isoformat()
            }
        }), 201

    except Exception as e:
        logger.error(f"Error creating budget: {str(e)}")
        db.session.rollback()
        return jsonify({"error": "Internal server error"}), 500

@budgets_bp.route('/', methods=['GET'])
@jwt_required()
def get_budgets():
    try:
        current_user_id = get_jwt_identity()
        budgets = Budget.query.filter_by(user_id=current_user_id).all()

        return jsonify({
            "budgets": [{
                "id": budget.id,
                "name": budget.name,
                "amount": float(budget.amount),
                "start_date": budget.start_date.isoformat(),
                "end_date": budget.end_date.isoformat(),
                "created_at": budget.created_at.isoformat()
            } for budget in budgets]
        }), 200

    except Exception as e:
        logger.error(f"Error fetching budgets: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@budgets_bp.route('/<int:budget_id>', methods=['PUT'])
@jwt_required()
def update_budget(budget_id):
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        budget = Budget.query.filter_by(id=budget_id, user_id=current_user_id).first()
        if not budget:
            return jsonify({"error": "Budget not found"}), 404

        # Update fields
        if 'name' in data:
            budget.name = data['name']
        if 'amount' in data:
            budget.amount = data['amount']
        if 'start_date' in data:
            budget.start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
        if 'end_date' in data:
            budget.end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()

        db.session.commit()

        return jsonify({
            "message": "Budget updated successfully",
            "budget": {
                "id": budget.id,
                "name": budget.name,
                "amount": float(budget.amount),
                "start_date": budget.start_date.isoformat(),
                "end_date": budget.end_date.isoformat()
            }
        }), 200

    except Exception as e:
        logger.error(f"Error updating budget: {str(e)}")
        db.session.rollback()
        return jsonify({"error": "Internal server error"}), 500

@budgets_bp.route('/<int:budget_id>', methods=['DELETE'])
@jwt_required()
def delete_budget(budget_id):
    try:
        current_user_id = get_jwt_identity()
        budget = Budget.query.filter_by(id=budget_id, user_id=current_user_id).first()
        
        if not budget:
            return jsonify({"error": "Budget not found"}), 404

        db.session.delete(budget)
        db.session.commit()

        return jsonify({"message": "Budget deleted successfully"}), 200

    except Exception as e:
        logger.error(f"Error deleting budget: {str(e)}")
        db.session.rollback()
        return jsonify({"error": "Internal server error"}), 500