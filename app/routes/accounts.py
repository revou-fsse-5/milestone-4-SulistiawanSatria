from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.account import Account
from app.models.transaction import Transaction
from app.models.user import User
from app.forms.account import AccountForm
from app.extensions import db
from datetime import datetime, timedelta
import logging
import random
import string

accounts_bp = Blueprint('accounts', __name__, url_prefix='/accounts')
logger = logging.getLogger(__name__)

def generate_account_number():
    """Generate unique account number"""
    return ''.join(random.choices(string.digits, k=10))

def validate_account_ownership(account_id, user_id):
    """Validate account ownership"""
    account = Account.query.filter_by(id=account_id, user_id=user_id).first()
    if not account:
        return None
    return account

@accounts_bp.route('/', methods=['GET'])
@jwt_required()
def get_accounts():
    try:
        current_user_id = get_jwt_identity()
        accounts = Account.query.filter_by(user_id=current_user_id).all()

        # Check if request wants JSON response
        if request.headers.get('Accept') == 'application/json':
            return jsonify({
                "accounts": [{
                    "id": account.id,
                    "account_number": account.account_number,
                    "account_type": account.account_type,
                    "balance": float(account.balance),
                    "created_at": account.created_at.isoformat(),
                    "updated_at": account.updated_at.isoformat()
                } for account in accounts]
            }), 200
        
        # Return HTML template
        return render_template('accounts/list.html', accounts=accounts)

    except Exception as e:
        logger.error(f"Error fetching accounts: {str(e)}")
        if request.headers.get('Accept') == 'application/json':
            return jsonify({"error": "Internal server error"}), 500
        flash('Error fetching accounts', 'error')
        return render_template('accounts/list.html', accounts=[])

@accounts_bp.route('/create', methods=['GET'])
@jwt_required()
def create_account_page():
    form = AccountForm()
    return render_template('accounts/create.html', form=form)


@accounts_bp.route('/', methods=['POST'])
@jwt_required()
def create_account():
    try:
        current_user_id = get_jwt_identity()

        # Handle form submission
        if request.content_type == 'application/x-www-form-urlencoded':
            form = AccountForm()
            if form.validate_on_submit():
                account_number = generate_account_number()
                while Account.query.filter_by(account_number=account_number).first():
                    account_number = generate_account_number()

                account = Account(
                    user_id=current_user_id,
                    account_type=form.account_type.data,
                    account_number=account_number,
                    balance=form.initial_balance.data,
                    currency=form.currency.data
                )
                db.session.add(account)
                db.session.commit()

                flash('Account created successfully!', 'success')
                return redirect(url_for('accounts.get_accounts'))
            else:
                for field, errors in form.errors.items():
                    for error in errors:
                        flash(f'{field}: {error}', 'error')
                return render_template('accounts/create.html', form=form)

        # Handle JSON request
        data = request.get_json()
        if 'account_type' not in data:
            return jsonify({"error": "Account type is required"}), 400

        valid_types = ['savings', 'checking', 'investment']
        if data['account_type'] not in valid_types:
            return jsonify({"error": f"Account type must be one of: {', '.join(valid_types)}"}), 400

        account_number = generate_account_number()
        while Account.query.filter_by(account_number=account_number).first():
            account_number = generate_account_number()

        account = Account(
            user_id=current_user_id,
            account_type=data['account_type'],
            account_number=account_number,
            balance=data.get('initial_balance', 0.00),
            currency=data.get('currency', 'USD')
        )

        db.session.add(account)
        db.session.commit()

        return jsonify({
            "message": "Account created successfully",
            "account": {
                "id": account.id,
                "account_number": account.account_number,
                "account_type": account.account_type,
                "balance": float(account.balance),
                "created_at": account.created_at.isoformat(),
                "updated_at": account.updated_at.isoformat()
            }
        }), 201

    except Exception as e:
        logger.error(f"Error creating account: {str(e)}")
        db.session.rollback()
        if request.content_type == 'application/x-www-form-urlencoded':
            flash('Error creating account', 'error')
            return render_template('accounts/create.html', form=AccountForm())
        return jsonify({"error": "Internal server error"}), 500

