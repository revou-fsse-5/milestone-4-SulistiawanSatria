# app/models/account.py
from app import db
from datetime import datetime

class Account(db.Model):
    __tablename__ = 'accounts'  # Tambahkan di line 5 ini
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    account_type = db.Column(db.String(50), nullable=False)
    account_number = db.Column(db.String(50), unique=True, nullable=False)
    balance = db.Column(db.Numeric(10, 2), default=0.00)
    currency = db.Column(db.String(3), default='USD')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    from_transactions = db.relationship('Transaction', 
                                      backref='from_account',
                                      foreign_keys='Transaction.from_account_id',
                                      lazy=True)
    to_transactions = db.relationship('Transaction',
                                    backref='to_account',
                                    foreign_keys='Transaction.to_account_id',
                                    lazy=True)

    def __repr__(self):
        return f'<Account {self.account_number}>'