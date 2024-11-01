from flask import Blueprint, request, jsonify, render_template
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.bill import Bill
from app.models.account import Account
from app.extensions import db
from datetime import datetime
import logging

bills_bp = Blueprint('bills', __name__, url_prefix='/bills')
logger = logging.getLogger(__name__)

@bills_bp.route('/create', methods=['GET'])
@jwt_required()
def create_bill_page():
    accounts = Account.query.filter_by(user_id=get_jwt_identity()).all()
    return render_template('bills/create.html', accounts=accounts)

@bills_bp.route('/', methods=['GET'])
@jwt_required()
def list_bills():
    bills = Bill.query.filter_by(user_id=get_jwt_identity()).all()
    return render_template('bills/list.html', bills=bills)

# API Endpoints
@bills_bp.route('/api/create', methods=['POST'])
@jwt_required()
def create_bill():
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()

        required_fields = ['biller_name', 'amount', 'due_date', 'account_id']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"{field} is required"}), 400

        account = Account.query.filter_by(
            id=data['account_id'],
            user_id=current_user_id
        ).first()
        
        if not account:
            return jsonify({"error": "Account not found"}), 404

        bill = Bill(
            user_id=current_user_id,
            biller_name=data['biller_name'],
            amount=data['amount'],
            due_date=datetime.strptime(data['due_date'], '%Y-%m-%d').date(),
            account_id=data['account_id']
        )

        db.session.add(bill)
        db.session.commit()

        return jsonify({
            "message": "Bill scheduled successfully",
            "bill": {
                "id": bill.id,
                "biller_name": bill.biller_name,
                "amount": float(bill.amount),
                "due_date": bill.due_date.isoformat(),
                "status": bill.status
            }
        }), 201

    except Exception as e:
        logger.error(f"Error scheduling bill: {str(e)}")
        db.session.rollback()
        return jsonify({"error": "Internal server error"}), 500

@bills_bp.route('/', methods=['GET'])
@jwt_required()
def get_bills():
    try:
        current_user_id = get_jwt_identity()
        bills = Bill.query.filter_by(user_id=current_user_id).all()

        return jsonify({
            "bills": [{
                "id": bill.id,
                "biller_name": bill.biller_name,
                "amount": float(bill.amount),
                "due_date": bill.due_date.isoformat(),
                "status": bill.status,
                "account": {
                    "id": bill.account.id,
                    "account_number": bill.account.account_number
                }
            } for bill in bills]
        }), 200

    except Exception as e:
        logger.error(f"Error fetching bills: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@bills_bp.route('/<int:bill_id>', methods=['PUT'])
@jwt_required()
def update_bill(bill_id):
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        bill = Bill.query.filter_by(id=bill_id, user_id=current_user_id).first()
        if not bill:
            return jsonify({"error": "Bill not found"}), 404

        # Update fields
        if 'biller_name' in data:
            bill.biller_name = data['biller_name']
        if 'amount' in data:
            bill.amount = data['amount']
        if 'due_date' in data:
            bill.due_date = datetime.strptime(data['due_date'], '%Y-%m-%d').date()
        if 'status' in data:
            bill.status = data['status']
        if 'account_id' in data:
            # Validate new account ownership
            account = Account.query.filter_by(
                id=data['account_id'],
                user_id=current_user_id
            ).first()
            if not account:
                return jsonify({"error": "Account not found"}), 404
            bill.account_id = data['account_id']

        db.session.commit()

        return jsonify({
            "message": "Bill updated successfully",
            "bill": {
                "id": bill.id,
                "biller_name": bill.biller_name,
                "amount": float(bill.amount),
                "due_date": bill.due_date.isoformat(),
                "status": bill.status
            }
        }), 200

    except Exception as e:
        logger.error(f"Error updating bill: {str(e)}")
        db.session.rollback()
        return jsonify({"error": "Internal server error"}), 500

@bills_bp.route('/<int:bill_id>', methods=['DELETE'])
@jwt_required()
def delete_bill(bill_id):
    try:
        current_user_id = get_jwt_identity()
        bill = Bill.query.filter_by(id=bill_id, user_id=current_user_id).first()
        
        if not bill:
            return jsonify({"error": "Bill not found"}), 404

        db.session.delete(bill)
        db.session.commit()

        return jsonify({"message": "Bill deleted successfully"}), 200

    except Exception as e:
        logger.error(f"Error deleting bill: {str(e)}")
        db.session.rollback()
        return jsonify({"error": "Internal server error"}), 500