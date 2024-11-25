from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.account_history import AccountHistory
from app.models.account import Account
from app.models.transaction import Transaction
from app.models.user import User
from app.forms.account import AccountForm, EditAccountForm
from app.extensions import db
from datetime import datetime, timedelta
import logging
import random
import string

accounts_bp = Blueprint('accounts', __name__, url_prefix='/accounts')
logger = logging.getLogger(__name__)

def generate_account_number():
    return ''.join(random.choices(string.digits, k=10))

def validate_account_ownership(account_id, user_id):
    return Account.query.filter_by(id=account_id, user_id=user_id).first()

@accounts_bp.route('/', methods=['GET'])
@jwt_required()
def get_accounts():
    try:
        current_user_id = get_jwt_identity()
        accounts = Account.query.filter_by(user_id=current_user_id).all()
        accounts = [f"{acc.id} || {acc.account_number} || {acc.balance} || u_id: {acc.user_id}" for acc in accounts]
        return jsonify({"accounts": accounts, "message": "success"}), 200
        return render_template('accounts/list.html',
                            accounts=accounts,
                            is_authenticated=True)
    except Exception as e:
        logger.error(f"Error fetching accounts: {str(e)}")
        return jsonify({"error": f"Error fetching accounts: {str(e)}"}), 400
        # flash('Failed to fetch accounts', 'error')
        # return render_template('accounts/list.html',
        #                     accounts=[],
        #                     is_authenticated=True)

@accounts_bp.route('/create', methods=['GET'])
@jwt_required()
def create_account_page():
    form = AccountForm()
    return render_template('accounts/create.html',
                        form=form,
                        is_authenticated=True)

@accounts_bp.route('/', methods=['POST'])
@jwt_required()
def create_account():
    try:
        current_user_id = get_jwt_identity()
        form = AccountForm()
        
        if form.validate_on_submit():
            account_number = generate_account_number()
            while Account.query.filter_by(account_number=account_number).first():
                account_number = generate_account_number()

            new_account = Account(
                user_id=current_user_id,
                account_number=account_number,
                account_type=form.account_type.data,
                balance=form.initial_balance.data
            )
            
            db.session.add(new_account)
            db.session.commit()

            return jsonify({"message": f"success to create {account_number}"}), 201
            flash('Account created successfully!', 'success')
            return redirect(url_for('accounts.get_accounts'))

        return jsonify({"message": "form is not filled"}), 400
        return render_template('accounts/create.html',
                            form=form,
                            is_authenticated=True)

    except Exception as e:
        logger.error(f"Error creating account: {str(e)}")
        db.session.rollback()
        flash('Failed to create account', 'error')
        # return redirect(url_for('accounts.get_accounts'))
        return jsonify({"message": "failed to create accounts"}), 400

@accounts_bp.route('/<int:account_id>/details', methods=['GET'])
@jwt_required()
def get_account_details(account_id):
    try:
        current_user_id = get_jwt_identity()
        account = validate_account_ownership(account_id, current_user_id)

        if not account:
            flash('Account not found', 'error')
            return redirect(url_for('accounts.get_accounts'))

        # Ambil history perubahan
        account_history = AccountHistory.query\
            .filter_by(account_id=account_id)\
            .order_by(AccountHistory.changed_at.desc())\
            .all()

        return render_template('accounts/detail.html',
                            account=account,
                            account_history=account_history,
                            is_authenticated=True)
    except Exception as e:
        logger.error(f"Error fetching account details: {str(e)}")
        flash('Failed to fetch account details', 'error')
        return redirect(url_for('accounts.get_accounts'))

@accounts_bp.route('/<int:account_id>/edit', methods=['GET', 'POST'])
@jwt_required()
def edit_account(account_id):
    try:
        current_user_id = get_jwt_identity()
        account = validate_account_ownership(account_id, current_user_id)
        
        if not account:
            flash('Account not found', 'error')
            return redirect(url_for('accounts.get_accounts'))

        # Gunakan EditAccountForm bukan AccountForm
        form = EditAccountForm(obj=account)
        
        if request.method == 'POST':
            if form.validate_on_submit():
                # Record old values before update
                old_status = account.status
                
                # Update account
                account.status = form.status.data
                account.updated_at = datetime.utcnow()
                
                # Create history record if there are changes
                if old_status != account.status:
                    history = AccountHistory(
                        account_id=account.id,
                        field_name='status',
                        old_value=old_status,
                        new_value=account.status
                    )
                    db.session.add(history)
                    
                try:
                    db.session.commit()
                    flash('Account updated successfully!', 'success')
                    return redirect(url_for('accounts.get_account_details', account_id=account_id))
                except Exception as e:
                    db.session.rollback()
                    logger.error(f"Database error while updating account: {str(e)}")
                    flash('Failed to update account', 'error')
            else:
                # Tampilkan error validasi
                for field, errors in form.errors.items():
                    for error in errors:
                        flash(f'{field}: {error}', 'error')

        return render_template('accounts/edit.html',
                            form=form,
                            account=account,
                            is_authenticated=True)
                            
    except Exception as e:
        logger.error(f"Error updating account: {str(e)}")
        flash('Failed to update account', 'error')
        return redirect(url_for('accounts.get_account_details', account_id=account_id))


