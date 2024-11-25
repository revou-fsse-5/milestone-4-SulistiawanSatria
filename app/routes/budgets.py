from flask import Blueprint, request, jsonify, render_template, redirect, url_for
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.budget import Budget
from app.extensions import db
from datetime import datetime
import logging
from flask_wtf import FlaskForm
from wtforms import StringField, DecimalField, DateField
from wtforms.validators import DataRequired

class BudgetForm(FlaskForm):
    name = StringField('Budget Name', validators=[DataRequired()])
    amount = DecimalField('Amount', validators=[DataRequired()])
    start_date = DateField('Start Date', validators=[DataRequired()])
    end_date = DateField('End Date', validators=[DataRequired()])

budgets_bp = Blueprint('budgets', __name__, url_prefix='/budgets')
logger = logging.getLogger(__name__)

@budgets_bp.route('/create', methods=['POST'])
@jwt_required()
def create_budget_page():
    form = BudgetForm()
    if form.validate_on_submit():
        budget = Budget(
            user_id=get_jwt_identity(),
            name=form.name.data,
            amount=form.amount.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data
        )
        db.session.add(budget)
        db.session.commit()
        return jsonify({budget: budget.name}), 200
        return redirect(url_for('budgets.list_budgets'))
    
    return jsonify({"error": "failed to create budget - form not filled"}), 400
    return render_template('budgets/create.html', form=form)

@budgets_bp.route('/', methods=['GET'])
@jwt_required()
def list_budgets():
    budgets = Budget.query.filter_by(user_id=get_jwt_identity()).all()
    budgets = [
        {
            "id": budget.id,
            "name": budget.name,
            "start_date": budget.start_date,
            "end_date": budget.end_date,
            "amount": float(budget.amount)
        } for budget in budgets 
    ]
    return jsonify({"budgets": budgets}), 200
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