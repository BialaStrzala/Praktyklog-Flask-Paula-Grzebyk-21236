from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from models import (
    db,
    FormularzPraktyk, EfektUczeniaFormularz, EfektUczenia,
    StudentProfil, OpiekunProfil,
)
from datetime import date

formularz_api_bp = Blueprint('api_formularz', __name__, url_prefix='/api/formularz')


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


def _parse_date(value):
    """YYYY-MM-DD → date. None if empty, False if malformed."""
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except (ValueError, TypeError):
        return False


def _efekt_to_dict(e: EfektUczeniaFormularz) -> dict:
    return {
        'id':                          e.id,
        'efekt_uczenia_id':            e.efekt_uczenia_id,
        'kod':                         e.efekt.kod  if e.efekt else None,
        'opis_efektu':                 e.efekt.opis if e.efekt else None,
        'czy_potwierdzony_zakladowy':  e.czy_potwierdzony_zakladowy,
        'czy_potwierdzony_uczelniany': e.czy_potwierdzony_uczelniany,
        'uwagi':                       e.uwagi,
    }


def _formularz_to_dict(f: FormularzPraktyk, include_efekty: bool = True) -> dict:
    d = {
        'id':                            f.id,
        'student_id':                    f.student_id,
        'opiekun_uczelniany_id':         f.opiekun_uczelniany_id,
        'opiekun_zakladowy_id':          f.opiekun_zakladowy_id,
        'firma_id':                      f.firma_id,
        'harmonogram_praktyk_id':        f.harmonogram_praktyk_id,
        'data_rozpoczecia':              f.data_rozpoczecia.isoformat()  if f.data_rozpoczecia  else None,
        'data_zakonczenia':              f.data_zakonczenia.isoformat()  if f.data_zakonczenia  else None,
        'status':                        f.status,
        'opinia_opiekuna_zakladowego':   f.opinia_opiekuna_zakladowego,
        'opinia_opiekuna_uczelnianego':  f.opinia_opiekuna_uczelnianego,
        'ocena_opiekuna_zakladowego':    f.ocena_opiekuna_zakladowego,
        'ocena_opiekuna_uczelnianego':   f.ocena_opiekuna_uczelnianego,
        'ocena_sprawozdanie':            f.ocena_sprawozdanie,
        'ocena_egzamin':                 f.ocena_egzamin,
        'ocena_koncowa':                 f.ocena_koncowa,
        'utworzono':                     f.utworzono.isoformat()     if f.utworzono     else None,
        'zaktualizowano':                f.zaktualizowano.isoformat() if f.zaktualizowano else None,
    }
    if include_efekty:
        d['efekty_uczenia'] = [_efekt_to_dict(e) for e in f.efekty_uczenia]
    return d


def _get_opiekun_profil():
    """Return OpiekunProfil for the currently logged-in opiekun, or None."""
    return OpiekunProfil.query.filter_by(uzytkownik_id=current_user.id).first()


def _get_student_profil():
    """Return StudentProfil for the currently logged-in student, or None."""
    return StudentProfil.query.filter_by(uzytkownik_id=current_user.id).first()


# ─────────────────────────────────────────────────────────────────
# GET /api/formularz
# ─────────────────────────────────────────────────────────────────

