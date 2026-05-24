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
# === HARMONOGRAMY PRAKTYK ===
# ============================================================================

# === WYSWIETL LISTE ===
@admin_bp.route('/harmonogramy/', methods=['GET'])
@role_required('admin')
def harmonogramy():

    harmonogramy = models.HarmonogramPraktyk.query.filter_by(
        status='oczekuje'
    ).order_by(
        models.HarmonogramPraktyk.utworzono.desc()
    ).all()

    return render_template(
        'components/harmonogramy_wszystkie.html',
        harmonogramy=harmonogramy
    )


# === JEDEN HARMONOGRAM ===
@admin_bp.route('/harmonogram/<int:harmonogram_id>', methods=['GET'])
@role_required('admin')
def harmonogram(harmonogram_id):

    harmonogram = models.HarmonogramPraktyk.query.filter_by(
        id=harmonogram_id
    ).first_or_404()

    profil = models.StudentProfil.query.filter_by(
        id=harmonogram.student_id
    ).first()

    opiekunowie_uczelniani = models.OpiekunProfil.query.filter_by(
        typ_opiekuna='uczelniany'
    ).all()

    return render_template(
        'components/harmonogram_widok.html',
        profil=profil,
        harmonogram=harmonogram,
        opiekunowie_uczelniani=opiekunowie_uczelniani
    )


# === HARMONOGRAM -> AKCEPTUJ ===
@admin_bp.route('/harmonogram/akceptuj/<int:harmonogram_id>', methods=['POST'])
@role_required('admin')
def harmonogram_akceptuj(harmonogram_id):

    harmonogram = models.HarmonogramPraktyk.query.filter_by(
        id=harmonogram_id
    ).first_or_404()

    opiekun_uczelniany_id = request.form.get(
        'opiekun_uczelniany_id'
    )

    if not opiekun_uczelniany_id:
        return redirect(
            url_for(
                'admin.harmonogram',
                harmonogram_id=harmonogram.id
            )
        )

    harmonogram.opiekun_uczelniany_id = opiekun_uczelniany_id
    harmonogram.status = 'zaakceptowany'

    formularz = models.FormularzPraktyk(
        student_id=harmonogram.student_id,
        opiekun_zakladowy_id=harmonogram.opiekun_zakladowy_id,
        opiekun_uczelniany_id=opiekun_uczelniany_id,
        firma_id=harmonogram.firma_id,
        harmonogram_praktyk_id=harmonogram.id,
        status='w_trakcie'
    )

    models.db.session.add(formularz)
    models.db.session.commit()


    return redirect(url_for('admin.harmonogramy'))


# === HARMONOGRAM -> ODRZUĆ ===
@admin_bp.route('/harmonogram/odrzuc/<int:harmonogram_id>', methods=['POST'])
@role_required('admin')
def harmonogram_odrzuc(harmonogram_id):

    harmonogram = models.HarmonogramPraktyk.query.filter_by(
        id=harmonogram_id
    ).first_or_404()

    powod_odrzucenia = request.form.get(
        'powod_odrzucenia',
        ''
    ).strip()

    harmonogram.status = 'odrzucony'
    harmonogram.powod_odrzucenia = powod_odrzucenia

    models.db.session.commit()


    return redirect(url_for('admin.harmonogramy'))

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
    return render_template('components/profil_uzytkownika.html', uzytkownik_profil=uzytkownik_profil, uzytkownik=uzytkownik)


# === PROFIL UZYTKOWNIKA -> EDYTUJ ===
@admin_bp.route('/profil-uzytkownika/edytuj/<int:uzytkownik_id>', methods=['GET', 'POST'])
@role_required('admin')
def profil_uzytkownika_edytuj(uzytkownik_id):
    uzytkownik = models.Uzytkownik.query.filter_by(id=uzytkownik_id).first()
    if uzytkownik.rola == 'student':
        uzytkownik_profil = models.StudentProfil.query.filter_by(uzytkownik_id=uzytkownik_id).first()
    elif uzytkownik.rola in ['opiekun_zakladowy', 'opiekun_uczelniany']:
        uzytkownik_profil = models.OpiekunProfil.query.filter_by(uzytkownik_id=uzytkownik_id).first()
    else:
        uzytkownik_profil = None
    
    return render_template('components/profil_uzytkownika_edytuj.html',
        uzytkownik=uzytkownik,
        uzytkownik_profil=uzytkownik_profil
    )


# === PROFIL UZYTKOWNIKA -> USUN ===
@admin_bp.route('/profil-uzytkownika/usun/<int:uzytkownik_id>', methods=['POST'])
@role_required('admin')
def profil_uzytkownika_usun(uzytkownik_id):
    return 'tbd'