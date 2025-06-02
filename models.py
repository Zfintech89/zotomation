# models.py
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import json

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    presentations = db.relationship('Presentation', backref='user', lazy=True, cascade="all, delete-orphan")
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'created_at': self.created_at.isoformat()
        }

class Presentation(db.Model):
    __tablename__ = 'presentations'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    topic = db.Column(db.String(200), nullable=False)
    template_id = db.Column(db.String(50), nullable=False)
    slide_count = db.Column(db.Integer, default=6)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    slides = db.relationship('Slide', backref='presentation', lazy=True, cascade="all, delete-orphan", order_by="Slide.slide_order")
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'topic': self.topic,
            'template_id': self.template_id,
            'slide_count': self.slide_count,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'slides': [slide.to_dict() for slide in self.slides]
        }

class Slide(db.Model):
    __tablename__ = 'slides'
    
    id = db.Column(db.Integer, primary_key=True)
    presentation_id = db.Column(db.Integer, db.ForeignKey('presentations.id'), nullable=False)
    slide_order = db.Column(db.Integer, nullable=False)
    layout = db.Column(db.String(50), nullable=False)
    content_json = db.Column(db.Text, nullable=False)
    
    @property
    def content(self):
        return json.loads(self.content_json)
    
    @content.setter
    def content(self, content_dict):
        self.content_json = json.dumps(content_dict)
    
    def to_dict(self):
        return {
            'id': self.id,
            'presentation_id': self.presentation_id,
            'slide_order': self.slide_order,
            'layout': self.layout,
            'content': self.content
        }