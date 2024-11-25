from flask import Blueprint, request, jsonify, render_template, redirect, url_for
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.bill import Bill
from app.models.account import Account
from app.extensions import db
from datetime import datetime
import logging
from flask_wtf import FlaskForm
from wtforms import StringField, DecimalField, DateField, SelectField
from wtforms.validators import DataRequired

bills_bp = Blueprint('bills', __name__, url_prefix='/bills')
logger = logging.getLogger(__name__)

class BillForm(FlaskForm):
    biller_name = StringField('Biller Name', validators=[DataRequired()])
    amount = DecimalField('Amount', validators=[DataRequired()])
    due_date = DateField('Due Date', validators=[DataRequired()])
    account_id = SelectField('Account', coerce=int, validators=[DataRequired()])

@bills_bp.route('/create', methods=['GET', 'POST'])
@jwt_required()
def create_bill_page():  # Gunakan nama ini konsisten
    form = BillForm()
    accounts = Account.query.filter_by(user_id=get_jwt_identity()).all()
    form.account_id.choices = [(a.id, f"{a.account_type} (*{a.account_number[-4:]})") for a in accounts]
    
    if form.validate_on_submit():
        bill = Bill(
            user_id=get_jwt_identity(),
            biller_name=form.biller_name.data,
            amount=form.amount.data,
            due_date=form.due_date.data,
            account_id=form.account_id.data
        )
        db.session.add(bill)
        db.session.commit()
        return redirect(url_for('bills.list_bills'))
        
    return render_template('bills/create.html', form=form, accounts=accounts)

@bills_bp.route('/', methods=['GET'])
@jwt_required()
def list_bills():
    bills = Bill.query.filter_by(user_id=get_jwt_identity()).all()
    bills = [
        {
            "id": b.id,
            "u_id": b.user_id,
            "biller_name": b.biller_name,
            "amount": float(b.amount),
            "due_date": b.due_date,
            "accpunt_id": b.account_id,
            "status": b.status,
            "desc": b.description
        }
        for b in bills
    ]
    # return render_template('bills/list.html', bills=bills)
    return jsonify({"bills": bills, "message": "success"}), 200

# API Endpoints
@bills_bp.route('/api/create', methods=['POST'])
@jwt_required()
def create_bill_api():
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