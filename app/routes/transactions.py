from flask import Blueprint, render_template, request
from flask import Blueprint, render_template, request, jsonify, make_response
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.transaction import Transaction
from app.models.account import Account
from app.models.transaction_category import TransactionCategory
from app.extensions import db
from datetime import datetime, timedelta
from sqlalchemy import or_

transactions_bp = Blueprint('transactions', __name__, url_prefix='/transactions')

def validate_account_ownership(account_id, user_id):
    """Validate account ownership"""
    account = Account.query.filter_by(id=account_id, user_id=user_id).first()
    if not account:
        return None
    return account

@transactions_bp.route('/', methods=['GET'])
@jwt_required()
def list_transactions():
    try:
        current_user_id = get_jwt_identity()
        accounts = Account.query.filter_by(user_id=current_user_id).all()
        account_ids = [account.id for account in accounts]
        
        # Pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # Filter parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        transaction_type = request.args.get('type')
        min_amount = request.args.get('min_amount')
        max_amount = request.args.get('max_amount')
        category_id = request.args.get('category_id')
        account_id = request.args.get('account_id')
        
        # Base query
        query = Transaction.query.filter(
            or_(
                Transaction.from_account_id.in_(account_ids),
                Transaction.to_account_id.in_(account_ids)
            )
        )
        
        # Apply filters
        if start_date:
            query = query.filter(Transaction.created_at >= datetime.strptime(start_date, '%Y-%m-%d'))
        if end_date:
            query = query.filter(Transaction.created_at <= datetime.strptime(end_date, '%Y-%m-%d'))
        if transaction_type:
            query = query.filter(Transaction.type == transaction_type)
        if min_amount:
            query = query.filter(Transaction.amount >= float(min_amount))
        if max_amount:
            query = query.filter(Transaction.amount <= float(max_amount))
        if category_id:
            query = query.filter(Transaction.category_id == category_id)
        if account_id:
            query = query.filter(
                or_(
                    Transaction.from_account_id == account_id,
                    Transaction.to_account_id == account_id
                )
            )
        
        # Execute paginated query
        paginated_transactions = query.order_by(Transaction.created_at.desc())\
                                    .paginate(page=page, per_page=per_page)
        
        # Format transactions for template
        transactions = [{
            "id": t.id,
            "type": t.type,
            "amount": float(t.amount),
            "description": t.description,
            "created_at": t.created_at.isoformat(),
            "from_account_id": t.from_account_id,
            "to_account_id": t.to_account_id,
            "category": t.category.name if t.category else None,
            "status": t.status
        } for t in paginated_transactions.items]
        
        # Format pagination info
        pagination = {
            "total_items": paginated_transactions.total,
            "total_pages": paginated_transactions.pages,
            "current_page": page,
            "per_page": per_page,
            "has_next": paginated_transactions.has_next,
            "has_prev": paginated_transactions.has_prev
        }
        
        return render_template('transactions/list.html', transactions=transactions, pagination=pagination)
        
    except Exception as e:
        print("Error:", str(e))
        return render_template('error/500.html', error="Internal server error"), 500

