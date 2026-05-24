from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from models import (
    db,
    HarmonogramPraktyk, EfektUczeniaHarmonogram, EfektUczenia,
    StudentProfil, FormularzPraktyk,
)
from datetime import date

harmonogram_api_bp = Blueprint('api_harmonogram', __name__, url_prefix='/api/harmonogram')


# ─────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────

def _require_roles(*roles):
    return None
    if not current_user.is_authenticated:
        return jsonify({'error': 'Wymagane logowanie.'}), 401
    if current_user.rola not in roles:
        return jsonify({'error': 'Brak uprawnień.'}), 403
    return None


def _efekt_to_dict(e: EfektUczeniaHarmonogram) -> dict:
    return {
        'id':                    e.id,
        'efekt_uczenia_id':      e.efekt_uczenia_id,
        'kod':                   e.efekt.kod  if e.efekt else None,
        'opis_efektu':           e.efekt.opis if e.efekt else None,
        'opis_realizacji':       e.opis,
    }


def _harmonogram_to_dict(h: HarmonogramPraktyk, include_efekty: bool = True) -> dict:
    d = {
        'id':                          h.id,
        'student_id':                  h.student_id,
        'opiekun_zakladowy_id':        h.opiekun_zakladowy_id,
        'firma_id':                    h.firma_id,
        'planowana_liczba_dni':        h.planowana_liczba_dni,
        'planowana_data_rozpoczecia':  h.planowana_data_rozpoczecia.isoformat()
                                       if h.planowana_data_rozpoczecia else None,
        'planowana_data_zakonczenia':  h.planowana_data_zakonczenia.isoformat()
                                       if h.planowana_data_zakonczenia else None,
        'status':                      h.status,
        'powod_odrzucenia':            h.powod_odrzucenia,
        'utworzono':                   h.utworzono.isoformat() if h.utworzono else None,
    }
    if include_efekty:
        d['efekty'] = [_efekt_to_dict(e) for e in h.efekty_harmonogramu]
    return d


def _get_student_profil():
    """Return StudentProfil for the currently logged-in student, or None."""
    return StudentProfil.query.filter_by(uzytkownik_id=current_user.id).first()


# ─────────────────────────────────────────────────────────────────
# GET /api/harmonogram
# ─────────────────────────────────────────────────────────────────

@harmonogram_api_bp.route('', methods=['GET'])
@login_required
def get_harmonogramy():
    """
    Pobierz listę harmonogramów.
    ---
    tags:
      - Harmonogram
    security:
      - cookieAuth: []
    parameters:
      - in: query
        name: status
        schema:
          type: string
          enum: [oczekuje, zaakceptowany, odrzucony]
        description: Filtruj po statusie
      - in: query
        name: student_id
        schema:
          type: integer
        description: Filtruj po ID profilu studenta
    responses:
      200:
        description: Lista harmonogramów
      401:
        description: Wymagane logowanie
      403:
        description: Brak uprawnień
    """
    # Student widzi tylko własne; reszta – wszystkie
    if current_user.rola == 'student':
        profil = _get_student_profil()
        if not profil:
            return jsonify({'error': 'Brak profilu studenta.'}), 404
        query = HarmonogramPraktyk.query.filter_by(student_id=profil.id)
    else:
        err = _require_roles('admin', 'dziekanat', 'opiekun')
        if err:
            return err
        query = HarmonogramPraktyk.query

        # Opcjonalne filtry (tylko dla ról z pełnym dostępem)
        student_id = request.args.get('student_id', type=int)
        if student_id:
            query = query.filter_by(student_id=student_id)

    status = request.args.get('status')
    if status:
        query = query.filter_by(status=status)

    harmonogramy = query.order_by(HarmonogramPraktyk.id.desc()).all()
    return jsonify({
        'count':       len(harmonogramy),
        'harmonogramy': [_harmonogram_to_dict(h, include_efekty=False) for h in harmonogramy],
    }), 200


# ─────────────────────────────────────────────────────────────────
# GET /api/harmonogram/<id>
# ─────────────────────────────────────────────────────────────────

