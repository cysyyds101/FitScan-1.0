from app import db
from passlib.hash import pbkdf2_sha256 as sha256

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    measurements = db.relationship('Measurement', backref='user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = sha256.hash(password)
    
    def check_password(self, password):
        return sha256.verify(password, self.password_hash)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email
        }