@transactions_bp.route('/deposit', methods=['POST'])
@jwt_required()
def create_deposit():
    try:
        data = request.get_json()
        user_id = get_jwt_identity()
        
        # Validasi input
        required_fields = ['account_id', 'amount']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"{field} is required"}), 400
        
        account_id = data['account_id']
        amount = float(data['amount'])
        
        if amount <= 0:
            return jsonify({"error": "Amount must be positive"}), 400

        # Validasi account ownership
        account = validate_account_ownership(account_id, user_id)
        if not account:
            return jsonify({"error": "Account not found"}), 404
        
        # Create transaction with category
        transaction = Transaction(
            from_account_id=None,
            to_account_id=account_id,
            amount=amount,
            type='deposit',
            description=data.get('description', 'Deposit'),
            category_id=data.get('category_id'),
            status='completed'
        )

        # Update account balance
        account.balance += amount
        
        db.session.add(transaction)
        db.session.commit()
        
        return jsonify({
            "message": "Deposit successful",
            "transaction": {
                "id": transaction.id,
                "amount": float(transaction.amount),
                "type": transaction.type,
                "description": transaction.description,
                "created_at": transaction.created_at.isoformat(),
                "status": transaction.status
            },
            "account": {
                "id": account.id,
                "balance": float(account.balance)
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        print("Error:", str(e))
        return jsonify({"error": "Internal server error"}), 500

@transactions_bp.route('/withdraw', methods=['POST'])
@jwt_required()
def create_withdraw():
    try:
        data = request.get_json()
        user_id = get_jwt_identity()
        
        # Validasi input
        required_fields = ['account_id', 'amount']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"{field} is required"}), 400
        
        account_id = data['account_id']
        amount = float(data['amount'])
        
        if amount <= 0:
            return jsonify({"error": "Amount must be positive"}), 400

        # Validasi account ownership
        account = validate_account_ownership(account_id, user_id)
        if not account:
            return jsonify({"error": "Account not found"}), 404
        
        # Check sufficient balance
        if account.balance < amount:
            return jsonify({"error": "Insufficient balance"}), 400
        
        # Create transaction
        transaction = Transaction(
            from_account_id=account_id,
            to_account_id=None,
            amount=amount,
            type='withdraw',
            description=data.get('description', 'Withdrawal'),
            category_id=data.get('category_id'),
            status='completed'
        )

        # Update account balance
        account.balance -= amount
        
        db.session.add(transaction)
        db.session.commit()
        
        return jsonify({
            "message": "Withdrawal successful",
            "transaction": {
                "id": transaction.id,
                "amount": float(transaction.amount),
                "type": transaction.type,
                "description": transaction.description,
                "created_at": transaction.created_at.isoformat(),
                "status": transaction.status
            },
            "account": {
                "id": account.id,
                "balance": float(account.balance)
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        print("Error:", str(e))
        return jsonify({"error": "Internal server error"}), 500

@transactions_bp.route('/transfer', methods=['POST'])
@jwt_required()
def create_transfer():
    try:
        data = request.get_json()
        user_id = get_jwt_identity()
        
        # Validasi input
        required_fields = ['from_account_id', 'to_account_id', 'amount']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"{field} is required"}), 400
        
        from_account_id = data['from_account_id']
        to_account_id = data['to_account_id']
        amount = float(data['amount'])
        
        if amount <= 0:
            return jsonify({"error": "Amount must be positive"}), 400
        
        # Validate source account ownership
        from_account = validate_account_ownership(from_account_id, user_id)
        if not from_account:
            return jsonify({"error": "Source account not found"}), 404
        
        # Validate destination account
        to_account = Account.query.get(to_account_id)
        if not to_account:
            return jsonify({"error": "Destination account not found"}), 404
        
        # Check sufficient balance
        if from_account.balance < amount:
            return jsonify({"error": "Insufficient balance"}), 400
        
        # Create transaction
        transaction = Transaction(
            from_account_id=from_account_id,
            to_account_id=to_account_id,
            amount=amount,
            type='transfer',
            description=data.get('description', 'Transfer'),
            category_id=data.get('category_id'),
            status='completed'
        )

        # Update account balances
        from_account.balance -= amount
        to_account.balance += amount
        
        db.session.add(transaction)
        db.session.commit()
        
        return jsonify({
            "message": "Transfer successful",
            "transaction": {
                "id": transaction.id,
                "amount": float(transaction.amount),
                "type": transaction.type,
                "description": transaction.description,
                "created_at": transaction.created_at.isoformat(),
                "status": transaction.status
            },
            "from_account": {
                "id": from_account.id,
                "balance": float(from_account.balance)
            },
            "to_account": {
                "id": to_account.id,
                "balance": float(to_account.balance)
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        print("Error:", str(e))
        return jsonify({"error": "Internal server error"}), 500

@transactions_bp.route('/<int:transaction_id>', methods=['GET'])
@jwt_required()
def get_transaction(transaction_id):
    try:
        current_user_id = 1 
        accounts = Account.query.filter_by(user_id=current_user_id).all()
        account_ids = [account.id for account in accounts]
        
        transaction = Transaction.query.filter(
            Transaction.id == transaction_id,
            or_(
                Transaction.from_account_id.in_(account_ids),
                Transaction.to_account_id.in_(account_ids)
            )
        ).first()
        
        if not transaction:
            return jsonify({"error": "Transaction not found"}), 404
        
        return jsonify({
            "transaction": {
                "id": transaction.id,
                "type": transaction.type,
                "amount": float(transaction.amount),
                "description": transaction.description,
                "created_at": transaction.created_at.isoformat(),
                "from_account_id": transaction.from_account_id,
                "to_account_id": transaction.to_account_id,
                "category": transaction.category.name if transaction.category else None,
                "status": transaction.status
            }
        }), 200
        
    except Exception as e:
        print("Error:", str(e))
        return jsonify({"error": "Internal server error"}), 500

@transactions_bp.route('/categories', methods=['GET'])
@jwt_required()
def get_transaction_categories():
    """Get list of transaction categories"""
    try:
        categories = TransactionCategory.query.all()
        return jsonify({
            "categories": [{
                "id": category.id,
                "name": category.name,
                "description": category.description
            } for category in categories]
        }), 200
    except Exception as e:
        print("Error:", str(e))
        return jsonify({"error": "Internal server error"}), 500

@transactions_bp.route('/statistics', methods=['GET'])
@jwt_required()
def get_transaction_statistics():
    """Get transaction statistics for the current user"""
    try:
        current_user_id = get_jwt_identity()
        accounts = Account.query.filter_by(user_id=current_user_id).all()
        account_ids = [account.id for account in accounts]
        
        # Time range filter
        days = request.args.get('days', 30, type=int)
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Get transactions within time range
        transactions = Transaction.query.filter(
            or_(
                Transaction.from_account_id.in_(account_ids),
                Transaction.to_account_id.in_(account_ids)
            ),
            Transaction.created_at >= start_date
        ).all()
        
        # Calculate statistics
        total_inflow = sum(float(t.amount) for t in transactions if t.to_account_id in account_ids)
        total_outflow = sum(float(t.amount) for t in transactions if t.from_account_id in account_ids)
        
        # Category breakdown
        category_stats = {}
        for transaction in transactions:
            if transaction.category:
                if transaction.category.name not in category_stats:
                    category_stats[transaction.category.name] = 0
                if transaction.from_account_id in account_ids:
                    category_stats[transaction.category.name] += float(transaction.amount)
        
        return jsonify({
            "period": f"Last {days} days",
            "total_transactions": len(transactions),
            "total_inflow": total_inflow,
            "total_outflow": total_outflow,
            "net_flow": total_inflow - total_outflow,
            "category_breakdown": category_stats,
            "average_transaction_amount": (total_inflow + total_outflow) / (len(transactions) if transactions else 1)
        }), 200
        
    except Exception as e:
        print("Error:", str(e))
        return jsonify({"error": "Internal server error"}), 500

@transactions_bp.route('/export', methods=['GET'])
@jwt_required()
def export_transactions():
    """Export transactions to CSV"""
    try:
        current_user_id = get_jwt_identity()
        accounts = Account.query.filter_by(user_id=current_user_id).all()
        account_ids = [account.id for account in accounts]
        
        # Get filter parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Build query
        query = Transaction.query.filter(
            or_(
                Transaction.from_account_id.in_(account_ids),
                Transaction.to_account_id.in_(account_ids)
            )
        )
        
        if start_date:
            query = query.filter(Transaction.created_at >= datetime.strptime(start_date, '%Y-%m-%d'))
        if end_date:
            query = query.filter(Transaction.created_at <= datetime.strptime(end_date, '%Y-%m-%d'))
        
        transactions = query.order_by(Transaction.created_at.desc()).all()
        
        # Generate CSV data
        csv_data = "Date,Type,Amount,Description,Category,From Account,To Account,Status\n"
        
        for t in transactions:
            from_account = Account.query.get(t.from_account_id) if t.from_account_id else None
            to_account = Account.query.get(t.to_account_id) if t.to_account_id else None
            
            csv_data += f"{t.created_at.strftime('%Y-%m-%d %H:%M:%S')},"
            csv_data += f"{t.type},"
            csv_data += f"{float(t.amount)},"
            csv_data += f"\"{t.description if t.description else ''}\"," 
            csv_data += f"{t.category.name if t.category else ''},"
            csv_data += f"{from_account.account_number if from_account else ''},"
            csv_data += f"{to_account.account_number if to_account else ''},"
            csv_data += f"{t.status}\n"
        
        # Create response with CSV file
        response = make_response(csv_data)
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename=transactions_{datetime.now().strftime("%Y%m%d")}.csv'
        
        return response

    except Exception as e:
        print("Error:", str(e))
        return jsonify({"error": "Internal server error"}), 500

@transactions_bp.route('/summary', methods=['GET'])
@jwt_required()
def get_transaction_summary():
    """Get transaction summary by time period"""
    try:
        current_user_id = get_jwt_identity()
        accounts = Account.query.filter_by(user_id=current_user_id).all()
        account_ids = [account.id for account in accounts]
        
        # Get time period from query params (daily, weekly, monthly, yearly)
        period = request.args.get('period', 'monthly')
        
        # Calculate date ranges
        end_date = datetime.utcnow()
        if period == 'daily':
            start_date = end_date - timedelta(days=30)  # Last 30 days
            date_format = '%Y-%m-%d'
            date_trunc = 'day'
        elif period == 'weekly':
            start_date = end_date - timedelta(weeks=12)  # Last 12 weeks
            date_format = '%Y-W%W'
            date_trunc = 'week'
        elif period == 'yearly':
            start_date = end_date - timedelta(days=365*2)  # Last 2 years
            date_format = '%Y'
            date_trunc = 'year'
        else:  # monthly
            start_date = end_date - timedelta(days=365)  # Last 12 months
            date_format = '%Y-%m'
            date_trunc = 'month'
        
        # Get transactions
        transactions = Transaction.query.filter(
            or_(
                Transaction.from_account_id.in_(account_ids),
                Transaction.to_account_id.in_(account_ids)
            ),
            Transaction.created_at.between(start_date, end_date)
        ).all()
        
        # Organize transactions by period
        summary = {}
        for transaction in transactions:
            period_key = transaction.created_at.strftime(date_format)
            
            if period_key not in summary:
                summary[period_key] = {
                    'inflow': 0,
                    'outflow': 0,
                    'transfer': 0,
                    'count': 0
                }
            
            amount = float(transaction.amount)
            if transaction.to_account_id in account_ids and not transaction.from_account_id in account_ids:
                summary[period_key]['inflow'] += amount
            elif transaction.from_account_id in account_ids and not transaction.to_account_id in account_ids:
                summary[period_key]['outflow'] += amount
            else:
                summary[period_key]['transfer'] += amount
            
            summary[period_key]['count'] += 1
        
        return jsonify({
            "period": period,
            "start_date": start_date.strftime('%Y-%m-%d'),
            "end_date": end_date.strftime('%Y-%m-%d'),
            "summary": summary
        }), 200

    except Exception as e:
        print("Error:", str(e))
        return jsonify({"error": "Internal server error"}), 500

@transactions_bp.route('/create', methods=['GET', 'POST'])
@jwt_required()
def create_transaction():
    if request.method == 'POST':
        data = request.form
        try:
            transaction = Transaction(
                from_account_id=data.get('from_account_id'),
                to_account_id=data.get('to_account_id'),
                amount=data.get('amount'),
                transaction_type=data.get('transaction_type'),
                description=data.get('description')
            )
            db.session.add(transaction)
            db.session.commit()
            return jsonify({'message': 'Transaction created successfully'}), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 400
    
    # GET method - render transaction form
    accounts = Account.query.all()
    return render_template('transactions/create.html', accounts=accounts)
