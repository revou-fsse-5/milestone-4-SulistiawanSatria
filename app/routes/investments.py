from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.investment import Investment
from app.models.user import User
from app.extensions import db
import logging

investments_bp = Blueprint('investments', __name__, url_prefix='/investments')
logger = logging.getLogger(__name__)

@investments_bp.route('', methods=['POST'])
@jwt_required()
def create_investment():
    try:
        data = request.get_json()
        current_user_id = get_jwt_identity()

        # Validasi input
        required_fields = ['investment_type', 'amount']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"{field} is required"}), 400

        investment = Investment(
            user_id=current_user_id,
            investment_type=data['investment_type'],
            amount=data['amount']
        )

        db.session.add(investment)
        db.session.commit()

        return jsonify({
            "message": "Investment created successfully",
            "investment": {
                "id": investment.id,
                "type": investment.investment_type,
                "amount": float(investment.amount),
                "status": investment.status
            }
        }), 201

    except Exception as e:
        logger.error(f"Error creating investment: {str(e)}")
        db.session.rollback()
        return jsonify({"error": "Internal server error"}), 500

@investments_bp.route('', methods=['GET'])
@jwt_required()
def get_investments():
    try:
        current_user_id = get_jwt_identity()
        investments = Investment.query.filter_by(user_id=current_user_id).all()

        return jsonify({
            "investments": [{
                "id": inv.id,
                "type": inv.investment_type,
                "amount": float(inv.amount),
                "status": inv.status,
                "created_at": inv.created_at.isoformat()
            } for inv in investments]
        }), 200

    except Exception as e:
        logger.error(f"Error fetching investments: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@investments_bp.route('/<int:id>', methods=['PUT'])
@jwt_required()
def update_investment(id):
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        investment = Investment.query.filter_by(
            id=id, 
            user_id=current_user_id
        ).first()
        
        if not investment:
            return jsonify({"error": "Investment not found"}), 404

        if 'investment_type' in data:
            investment.investment_type = data['investment_type']
        if 'amount' in data:
            investment.amount = data['amount']
        if 'status' in data:
            investment.status = data['status']

        db.session.commit()

        return jsonify({
            "message": "Investment updated successfully",
            "investment": {
                "id": investment.id,
                "type": investment.investment_type,
                "amount": float(investment.amount),
                "status": investment.status
            }
        }), 200

    except Exception as e:
        logger.error(f"Error updating investment: {str(e)}")
        db.session.rollback()
        return jsonify({"error": "Internal server error"}), 500

@investments_bp.route('/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_investment(id):
    try:
        current_user_id = get_jwt_identity()
        investment = Investment.query.filter_by(
            id=id, 
            user_id=current_user_id
        ).first()
        
        if not investment:
            return jsonify({"error": "Investment not found"}), 404

        db.session.delete(investment)
        db.session.commit()

        return jsonify({"message": "Investment deleted successfully"}), 200

    except Exception as e:
        logger.error(f"Error deleting investment: {str(e)}")
        db.session.rollback()
        return jsonify({"error": "Internal server error"}), 500