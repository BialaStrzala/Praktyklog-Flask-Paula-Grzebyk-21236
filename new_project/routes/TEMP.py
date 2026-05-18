from flask import Blueprint, request, jsonify
from models import db, Uzytkownik, StudentProfil
from datetime import datetime

api_bp = Blueprint('api', __name__)


# === Studenci (students) ===
@api_bp.route('/studenci', methods=['GET'])
def pobierz_studencow():
    students = StudentProfil.query.all()
    result = []
    for s in students:
        result.append({
            'id': s.id,
            'imie': s.uzytkownik.imie,
            'nazwisko': s.uzytkownik.nazwisko,
            'email': s.uzytkownik.email,
            'indeks': s.indeks,
        })
    return jsonify(result), 200


@api_bp.route('/studenci', methods=['POST'])
def utworz_studenta():
    data = request.get_json() or {}
    required = ['imie', 'nazwisko', 'email']
    for r in required:
        if not data.get(r):
            return jsonify({'error': f'Brak pola {r}'}), 400

    # create user
    if Uzytkownik.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Użytkownik o podanym email już istnieje'}), 409

    user = Uzytkownik(
        imie=data['imie'],
        nazwisko=data['nazwisko'],
        email=data['email'],
        rola='student'
    )
    db.session.add(user)
    db.session.commit()

    student = StudentProfil(
        uzytkownik_id=user.id,
        indeks=data.get('indeks'),
        rok_akademicki=data.get('rok_akademicki'),
        semestr=data.get('semestr'),
        kierunek=data.get('kierunek'),
        specjalnosc=data.get('specjalnosc')
    )
    db.session.add(student)
    db.session.commit()

    return jsonify({'id': student.id, 'message': 'Student utworzony'}), 201


@api_bp.route('/studenci/<int:student_id>', methods=['GET'])
def pobierz_studenta(student_id):
    s = StudentProfil.query.get_or_404(student_id)
    user = s.uzytkownik
    return jsonify({
        'id': s.id,
        'imie': user.imie,
        'nazwisko': user.nazwisko,
        'email': user.email,
        'indeks': s.indeks,
        'rok_akademicki': s.rok_akademicki,
        'semestr': s.semestr,
        'kierunek': s.kierunek,
        'specjalnosc': s.specjalnosc,
    }), 200


@api_bp.route('/studenci/<int:student_id>', methods=['PUT', 'PATCH'])
def aktualizuj_studenta(student_id):
    s = StudentProfil.query.get_or_404(student_id)
    data = request.get_json() or {}
    # update user fields
    if 'imie' in data:
        s.uzytkownik.imie = data['imie']
    if 'nazwisko' in data:
        s.uzytkownik.nazwisko = data['nazwisko']
    if 'email' in data:
        s.uzytkownik.email = data['email']

    # update student profile
    for field in ['indeks', 'rok_akademicki', 'semestr', 'kierunek', 'specjalnosc']:
        if field in data:
            setattr(s, field, data[field])

    db.session.commit()
    return jsonify({'message': 'Zaktualizowano studenta'}), 200


@api_bp.route('/studenci/<int:student_id>', methods=['DELETE'])
def usun_studenta(student_id):
    s = StudentProfil.query.get_or_404(student_id)
    # remove user and profile
    Uzytkownik.query.filter_by(id=s.uzytkownik_id).delete()
    db.session.commit()
    return jsonify({'message': 'Usunięto studenta'}), 200


# === Pozostałe endpoints (WIP) ===
@api_bp.route('/uzytkownicy', methods=['GET', 'POST'])
def uzytkownicy():
    return jsonify({'message': 'WIP - użytkownicy'}), 501


@api_bp.route('/opiekunowie', methods=['GET', 'POST'])
def opiekunowie():
    return jsonify({'message': 'WIP - opiekunowie'}), 501


@api_bp.route('/dzienniki', methods=['GET', 'POST'])
def dzienniki():
    return jsonify({'message': 'WIP - dzienniki'}), 501


@api_bp.route('/efekty', methods=['GET', 'POST'])
def efekty():
    return jsonify({'message': 'WIP - efekty'}), 501


@api_bp.route('/potwierdzenia', methods=['GET', 'POST'])
def potwierdzenia():
    return jsonify({'message': 'WIP - potwierdzenia'}), 501


@api_bp.route('/logowanie', methods=['POST'])
def api_logowanie():
    return jsonify({'message': 'WIP - logowanie'}), 501
