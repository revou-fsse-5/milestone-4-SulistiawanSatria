from app import db
from datetime import datetime

class Account(db.Model):
    __tablename__ = 'accounts'
    id = db.Column(db.Integer, primary_key=True)
    account_number = db.Column(db.String(20), unique=True, nullable=False)
    account_type = db.Column(db.String(20), nullable=False)
    balance = db.Column(db.Float, default=0.0)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    status = db.Column(db.String(20), default='active', nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('accounts', lazy=True))
    
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