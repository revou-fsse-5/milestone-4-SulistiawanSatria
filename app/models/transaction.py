# app/models/transaction.py
from app import db
from datetime import datetime

class Transaction(db.Model):
    __tablename__ = 'transactions'  # Tambahkan ini
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    from_account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=True)
    to_account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=True)
    type = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    description = db.Column(db.String(200))
    status = db.Column(db.String(20), default='completed')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Transaction {self.id}>'
    
    def to_dict(self):
        """Convert Transaction object to a dictionary for JSON serialization"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'from_account_id': self.from_account_id,
            'to_account_id': self.to_account_id,
            'type': self.type,
            'amount': str(self.amount),  # Convert Numeric to string for JSON serialization
            'description': self.description,
            'status': self.status,
            'created_at': self.created_at.isoformat(),  # Convert datetime to ISO string
            'updated_at': self.updated_at.isoformat()  # Convert datetime to ISO string
        }