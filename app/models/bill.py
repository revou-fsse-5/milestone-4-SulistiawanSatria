from app.extensions import db
from datetime import datetime

class Bill(db.Model):
    __tablename__ = 'bills'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    biller_name = db.Column(db.String(255), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=False)
    status = db.Column(db.String(50), default='pending')
    description = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Use property for lazy loading
    @property
    def account(self):
        from app.models.account import Account
        return Account.query.get(self.account_id)

    @property
    def user(self):
        from app.models.user import User
        return User.query.get(self.user_id)
