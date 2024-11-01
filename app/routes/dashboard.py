from flask import Blueprint, render_template, jsonify, request, redirect, url_for, flash, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
from app.models.user import User
from app.models.account import Account
from app.models.transaction import Transaction
from app.models.budget import Budget
from app.utils.decorators import check_account_ownership
from app.utils.formatters import format_currency, format_date
from app import db, cache
from decimal import Decimal
from datetime import datetime, timedelta
import logging
import json

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

dashboard_bp = Blueprint('dashboard', __name__)

def format_transaction_data(transaction, include_accounts=True):
    """Helper function to format transaction data"""
    try:
        from_account = Account.query.get(transaction.from_account_id) if transaction.from_account_id else None
        to_account = Account.query.get(transaction.to_account_id) if transaction.to_account_id else None
        
        data = {
            'id': transaction.id,
            'type': transaction.type,
            'amount': float(transaction.amount),
            'description': transaction.description,
            'created_at': transaction.created_at,
            'status': transaction.status
        }
        
        if include_accounts:
            data.update({
                'from_account': {
                    'number': from_account.account_number if from_account else None,
                    'type': from_account.account_type if from_account else None
                } if from_account else None,
                'to_account': {
                    'number': to_account.account_number if to_account else None,
                    'type': to_account.account_type if to_account else None
                } if to_account else None
            })
            
        return data
    except Exception as e:
        logger.error(f"Error formatting transaction data: {str(e)}")
        return None

@dashboard_bp.before_request
def verify_auth():
    try:
        verify_jwt_in_request()
        return None
    except:
        return redirect(url_for('auth.login_page'))


@dashboard_bp.route('/')
@dashboard_bp.route('/dashboard')
def index():
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            flash('User not found', 'error')
            return redirect(url_for('auth.login_page'))
            
        template_data = {
            'user': user,
            'current_user': user,
            'total_balance': 0.00,
            'monthly_income': 0.00,
            'monthly_expenses': 0.00,
            'account_count': 0,
            'accounts': [],
            'recent_transactions': [],
            'budgets': []
        }

        # Get accounts
        accounts = Account.query.filter_by(user_id=current_user_id).all()
        if accounts:
            template_data['accounts'] = accounts
            template_data['account_count'] = len(accounts)
            template_data['total_balance'] = sum(float(account.balance) for account in accounts)

        # Get recent transactions
        account_ids = [account.id for account in accounts]
        if account_ids:
            transactions = Transaction.query.filter(
                (Transaction.from_account_id.in_(account_ids)) |
                (Transaction.to_account_id.in_(account_ids))
            ).order_by(Transaction.created_at.desc()).limit(5).all()
            
            template_data['recent_transactions'] = transactions

        return render_template('dashboard/index.html', **template_data)

    except Exception as e:
            logger.error(f"Dashboard error: {str(e)}")
    flash('Error loading dashboard', 'error')
    return redirect(url_for('auth.login_page'))

@dashboard_bp.route('/dashboard/account/<int:account_id>')
@jwt_required()
@check_account_ownership
def account_details(account_id):
    try:
        account = Account.query.get_or_404(account_id)
        
        transactions = Transaction.query.filter(
            (Transaction.from_account_id == account_id) |
            (Transaction.to_account_id == account_id)
        ).order_by(Transaction.created_at.desc()).limit(10).all()

        transactions_data = [format_transaction_data(t, include_accounts=False)
                           for t in transactions]

        return render_template('dashboard/account_details.html',
                               account=account,
                               transactions=transactions_data)

    except Exception as e:
        logger.error(f"Account details error: {str(e)}")
        flash('Error loading account details', 'error')
        return redirect(url_for('dashboard.index'))

@dashboard_bp.route('/dashboard/analytics')
@jwt_required()
def analytics():
    try:
        current_user_id = get_jwt_identity()
        accounts = Account.query.filter_by(user_id=current_user_id).all()
        account_ids = [account.id for account in accounts]

        transactions = Transaction.query.filter(
            (Transaction.from_account_id.in_(account_ids)) |
            (Transaction.to_account_id.in_(account_ids))
        ).order_by(Transaction.created_at.desc()).all()

        total_inflow = sum(float(t.amount) for t in transactions if t.to_account_id in account_ids)
        total_outflow = sum(float(t.amount) for t in transactions if t.from_account_id in account_ids)
        
        type_distribution = {}
        for t in transactions:
            if t.type in type_distribution:
                type_distribution[t.type] += 1
            else:
                type_distribution[t.type] = 1

        return render_template('dashboard/analytics.html',
                            total_inflow=total_inflow,
                            total_outflow=total_outflow,
                            net_flow=total_inflow - total_outflow,
                            type_distribution=type_distribution,
                            current_user=User.query.get(current_user_id))

    except Exception as e:
        logger.error(f"Analytics error: {str(e)}")
        flash('Error generating analytics', 'error')
        return redirect(url_for('dashboard.index'))

# Error handlers
@dashboard_bp.errorhandler(404)
def not_found_error(error):
    logger.warning(f"404 error: {str(error)}")
    return render_template('error/404.html'), 404

@dashboard_bp.errorhandler(401)
def unauthorized_error(error):
    logger.warning(f"401 error: {str(error)}")
    return redirect(url_for('auth.login_page'))

@dashboard_bp.errorhandler(500)
def internal_error(error):
    logger.error(f"500 error: {str(error)}")
    db.session.rollback()
    return render_template('error/500.html'), 500
