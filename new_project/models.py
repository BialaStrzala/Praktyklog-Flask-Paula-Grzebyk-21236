from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

# =========================================================================================================
# === MODELE ===
# =========================================================================================================

# === UZYTKOWNIK ===
class Uzytkownik(db.Model, UserMixin):
    __tablename__ = 'uzytkownik'

    id = db.Column(db.Integer, primary_key=True)
    imie = db.Column(db.String(100), nullable=False)
    nazwisko = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    #haslo_hash = db.Column(db.String(256), nullable=False)
    rola = db.Column(db.String(50), nullable=False)  # 'student', 'opiekun', 'dziekanat', 'admin'
    konto_aktywne = db.Column(db.Boolean, default=True)
    telefon = db.Column(db.String(20), nullable=True)
    utworzono = db.Column(db.DateTime, default=datetime.now)

    auth_provider = db.Column(db.String(50), default="microsoft")
    external_id = db.Column(db.String(255), unique=True)

    student_profil = db.relationship('StudentProfil', backref='uzytkownik', uselist=False, cascade='all, delete-orphan')
    opiekun_profil = db.relationship('OpiekunProfil', backref='uzytkownik', uselist=False, cascade='all, delete-orphan')

    def set_password(self, haslo):
        self.haslo_hash = generate_password_hash(haslo)

    def check_password(self, haslo):
        return check_password_hash(self.haslo_hash, haslo)


# === FIRMA ===
class Firma(db.Model):
    __tablename__ = 'firma'

    id = db.Column(db.Integer, primary_key=True)
    nazwa = db.Column(db.String(200), nullable=False)
    adres = db.Column(db.String(300), nullable=True)

    opiekunowie = db.relationship('OpiekunProfil', backref='firma', lazy=True, cascade='all, delete-orphan')
    formularze = db.relationship('FormularzPraktyk', backref='firma', lazy=True, cascade='all, delete-orphan')


# === PROFIL OPIEKUNA ===
class OpiekunProfil(db.Model):
    __tablename__ = 'opiekun_profil'

    id = db.Column(db.Integer, primary_key=True)
    uzytkownik_id = db.Column(db.Integer, db.ForeignKey('uzytkownik.id'), nullable=False)
    firma_id = db.Column(db.Integer, db.ForeignKey('firma.id'), nullable=True)  # tylko dla opiekuna zakladowego
    typ_opiekuna = db.Column(db.String(20), nullable=False)  # 'uczelniany', 'zakladowy'

    podpieci_studenci_zaklad = db.relationship(
        'StudentProfil',
        foreign_keys='StudentProfil.opiekun_zakladowy_id',
        backref='opiekun_zakladowy',
        lazy=True,
        cascade='all, delete-orphan'
    )
    podpieci_studenci_uczelnia = db.relationship(
        'StudentProfil',
        foreign_keys='StudentProfil.opiekun_uczelniany_id',
        backref='opiekun_uczelniany',
        lazy=True,
        cascade='all, delete-orphan'
    )


# === PROFIL STUDENTA ===
class StudentProfil(db.Model):
    __tablename__ = 'student_profil'

    id = db.Column(db.Integer, primary_key=True)
    uzytkownik_id = db.Column(db.Integer, db.ForeignKey('uzytkownik.id'), nullable=False)
    indeks = db.Column(db.String(10), unique=True, nullable=True)
    rok_akademicki = db.Column(db.String(9), nullable=True)
    semestr = db.Column(db.Integer, nullable=True)
    kierunek = db.Column(db.String(100), nullable=True)
    specjalnosc = db.Column(db.String(100), nullable=True)
    czy_stacjonarne = db.Column(db.Boolean, default=True)

    opiekun_zakladowy_id = db.Column(db.Integer, db.ForeignKey('opiekun_profil.id'), nullable=True)
    opiekun_uczelniany_id = db.Column(db.Integer, db.ForeignKey('opiekun_profil.id'), nullable=True)

    wpisy_dziennika = db.relationship('DziennikWpis', backref='student', lazy=True)
    formularze = db.relationship('FormularzPraktyk', backref='student', lazy=True)


# === EFEKTY UCZENIA ===
class EfektUczenia(db.Model):
    __tablename__ = 'efekt_uczenia'

    id = db.Column(db.Integer, primary_key=True)
    kod = db.Column(db.String(2), unique=True, nullable=False)
    opis = db.Column(db.Text, nullable=False)


# === FORMULARZ PRAKTYK ===
class FormularzPraktyk(db.Model):
    __tablename__ = 'formularz_praktyk'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student_profil.id'), nullable=False)
    opiekun_uczelniany_id = db.Column(db.Integer, db.ForeignKey('opiekun_profil.id'), nullable=True)
    opiekun_zakladowy_id = db.Column(db.Integer, db.ForeignKey('opiekun_profil.id'), nullable=True)
    firma_id = db.Column(db.Integer, db.ForeignKey('firma.id'), nullable=True)
    harmonogram_praktyk_id = db.Column(db.Integer, db.ForeignKey('harmonogram_praktyk.id'), nullable=True)

    data_rozpoczecia = db.Column(db.Date, nullable=True)
    data_zakonczenia = db.Column(db.Date, nullable=True)

    status = db.Column(db.String(50), nullable=False, default='w_trakcie') #w_trakcie, #zakonczone, #porzucone

    opinia_opiekuna_zakladowego = db.Column(db.Text, nullable=True)
    opinia_opiekuna_uczelnianego = db.Column(db.Text, nullable=True)

    ocena_opiekuna_zakladowego = db.Column(db.Float, nullable=True)
    ocena_opiekuna_uczelnianego = db.Column(db.Float, nullable=True)
    ocena_sprawozdanie = db.Column(db.Float, nullable=True)
    ocena_egzamin = db.Column(db.Float, nullable=True)
    ocena_koncowa = db.Column(db.Float, nullable=True)

    utworzono = db.Column(db.DateTime, default=datetime.now)
    zaktualizowano = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    harmonogram = db.relationship('HarmonogramPraktyk', backref='harmonogram_praktyk', lazy=True)
    efekty_uczenia = db.relationship('EfektUczeniaFormularz', backref='formularz_praktyk', lazy=True)
    opiekun_uczelniany = db.relationship('OpiekunProfil', foreign_keys=[opiekun_uczelniany_id], lazy=True)
    opiekun_zakladowy = db.relationship('OpiekunProfil', foreign_keys=[opiekun_zakladowy_id], lazy=True)


