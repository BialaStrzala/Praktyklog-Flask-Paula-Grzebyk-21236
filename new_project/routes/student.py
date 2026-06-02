from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
import models as models
from datetime import datetime, date
from functools import wraps
import re

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
    if current_user.rola == 'opiekun':
        profil = models.OpiekunProfil.query.filter_by(uzytkownik_id=current_user.id).first_or_404()
    return profil


# ============================================================================
# === DASHBOARD ===
# ============================================================================

@student_bp.route('/dashboard')
@role_required('student')
def dashboard():
    profil = models.StudentProfil.query.filter_by(uzytkownik_id=current_user.id).first()
    formularze_praktyk = models.FormularzPraktyk.query.filter_by(student_id=profil.id).all()
    now = datetime.utcnow()

    total_approved_logs = models.DziennikWpis.query.filter_by(student_id=profil.id, status='zatwierdzony').count()
    total_logs = models.DziennikWpis.query.filter_by(student_id=profil.id).count()

    for formularz in formularze_praktyk:
        formularz.wpisy_dodane = total_logs
        harmonogram = None
        if getattr(formularz, 'harmonogram_praktyk', None):
            harmonogram = models.HarmonogramPraktyk.query.get(formularz.harmonogram_praktyk)
        formularz.wpisy_wymagane = harmonogram.planowana_liczba_dni if harmonogram and getattr(harmonogram, 'planowana_liczba_dni', None) else 120

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

        formularz.opiekun_zakladowy_user = None
        formularz.opiekun_uczelniany_user = None
        if getattr(formularz, 'opiekun_zakladowy_id', None):
            op = models.OpiekunProfil.query.get(formularz.opiekun_zakladowy_id)
            formularz.opiekun_zakladowy_user = getattr(op, 'uzytkownik', None)
        if getattr(formularz, 'opiekun_uczelniany_id', None):
            op2 = models.OpiekunProfil.query.get(formularz.opiekun_uczelniany_id)
            formularz.opiekun_uczelniany_user = getattr(op2, 'uzytkownik', None)

    return render_template('student/dashboard.html', profil=profil, formularze_praktyk=formularze_praktyk, total_logs=total_logs, now=now)


# ============================================================================
# === PROFIL ===
# ============================================================================

# === WYSWIETL ===
@student_bp.route('/profil-uzytkownika', methods=['GET', 'POST'])
@role_required('student')
def profil_uzytkownika():
    uzytkownik = current_user
    return render_template('components/profil_uzytkownika.html', uzytkownik=uzytkownik)