@formularz_api_bp.route('', methods=['GET'])
@login_required
def get_formularze():
    """
    Pobierz listę formularzy praktyk.
    Student widzi tylko własne. Opiekun widzi formularze przypisane do niego.
    Admin i dziekanat widzą wszystkie.
    ---
    tags:
      - Formularz Praktyk
    security:
      - cookieAuth: []
    parameters:
      - in: query
        name: status
        schema:
          type: string
          enum: [w_trakcie, zakonczone, porzucone]
        description: Filtruj po statusie
      - in: query
        name: student_id
        schema:
          type: integer
        description: Filtruj po ID profilu studenta (tylko admin/dziekanat)
    responses:
      200:
        description: Lista formularzy
      401:
        description: Wymagane logowanie
      403:
        description: Brak uprawnień
    """
    rola = current_user.rola

    if rola == 'student':
        profil = _get_student_profil()
        if not profil:
            return jsonify({'error': 'Brak profilu studenta.'}), 404
        query = FormularzPraktyk.query.filter_by(student_id=profil.id)

    elif rola == 'opiekun':
        op = _get_opiekun_profil()
        if not op:
            return jsonify({'error': 'Brak profilu opiekuna.'}), 404
        if op.typ_opiekuna == 'zakladowy':
            query = FormularzPraktyk.query.filter_by(opiekun_zakladowy_id=op.id)
        else:
            query = FormularzPraktyk.query.filter_by(opiekun_uczelniany_id=op.id)

    elif rola in ('admin', 'dziekanat'):
        query = FormularzPraktyk.query
        student_id = request.args.get('student_id', type=int)
        if student_id:
            query = query.filter_by(student_id=student_id)

    else:
        return jsonify({'error': 'Brak uprawnień.'}), 403

    status = request.args.get('status')
    if status:
        query = query.filter_by(status=status)

    formularze = query.order_by(FormularzPraktyk.id.desc()).all()
    return jsonify({
        'count':      len(formularze),
        'formularze': [_formularz_to_dict(f, include_efekty=False) for f in formularze],
    }), 200


# ─────────────────────────────────────────────────────────────────
# GET /api/formularz/<id>
# ─────────────────────────────────────────────────────────────────

@formularz_api_bp.route('/<int:formularz_id>', methods=['GET'])
@login_required
def get_formularz(formularz_id):
    """
    Pobierz jeden formularz praktyk wraz z efektami uczenia.
    ---
    tags:
      - Formularz Praktyk
    security:
      - cookieAuth: []
    parameters:
      - in: path
        name: formularz_id
        required: true
        schema:
          type: integer
    responses:
      200:
        description: Dane formularza z efektami
      401:
        description: Wymagane logowanie
      403:
        description: Brak uprawnień
      404:
        description: Formularz nie istnieje
    """
    f = FormularzPraktyk.query.get(formularz_id)
    if f is None:
        return jsonify({'error': f'Formularz id={formularz_id} nie istnieje.'}), 404

    rola = current_user.rola

    if rola == 'student':
        profil = _get_student_profil()
        if not profil or f.student_id != profil.id:
            return jsonify({'error': 'Brak uprawnień.'}), 403

    elif rola == 'opiekun':
        op = _get_opiekun_profil()
        if not op:
            return jsonify({'error': 'Brak profilu opiekuna.'}), 404
        if f.opiekun_zakladowy_id != op.id and f.opiekun_uczelniany_id != op.id:
            return jsonify({'error': 'Brak uprawnień — formularz nie należy do Ciebie.'}), 403

    elif rola not in ('admin', 'dziekanat'):
        return jsonify({'error': 'Brak uprawnień.'}), 403

    return jsonify(_formularz_to_dict(f, include_efekty=True)), 200


# ─────────────────────────────────────────────────────────────────
# POST /api/formularz
# ─────────────────────────────────────────────────────────────────

