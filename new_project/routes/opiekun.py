from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
import models as models
from datetime import datetime
from functools import wraps

opiekun_bp = Blueprint('opiekun', __name__)

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

def get_profile():
    if current_user.rola == 'student':
        profil = models.StudentProfil.query.filter_by(uzytkownik_id=current_user.id).first_or_404()
    if current_user.rola == 'opiekun':
        profil = models.OpiekunProfil.query.filter_by(uzytkownik_id=current_user.id).first_or_404()
    return profil


# ============================================================================
# === DASHBOARD ===
# ============================================================================

@opiekun_bp.route('/dashboard')
@role_required('opiekun')
def dashboard():
    profil = get_profile()
    now = datetime.utcnow()
    studenci_aktywni = models.StudentProfil.query.join(models.FormularzPraktyk).filter(
        (models.FormularzPraktyk.opiekun_zakladowy_id == profil.id) | 
        (models.FormularzPraktyk.opiekun_uczelniany_id == profil.id),
        models.FormularzPraktyk.status == 'w_trakcie'
    ).distinct().all()

    wpisy_oczekujace = models.DziennikWpis.query.join(models.StudentProfil).join(models.FormularzPraktyk).filter(
        (models.FormularzPraktyk.opiekun_zakladowy_id == profil.id) | 
        (models.FormularzPraktyk.opiekun_uczelniany_id == profil.id),
        models.DziennikWpis.status == 'w_trakcie'
    ).all()
    
    return render_template('opiekun/dashboard.html', profil=profil, now=now, studenci_aktywni=studenci_aktywni, wpisy_oczekujace=wpisy_oczekujace)


# ============================================================================
# === DZIENNIK ===
# ============================================================================

# === WSZYSTKIE FORMULARZE ===
@opiekun_bp.route('/formularze', methods=['GET'])
@role_required('opiekun')
def formularze():
    current_user_profile = models.OpiekunProfil.query.filter_by(
        uzytkownik_id=current_user.id
    ).first()

    if current_user_profile.typ_opiekuna == 'zakladowy':
        formularze_praktyk = models.FormularzPraktyk.query.filter_by(
            opiekun_zakladowy_id=current_user_profile.id
        ).order_by(
            models.FormularzPraktyk.utworzono.desc()
        ).all()
    else:
        formularze_praktyk = models.FormularzPraktyk.query.filter_by(
            opiekun_uczelniany_id=current_user_profile.id
        ).order_by(
            models.FormularzPraktyk.utworzono.desc()
        ).all()

    # liczba wpisow
    for formularz in formularze_praktyk:
        wpisy = models.DziennikWpis.query.filter_by(
            student_id=formularz.student_id
        ).all()
        harmonogram = models.HarmonogramPraktyk.query.filter_by(
            student_id=formularz.student_id
        ).first()
        formularz.wpisy_wymagane = harmonogram.planowana_liczba_dni
        formularz.wpisy_dodane = len(wpisy)
        formularz.wpisy_do_zatwierdzenia = len([
            wpis for wpis in wpisy
            if wpis.status == 'w_trakcie'
        ])

        # okres praktyk
        formularz.planowana_liczba_dni = harmonogram.planowana_liczba_dni if harmonogram and getattr(harmonogram, 'planowana_liczba_dni', None) else 120
        formularz.utworzono_formatted = formularz.utworzono.strftime('%d.%m.%Y') if getattr(formularz, 'utworzono', None) else 'Brak daty'
        formularz.data_rozpoczecia_formatted = formularz.data_rozpoczecia.strftime('%d.%m.%Y') if getattr(formularz, 'data_rozpoczecia', None) else None
        formularz.data_zakonczenia_formatted = formularz.data_zakonczenia.strftime('%d.%m.%Y') if getattr(formularz, 'data_zakonczenia', None) else None
        try:
            if formularz.data_rozpoczecia and formularz.data_zakonczenia:
                formularz.pozostale_dni = (formularz.data_zakonczenia - formularz.data_rozpoczecia).days
            else:
                formularz.pozostale_dni = None
        except Exception:
            formularz.pozostale_dni = None

    return render_template(
        'opiekun/formularze.html',
        formularze_praktyk=formularze_praktyk
    )


# === WYSWIETL DZIENNIK ===
@opiekun_bp.route('/dziennik/<int:student_id>', methods=['GET'])
@role_required('opiekun')
def dziennik(student_id):

    logs = models.DziennikWpis.query.filter_by(
        student_id=student_id
    ).order_by(
        models.DziennikWpis.nr_dnia.asc()
    ).all()

    formularz = models.FormularzPraktyk.query.filter_by(
        student_id=student_id,
        status='w_trakcie'
    ).first()

    student = models.StudentProfil.query.filter_by(
        id=student_id
    ).first()

    return render_template(
        'opiekun/dziennik.html',
        logs=logs,
        formularz=formularz,
        student=student
    )


