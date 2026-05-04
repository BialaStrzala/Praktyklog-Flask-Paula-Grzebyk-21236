from app import app, db
import models as models

with app.app_context():
    db.drop_all()
    db.create_all()

    # Admin
    admin_uzytkownik = models.Uzytkownik(imie='admin', nazwisko='admin', email='admin@admin.pl', rola='admin')
    admin_uzytkownik.set_password('admin')
    db.session.add(admin_uzytkownik)
    db.session.commit()

    # Student
    student_uzytkownik = models.Uzytkownik(imie='Jan', nazwisko='Kowalski', email='student@student.pl', rola='student')
    student_uzytkownik.set_password('student')
    db.session.add(student_uzytkownik)
    db.session.commit()
    student_profil = models.StudentProfil(uzytkownik_id=student_uzytkownik.id, indeks='21222', rok_akademicki='2025/2026', semestr=6, kierunek='Informatyka', specjalnosc='ASK')
    db.session.add(student_profil)
    db.session.commit()

    # Firma
    firma = models.Firma(nazwa='Firma XYZ')
    db.session.add(firma)
    db.session.commit()

    # Opiekun Zakladowy
    opiekun_z_uzytkownik = models.Uzytkownik(imie='Anna', nazwisko='Nowak', email='opiekunz@opiekunz.pl', rola='opiekun_zakladowy')
    opiekun_z_uzytkownik.set_password('opiekunz')
    db.session.add(opiekun_z_uzytkownik)
    db.session.commit()
    opiekun_z_profil = models.OpiekunProfil(uzytkownik_id=opiekun_z_uzytkownik.id, firma_id=firma.id, typ_opiekuna='zakladowy')
    db.session.add(opiekun_z_profil)
    db.session.commit()

    print("DB initialized")

