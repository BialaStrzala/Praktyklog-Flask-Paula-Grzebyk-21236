from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from models import db, Uzytkownik, StudentProfil

student_api_bp = Blueprint('api_student', __name__, url_prefix='/api/student')

# =========================================================================================================
# === HELPERS ===
# =========================================================================================================

def _require_roles(*roles):
    return None
    if not current_user.is_authenticated:
        return jsonify({'error': 'Wymagane logowanie.'}), 401
    if current_user.rola not in roles:
        return jsonify({'error': 'Brak uprawnień.'}), 403
    return None


def _student_to_dict(profil: StudentProfil) -> dict:
    u: Uzytkownik = profil.uzytkownik
    return {
        'id':              profil.id,
        'uzytkownik_id':   u.id,
        'imie':            u.imie,
        'nazwisko':        u.nazwisko,
        'email':           u.email,
        'telefon':         u.telefon,
        'konto_aktywne':   u.konto_aktywne,
        'indeks':          profil.indeks,
        'rok_akademicki':  profil.rok_akademicki,
        'semestr':         profil.semestr,
        'kierunek':        profil.kierunek,
        'specjalnosc':     profil.specjalnosc,
        'czy_stacjonarne': profil.czy_stacjonarne,
        'opiekun_zakladowy_id':  profil.opiekun_zakladowy_id,
        'opiekun_uczelniany_id': profil.opiekun_uczelniany_id,
    }


# =========================================================================================================
# === GET /api/students ===
# =========================================================================================================

@student_api_bp.route('', methods=['GET'])
@login_required
def get_students():
    """
    Pobierz listę wszystkich studentów.
    ---
    tags:
      - Studenci
    security:
      - cookieAuth: []
    parameters:
      - in: query
        name: kierunek
        schema:
          type: string
        description: Filtruj po kierunku studiów
      - in: query
        name: rok_akademicki
        schema:
          type: string
        description: "Filtruj po roku akademickim, np. 2024/2025"
    responses:
      200:
        description: Lista studentów
        content:
          application/json:
            schema:
              type: object
              properties:
                count:
                  type: integer
                students:
                  type: array
                  items:
                    $ref: '#/components/schemas/Student'
      401:
        description: Wymagane logowanie
      403:
        description: Brak uprawnień
    """

    err = _require_roles('admin', 'dziekanat', 'opiekun', 'opiekun_zakladowy')
    if err:
        return err

    query = StudentProfil.query

    kierunek = request.args.get('kierunek')
    rok      = request.args.get('rok_akademicki')
    if kierunek:
        query = query.filter(StudentProfil.kierunek.ilike(f'%{kierunek}%'))
    if rok:
        query = query.filter_by(rok_akademicki=rok)

    profiles = query.all()
    return jsonify({
        'count':    len(profiles),
        'students': [_student_to_dict(p) for p in profiles],
    }), 200


# =========================================================================================================
# === GET /api/students/<id> ===
# =========================================================================================================

@student_api_bp.route('/<int:student_id>', methods=['GET'])
@login_required
def get_student(student_id):
    """
    Pobierz dane jednego studenta.
    ---
    tags:
      - Studenci
    security:
      - cookieAuth: []
    parameters:
      - in: path
        name: student_id
        required: true
        schema:
          type: integer
        description: ID profilu studenta (student_profil.id)
    responses:
      200:
        description: Dane studenta
      401:
        description: Wymagane logowanie
      403:
        description: Brak uprawnień
      404:
        description: Student nie istnieje
    """

    # Student może pobrać tylko własny profil; pozostałe role – wszystkich
    if current_user.rola == 'student':
        profil = StudentProfil.query.filter_by(uzytkownik_id=current_user.id).first()
        if not profil or profil.id != student_id:
            return jsonify({'error': 'Brak uprawnień.'}), 403
    else:
        err = _require_roles('admin', 'dziekanat', 'opiekun')
        if err:
            return err

    profil = StudentProfil.query.get(student_id)
    if profil is None:
        return jsonify({'error': f'Student o id={student_id} nie istnieje.'}), 404

    return jsonify(_student_to_dict(profil)), 200


# =========================================================================================================
# === POST /api/students ===
# =========================================================================================================