@formularz_api_bp.route('', methods=['POST'])
@login_required
def create_formularz():
    """
    Utwórz nowy formularz praktyk. Normalnie tworzony automatycznie
    po zatwierdzeniu harmonogramu — ten endpoint służy do ręcznego tworzenia
    przez admin/dziekanat.
    ---
    tags:
      - Formularz Praktyk
    security:
      - cookieAuth: []
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            required:
              - student_id
            properties:
              student_id:
                type: integer
                example: 1
              opiekun_uczelniany_id:
                type: integer
                example: 2
              opiekun_zakladowy_id:
                type: integer
                example: 3
              firma_id:
                type: integer
                example: 1
              harmonogram_praktyk_id:
                type: integer
                example: 4
              data_rozpoczecia:
                type: string
                format: date
                example: "2025-10-01"
              data_zakonczenia:
                type: string
                format: date
                example: "2025-11-30"
              status:
                type: string
                enum: [w_trakcie, zakonczone, porzucone]
                example: "w_trakcie"
    responses:
      201:
        description: Formularz utworzony
      400:
        description: Brak wymaganych pól lub student ma już aktywny formularz
      401:
        description: Wymagane logowanie
      403:
        description: Brak uprawnień
    """
    err = _require_roles('admin', 'dziekanat')
    if err:
        return err

    data = request.get_json(silent=True)
    if not data:
        return jsonify({'error': 'Oczekiwano danych JSON.'}), 400

    if not data.get('student_id'):
        return jsonify({'error': 'Brak wymaganych pól.', 'missing': ['student_id']}), 400

    # Guard: student może mieć tylko jeden aktywny formularz
    istniejacy = FormularzPraktyk.query.filter(
        FormularzPraktyk.student_id == data['student_id'],
        FormularzPraktyk.status == 'w_trakcie',
    ).first()
    if istniejacy:
        return jsonify({
            'error':        'Student ma już aktywny formularz praktyk.',
            'formularz_id': istniejacy.id,
        }), 400

    data_rozp  = _parse_date(data.get('data_rozpoczecia'))
    data_zakon = _parse_date(data.get('data_zakonczenia'))
    if data_rozp  is False: return jsonify({'error': 'Nieprawidłowy format data_rozpoczecia (YYYY-MM-DD).'}), 400
    if data_zakon is False: return jsonify({'error': 'Nieprawidłowy format data_zakonczenia (YYYY-MM-DD).'}), 400

    f = FormularzPraktyk(
        student_id=data['student_id'],
        opiekun_uczelniany_id=data.get('opiekun_uczelniany_id'),
        opiekun_zakladowy_id=data.get('opiekun_zakladowy_id'),
        firma_id=data.get('firma_id'),
        harmonogram_praktyk_id=data.get('harmonogram_praktyk_id'),
        data_rozpoczecia=data_rozp,
        data_zakonczenia=data_zakon,
        status=data.get('status', 'w_trakcie'),
    )
    db.session.add(f)
    db.session.commit()

    return jsonify({
        'message':   'Formularz utworzony.',
        'formularz': _formularz_to_dict(f),
    }), 201


# ─────────────────────────────────────────────────────────────────
# PUT /api/formularz/<id>
# ─────────────────────────────────────────────────────────────────

