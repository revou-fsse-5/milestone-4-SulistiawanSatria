from app import db
from datetime import datetime

class TransactionCategory(db.Model):
    __tablename__ = 'transaction_categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    description = db.Column(db.String(255))
    icon = db.Column(db.String(50))  # Icon identifier for UI
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<TransactionCategory {self.name}>'

    @staticmethod
    def get_default_categories():
        """Return list of default transaction categories"""
        return [
            'Food & Dining',
            'Transportation',
            'Shopping',
            'Entertainment',
            'Bills & Utilities',
            'Health & Medical',
            'Travel',
            'Education',
            'Business',
            'Others'
        ]