# === ZATWIERDZ WSZYSTKIE WPISY ===
@opiekun_bp.route('/dziennik/zatwierdz/<int:student_id>', methods=['POST'])
@role_required('opiekun')
def dziennik_zatwierdz(student_id):

    logs = models.DziennikWpis.query.filter_by(
        student_id=student_id
    ).all()

    for log in logs:

        # pomijaj już zatwierdzone / odrzucone
        if log.status in ['zatwierdzony', 'odrzucony']:
            continue

        log.status = 'zatwierdzony'
        log.data_zatwierdzenia = datetime.utcnow()

    models.db.session.commit()

    flash(
        'Wpisy zostały zatwierdzone.',
        'success'
    )

    return redirect(
        url_for(
            'opiekun.dziennik',
            student_id=student_id
        )
    )


# === ODRZUC WPIS ===
@opiekun_bp.route('/dziennik/odrzuc/<int:wpis_id>', methods=['POST'])
@role_required('opiekun')
def dziennik_odrzuc(wpis_id):

    wpis = models.DziennikWpis.query.filter_by(
        id=wpis_id
    ).first_or_404()

    powod_odrzucenia = request.form.get(
        'powod_odrzucenia',
        ''
    ).strip()

    if not powod_odrzucenia:

        flash(
            'Musisz podać powód odrzucenia wpisu.',
            'danger'
        )

        return redirect(
            url_for(
                'opiekun.dziennik',
                student_id=wpis.student_id
            )
        )

    wpis.status = 'odrzucony'
    wpis.powod_odrzucenia = powod_odrzucenia

    models.db.session.commit()

    flash(
        'Wpis został odrzucony.',
        'warning'
    )

    return redirect(
        url_for(
            'opiekun.dziennik',
            student_id=wpis.student_id
        )
    )


# ============================================================================
# === FORMULARZ ===
# ============================================================================

@opiekun_bp.route('/formularz/<int:formularz_id>', methods=['GET'])
@role_required('opiekun')
def formularz(formularz_id):
    formularz = models.FormularzPraktyk.query.filter_by(id=formularz_id).first_or_404()

    # liczba wpisow
    wpisy = models.DziennikWpis.query.filter_by(student_id=formularz.student_id).all()
    harmonogram = models.HarmonogramPraktyk.query.filter_by(student_id=formularz.student_id).first()
    formularz.wpisy_wymagane = harmonogram.planowana_liczba_dni
    formularz.liczba_wpisow = len(wpisy)

    print(formularz.wpisy_wymagane)
    print(formularz.liczba_wpisow)

    return render_template('components/formularz_praktyk.html', formularz=formularz)


# ============================================================================
# === PROFILE ===
# ============================================================================

# === WLASNY PROFIL ===
@opiekun_bp.route('/profil_uzytkownika', methods=['GET'])
@role_required('opiekun')
def profil_uzytkownika():
    uzytkownik = current_user
    profil = get_profile()
    profil.liczba_studentow_uczelnia = models.FormularzPraktyk.query.filter_by(
        opiekun_uczelniany_id=profil.id,
        status='w_trakcie'
    ).count()

    profil.liczba_studentow_zaklad = models.FormularzPraktyk.query.filter_by(
        opiekun_zakladowy_id=profil.id,
        status='w_trakcie'
    ).count()

    return render_template('components/profil_uzytkownika.html', uzytkownik=uzytkownik, profil=profil)


# === WLASNY PROFIL -> EDYTUJ ===
@opiekun_bp.route('/profil_uzytkownika/edytuj', methods=['GET', 'POST'])
@role_required('opiekun')
def edytuj_profil_uzytkownika():
    profil = get_profile()
    uzytkownik = current_user
    
    if request.method == 'POST':
        telefon = request.form.get('telefon') or None
        current_user.telefon = telefon
        models.db.session.commit()
        return redirect(url_for('opiekun.profil_uzytkownika'))

    return render_template('components/profil_uzytkownika_edytuj.html', uzytkownik=uzytkownik)


# === LISTA STUDENTOW ===
@opiekun_bp.route('/lista_studentow', methods=['GET'])
@role_required('opiekun')
def lista_studentow():
    current_user_profile = get_profile()

    if current_user_profile.typ_opiekuna == 'zakladowy':
        studenci = (
            models.Uzytkownik.query
            .join(models.StudentProfil)
            .join(
                models.FormularzPraktyk,
                models.FormularzPraktyk.student_id == models.StudentProfil.id
            )
            .filter(
                models.FormularzPraktyk.opiekun_zakladowy_id == current_user_profile.id
            )
            .distinct()
            .all()
        )
    else:
        studenci = (
            models.Uzytkownik.query
            .join(models.StudentProfil)
            .join(
                models.FormularzPraktyk,
                models.FormularzPraktyk.student_id == models.StudentProfil.id
            )
            .filter(
                models.FormularzPraktyk.opiekun_uczelniany_id == current_user_profile.id
            )
            .distinct()
            .all()
        )

    return render_template(
        'opiekun/lista_studentow.html',
        studenci=studenci
    )


# === PROFIL STUDENTA ===
@opiekun_bp.route('/profil_studenta/<int:uzytkownik_id>', methods=['GET'])
@role_required('opiekun')
def profil_studenta(uzytkownik_id):
    print(uzytkownik_id)
    uzytkownik = models.Uzytkownik.query.filter_by(
        id=uzytkownik_id
    ).first_or_404()

    print(uzytkownik)
    return render_template(
        'components/profil_uzytkownika.html',
        uzytkownik=uzytkownik
    )