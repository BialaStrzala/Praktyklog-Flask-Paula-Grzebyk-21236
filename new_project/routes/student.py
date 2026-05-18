from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
import models as models
from datetime import datetime, date
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

def get_profile():
    if current_user.rola == 'student':
        profil = models.StudentProfil.query.filter_by(uzytkownik_id=current_user.id).first_or_404()
    if current_user.rola in ['opiekun_uczelniany', 'opiekun_zakladowy']:
        profil = models.OpiekunProfil.query.filter_by(uzytkownik_id=current_user.id).first_or_404()
    return profil


# === DASHBOARD ===
@student_bp.route('/dashboard')
@role_required('student')
def dashboard():
    profil = models.StudentProfil.query.filter_by(uzytkownik_id=current_user.id).first()
    return render_template('student/dashboard.html', profil=profil)


# === PROFIL STUDENTA ===
@student_bp.route('/profil-studenta', methods=['GET', 'POST'])
@role_required('student')
def profil_studenta():
    profil = models.StudentProfil.query.filter_by(uzytkownik_id=current_user.id).first()
    return render_template('student/profil_studenta.html', profil=profil)


# ============================================================================
# === HARMONOGRAM ===
# ============================================================================


# === HARMONOGRAM PRAKTYK -> WYSWIETL ===
@student_bp.route('/harmonogram', methods=['GET', 'POST'])
@role_required('student')
def moj_harmonogram():
    profil = get_profile()

    harmonogram = (
        models.HarmonogramPraktyk.query
        .filter_by(student_id=profil.id)
        .order_by(models.HarmonogramPraktyk.id.desc())
        .first()
    )

    if harmonogram is None:
        flash('Nie masz jeszcze harmonogramu praktyk. Wypełnij poniższy formularz.', 'info')
        return redirect(url_for('student.nowy_harmonogram'))
 
    efekty_uczenia_all = models.EfektUczenia.query.order_by(models.EfektUczenia.kod).all()
 
    return render_template(
        'student/harmonogram_widok.html',
        harmonogram=harmonogram,
        efekty_uczenia_all=efekty_uczenia_all,
    )

# === HARMONOGRAM PRAKTYK -> NOWY ===
@student_bp.route('/harmonogram/nowy', methods=['GET', 'POST'])
@role_required('student')
def nowy_harmonogram():
    profil = get_profile()
 
    # Student moze miec tylko 1 oczekujacy/zaakceptowany harmonogram
    istniejacy = models.HarmonogramPraktyk.query.filter(
        models.HarmonogramPraktyk.student_id == profil.id,
        models.HarmonogramPraktyk.status.in_(['oczekuje', 'zaakceptowany'])
    ).first()
 
    if istniejacy:
        flash('Masz już aktywny harmonogram praktyk. Możesz go przeglądać lub edytować.', 'warning')
        return redirect(url_for('student.moj_harmonogram'))
 
    efekty_uczenia_all = models.EfektUczenia.query.order_by(models.EfektUczenia.kod).all()
    firmy = models.Firma.query.order_by(models.Firma.nazwa).all()
    opiekunowie_zakladowi = (
        models.OpiekunProfil.query
        .filter_by(typ_opiekuna='zakladowy')
        .join(models.OpiekunProfil.uzytkownik)
        .all()
    )
 
    if request.method == 'POST':
        firma_id = request.form.get('firma_id') or None
        opiekun_zakladowy_id = request.form.get('opiekun_zakladowy_id') or None
        planowana_liczba_dni = request.form.get('planowana_liczba_dni', type=int)
        data_start_str = request.form.get('planowana_data_rozpoczecia')
        data_koniec_str = request.form.get('planowana_data_zakonczenia')
 
        # Validate: planowana_liczba_dni MUST be 120
        if planowana_liczba_dni != 120:
            flash('Liczba dni praktyki musi wynosić dokładnie 120 dni roboczych.', 'danger')
            return render_template(
                'student/harmonogram_nowy.html',
                harmonogram=None,
                efekty_uczenia_all=efekty_uczenia_all,
                firmy=firmy,
                opiekunowie_zakladowi=opiekunowie_zakladowi,
            )
 
        # Parse dates
        try:
            planowana_data_rozpoczecia = date.fromisoformat(data_start_str) if data_start_str else None
            planowana_data_zakonczenia = date.fromisoformat(data_koniec_str) if data_koniec_str else None
        except ValueError:
            flash('Nieprawidłowy format daty.', 'danger')
            return render_template(
                'student/harmonogram_nowy.html',
                harmonogram=None,
                efekty_uczenia_all=efekty_uczenia_all,
                firmy=firmy,
                opiekunowie_zakladowi=opiekunowie_zakladowi,
            )
 
        # Validate: all 13 effects must have descriptions
        efekt_opisy = request.form.getlist('efekt_opis[]')
        if len(efekt_opisy) < 13 or any(not opis.strip() for opis in efekt_opisy):
            flash('Wszystkie 13 efektów muszą mieć opisane przykładowe prace.', 'danger')
            return render_template(
                'student/harmonogram_nowy.html',
                harmonogram=None,
                efekty_uczenia_all=efekty_uczenia_all,
                firmy=firmy,
                opiekunowie_zakladowi=opiekunowie_zakladowi,
            )
 
        harmonogram = models.HarmonogramPraktyk(
            student_id=profil.id,
            firma_id=firma_id,
            opiekun_zakladowy_id=opiekun_zakladowy_id,
            planowana_liczba_dni=planowana_liczba_dni,
            planowana_data_rozpoczecia=planowana_data_rozpoczecia,
            planowana_data_zakonczenia=planowana_data_zakonczenia,
            status='oczekuje',
        )
        models.db.session.add(harmonogram)
        models.db.session.flush()
 
        _zapisz_efekty(harmonogram.id)
 
        models.db.session.commit()
        flash('Harmonogram praktyk został przesłany. Czeka na zatwierdzenie przez dziekanat.', 'success')
        return redirect(url_for('student.moj_harmonogram'))
 
    return render_template(
        'student/harmonogram_nowy.html',
        harmonogram=None,
        efekty_uczenia_all=efekty_uczenia_all,
        firmy=firmy,
        opiekunowie_zakladowi=opiekunowie_zakladowi,
    )