@student_api_bp.route('', methods=['POST'])
@login_required
def create_student():
    """
    Utwórz nowego studenta (konto Uzytkownik + StudentProfil).
    ---
    tags:
      - Studenci
    security:
      - cookieAuth: []
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            required:
              - imie
              - nazwisko
              - email
            properties:
              imie:
                type: string
                example: Jan
              nazwisko:
                type: string
                example: Kowalski
              email:
                type: string
                example: s12345@student.uczelnia.pl
              telefon:
                type: string
                example: "+48 600 123 456"
              indeks:
                type: string
                example: "12345"
              rok_akademicki:
                type: string
                example: "2024/2025"
              semestr:
                type: integer
                example: 5
              kierunek:
                type: string
                example: Informatyka
              specjalnosc:
                type: string
                example: Inżynieria Oprogramowania
              czy_stacjonarne:
                type: boolean
                example: true
    responses:
      201:
        description: Student utworzony
      400:
        description: Brak wymaganych pól lub e-mail już istnieje
      401:
        description: Wymagane logowanie
      403:
        description: Brak uprawnień
    """

    err = _require_roles('student', 'admin', 'dziekanat')
    if err:
        return err

    data = request.get_json(silent=True)
    if not data:
        return jsonify({'error': 'Oczekiwano danych JSON.'}), 400

    # Walidacja wymaganych pól
    required = ['imie', 'nazwisko', 'email']
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({'error': 'Brak wymaganych pól.', 'missing': missing}), 400

    # Unikalność emaila
    if Uzytkownik.query.filter_by(email=data['email']).first():
        return jsonify({'error': f"E-mail '{data['email']}' jest już zajęty."}), 400

    # Tworzenie użytkownika
    uzytkownik = Uzytkownik(
        imie=data['imie'],
        nazwisko=data['nazwisko'],
        email=data['email'],
        telefon=data.get('telefon'),
        rola='student',
        konto_aktywne=True,
        auth_provider='manual',
    )
    db.session.add(uzytkownik)
    db.session.flush()  # potrzebujemy uzytkownik.id

    # Tworzenie profilu studenta
    profil = StudentProfil(
        uzytkownik_id=uzytkownik.id,
        indeks=data.get('indeks'),
        rok_akademicki=data.get('rok_akademicki'),
        semestr=data.get('semestr'),
        kierunek=data.get('kierunek'),
        specjalnosc=data.get('specjalnosc'),
        czy_stacjonarne=data.get('czy_stacjonarne', True),
    )
    db.session.add(profil)
    db.session.commit()

    return jsonify({
        'message': 'Student utworzony.',
        'student': _student_to_dict(profil),
    }), 201


# =========================================================================================================
# === PUT /api/students/<id> ===
# =========================================================================================================

@student_api_bp.route('/<int:student_id>', methods=['PUT'])
@login_required
def update_student(student_id):
    """
    Zaktualizuj dane studenta (częściowa aktualizacja – tylko podane pola).
    ---
    tags:
      - Studenci
    security:
      - cookieAuth: []
    parameters:
      - in: path
        name: student_id
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
              imie:
                type: string
              nazwisko:
                type: string
              telefon:
                type: string
              indeks:
                type: string
              rok_akademicki:
                type: string
              semestr:
                type: integer
              kierunek:
                type: string
              specjalnosc:
                type: string
              czy_stacjonarne:
                type: boolean
              konto_aktywne:
                type: boolean
    responses:
      200:
        description: Dane zaktualizowane
      400:
        description: Nieprawidłowe dane JSON
      401:
        description: Wymagane logowanie
      403:
        description: Brak uprawnień
      404:
        description: Student nie istnieje
    """

    err = _require_roles('student', 'admin', 'dziekanat')
    if err:
        return err

    profil = StudentProfil.query.get(student_id)
    if profil is None:
        return jsonify({'error': f'Student o id={student_id} nie istnieje.'}), 404

    data = request.get_json(silent=True)
    if not data:
        return jsonify({'error': 'Oczekiwano danych JSON.'}), 400

    u = profil.uzytkownik

    # Pola Uzytkownik
    if 'imie'          in data: u.imie          = data['imie']
    if 'nazwisko'      in data: u.nazwisko       = data['nazwisko']
    if 'telefon'       in data: u.telefon        = data['telefon']
    if 'konto_aktywne' in data: u.konto_aktywne  = bool(data['konto_aktywne'])

    # Pola StudentProfil
    if 'indeks'          in data: profil.indeks          = data['indeks']
    if 'rok_akademicki'  in data: profil.rok_akademicki   = data['rok_akademicki']
    if 'semestr'         in data: profil.semestr          = data['semestr']
    if 'kierunek'        in data: profil.kierunek         = data['kierunek']
    if 'specjalnosc'     in data: profil.specjalnosc      = data['specjalnosc']
    if 'czy_stacjonarne' in data: profil.czy_stacjonarne  = bool(data['czy_stacjonarne'])

    db.session.commit()
    return jsonify({
        'message': 'Dane zaktualizowane.',
        'student': _student_to_dict(profil),
    }), 200


# =========================================================================================================
# === DELETE /api/students/<id> ===
# =========================================================================================================

@student_api_bp.route('/<int:student_id>', methods=['DELETE'])
@login_required
def delete_student(student_id):
    """
    Usuń studenta (profil + konto użytkownika).
    Tylko admin.
    ---
    tags:
      - Studenci
    security:
      - cookieAuth: []
    parameters:
      - in: path
        name: student_id
        required: true
        schema:
          type: integer
    responses:
      200:
        description: Student usunięty
      401:
        description: Wymagane logowanie
      403:
        description: Brak uprawnień (tylko admin)
      404:
        description: Student nie istnieje
    """

    err = _require_roles('admin')
    if err:
        return err

    profil = StudentProfil.query.get(student_id)
    if profil is None:
        return jsonify({'error': f'Student o id={student_id} nie istnieje.'}), 404

    uzytkownik = profil.uzytkownik
    db.session.delete(profil)
    db.session.delete(uzytkownik)
    db.session.commit()

    return jsonify({'message': f'Student id={student_id} został usunięty.'}), 200