from flask import Blueprint, render_template, redirect, url_for, request
from flask_login import login_required, current_user
import models as models
from functools import wraps
from datetime import datetime

admin_bp = Blueprint('admin', __name__)

def role_required(rola):
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            if current_user.rola != rola:
                return redirect(url_for('auth.login'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# === DASHBOARD ===
@admin_bp.route('/dashboard')
@role_required('admin')
def dashboard():
    return render_template('admin/dashboard.html')


# ============================================================================
# === UZYTKOWNICY ===
# ============================================================================


# === UZYTKOWNICY ===
@admin_bp.route('/uzytkownicy')
@role_required('admin')
def uzytkownicy():
    uzytkownicy = models.Uzytkownik.query.all()
    return render_template('admin/uzytkownicy.html', uzytkownicy=uzytkownicy)


# === UZYTKOWNICY -> WYSWIETL PROFIL ===
@admin_bp.route('/profil-uzytkownika/<int:uzytkownik_id>', methods=['GET', 'POST'])
@role_required('admin')
def profil_uzytkownika(uzytkownik_id):
    uzytkownik = models.Uzytkownik.query.filter_by(id=uzytkownik_id).first()
    if uzytkownik.rola == 'student':
        uzytkownik_profil = models.StudentProfil.query.filter_by(uzytkownik_id=uzytkownik_id).first()
    elif uzytkownik.rola in ['opiekun_zakladowy', 'opiekun_uczelniany']:
        uzytkownik_profil = models.OpiekunProfil.query.filter_by(uzytkownik_id=uzytkownik_id).first()
    else:
        uzytkownik_profil = None
    return render_template('admin/profil_uzytkownika.html', uzytkownik_profil=uzytkownik_profil, uzytkownik=uzytkownik)


# === PROFIL UZYTKOWNIKA -> EDYTUJ ===
@admin_bp.route('/profil-uzytkownika/edytuj/', methods=['POST'])
@role_required('admin')
def profil_uzytkownika_edytuj():
    return 'Edytuj'


# === PROFIL UZYTKOWNIKA -> USUN ===
@admin_bp.route('/profil-uzytkownika/usun/<int:uzytkownik_id>', methods=['POST'])
@role_required('admin')
def profil_uzytkownika_usun(uzytkownik_id):
    return 'tbd'