@accounts_bp.route('/<int:account_id>/statement', methods=['GET'])
@jwt_required()
def get_account_statement(account_id):
    try:
        current_user_id = get_jwt_identity()
        account = validate_account_ownership(account_id, current_user_id)

        if not account:
            flash('Account not found', 'error')
            return redirect(url_for('accounts.get_accounts'))

        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        query = Transaction.query.filter(
            (Transaction.from_account_id == account_id) |
            (Transaction.to_account_id == account_id)
        )

        if start_date:
            query = query.filter(Transaction.created_at >= datetime.strptime(start_date, '%Y-%m-%d'))
        if end_date:
            query = query.filter(Transaction.created_at <= datetime.strptime(end_date, '%Y-%m-%d'))

        transactions = query.order_by(Transaction.created_at.desc()).all()

        return render_template('accounts/statement.html',
                            account=account,
                            transactions=transactions,
                            start_date=start_date,
                            end_date=end_date,
                            is_authenticated=True)

    except Exception as e:
        logger.error(f"Error generating statement: {str(e)}")
        flash('Error generating account statement', 'error')
        return redirect(url_for('accounts.get_account_details', account_id=account_id))

@accounts_bp.route('/<int:account_id>/summary', methods=['GET'])
@jwt_required()
def get_account_summary(account_id):
    try:
        current_user_id = get_jwt_identity()
        account = validate_account_ownership(account_id, current_user_id)

        if not account:
            return jsonify({"error": "Account not found"}), 404

        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        transactions = Transaction.query.filter(
            (Transaction.from_account_id == account_id) |
            (Transaction.to_account_id == account_id),
            Transaction.created_at >= thirty_days_ago
        ).all()

        total_inflow = sum(t.amount for t in transactions if t.to_account_id == account_id)
        total_outflow = sum(t.amount for t in transactions if t.from_account_id == account_id)
        
        summary_data = {
            "account_info": {
                "id": account.id,
                "account_number": account.account_number,
                "current_balance": float(account.balance)
            },
            "thirty_day_summary": {
                "total_transactions": len(transactions),
                "total_inflow": float(total_inflow),
                "total_outflow": float(total_outflow),
                "net_flow": float(total_inflow - total_outflow)
            }
        }

        if request.headers.get('Accept') == 'application/json':
            return jsonify(summary_data)

        return render_template('accounts/summary.html',
                            account=account,
                            summary=summary_data['thirty_day_summary'],
                            is_authenticated=True)

    except Exception as e:
        logger.error(f"Error getting account summary: {str(e)}")
        if request.headers.get('Accept') == 'application/json':
            return jsonify({"error": "Internal server error"}), 500
        flash('Error fetching account summary', 'error')
        return redirect(url_for('accounts.get_account_details', account_id=account_id))

@accounts_bp.route('/<int:account_id>', methods=['GET'])
@jwt_required()
def get_account(account_id):
    try:
        current_user_id = get_jwt_identity()
        account = validate_account_ownership(account_id, current_user_id)
        
        if not account:
            return jsonify({"error": "Account not found"}), 404
            
        account_data = {
            "id": account.id,  
            "user_id": account.user_id,
            "account_type": account.account_type,
            "account_number": account.account_number,
            "balance": float(account.balance),
            "created_at": account.created_at.strftime("%Y-%m-%dT%H:%M:%S"),
            "updated_at": account.updated_at.strftime("%Y-%m-%dT%H:%M:%S") if account.updated_at else None
        }
        
        return jsonify({
            "account": account_data,
            "message": "success"
        }), 200

    except Exception as e:
        logger.error(f"Error fetching account details: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500
    
@accounts_bp.route('/<int:account_id>', methods=['PUT'])
@jwt_required()
def update_account(account_id):
    try:
        current_user_id = get_jwt_identity()
        
        # Validasi kepemilikan akun
        account = Account.query.get(account_id)
        if not account:
            return jsonify({"error": "Account not found"}), 404
            
        if str(account.user_id) != current_user_id:
            return jsonify({"error": "Unauthorized access"}), 403
            
        # Ambil data dari request body
        data = request.get_json()
        
        # Update field yang diizinkan
        if 'account_type' in data:
            account.account_type = data['account_type']
        if 'account_number' in data:
            account.account_number = data['account_number']
            
        account.updated_at = datetime.utcnow()
        
        # Simpan perubahan
        db.session.commit()
        
        return jsonify({
            "message": "Account updated successfully",
            "account": {
                "id": account.id,
                "account_type": account.account_type,
                "account_number": account.account_number,
                "updated_at": account.updated_at.strftime("%Y-%m-%dT%H:%M:%S")
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating account: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@accounts_bp.route('/<int:account_id>', methods=['DELETE'])
@jwt_required()
def delete_account(account_id):
    try:
        current_user_id = get_jwt_identity()
        account = validate_account_ownership(account_id, current_user_id)
        
        if not account:
            return jsonify({"error": "Account not found"}), 404
        
        db.session.delete(account)
        db.session.commit()
        
        return jsonify({"message": "Account deleted successfully"})
    except Exception as e:
        logger.error(f"Error deleting account: {str(e)}")
        db.session.rollback()
        return jsonify({"error": "Failed to delete account"}), 500