@accounts_bp.route('/<int:account_id>', methods=['GET'])
@jwt_required()
def get_account(account_id):
    try:
        current_user_id = get_jwt_identity()
        account = validate_account_ownership(account_id, current_user_id)

        if not account:
            if request.headers.get('Accept') == 'application/json':
                return jsonify({"error": "Account not found"}), 404
            flash('Account not found', 'error')
            return redirect(url_for('accounts.get_accounts'))

        # Get recent transactions
        recent_transactions = Transaction.query.filter(
            (Transaction.from_account_id == account_id) |
            (Transaction.to_account_id == account_id)
        ).order_by(Transaction.created_at.desc()).limit(5).all()

        if request.headers.get('Accept') == 'application/json':
            return jsonify({
                "account": {
                    "id": account.id,
                    "account_number": account.account_number,
                    "account_type": account.account_type,
                    "balance": float(account.balance),
                    "created_at": account.created_at.isoformat(),
                    "updated_at": account.updated_at.isoformat(),
                    "recent_transactions": [{
                        "id": t.id,
                        "type": t.type,
                        "amount": float(t.amount),
                        "description": t.description,
                        "created_at": t.created_at.isoformat()
                    } for t in recent_transactions]
                }
            }), 200

        # Get monthly statistics for HTML view
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        monthly_transactions = Transaction.query.filter(
            (Transaction.from_account_id == account_id) |
            (Transaction.to_account_id == account_id),
            Transaction.created_at >= thirty_days_ago
        ).all()

        monthly_deposits = sum(float(t.amount) for t in monthly_transactions if t.to_account_id == account_id)
        monthly_withdrawals = sum(float(t.amount) for t in monthly_transactions if t.from_account_id == account_id)
        monthly_avg_balance = float(account.balance)  # Simplified for now

        return render_template('accounts/detail.html',
                             account=account,
                             recent_transactions=recent_transactions,
                             monthly_deposits=monthly_deposits,
                             monthly_withdrawals=monthly_withdrawals,
                             monthly_avg_balance=monthly_avg_balance)

    except Exception as e:
        logger.error(f"Error fetching account: {str(e)}")
        if request.headers.get('Accept') == 'application/json':
            return jsonify({"error": "Internal server error"}), 500
        flash('Error fetching account details', 'error')
        return redirect(url_for('accounts.get_accounts'))

@accounts_bp.route('/<int:account_id>', methods=['PUT'])
@jwt_required()
def update_account(account_id):
    try:
        current_user_id = get_jwt_identity()
        account = validate_account_ownership(account_id, current_user_id)

        if not account:
            return jsonify({"error": "Account not found"}), 404

        data = request.get_json()
        
        # Validate updatable fields
        updatable_fields = ['account_type']
        update_data = {}
        
        for field in updatable_fields:
            if field in data:
                if field == 'account_type':
                    valid_types = ['savings', 'checking', 'investment']
                    if data[field] not in valid_types:
                        return jsonify({"error": f"Account type must be one of: {', '.join(valid_types)}"}), 400
                update_data[field] = data[field]

        if not update_data:
            return jsonify({"error": "No valid fields to update"}), 400

        # Update account
        for field, value in update_data.items():
            setattr(account, field, value)
        
        account.updated_at = datetime.utcnow()
        db.session.commit()

        return jsonify({
            "message": "Account updated successfully",
            "account": {
                "id": account.id,
                "account_number": account.account_number,
                "account_type": account.account_type,
                "balance": float(account.balance),
                "created_at": account.created_at.isoformat(),
                "updated_at": account.updated_at.isoformat()
            }
        }), 200

    except Exception as e:
        logger.error(f"Error updating account: {str(e)}")
        db.session.rollback()
        return jsonify({"error": "Internal server error"}), 500

@accounts_bp.route('/<int:account_id>', methods=['DELETE'])
@jwt_required()
def delete_account(account_id):
    try:
        current_user_id = get_jwt_identity()
        account = validate_account_ownership(account_id, current_user_id)

        if not account:
            return jsonify({"error": "Account not found"}), 404

        # Check if account has balance
        if float(account.balance) > 0:
            return jsonify({
                "error": "Cannot delete account with remaining balance", 
                "balance": float(account.balance)
            }), 400

        # Check for pending transactions
        pending_transactions = Transaction.query.filter(
            (Transaction.from_account_id == account_id) |
            (Transaction.to_account_id == account_id)
        ).filter(Transaction.status == 'pending').first()

        if pending_transactions:
            return jsonify({"error": "Cannot delete account with pending transactions"}), 400

        # Soft delete approach
        account.status = 'closed'
        account.closed_at = datetime.utcnow()
        db.session.commit()

        if request.headers.get('Accept') == 'application/json':
            return jsonify({
                "message": "Account closed successfully",
                "account_id": account_id
            }), 200

        flash('Account deleted successfully', 'success')
        return redirect(url_for('accounts.get_accounts'))

    except Exception as e:
        logger.error(f"Error deleting account: {str(e)}")
        db.session.rollback()
        if request.headers.get('Accept') == 'application/json':
            return jsonify({"error": "Internal server error"}), 500
        flash('Error deleting account', 'error')
        return redirect(url_for('accounts.get_accounts'))

