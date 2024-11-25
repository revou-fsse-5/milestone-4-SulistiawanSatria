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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard')
@jwt_required()
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
            'is_authenticated': True,
            'total_balance': Decimal('0.00'),
            'monthly_income': Decimal('0.00'),
            'monthly_expenses': Decimal('0.00'),
            'account_count': 0,
            'accounts': [],
            'recent_transactions': [],
            'budgets': []
        }


        verify_jwt_in_request()

        accounts = Account.query.filter_by(user_id=current_user_id).all()
        if accounts:
            template_data['accounts'] = accounts
            template_data['account_count'] = len(accounts)
            template_data['total_balance'] = sum(Decimal(str(account.balance)) for account in accounts)

            account_ids = [account.id for account in accounts]
            transactions = Transaction.query.filter(
                (Transaction.from_account_id.in_(account_ids)) |
                (Transaction.to_account_id.in_(account_ids))
            ).order_by(Transaction.created_at.desc()).limit(5).all()
            
            template_data['recent_transactions'] = [{
                'id': t.id,
                'from_account_id': t.from_account_id,
                'to_account_id': t.to_account_id,
                'type': t.type,
                'amount': float(t.amount),
                'description': t.description,
                'status': t.status,
                'created_at': t.created_at,
                'updated_at': t.updated_at
            } for t in transactions]

        return render_template('dashboard/index.html', **template_data)
        
    except Exception as e:
        logger.error(f"Dashboard error: {str(e)}")
        flash('Session expired, please login again', 'error')
        return redirect(url_for('auth.login_page'))

@dashboard_bp.route('/dashboard/analytics')
@jwt_required()
def analytics():
    try:
        current_user_id = get_jwt_identity()
        accounts = Account.query.filter_by(user_id=current_user_id).all()
        
        if not accounts:
            flash('No accounts found', 'warning')
            return redirect(url_for('dashboard.index'))

        account_ids = [account.id for account in accounts]
        transactions = Transaction.query.filter(
            (Transaction.from_account_id.in_(account_ids)) |
            (Transaction.to_account_id.in_(account_ids))
        ).order_by(Transaction.created_at.desc()).all()

        total_inflow = sum(Decimal(str(t.amount)) for t in transactions if t.to_account_id in account_ids)
        total_outflow = sum(Decimal(str(t.amount)) for t in transactions if t.from_account_id in account_ids)
        
        type_distribution = {}
        for t in transactions:
            if t.type in type_distribution:
                type_distribution[t.type] += 1
            else:
                type_distribution[t.type] = 1

        return render_template('dashboard/analytics.html',
                           total_inflow=float(total_inflow),
                           total_outflow=float(total_outflow),
                           net_flow=float(total_inflow - total_outflow),
                           type_distribution=type_distribution,
                           current_user=User.query.get(current_user_id),
                           is_authenticated=True)

    except Exception as e:
        logger.error(f"Analytics error: {str(e)}")
        flash('Error generating analytics', 'error')
        return redirect(url_for('dashboard.index'))

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
