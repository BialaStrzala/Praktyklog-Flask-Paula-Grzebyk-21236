from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

# =========================================================================================================
# === MODELE ===
# =========================================================================================================

# === USER ===
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(50), nullable=False)  # 'student', 'supervisor', 'admin'
    is_active = db.Column(db.Boolean, default=True)

    student_profile = db.relationship('StudentProfile', backref='user', uselist=False)
    supervisor_profile = db.relationship('SupervisorProfile', backref='user', uselist=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


# === STUDENT ===
class StudentProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    full_name = db.Column(db.String(150), nullable=False)
    student_id = db.Column(db.String(50), unique=True, nullable=False)
    college_major = db.Column(db.String(50), nullable=True)
    college_specialization = db.Column(db.String(50), nullable=True)
    internship_place = db.Column(db.String(100), nullable=True)
    internship_start_date = db.Column(db.Date, nullable=True)
    internship_end_date = db.Column(db.Date, nullable=True)

    workplace_supervisor_id = db.Column(db.Integer, db.ForeignKey('supervisor_profile.id'), nullable=True)
    college_supervisor_id = db.Column(db.Integer, db.ForeignKey('supervisor_profile.id'), nullable=True)

    logs = db.relationship('InternshipLog', backref='student', lazy=True)


# === OPIEKUN ===
class SupervisorProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    full_name = db.Column(db.String(150), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # 'college' or 'workplace'
    workplace = db.Column(db.String(50), nullable=True)

    assigned_students = db.relationship('StudentProfile',
                                        foreign_keys=[StudentProfile.workplace_supervisor_id],
                                        backref='workplace_supervisor')
    college_students = db.relationship('StudentProfile',
                                       foreign_keys=[StudentProfile.college_supervisor_id],
                                       backref='college_supervisor')


# === ADMIN ===
class AdminProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    full_name = db.Column(db.String(150), nullable=False)


# === WPIS DO DZIENNIKA ===
class InternshipLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student_profile.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    description = db.Column(db.Text, nullable=False)
    hours_worked = db.Column(db.Float, nullable=True)
    workplace_supervisor_signed = db.Column(db.Boolean, default=False)
    college_supervisor_signed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)


# === POTWIERDZENIE NAUCZANIA ===
class Confirmationlog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student_profile.id'), nullable=False)
    workplace_supervisor_signed = db.Column(db.Boolean, default=False)
    workplace_supervisor_signed_date = db.Column(db.DateTime, nullable=True)
    college_supervisor_opinion = db.Column(db.String(500), nullable=True)
    college_supervisor_signed = db.Column(db.Boolean, default=False)
    college_supervisor_signed_date = db.Column(db.DateTime, nullable=True)
    
    student = db.relationship('StudentProfile', backref='confirmations', foreign_keys=[student_id])
    learning_effects = db.relationship('LearningEffects', backref='confirmation', lazy=True)


# === EFEKTY UCZENIA SIE ===
class LearningEffects(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    confirmation_id = db.Column(db.Integer, db.ForeignKey('confirmationlog.id'), nullable=True)
    number = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(200), nullable=True)
    is_approved = db.Column(db.Boolean, default=False)