# === HARMONOGRAM PRAKTYK -> EDYTUJ ===
@student_bp.route('/harmonogram/edytuj/<int:harmonogram_id>', methods=['GET', 'POST'])
@role_required('student')
def edytuj_harmonogram(harmonogram_id):
    profil = get_profile()
    harmonogram = models.HarmonogramPraktyk.query.filter_by(
        id=harmonogram_id,
        student_id=profil.id
    ).first_or_404()

    if harmonogram.status != 'oczekuje':
        flash('Możesz edytować harmonogram tylko w statusie oczekuje.', 'warning')
        return redirect(url_for('student.moj_harmonogram'))

    efekty_uczenia_all = models.EfektUczenia.query.order_by(models.EfektUczenia.kod).all()
    firmy = models.Firma.query.order_by(models.Firma.nazwa).all()
    opiekunowie_zakladowi = (
        models.OpiekunProfil.query
        .filter_by(typ_opiekuna='zakladowy')
        .join(models.OpiekunProfil.uzytkownik)
        .all()
    )

    if request.method == 'POST':
        firma_id = request.form.get('firma_id') or None
        opiekun_zakladowy_id = request.form.get('opiekun_zakladowy_id') or None
        planowana_liczba_dni = request.form.get('planowana_liczba_dni', type=int)
        data_start_str = request.form.get('planowana_data_rozpoczecia')
        data_koniec_str = request.form.get('planowana_data_zakonczenia')

        if planowana_liczba_dni != 120:
            flash('Liczba dni praktyki musi wynosić dokładnie 120 dni roboczych.', 'danger')
            return render_template(
                'student/harmonogram_nowy.html',
                harmonogram=harmonogram,
                efekty_uczenia_all=efekty_uczenia_all,
                firmy=firmy,
                opiekunowie_zakladowi=opiekunowie_zakladowi,
            )

        try:
            planowana_data_rozpoczecia = date.fromisoformat(data_start_str) if data_start_str else None
            planowana_data_zakonczenia = date.fromisoformat(data_koniec_str) if data_koniec_str else None
        except ValueError:
            flash('Nieprawidłowy format daty.', 'danger')
            return render_template(
                'student/harmonogram_nowy.html',
                harmonogram=harmonogram,
                efekty_uczenia_all=efekty_uczenia_all,
                firmy=firmy,
                opiekunowie_zakladowi=opiekunowie_zakladowi,
            )

        efekt_opisy = request.form.getlist('efekt_opis[]')
        if len(efekt_opisy) < 13 or any(not opis.strip() for opis in efekt_opisy):
            flash('Wszystkie 13 efektów muszą mieć opisane przykładowe prace.', 'danger')
            return render_template(
                'student/harmonogram_nowy.html',
                harmonogram=harmonogram,
                efekty_uczenia_all=efekty_uczenia_all,
                firmy=firmy,
                opiekunowie_zakladowi=opiekunowie_zakladowi,
            )

        harmonogram.firma_id = firma_id
        harmonogram.opiekun_zakladowy_id = opiekun_zakladowy_id
        harmonogram.planowana_liczba_dni = planowana_liczba_dni
        harmonogram.planowana_data_rozpoczecia = planowana_data_rozpoczecia
        harmonogram.planowana_data_zakonczenia = planowana_data_zakonczenia

        models.EfektUczeniaHarmonogram.query.filter_by(harmonogram_praktyk_id=harmonogram.id).delete()
        _zapisz_efekty(harmonogram.id)
        models.db.session.commit()

        flash('Harmonogram praktyk został zaktualizowany.', 'success')
        return redirect(url_for('student.moj_harmonogram'))

    return render_template(
        'student/harmonogram_nowy.html',
        harmonogram=harmonogram,
        efekty_uczenia_all=efekty_uczenia_all,
        firmy=firmy,
        opiekunowie_zakladowi=opiekunowie_zakladowi,
    )


# === ZAPISZ EFEKTY UCZENIA ===
def _zapisz_efekty(harmonogram_id: int):
    efekt_ids = [e.id for e in models.EfektUczenia.query.order_by(models.EfektUczenia.kod).all()]
    efekt_opisy = request.form.getlist('efekt_opis[]')
 
    for efekt_id, opis in zip(efekt_ids, efekt_opisy):
        wpis = models.EfektUczeniaHarmonogram(
            harmonogram_praktyk_id=harmonogram_id,
            efekt_uczenia_id=efekt_id,
            opis=opis.strip() if opis.strip() else None,
        )
        models.db.session.add(wpis)


# ============================================================================
# === FORMULARZ ===
# ============================================================================


# === FORMULARZ PRAKTYK ===
@student_bp.route('/formularz', methods=['GET', 'POST'])
@role_required('student')
def formularz():
    return render_template('formularz.html')


# ============================================================================
# === DZIENNIK ===
# ============================================================================


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