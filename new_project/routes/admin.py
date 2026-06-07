from flask import Blueprint, flash, render_template, redirect, url_for, request
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
    now = datetime.utcnow()
    profil = None

    aktywne_praktyki = models.FormularzPraktyk.query.filter_by(status='w_trakcie').count()
    niezatwierdzone_harmonogramy = models.HarmonogramPraktyk.query.filter_by(status='oczekuje').count()

    return render_template('admin/dashboard.html', now=now, profil=profil, aktywne_praktyki=aktywne_praktyki, niezatwierdzone_harmonogramy=niezatwierdzone_harmonogramy)


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
# === FORMULARZE PRAKTYK ===
# ============================================================================

# === WSZYSTKIE FORMULARZE ===
@admin_bp.route('/formularze', methods=['GET'])
@role_required('admin')
def formularze():
    formularze_praktyk = models.FormularzPraktyk.query.order_by(
        models.FormularzPraktyk.utworzono.desc()).all()

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
        'admin/formularze.html',
        formularze_praktyk=formularze_praktyk
    )

# === WYSWIETL FORMULARZ ===
@admin_bp.route('/formularz/<int:formularz_id>', methods=['GET'])
@role_required('admin')
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


# === WYSWIETL DZIENNIK ===
@admin_bp.route('/dziennik/<int:student_id>', methods=['GET'])
@role_required('admin')
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
        'admin/dziennik.html',
        logs=logs,
        formularz=formularz,
        student=student
    )

# ============================================================================
# === ZAKONCZ PRAKTYKI ===
# ============================================================================
@admin_bp.route('/zakoncz-praktyki/<int:formularz_id>', methods=['POST'])
@role_required('admin')
def zakoncz_praktyki(formularz_id):
    formularz = models.FormularzPraktyk.query.get_or_404(formularz_id)

    # czy wszystkie wpisy zatwierdzone?
    wpisy = models.DziennikWpis.query.filter_by(student_id=formularz.student_id).all()
    if any(wpis.status != 'zatwierdzony' for wpis in wpisy):
        flash('Nie można zakończyć praktyk. Wszystkie wpisy muszą być zatwierdzone.', 'danger')
        return redirect(url_for('admin.formularz', formularz_id=formularz.id))
    if len(wpisy) < formularz.planowana_liczba_dni:
        flash('Nie można zakończyć praktyk. Liczba zatwierdzonych wpisów jest mniejsza niż planowana liczba dni praktyk.', 'danger')
        return redirect(url_for('admin.formularz', formularz_id=formularz.id))

    formularz.status = 'zakonczone'
    models.db.session.commit()
    flash('Praktyki zostały zakończone.', 'success')
    return redirect(url_for('admin.formularze'))


# === DODAJ OCENY -> FORMULARZ ===
@admin_bp.route('/formularz/oceny/<int:formularz_id>', methods=['GET'])
@role_required('admin')
def formularz_oceny(formularz_id):
    formularz = models.FormularzPraktyk.query.filter_by(id=formularz_id).first_or_404()

    # liczba wpisow
    wpisy = models.DziennikWpis.query.filter_by(student_id=formularz.student_id).all()
    harmonogram = models.HarmonogramPraktyk.query.filter_by(student_id=formularz.student_id).first()
    formularz.wpisy_wymagane = harmonogram.planowana_liczba_dni
    formularz.liczba_wpisow = len(wpisy)

    return render_template('components/formularz_praktyk_oceny.html', formularz=formularz, current_user_profil=None)


# === ZAPISZ OCENY FORMULARZA ===
@admin_bp.route('/zapisz-oceny-formularz/<int:formularz_id>', methods=['POST'])
@role_required('admin')
def zapisz_oceny_formularz(formularz_id):
    formularz = models.FormularzPraktyk.query.get_or_404(formularz_id)

    # logika zapisywania ocen
    ocena_sprawozdanie = request.form.get('ocena_sprawozdanie')
    ocena_egzamin = request.form.get('ocena_egzamin')
    ocena_koncowa = request.form.get('ocena_koncowa')

    #sprawozdanie
    if not ocena_sprawozdanie:
        flash('Ocena sprawozdania jest wymagana.', 'danger')
        return redirect(url_for('admin.formularz_oceny', formularz_id=formularz_id))
    try:
        formularz.ocena_opiekuna_uczelnianego = float(ocena_sprawozdanie) if ocena_sprawozdanie else None
    except (ValueError, TypeError):
        flash('Niepoprawna wartość oceny sprawozdania.', 'danger')
        return redirect(url_for('admin.formularz_oceny', formularz_id=formularz_id))

    #egzamin
    if not ocena_egzamin:
        flash('Ocena egzaminu jest wymagana.', 'danger')
        return redirect(url_for('admin.formularz_oceny', formularz_id=formularz_id))
    try:
        formularz.ocena_opiekuna_zakladowego = float(ocena_egzamin) if ocena_egzamin else None
    except (ValueError, TypeError):
        flash('Niepoprawna wartość oceny zakładowego.', 'danger')
        return redirect(url_for('admin.formularz_oceny', formularz_id=formularz_id))

    #koncowa
    if not ocena_koncowa:
        flash('Ocena końcowa jest wymagana.', 'danger')
        return redirect(url_for('admin.formularz_oceny', formularz_id=formularz_id))
    try:
        formularz.ocena_koncowa = float(ocena_koncowa) if ocena_koncowa else None
    except (ValueError, TypeError):
        flash('Niepoprawna wartość oceny końcowej.', 'danger')
        return redirect(url_for('admin.formularz_oceny', formularz_id=formularz_id))

    # zakonczenie praktyk
    if formularz.ocena_opiekuna_uczelnianego and formularz.ocena_opiekuna_zakladowego and formularz.ocena_koncowa and formularz.ocena_sprawozdanie and formularz.ocena_egzamin:
        formularz.status = 'zakonczone'

    models.db.session.commit()
    flash('Oceny końcowe zostały zapisane.', 'success')

    return redirect(url_for('admin.formularz', formularz_id=formularz.id))


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
    elif uzytkownik.rola == 'opiekun':
        uzytkownik_profil = models.OpiekunProfil.query.filter_by(uzytkownik_id=uzytkownik_id).first()
        uzytkownik.opiekun_profil.liczba_studentow_uczelnia = (
            models.FormularzPraktyk.query.filter_by(
                opiekun_uczelniany_id=uzytkownik_profil.id,
                status='w_trakcie'
            ).count()
        )
        uzytkownik.opiekun_profil.liczba_studentow_zaklad = (
            models.FormularzPraktyk.query.filter_by(
                opiekun_zakladowy_id=uzytkownik_profil.id,
                status='w_trakcie'
            ).count()
        )
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
        uzytkownik_profil.liczba_studentow_uczelnia = models.FormularzPraktyk.query.filter_by(
            opiekun_uczelniany_id=uzytkownik_profil.id,
            status='w_trakcie'
        ).count()

        uzytkownik_profil.liczba_studentow_zaklad = models.FormularzPraktyk.query.filter_by(
            opiekun_zakladowy_id=uzytkownik_profil.id,
            status='w_trakcie'
        ).count()
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
    uzytkownik = models.Uzytkownik.query.get_or_404(uzytkownik_id)
    uzytkownik.konto_aktywne = False
    models.db.session.commit()
    flash(
        f'Użytkownik został zdezaktywowany.',
        'success'
    )

    return redirect(url_for('admin.uzytkownicy'))