# === EFEKTY UCZENIA – POWIĄZANIE Z FORMULARZEM ===
class EfektUczeniaFormularz(db.Model):
    __tablename__ = 'efekt_uczenia_formularz'

    id = db.Column(db.Integer, primary_key=True)
    formularz_praktyk_id = db.Column(db.Integer, db.ForeignKey('formularz_praktyk.id'), nullable=False)
    efekt_uczenia_id = db.Column(db.Integer, db.ForeignKey('efekt_uczenia.id'), nullable=False)
    czy_potwierdzony_zakladowy = db.Column(db.Boolean, default=False)
    czy_potwierdzony_uczelniany = db.Column(db.Boolean, default=False)
    uwagi = db.Column(db.Text, nullable=True)

    efekt = db.relationship('EfektUczenia', backref='powiazania_formularz')


# === HARMONOGRAM PRAKTYK - Wniosek o praktyki ===
class HarmonogramPraktyk(db.Model):
    __tablename__ = 'harmonogram_praktyk'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student_profil.id'), nullable=False)
    opiekun_zakladowy_id = db.Column(db.Integer, db.ForeignKey('opiekun_profil.id'), nullable=False)
    firma_id = db.Column(db.Integer, db.ForeignKey('firma.id'), nullable=True)

    student = db.relationship('StudentProfil', foreign_keys=[student_id], lazy=True)
    opiekun_zakladowy = db.relationship('OpiekunProfil', foreign_keys=[opiekun_zakladowy_id], lazy=True)
    firma = db.relationship('Firma', foreign_keys=[firma_id], lazy=True)

    planowana_liczba_dni = db.Column(db.Integer, nullable=False)
    planowana_data_rozpoczecia = db.Column(db.Date, nullable=True)
    planowana_data_zakonczenia = db.Column(db.Date, nullable=True)
    
    status = db.Column(db.String(50), nullable=False, default="oczekuje") #oczekuje, zaakceptowany, odrzucony
    powod_odrzucenia = db.Column(db.String(500), nullable=True)
    utworzono = db.Column(db.DateTime, default=datetime.now)

    efekty_harmonogramu = db.relationship('EfektUczeniaHarmonogram', backref='harmonogram', lazy=True, cascade='all, delete-orphan')


# === EFEKTY UCZENIA – POWIĄZANIE Z HARMONOGRAMEM ===
class EfektUczeniaHarmonogram(db.Model):
    __tablename__ = 'efekt_uczenia_harmonogram'

    id = db.Column(db.Integer, primary_key=True)
    harmonogram_praktyk_id = db.Column(db.Integer, db.ForeignKey('harmonogram_praktyk.id'), nullable=False)
    efekt_uczenia_id = db.Column(db.Integer, db.ForeignKey('efekt_uczenia.id'), nullable=False)
    opis = db.Column(db.Text, nullable=True)

    efekt = db.relationship('EfektUczenia', backref='powiazania_harmonogram')


# === DZIENNIK PRAKTYK – WPIS ===
class DziennikWpis(db.Model):
    __tablename__ = 'dziennik_wpis'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student_profil.id'), nullable=False)
    nr_dnia = db.Column(db.Integer, nullable=False)
    data = db.Column(db.Date, nullable=False)
    liczba_godzin = db.Column(db.Float, nullable=False)
    opis = db.Column(db.Text, nullable=False)

    #czy_zatwierdzony = db.Column(db.Boolean, nullable=True, default=False)
    status = db.Column(db.String(20), nullable=False, default='w_trakcie') #w_trakcie, zatwierdzony, odrzucony
    powod_odrzucenia = db.Column(db.Text, nullable=True)

    utworzono = db.Column(db.DateTime, default=datetime.now)
    zaktualizowano = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    efekty = db.relationship('DziennikEfekt', backref='wpis', lazy=True)


# === DZIENNIK PRAKTYK – EFEKT UCZENIA WPISU ===
class DziennikEfekt(db.Model):
    __tablename__ = 'dziennik_efekt'

    id = db.Column(db.Integer, primary_key=True)
    dziennik_wpis_id = db.Column(db.Integer, db.ForeignKey('dziennik_wpis.id'), nullable=False)
    efekt_uczenia_id = db.Column(db.Integer, db.ForeignKey('efekt_uczenia.id'), nullable=False)
    #jeden wpis moze miec wiele efektow

    efekt_uczenia = db.relationship('EfektUczenia', lazy=True)