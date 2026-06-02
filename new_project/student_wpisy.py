from app import app, db
import models as models
from datetime import date

with app.app_context():
    me_uzytkownik = models.Uzytkownik.query.filter_by(imie='Paula').first()
    me_profil = models.StudentProfil.query.filter_by(uzytkownik_id=me_uzytkownik.id).first()
    harmonogram = models.HarmonogramPraktyk.query.filter_by(student_id=me_profil.id).first()
    formularz = models.FormularzPraktyk.query.filter_by(student_id=me_profil.id).first()
    liczba_wpisow = models.DziennikWpis.query.filter_by(student_id=me_profil.id).count()

    # Wpisy
    wpis1 = models.DziennikWpis(
        student_id=me_profil.id,
        nr_dnia=liczba_wpisow+1,
        data=date.fromisoformat('2026-07-04'),
        liczba_godzin=8,
        opis="Pierwszy dzień praktyk. Zapoznanie się z zespołem i środowiskiem pracy."
        )
    wpis2 = models.DziennikWpis(student_id=me_profil.id, nr_dnia=liczba_wpisow+2, data=date.fromisoformat('2026-07-05'), liczba_godzin=7, opis="Drugi dzień praktyk. Udział w spotkaniu projektowym i rozpoczęcie pracy nad zadaniem.")
    wpis3 = models.DziennikWpis(student_id=me_profil.id, nr_dnia=liczba_wpisow+3, data=date.fromisoformat('2026-07-06'), liczba_godzin=8, opis="Trzeci dzień praktyk. Kontynuacja pracy nad zadaniem i konsultacje z opiekunem zakładowym.", status='odrzucony')
    db.session.add(wpis1)
    db.session.add(wpis2)
    db.session.add(wpis3)
    db.session.commit()

    print('Dodano przykladowe wpisy')