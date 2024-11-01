from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.transaction import Transaction
from app.models.bill import Bill
from app import db, cache
from datetime import datetime, timedelta
from app.models.transaction_category import TransactionCategory

api_bp = Blueprint('api', __name__)

@api_bp.route('/api/transactions/filter', methods=['POST'])
@jwt_required()
def filter_transactions():
    data = request.get_json()
    user_id = get_jwt_identity()
    
    query = Transaction.query.filter_by(user_id=user_id)
    
    if data.get('date'):
        date = datetime.strptime(data['date'], '%Y-%m-%d')
        query = query.filter(Transaction.created_at >= date)
    
    if data.get('category'):
        query = query.filter_by(category_id=data['category'])
    
    transactions = query.order_by(Transaction.created_at.desc()).all()
    
    return jsonify([t.to_dict() for t in transactions])

@api_bp.route('/api/transactions/export')
@jwt_required()
def export_transactions():
    user_id = get_jwt_identity()
    transactions = Transaction.query.filter_by(user_id=user_id).all()
    
    # Generate CSV
    csv_data = "Date,Description,Amount,Category\n"
    for t in transactions:
        csv_data += f"{t.created_at},{t.description},{t.amount},{t.category.name}\n"
    
    return csv_data, 200, {
        'Content-Type': 'text/csv',
        'Content-Disposition': 'attachment; filename=transactions.csv'
    }

@api_bp.route('/api/bills/due')
@jwt_required()
def get_due_bills():
    user_id = get_jwt_identity()
    due_date = datetime.now() + timedelta(days=7)
    
    bills = Bill.query.filter_by(user_id=user_id)\
        .filter(Bill.due_date <= due_date)\
        .filter(Bill.status == 'pending')\
        .all()
    
    return jsonify([b.to_dict() for b in bills])

@api_bp.route('/api/transactions/spending')
@jwt_required()
def get_spending_data():
    user_id = get_jwt_identity()
    
    # Get spending data grouped by category
    spending_data = db.session.query(
        TransactionCategory.name,
        db.func.sum(Transaction.amount)
    ).join(Transaction)\
     .filter(Transaction.user_id == user_id)\
     .filter(Transaction.type == 'expense')\
     .group_by(TransactionCategory.name)\
     .all()
    
    categories = [item[0] for item in spending_data]
    amounts = [float(item[1]) for item in spending_data]
    
    return jsonify({
        'categories': categories,
        'amounts': amounts
    })
