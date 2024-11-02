from app.extensions import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    __tablename__ = 'users'
   
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships bisa ditambahkan di sini
    # accounts = db.relationship('Account', backref='user', lazy=True)
    # transactions = db.relationship('Transaction', backref='user', lazy=True)

    @property
    def password(self):
        """
        Prevent password from being accessed
        """
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        """
        Set password to a hashed password
        """
        self.password_hash = generate_password_hash(password)

    def set_password(self, password):
        """
        Alternative method to set password
        """
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """
        Check if the provided password matches the hash
        """
        return check_password_hash(self.password_hash, password)
   
    def to_dict(self):
        """
        Convert user object to dictionary
        """
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def from_dict(self, data):
        """
        Update user object from dictionary
        """
        for field in ['username', 'email']:
            if field in data:
                setattr(self, field, data[field])
        if 'password' in data:
            self.set_password(data['password'])
   
    def __repr__(self):
        return f'<User {self.username}>'