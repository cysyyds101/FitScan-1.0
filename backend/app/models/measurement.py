from app import db
from datetime import datetime

class Measurement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    shoulder_width = db.Column(db.Float, nullable=False)
    arm_length = db.Column(db.Float, nullable=False)
    leg_length = db.Column(db.Float, nullable=False)
    height = db.Column(db.Float, nullable=False)
    chest = db.Column(db.Float, nullable=False)
    waist = db.Column(db.Float, nullable=False)
    hip = db.Column(db.Float, nullable=False)
    size_recommendation = db.Column(db.String(50), nullable=False)
    slim_size_recommendation = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'shoulderWidth': self.shoulder_width,
            'armLength': self.arm_length,
            'legLength': self.leg_length,
            'height': self.height,
            'chest': self.chest,
            'waist': self.waist,
            'hip': self.hip,
            'sizeRecommendation': self.size_recommendation,
            'slimSizeRecommendation': self.slim_size_recommendation,
            'date': self.created_at.strftime('%Y-%m-%d'),
            'time': self.created_at.strftime('%H:%M')
        }
