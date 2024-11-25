from app import db
from datetime import datetime

class AccountHistory(db.Model):
    __tablename__ = 'account_history'
    
    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.Integer, db.ForeignKey('accounts.id', ondelete='CASCADE'), nullable=False)
    field_name = db.Column(db.String(50), nullable=False)
    old_value = db.Column(db.String(255), nullable=False)
    new_value = db.Column(db.String(255), nullable=False)
    changed_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    account = db.relationship('Account', backref=db.backref('history', lazy='dynamic'))
    
    def __repr__(self):
        return f'<AccountHistory {self.account_id}: {self.field_name}>'