@formularz_api_bp.route('/<int:formularz_id>', methods=['PUT'])
@login_required
def update_formularz(formularz_id):
    """
    Aktualizuj formularz. Dostępne pola zależą od roli:

    - **admin / dziekanat** – wszystkie pola
    - **opiekun_zakladowy** – opinia, ocena, potwierdzenie efektów (własne formularze)
    - **opiekun_uczelniany** – opinia, ocena (własne formularze)
    - **student** – brak dostępu (403)
    ---
    tags:
      - Formularz Praktyk
    security:
      - cookieAuth: []
    parameters:
      - in: path
        name: formularz_id
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
              status:
                type: string
                enum: [w_trakcie, zakonczone, porzucone]
              data_rozpoczecia:
                type: string
                format: date
              data_zakonczenia:
                type: string
                format: date
              opiekun_uczelniany_id:
                type: integer
              opiekun_zakladowy_id:
                type: integer
              firma_id:
                type: integer
              opinia_opiekuna_zakladowego:
                type: string
              opinia_opiekuna_uczelnianego:
                type: string
              ocena_opiekuna_zakladowego:
                type: number
              ocena_opiekuna_uczelnianego:
                type: number
              ocena_sprawozdanie:
                type: number
              ocena_egzamin:
                type: number
              ocena_koncowa:
                type: number
              efekty_uczenia:
                type: array
                description: >
                  Lista efektów do aktualizacji (tylko opiekun_zakladowy i admin).
                  Przekaż id istniejącego EfektUczeniaFormularz.
                items:
                  type: object
                  properties:
                    id:
                      type: integer
                    czy_potwierdzony_zakladowy:
                      type: boolean
                    czy_potwierdzony_uczelniany:
                      type: boolean
                    uwagi:
                      type: string
    responses:
      200:
        description: Formularz zaktualizowany
      400:
        description: Nieprawidłowe dane
      401:
        description: Wymagane logowanie
      403:
        description: Brak uprawnień
      404:
        description: Formularz nie istnieje
    """
    f = FormularzPraktyk.query.get(formularz_id)
    if f is None:
        return jsonify({'error': f'Formularz id={formularz_id} nie istnieje.'}), 404

    data = request.get_json(silent=True)
    if not data:
        return jsonify({'error': 'Oczekiwano danych JSON.'}), 400

    rola = current_user.rola

    # ── STUDENT – brak dostępu do PUT ──
    if rola == 'student':
        return jsonify({'error': 'Student nie może edytować formularza.'}), 403

    # ── OPIEKUN ZAKŁADOWY ──
    elif rola == 'opiekun':
        op = _get_opiekun_profil()
        if not op:
            return jsonify({'error': 'Brak profilu opiekuna.'}), 404

        if op.typ_opiekuna == 'zakladowy':
            if f.opiekun_zakladowy_id != op.id:
                return jsonify({'error': 'Brak uprawnień — formularz nie należy do Ciebie.'}), 403
            # Dozwolone pola dla opiekuna zakładowego
            if 'opinia_opiekuna_zakladowego'  in data: f.opinia_opiekuna_zakladowego  = data['opinia_opiekuna_zakladowego']
            if 'ocena_opiekuna_zakladowego'   in data: f.ocena_opiekuna_zakladowego   = data['ocena_opiekuna_zakladowego']
            if 'efekty_uczenia'               in data: _aktualizuj_efekty(data['efekty_uczenia'], moze_zakladowy=True)

        elif op.typ_opiekuna == 'uczelniany':
            if f.opiekun_uczelniany_id != op.id:
                return jsonify({'error': 'Brak uprawnień — formularz nie należy do Ciebie.'}), 403
            # Dozwolone pola dla opiekuna uczelnianego
            if 'opinia_opiekuna_uczelnianego' in data: f.opinia_opiekuna_uczelnianego = data['opinia_opiekuna_uczelnianego']
            if 'ocena_opiekuna_uczelnianego'  in data: f.ocena_opiekuna_uczelnianego  = data['ocena_opiekuna_uczelnianego']
            if 'efekty_uczenia'               in data: _aktualizuj_efekty(data['efekty_uczenia'], moze_uczelniany=True)

        else:
            return jsonify({'error': 'Nieznany typ opiekuna.'}), 400

    # ── ADMIN / DZIEKANAT – pełen dostęp ──
    elif rola in ('admin', 'dziekanat'):
        if 'status'               in data: f.status                        = data['status']
        if 'opiekun_uczelniany_id' in data: f.opiekun_uczelniany_id        = data['opiekun_uczelniany_id']
        if 'opiekun_zakladowy_id'  in data: f.opiekun_zakladowy_id         = data['opiekun_zakladowy_id']
        if 'firma_id'             in data: f.firma_id                      = data['firma_id']

        if 'data_rozpoczecia' in data:
            d = _parse_date(data['data_rozpoczecia'])
            if d is False: return jsonify({'error': 'Nieprawidłowy format data_rozpoczecia.'}), 400
            f.data_rozpoczecia = d
        if 'data_zakonczenia' in data:
            d = _parse_date(data['data_zakonczenia'])
            if d is False: return jsonify({'error': 'Nieprawidłowy format data_zakonczenia.'}), 400
            f.data_zakonczenia = d

        if 'opinia_opiekuna_zakladowego'  in data: f.opinia_opiekuna_zakladowego  = data['opinia_opiekuna_zakladowego']
        if 'opinia_opiekuna_uczelnianego' in data: f.opinia_opiekuna_uczelnianego = data['opinia_opiekuna_uczelnianego']
        if 'ocena_opiekuna_zakladowego'   in data: f.ocena_opiekuna_zakladowego   = data['ocena_opiekuna_zakladowego']
        if 'ocena_opiekuna_uczelnianego'  in data: f.ocena_opiekuna_uczelnianego  = data['ocena_opiekuna_uczelnianego']
        if 'ocena_sprawozdanie'           in data: f.ocena_sprawozdanie           = data['ocena_sprawozdanie']
        if 'ocena_egzamin'                in data: f.ocena_egzamin                = data['ocena_egzamin']
        if 'ocena_koncowa'                in data: f.ocena_koncowa                = data['ocena_koncowa']

        if 'efekty_uczenia' in data:
            _aktualizuj_efekty(data['efekty_uczenia'], moze_zakladowy=True, moze_uczelniany=True)

    else:
        return jsonify({'error': 'Brak uprawnień.'}), 403

    db.session.commit()
    return jsonify({
        'message':   'Formularz zaktualizowany.',
        'formularz': _formularz_to_dict(f),
    }), 200


