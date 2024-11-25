from app.extensions import db
from datetime import datetime

class Investment(db.Model):  # Tambah db.Model
    __tablename__ = 'investments'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    investment_type = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(50), default='active')

    # Relationship
    user = db.relationship('User', backref='investments')