@harmonogram_api_bp.route('/<int:harmonogram_id>', methods=['GET'])
@login_required
def get_harmonogram(harmonogram_id):
    """
    Pobierz jeden harmonogram (ze szczegółami efektów uczenia).
    ---
    tags:
      - Harmonogram
    security:
      - cookieAuth: []
    parameters:
      - in: path
        name: harmonogram_id
        required: true
        schema:
          type: integer
    responses:
      200:
        description: Dane harmonogramu z efektami uczenia
      401:
        description: Wymagane logowanie
      403:
        description: Brak uprawnień
      404:
        description: Nie znaleziono harmonogramu
    """
    h = HarmonogramPraktyk.query.get(harmonogram_id)
    if h is None:
        return jsonify({'error': f'Harmonogram id={harmonogram_id} nie istnieje.'}), 404

    # Student może zobaczyć tylko swój własny
    if current_user.rola == 'student':
        profil = _get_student_profil()
        if not profil or h.student_id != profil.id:
            return jsonify({'error': 'Brak uprawnień.'}), 403
    else:
        err = _require_roles('admin', 'dziekanat', 'opiekun')
        if err:
            return err

    return jsonify(_harmonogram_to_dict(h, include_efekty=True)), 200


# ─────────────────────────────────────────────────────────────────
# POST /api/harmonogram
# ─────────────────────────────────────────────────────────────────

@harmonogram_api_bp.route('', methods=['POST'])
@login_required
def create_harmonogram():
    """
    Utwórz nowy harmonogram praktyk (tylko student).
    Student może mieć tylko jeden aktywny harmonogram (status: oczekuje lub zaakceptowany).
    ---
    tags:
      - Harmonogram
    security:
      - cookieAuth: []
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            required:
              - opiekun_zakladowy_id
              - planowana_liczba_dni
            properties:
              opiekun_zakladowy_id:
                type: integer
                example: 2
              firma_id:
                type: integer
                example: 1
              planowana_liczba_dni:
                type: integer
                example: 30
              planowana_data_rozpoczecia:
                type: string
                format: date
                example: "2025-10-01"
              planowana_data_zakonczenia:
                type: string
                format: date
                example: "2025-11-30"
              efekty:
                type: array
                description: Lista efektów uczenia do zadeklarowania
                items:
                  type: object
                  properties:
                    efekt_uczenia_id:
                      type: integer
                      example: 3
                    opis:
                      type: string
                      example: "Zrealizuję ten efekt poprzez..."
    responses:
      201:
        description: Harmonogram utworzony
      400:
        description: Brak wymaganych pól lub student ma już aktywny harmonogram
      401:
        description: Wymagane logowanie
      403:
        description: Brak uprawnień (tylko student)
    """
    err = _require_roles('student')
    if err:
        return err

    profil = _get_student_profil()
    if not profil:
        return jsonify({'error': 'Brak profilu studenta dla tego konta.'}), 404

    # Guard: tylko jeden aktywny harmonogram
    istniejacy = HarmonogramPraktyk.query.filter(
        HarmonogramPraktyk.student_id == profil.id,
        HarmonogramPraktyk.status.in_(['oczekuje', 'zaakceptowany'])
    ).first()
    if istniejacy:
        return jsonify({
            'error':          'Masz już aktywny harmonogram.',
            'harmonogram_id': istniejacy.id,
            'status':         istniejacy.status,
        }), 400

    data = request.get_json(silent=True)
    if not data:
        return jsonify({'error': 'Oczekiwano danych JSON.'}), 400

    # Walidacja wymaganych pól
    required = ['opiekun_zakladowy_id', 'planowana_liczba_dni']
    missing = [f for f in required if data.get(f) is None]
    if missing:
        return jsonify({'error': 'Brak wymaganych pól.', 'missing': missing}), 400

    # Parsowanie dat
    data_start  = _parse_date(data.get('planowana_data_rozpoczecia'))
    data_koniec = _parse_date(data.get('planowana_data_zakonczenia'))
    if data_start  is False: return jsonify({'error': 'Nieprawidłowy format planowana_data_rozpoczecia (YYYY-MM-DD).'}), 400
    if data_koniec is False: return jsonify({'error': 'Nieprawidłowy format planowana_data_zakonczenia (YYYY-MM-DD).'}), 400

    harmonogram = HarmonogramPraktyk(
        student_id=profil.id,
        opiekun_zakladowy_id=data['opiekun_zakladowy_id'],
        firma_id=data.get('firma_id'),
        planowana_liczba_dni=data['planowana_liczba_dni'],
        planowana_data_rozpoczecia=data_start,
        planowana_data_zakonczenia=data_koniec,
        status='oczekuje',
    )
    db.session.add(harmonogram)
    db.session.flush()  # potrzebujemy harmonogram.id

    _zapisz_efekty(harmonogram.id, data.get('efekty', []))

    db.session.commit()
    return jsonify({
        'message':    'Harmonogram przesłany. Oczekuje na zatwierdzenie.',
        'harmonogram': _harmonogram_to_dict(harmonogram),
    }), 201


# ─────────────────────────────────────────────────────────────────
# PUT /api/harmonogram/<id>
# ─────────────────────────────────────────────────────────────────

