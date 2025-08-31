from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from sqlalchemy.sql import func
from flask_login import UserMixin

db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)  # логин для входа
    phone = db.Column(db.String(20), unique=True, nullable=False)  # номер телефона
    password_hash = db.Column(db.String(128), nullable=False)
    first_name = db.Column(db.String(50))  # имя
    last_name = db.Column(db.String(50))   # фамилия
    role = db.Column(db.String(20), default='player')  # player, captain, admin
    position = db.Column(db.String(50))  # вратарь, защитник, нападающий
    number = db.Column(db.Integer)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=func.now())
    
    responses = db.relationship('EventResponse', backref='user', lazy=True)
    lineup_assignments = db.relationship('LineupAssignment', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_full_name(self):
        """Возвращает полное имя игрока для отображения"""
        if self.last_name and self.first_name:
            return f"{self.last_name} {self.first_name}"
        elif self.last_name:
            return self.last_name
        elif self.first_name:
            return self.first_name
        else:
            return self.username

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    event_type = db.Column(db.String(20), nullable=False)  # game, training
    datetime = db.Column(db.DateTime, nullable=False)
    location = db.Column(db.String(200))
    opponent = db.Column(db.String(100))  # для игр
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=func.now())
    
    responses = db.relationship('EventResponse', backref='event', lazy=True)
    lineup = db.relationship('Lineup', backref='event', uselist=False)

class EventResponse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    status = db.Column(db.String(20), nullable=False)  # attending, not_attending, maybe
    comment = db.Column(db.Text)
    responded_at = db.Column(db.DateTime, default=func.now())

class Lineup(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=func.now())
    
    assignments = db.relationship('LineupAssignment', backref='lineup', lazy=True)

class LineupAssignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lineup_id = db.Column(db.Integer, db.ForeignKey('lineup.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    position = db.Column(db.String(50), nullable=False)
    line = db.Column(db.String(20))  # звено (1-6)
    jersey_type = db.Column(db.String(20))  # white, black, goalkeeper
    created_at = db.Column(db.DateTime, default=func.now())