@accounts_bp.route('/<int:account_id>/statement', methods=['GET'])
@jwt_required()
def get_account_statement(account_id):
    try:
        current_user_id = get_jwt_identity()
        account = validate_account_ownership(account_id, current_user_id)

        if not account:
            return jsonify({"error": "Account not found"}), 404

        # Get query parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Build query
        query = Transaction.query.filter(
            (Transaction.from_account_id == account_id) |
            (Transaction.to_account_id == account_id)
        )

        # Apply date filters if provided
        if start_date:
            query = query.filter(Transaction.created_at >= datetime.strptime(start_date, '%Y-%m-%d'))
        if end_date:
            query = query.filter(Transaction.created_at <= datetime.strptime(end_date, '%Y-%m-%d'))

        transactions = query.order_by(Transaction.created_at.desc()).all()

        if request.headers.get('Accept') == 'application/json':
            return jsonify({
                "account": {
                    "id": account.id,
                    "account_number": account.account_number,
                    "account_type": account.account_type,
                    "current_balance": float(account.balance)
                },
                "transactions": [{
                    "id": t.id,
                    "type": t.type,
                    "amount": float(t.amount),
                    "description": t.description,
                    "created_at": t.created_at.isoformat(),
                    "is_debit": t.from_account_id == account_id
                } for t in transactions]
            }), 200

        # Return HTML template
        return render_template('accounts/statement.html',
                             account=account,
                             transactions=transactions,
                             start_date=start_date,
                             end_date=end_date)

    except Exception as e:
        logger.error(f"Error generating statement: {str(e)}")
        if request.headers.get('Accept') == 'application/json':
            return jsonify({"error": "Internal server error"}), 500
        flash('Error generating account statement', 'error')
        return redirect(url_for('accounts.get_account', account_id=account_id))

@accounts_bp.route('/types', methods=['GET'])
@jwt_required()
def get_account_types():
    """Get list of valid account types"""
    account_types = [
        {
            "type": "savings",
            "description": "Standard savings account with interest"
        },
        {
            "type": "checking",
            "description": "Everyday checking account"
        },
        {
            "type": "investment",
            "description": "Investment account for stocks and funds"
        }
    ]

    if request.headers.get('Accept') == 'application/json':
        return jsonify({"account_types": account_types}), 200

    return render_template('accounts/types.html', account_types=account_types)

@accounts_bp.route('/<int:account_id>/summary', methods=['GET'])
@jwt_required()
def get_account_summary(account_id):
    """Get account summary with basic analytics"""
    try:
        current_user_id = get_jwt_identity()
        account = validate_account_ownership(account_id, current_user_id)

        if not account:
            return jsonify({"error": "Account not found"}), 404

        # Get transactions for the last 30 days
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        transactions = Transaction.query.filter(
            (Transaction.from_account_id == account_id) |
            (Transaction.to_account_id == account_id),
            Transaction.created_at >= thirty_days_ago
        ).all()

        # Calculate statistics
        total_inflow = sum(float(t.amount) for t in transactions if t.to_account_id == account_id)
        total_outflow = sum(float(t.amount) for t in transactions if t.from_account_id == account_id)
        
        summary_data = {
            "account_info": {
                "id": account.id,
                "account_number": account.account_number,
                "account_type": account.account_type,
                "current_balance": float(account.balance)
            },
            "thirty_day_summary": {
                "total_transactions": len(transactions),
                "total_inflow": total_inflow,
                "total_outflow": total_outflow,
                "net_flow": total_inflow - total_outflow
            }
        }

        if request.headers.get('Accept') == 'application/json':
            return jsonify(summary_data), 200

        return render_template('accounts/summary.html', 
                             account=account,
                             summary=summary_data['thirty_day_summary'])

    except Exception as e:
        logger.error(f"Error getting account summary: {str(e)}")
        if request.headers.get('Accept') == 'application/json':
            return jsonify({"error": "Internal server error"}), 500
        flash('Error fetching account summary', 'error')
        return redirect(url_for('accounts.get_account', account_id=account_id))