@harmonogram_api_bp.route('/<int:harmonogram_id>', methods=['PUT'])
@login_required
def update_harmonogram(harmonogram_id):
    """
    Aktualizuj harmonogram. Dwa tryby zależnie od roli:

    **Student** – edycja własnych danych (tylko gdy status='oczekuje').

    **Admin / Dziekanat** – zmiana statusu: zatwierdzenie lub odrzucenie.
    - Zatwierdzenie (`akcja: zatwierdz`): wymaga `opiekun_uczelniany_id`; tworzy FormularzPraktyk.
    - Odrzucenie (`akcja: odrzuc`): wymaga `powod_odrzucenia`.
    ---
    tags:
      - Harmonogram
    security:
      - cookieAuth: []
    parameters:
      - in: path
        name: harmonogram_id
        required: true
        schema:
          type: integer
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            properties:
              opiekun_zakladowy_id:
                type: integer
              firma_id:
                type: integer
              planowana_liczba_dni:
                type: integer
              planowana_data_rozpoczecia:
                type: string
                format: date
              planowana_data_zakonczenia:
                type: string
                format: date
              efekty:
                type: array
                items:
                  type: object
                  properties:
                    efekt_uczenia_id:
                      type: integer
                    opis:
                      type: string
              akcja:
                type: string
                enum: [zatwierdz, odrzuc]
                description: Tylko dla admin/dziekanat
              opiekun_uczelniany_id:
                type: integer
                description: Wymagane przy akcja=zatwierdz
              powod_odrzucenia:
                type: string
                description: Wymagane przy akcja=odrzuc
    responses:
      200:
        description: Harmonogram zaktualizowany
      400:
        description: Nieprawidłowe dane lub niedozwolona akcja
      401:
        description: Wymagane logowanie
      403:
        description: Brak uprawnień
      404:
        description: Harmonogram nie istnieje
    """
    h = HarmonogramPraktyk.query.get(harmonogram_id)
    if h is None:
        return jsonify({'error': f'Harmonogram id={harmonogram_id} nie istnieje.'}), 404

    data = request.get_json(silent=True)
    if not data:
        return jsonify({'error': 'Oczekiwano danych JSON.'}), 400

    # ── STUDENT: edycja własnego harmonogramu ──
    if current_user.rola == 'student':
        profil = _get_student_profil()
        if not profil or h.student_id != profil.id:
            return jsonify({'error': 'Brak uprawnień.'}), 403
        if h.status != 'oczekuje':
            return jsonify({'error': f"Nie można edytować harmonogramu w statusie '{h.status}'."}), 400

        if 'opiekun_zakladowy_id' in data: h.opiekun_zakladowy_id = data['opiekun_zakladowy_id']
        if 'firma_id'             in data: h.firma_id             = data['firma_id']
        if 'planowana_liczba_dni' in data: h.planowana_liczba_dni = data['planowana_liczba_dni']

        if 'planowana_data_rozpoczecia' in data:
            d = _parse_date(data['planowana_data_rozpoczecia'])
            if d is False: return jsonify({'error': 'Nieprawidłowy format planowana_data_rozpoczecia.'}), 400
            h.planowana_data_rozpoczecia = d

        if 'planowana_data_zakonczenia' in data:
            d = _parse_date(data['planowana_data_zakonczenia'])
            if d is False: return jsonify({'error': 'Nieprawidłowy format planowana_data_zakonczenia.'}), 400
            h.planowana_data_zakonczenia = d

        if 'efekty' in data:
            EfektUczeniaHarmonogram.query.filter_by(harmonogram_praktyk_id=h.id).delete()
            _zapisz_efekty(h.id, data['efekty'])

        db.session.commit()
        return jsonify({
            'message':     'Harmonogram zaktualizowany.',
            'harmonogram': _harmonogram_to_dict(h),
        }), 200

    # ── ADMIN / DZIEKANAT: zatwierdzenie lub odrzucenie ──
    err = _require_roles('admin', 'dziekanat')
    if err:
        return err

    akcja = data.get('akcja')

    if akcja == 'odrzuc':
        powod = (data.get('powod_odrzucenia') or '').strip()
        if not powod:
            return jsonify({'error': "Pole 'powod_odrzucenia' jest wymagane przy odrzuceniu."}), 400
        h.status = 'odrzucony'
        h.powod_odrzucenia = powod
        db.session.commit()
        return jsonify({
            'message':     'Harmonogram odrzucony.',
            'harmonogram': _harmonogram_to_dict(h),
        }), 200

    elif akcja == 'zatwierdz':
        if h.status != 'oczekuje':
            return jsonify({'error': f"Harmonogram ma już status '{h.status}'. Można zatwierdzić tylko oczekujące."}), 400

        opiekun_uczelniany_id = data.get('opiekun_uczelniany_id')
        if not opiekun_uczelniany_id:
            return jsonify({'error': "Pole 'opiekun_uczelniany_id' jest wymagane przy zatwierdzaniu."}), 400

        h.status = 'zaakceptowany'
        h.powod_odrzucenia = None

        # Utwórz FormularzPraktyk jeśli nie istnieje aktywny
        istniejacy = FormularzPraktyk.query.filter(
            FormularzPraktyk.student_id == h.student_id,
            FormularzPraktyk.status == 'w_trakcie',
        ).first()
        formularz_id = istniejacy.id if istniejacy else None

        if not istniejacy:
            formularz = FormularzPraktyk(
                student_id=h.student_id,
                firma_id=h.firma_id,
                opiekun_zakladowy_id=h.opiekun_zakladowy_id,
                opiekun_uczelniany_id=opiekun_uczelniany_id,
                harmonogram_praktyk_id=h.id,
                data_rozpoczecia=h.planowana_data_rozpoczecia,
                data_zakonczenia=h.planowana_data_zakonczenia,
                status='w_trakcie',
            )
            db.session.add(formularz)
            db.session.flush()
            formularz_id = formularz.id

        db.session.commit()
        return jsonify({
            'message':        'Harmonogram zatwierdzony. Formularz praktyk utworzony.',
            'harmonogram':    _harmonogram_to_dict(h),
            'formularz_id':   formularz_id,
        }), 200

    else:
        return jsonify({
            'error': "Nieznana akcja. Dla admin/dziekanat podaj 'akcja': 'zatwierdz' lub 'odrzuc'.",
        }), 400


