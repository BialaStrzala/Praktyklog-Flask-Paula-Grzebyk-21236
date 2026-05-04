from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
import models as models
from datetime import datetime
from functools import wraps

student_bp = Blueprint('student', __name__)

def role_required(rola):
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            if current_user.rola != rola:
                flash('Access denied.')
                return redirect(url_for('auth.login'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# === DASHBOARD ===
@student_bp.route('/dashboard')
@role_required('student')
def dashboard():
    return render_template('student/dashboard.html')


# === PROFIL STUDENTA ===
@student_bp.route('/profil-studenta', methods=['GET', 'POST'])
@role_required('student')
def profil_studenta():
    profil = models.StudentProfil.query.filter_by(uzytkownik_id=current_user.id).first()
    return render_template('student/profil_studenta.html', profil=profil)


# === HARMONOGRAM PRAKTYK ===
@student_bp.route('/harmonogram', methods=['GET', 'POST'])
@role_required('student')
def harmonogram():
    return 'harmonogram'

# === FORMULARZ PRAKTYK ===
@student_bp.route('/formularz', methods=['GET', 'POST'])
@role_required('student')
def harmonogram():
    return render_template('formularz.html')


# === DZIENNIK ===
@student_bp.route('/dziennik', methods=['GET', 'POST'])
@role_required('student')
def dziennik():
    profil = models.StudentProfil.query.filter_by(uzytkownik_id=current_user.id).first()
    wpisy = models.DziennikWpis.query.filter_by(student_id=current_user.id).all()
    return render_template('student/dziennik.html', profil=profil, wpisy=wpisy)


# === DZIENNIK -> USUN WPIS
@student_bp.route('/dziennik/usun/<int:wpis_id>', methods=['POST'])
@role_required('student')
def dziennik_usun(wpis_id):
    return 'tba'


# === DZIENNIK -> EDYTUJ WPIS
@student_bp.route('/dziennik/edytuj', methods=['POST'])
@role_required('student')
def dziennik_edytuj():
    return 'tba'