# === EDYTUJ ===
@student_bp.route('/profil-uzytkownika/edytuj', methods=['GET', 'POST'])
@role_required('student')
def edytuj_profil_uzytkownika():
    profil = models.StudentProfil.query.filter_by(
        uzytkownik_id=current_user.id
    ).first()

    uzytkownik = current_user

    if request.method == 'POST':
        telefon = (request.form.get('telefon') or '').strip()
        kierunek = (request.form.get('kierunek') or '').strip()
        specjalnosc = (request.form.get('specjalnosc') or '').strip()
        semestr = (request.form.get('semestr') or '').strip()
        rok_akademicki = (request.form.get('rok_akademicki') or '').strip()

        if telefon:
            telefon_clean = re.sub(r'[\s\-]', '', telefon)
            if not re.fullmatch(r'^\+?\d{9,15}$', telefon_clean):
                flash(
                    'Nieprawidłowy numer telefonu.',
                    'danger'
                )
                return render_template(
                    'components/profil_uzytkownika_edytuj.html',
                    uzytkownik=uzytkownik
                )
            telefon = telefon_clean
        else:
            telefon = None

        if semestr:
            try:
                semestr = int(semestr)
                if semestr < 1 or semestr > 8:
                    raise ValueError()

            except ValueError:
                flash(
                    'Semestr musi być liczbą od 1 do 8.',
                    'danger'
                )
                return render_template(
                    'components/profil_uzytkownika_edytuj.html',
                    uzytkownik=uzytkownik
                )
        else:
            semestr = None

        if rok_akademicki:
            rok_akademicki = re.sub(
                r'\s+',
                '',
                rok_akademicki
            )
            match = re.fullmatch(
                r'(\d{4})/(\d{4})',
                rok_akademicki
            )

            if not match:
                flash(
                    'Rok akademicki musi mieć format 2025/2026.',
                    'danger'
                )
                return render_template(
                    'components/profil_uzytkownika_edytuj.html',
                    uzytkownik=uzytkownik
                )

            rok_start = int(match.group(1))
            rok_koniec = int(match.group(2))

            if rok_koniec != rok_start + 1:
                flash(
                    'Niepoprawny rok akademicki.',
                    'danger'
                )
                return render_template(
                    'components/profil_uzytkownika_edytuj.html',
                    uzytkownik=uzytkownik
                )
        else:
            rok_akademicki = None


        if kierunek:
            kierunek = kierunek[0].upper() + kierunek[1:]
        else:
            kierunek = None

        if specjalnosc:
            specjalnosc = specjalnosc[0].upper() + specjalnosc[1:]
        else:
            specjalnosc = None

        current_user.telefon = telefon
        profil.kierunek = kierunek
        profil.specjalnosc = specjalnosc
        profil.semestr = semestr
        profil.rok_akademicki = rok_akademicki
        models.db.session.commit()
        flash(
            'Profil został zaktualizowany.',
            'success'
        )
        return redirect(
            url_for('student.profil_uzytkownika')
        )

    return render_template(
        'components/profil_uzytkownika_edytuj.html',
        uzytkownik=uzytkownik
    )


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
    firmy = models.Firma.query.order_by(models.Firma.nazwa).distinct().all()
    opiekunowie_zakladowi = (
        models.OpiekunProfil.query
        .filter_by(typ_opiekuna='zakladowy')
        .join(models.OpiekunProfil.uzytkownik)
        .distinct().all()
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
 
        # walidacja
        efekt_opisy = request.form.getlist('efekt_opis[]')
        blad = validate_harmonogram(
            firma_id=firma_id,
            opiekun_zakladowy_id=opiekun_zakladowy_id,
            planowana_liczba_dni=planowana_liczba_dni,
            data_rozpoczecia=planowana_data_rozpoczecia,
            data_zakonczenia=planowana_data_zakonczenia,
            efekt_opisy=efekt_opisy
        )
        if blad:
            flash(blad, 'danger')
            return render_template(
                'student/harmonogram_nowy.html',
                harmonogram=harmonogram if 'harmonogram' in locals() else None,
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
        blad = validate_harmonogram(
            firma_id=firma_id,
            opiekun_zakladowy_id=opiekun_zakladowy_id,
            planowana_liczba_dni=planowana_liczba_dni,
            data_rozpoczecia=planowana_data_rozpoczecia,
            data_zakonczenia=planowana_data_zakonczenia,
            efekt_opisy=efekt_opisy
        )
        if blad:
            flash(blad, 'danger')
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


def validate_harmonogram(
    firma_id,
    opiekun_zakladowy_id,
    planowana_liczba_dni,
    data_rozpoczecia,
    data_zakonczenia,
    efekt_opisy
):
    # liczba dni
    if planowana_liczba_dni != 120:
        return 'Liczba dni praktyki musi wynosić dokładnie 120 dni roboczych.'

    # firma i opiekun
    opiekun = models.OpiekunProfil.query.get(opiekun_zakladowy_id)

    if not opiekun:
        return 'Wybrany opiekun zakładowy nie istnieje.'

    if str(opiekun.firma_id) != str(firma_id):
        return 'Wybrany opiekun zakładowy nie należy do wskazanej firmy.'

    # daty
    if not data_rozpoczecia or not data_zakonczenia:
        return 'Należy podać datę rozpoczęcia i zakończenia praktyk.'

    if data_zakonczenia <= data_rozpoczecia:
        return 'Data zakończenia musi być późniejsza niż data rozpoczęcia.'

    # minimum 120 dni kalendarzowych między datami
    liczba_dni = (data_zakonczenia - data_rozpoczecia).days

    if liczba_dni < 120:
        return 'Okres praktyk musi obejmować co najmniej 120 dni.'

    # efekty uczenia
    if len(efekt_opisy) < 13:
        return 'Wszystkie 13 efektów muszą mieć opisane przykładowe prace.'

    if any(not opis.strip() for opis in efekt_opisy):
        return 'Wszystkie 13 efektów muszą mieć opisane przykładowe prace.'

    return None

# ============================================================================
# === FORMULARZ ===
# ============================================================================

# === FORMULARZ PRAKTYK ===
@student_bp.route('/formularz', methods=['GET', 'POST'])
@role_required('student')
def formularz():
    profil = models.StudentProfil.query.filter_by(uzytkownik_id=current_user.id).first_or_404()
    formularz = models.FormularzPraktyk.query.filter_by(student_id=profil.id).first()
    if formularz is None:
        flash('Nie masz jeszcze formularza praktyk. Wypełnij poniższy formularz.', 'info')
        return redirect(url_for('student.moj_harmonogram'))
    harmonogram = models.HarmonogramPraktyk.query.filter_by(student_id=profil.id).first()
    formularz.wpisy_wymagane = harmonogram.planowana_liczba_dni if harmonogram and getattr(harmonogram, 'planowana_liczba_dni', None) else 120
    formularz.liczba_wpisow = models.DziennikWpis.query.filter_by(student_id=profil.id).count()

    return render_template('components/formularz_praktyk.html',
        profil=profil,
        formularz=formularz
    )


# ============================================================================
# === DZIENNIK ===
# ============================================================================

# === ZAPISZ EFEKTY WPISU ===
def _zapisz_efekty_wpisu(wpis_id: int, selected_effect_ids: list[str]):
    models.DziennikEfekt.query.filter_by(
        dziennik_wpis_id=wpis_id
    ).delete()

    try:
        selected_ids = {int(i) for i in selected_effect_ids if i}
    except ValueError:
        selected_ids = set()

    for efekt_id in selected_ids:
        models.db.session.add(
            models.DziennikEfekt(
                dziennik_wpis_id=wpis_id,
                efekt_uczenia_id=efekt_id,
            )
        )

# walidacja
def waliduj_wpis_dziennika(
    formularz,
    entry_date,
    hours,
    description
):
    if not formularz:
        return 'Nie posiadasz aktywnego formularza praktyk.'

    if formularz.status in ['zakonczone', 'porzucone']:
        return 'Nie można dodawać wpisów do zakończonych lub porzuconych praktyk.'

    if not description.strip():
        return 'Opis wykonanych prac jest wymagany.'

    if hours <= 0:
        return 'Liczba godzin musi być większa od 0.'

    if not formularz.data_rozpoczecia:
        return 'Formularz praktyk nie posiada daty rozpoczęcia.'

    if entry_date < formularz.data_rozpoczecia:
        return (
            f'Data wpisu nie może być wcześniejsza niż '
            f'data rozpoczęcia praktyk ({formularz.data_rozpoczecia:%d.%m.%Y}).'
        )

    if formularz.data_zakonczenia and entry_date > formularz.data_zakonczenia:
        return (
            f'Data wpisu nie może być późniejsza niż '
            f'data zakończenia praktyk ({formularz.data_zakonczenia:%d.%m.%Y}).'
        )

    return None

# === DZIENNIK - WSZYSTKIE WPISY ===
@student_bp.route('/dziennik', methods=['GET', 'POST'])
@role_required('student')
def dziennik():

    profil = models.StudentProfil.query.filter_by(
        uzytkownik_id=current_user.id
    ).first_or_404()

    efekty_uczenia_all = models.EfektUczenia.query.order_by(
        models.EfektUczenia.kod
    ).all()

    formularz = models.FormularzPraktyk.query.filter_by(student_id=profil.id, status='w_trakcie').first()

    # nowy wpis
    if request.method == 'POST':
        date_str = request.form.get('date')
        description = request.form.get('description', '').strip()
        hours_worked = request.form.get('hours_worked')
        selected_effect_ids = request.form.getlist('effect_ids[]')

        # walidacja
        if not date_str or not description:
            flash(
                'Data i opis wykonanych prac są wymagane.',
                'danger'
            )
            return redirect(url_for('student.dziennik'))

        # data
        try:
            entry_date = date.fromisoformat(date_str)
        except ValueError:
            flash(
                'Nieprawidłowy format daty.',
                'danger'
            )
            return redirect(url_for('student.dziennik'))

        # godziny
        try:
            hours = float(hours_worked) if hours_worked else 0.0
        except ValueError:
            flash(
                'Nieprawidłowa liczba godzin.',
                'danger'
            )
            return redirect(url_for('student.dziennik'))

        # nowy wpis
        new_log = models.DziennikWpis(
            student_id=profil.id,
            nr_dnia=(
                models.DziennikWpis.query.filter_by(
                    student_id=profil.id
                ).count() + 1
            ),
            data=entry_date,
            liczba_godzin=hours,
            opis=description,
            status='w_trakcie',
        )

        blad = waliduj_wpis_dziennika(
            formularz=formularz,
            entry_date=entry_date,
            hours=float(hours or 0),
            description=description
        )
        if blad:
            flash(blad, 'danger')
            return redirect(url_for('student.dziennik'))

        models.db.session.add(new_log)
        models.db.session.flush()

        # efekty nauki
        _zapisz_efekty_wpisu(
            wpis_id=new_log.id,
            selected_effect_ids=selected_effect_ids
        )

        models.db.session.commit()
        return redirect(url_for('student.dziennik'))

    # wpisy
    wpisy = models.DziennikWpis.query.filter_by(
        student_id=profil.id
    ).order_by(
        models.DziennikWpis.nr_dnia.asc()
    ).all()

    total_working_days = len(wpisy)

    total_hours_worked = sum(
        w.liczba_godzin or 0
        for w in wpisy
    )

    return render_template(
        'student/dziennik.html',
        profil=profil,
        logs=wpisy,
        efekty_uczenia_all=efekty_uczenia_all,
        total_working_days=total_working_days,
        total_hours_worked=total_hours_worked,
        formularz=formularz
    )


# === DZIENNIK -> EDYTUJ WPIS ===
@student_bp.route('/dziennik/wpis/edytuj/<int:wpis_id>', methods=['GET', 'POST'])
@role_required('student')
def dziennik_wpis_edytuj(wpis_id):
    profil = models.StudentProfil.query.filter_by(
        uzytkownik_id=current_user.id
    ).first_or_404()

    wpis = models.DziennikWpis.query.filter_by(
        id=wpis_id,
        student_id=profil.id
    ).first_or_404()

    efekty_uczenia_all = models.EfektUczenia.query.order_by(
        models.EfektUczenia.kod
    ).all()

    formularz = models.FormularzPraktyk.query.filter_by(student_id=profil.id, status='w_trakcie').first()

    if request.method == 'POST':
        date_str = request.form.get('date')
        description = request.form.get('description', '').strip()
        hours_worked = request.form.get('hours_worked')
        selected_effect_ids = request.form.getlist('effect_ids[]')

        # walidacja
        if not date_str or not description:
            flash(
                'Data i opis są wymagane.',
                'danger'
            )
            return redirect(
                url_for(
                    'student.dziennik_wpis_edytuj',
                    wpis_id=wpis.id
                )
            )

        # data
        try:
            wpis.data = date.fromisoformat(date_str)

        except ValueError:
            flash(
                'Nieprawidłowy format daty.',
                'danger'
            )

            return redirect(
                url_for(
                    'student.dziennik_wpis_edytuj',
                    wpis_id=wpis.id
                )
            )
        try:
            wpis.liczba_godzin = (
                float(hours_worked)
                if hours_worked else 0.0
            )

        except ValueError:
            wpis.liczba_godzin = 0.0

        # opis
        wpis.opis = description
        wpis.data = date.fromisoformat(date_str)
        wpis.opis = description
        wpis.liczba_godzin = float(hours_worked or 0)

        if wpis.status == 'odrzucony':
            wpis.status = 'w_trakcie'
            wpis.powod_odrzucenia = None

        # efekty nauki
        _zapisz_efekty_wpisu(
            wpis_id=wpis.id,
            selected_effect_ids=selected_effect_ids
        )

        blad = waliduj_wpis_dziennika(
            formularz=formularz,
            entry_date=date.fromisoformat(date_str),
            hours=float(hours_worked or 0),
            description=description
        )
        if blad:
            flash(blad, 'danger')
            return redirect(url_for('student.dziennik'))

        models.db.session.commit()
        flash('Wpis został zaktualizowany.', 'success')
        return redirect(url_for('student.dziennik'))

    return render_template(
        'components/dziennik_wpis_edytuj.html',
        profil=profil,
        log=wpis,
        efekty_uczenia_all=efekty_uczenia_all,
    )


# === DZIENNIK -> USUN WPIS ===
@student_bp.route('/dziennik/usun/<int:wpis_id>', methods=['POST'])
@role_required('student')
def dziennik_usun(wpis_id):
    profil = models.StudentProfil.query.filter_by(
        uzytkownik_id=current_user.id
    ).first_or_404()

    wpis = models.DziennikWpis.query.filter_by(
        id=wpis_id,
        student_id=profil.id
    ).first_or_404()

    models.db.session.delete(wpis)
    models.db.session.commit()
    return redirect(url_for('student.dziennik'))