# ─────────────────────────────────────────────────────────────────
# DELETE /api/harmonogram/<id>
# ─────────────────────────────────────────────────────────────────

@harmonogram_api_bp.route('/<int:harmonogram_id>', methods=['DELETE'])
@login_required
def delete_harmonogram(harmonogram_id):
    """
    Usuń harmonogram wraz z efektami. Tylko admin.
    Nie można usunąć harmonogramu ze statusem 'zaakceptowany'
    (istnieje powiązany formularz praktyk).
    ---
    tags:
      - Harmonogram
    security:
      - cookieAuth: []
    parameters:
      - in: path
        name: harmonogram_id
        required: true
        schema:
          type: integer
    responses:
      200:
        description: Harmonogram usunięty
      400:
        description: Nie można usunąć zaakceptowanego harmonogramu
      401:
        description: Wymagane logowanie
      403:
        description: Brak uprawnień (tylko admin)
      404:
        description: Nie znaleziono harmonogramu
    """
    err = _require_roles('admin')
    if err:
        return err

    h = HarmonogramPraktyk.query.get(harmonogram_id)
    if h is None:
        return jsonify({'error': f'Harmonogram id={harmonogram_id} nie istnieje.'}), 404

    if h.status == 'zaakceptowany':
        return jsonify({
            'error': 'Nie można usunąć zaakceptowanego harmonogramu — istnieje powiązany formularz praktyk.',
        }), 400

    # Usuń efekty (brak cascade w modelu, robimy ręcznie)
    EfektUczeniaHarmonogram.query.filter_by(harmonogram_praktyk_id=h.id).delete()
    db.session.delete(h)
    db.session.commit()

    return jsonify({'message': f'Harmonogram id={harmonogram_id} został usunięty.'}), 200


# ─────────────────────────────────────────────────────────────────
# INTERNAL HELPERS
# ─────────────────────────────────────────────────────────────────

def _parse_date(value):
    """
    Parse an ISO date string (YYYY-MM-DD) → date object.
    Returns None  if value is None/empty.
    Returns False if the string is present but malformed.
    """
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except (ValueError, TypeError):
        return False


def _zapisz_efekty(harmonogram_id: int, efekty: list):
    """
    Persist a list of effect dicts to EfektUczeniaHarmonogram.
    Each dict should have: { efekt_uczenia_id: int, opis: str|None }
    Rows with missing/invalid efekt_uczenia_id are skipped.
    """
    for item in efekty:
        efekt_id = item.get('efekt_uczenia_id')
        if not efekt_id:
            continue
        # Verify the EfektUczenia actually exists
        if not EfektUczenia.query.get(efekt_id):
            continue
        wpis = EfektUczeniaHarmonogram(
            harmonogram_praktyk_id=harmonogram_id,
            efekt_uczenia_id=efekt_id,
            opis=(item.get('opis') or '').strip() or None,
        )
        db.session.add(wpis)