# ─────────────────────────────────────────────────────────────────
# DELETE /api/formularz/<id>
# ─────────────────────────────────────────────────────────────────

@formularz_api_bp.route('/<int:formularz_id>', methods=['DELETE'])
@login_required
def delete_formularz(formularz_id):
    """
    Usuń formularz praktyk wraz z efektami. Tylko admin.
    Nie można usunąć formularza w statusie 'w_trakcie'.
    ---
    tags:
      - Formularz Praktyk
    security:
      - cookieAuth: []
    parameters:
      - in: path
        name: formularz_id
        required: true
        schema:
          type: integer
    responses:
      200:
        description: Formularz usunięty
      400:
        description: Nie można usunąć aktywnego formularza
      401:
        description: Wymagane logowanie
      403:
        description: Brak uprawnień (tylko admin)
      404:
        description: Formularz nie istnieje
    """
    err = _require_roles('admin')
    if err:
        return err

    f = FormularzPraktyk.query.get(formularz_id)
    if f is None:
        return jsonify({'error': f'Formularz id={formularz_id} nie istnieje.'}), 404

    if f.status == 'w_trakcie':
        return jsonify({
            'error': "Nie można usunąć aktywnego formularza (status='w_trakcie'). Najpierw zmień status.",
        }), 400

    # Efekty nie mają cascade w modelu — usuwamy ręcznie
    EfektUczeniaFormularz.query.filter_by(formularz_praktyk_id=f.id).delete()
    db.session.delete(f)
    db.session.commit()

    return jsonify({'message': f'Formularz id={formularz_id} został usunięty.'}), 200


# ─────────────────────────────────────────────────────────────────
# INTERNAL HELPERS
# ─────────────────────────────────────────────────────────────────

def _aktualizuj_efekty(
    efekty: list,
    moze_zakladowy: bool = False,
    moze_uczelniany: bool = False,
):
    """
    Partial-update existing EfektUczeniaFormularz rows by their id.
    Only fields the caller is allowed to change are written.

    Expects each item: { id: int, czy_potwierdzony_zakladowy?, czy_potwierdzony_uczelniany?, uwagi? }
    Rows with unknown id are silently skipped.
    """
    for item in efekty:
        efekt_id = item.get('id')
        if not efekt_id:
            continue
        e = EfektUczeniaFormularz.query.get(efekt_id)
        if e is None:
            continue
        if moze_zakladowy  and 'czy_potwierdzony_zakladowy'  in item:
            e.czy_potwierdzony_zakladowy  = bool(item['czy_potwierdzony_zakladowy'])
        if moze_uczelniany and 'czy_potwierdzony_uczelniany' in item:
            e.czy_potwierdzony_uczelniany = bool(item['czy_potwierdzony_uczelniany'])
        if 'uwagi' in item:
            e.uwagi = (item['uwagi'] or '').strip() or None