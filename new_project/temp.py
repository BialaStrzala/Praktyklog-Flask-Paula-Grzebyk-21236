from app import app, db
import models as models
from datetime import date

with app.app_context():
    me_uzytkownik = models.Uzytkownik.query.filter_by(imie='Paula').first()
    me_profil_opiekuna = models.OpiekunProfil.query.filter_by(uzytkownik_id=me_uzytkownik.id).first()

    # Praktyki studenta 2
    harmonogram = models.HarmonogramPraktyk(
        student_id=2,
        opiekun_zakladowy_id=me_profil_opiekuna.id,
        firma_id=1,
        planowana_liczba_dni=120,
        planowana_data_rozpoczecia=date.fromisoformat('2026-07-01'),
        planowana_data_zakonczenia=date.fromisoformat('2027-02-01'),
        status='zaakceptowany',
    )
    db.session.add(harmonogram)
    db.session.commit()

    formularz = models.FormularzPraktyk(
        student_id=2, 
        opiekun_zakladowy_id=me_profil_opiekuna.id, 
        firma_id=harmonogram.firma_id, 
        harmonogram_praktyk_id=harmonogram.id, 
        data_rozpoczecia=harmonogram.planowana_data_rozpoczecia,
        data_zakonczenia=harmonogram.planowana_data_zakonczenia,
        status = 'w_trakcie',
        )
    models.db.session.add(formularz)
    models.db.session.commit()

    # Wpisy studenta 2
    wpis1 = models.DziennikWpis(
        student_id=2,
        nr_dnia=1,
        data=date.fromisoformat('2026-07-01'),
        liczba_godzin=8,
        opis="Pierwszy dzień praktyk. Zapoznanie się z zespołem i środowiskiem pracy."
        )
    wpis2 = models.DziennikWpis(student_id=2, nr_dnia=2, data=date.fromisoformat('2026-07-01'), liczba_godzin=7, opis="Drugi dzień praktyk. Udział w spotkaniu projektowym i rozpoczęcie pracy nad zadaniem.")
    wpis3 = models.DziennikWpis(student_id=2, nr_dnia=3, data=date.fromisoformat('2026-07-02'), liczba_godzin=8, opis="Trzeci dzień praktyk. Kontynuacja pracy nad zadaniem i konsultacje z opiekunem zakładowym.")
    db.session.add(wpis1)
    db.session.add(wpis2)
    db.session.add(wpis3)
    db.session.commit()

    print('Dodano dane studenta 2 podpiete pod aktualnego uzytkownika jako opiekuna zakladowego')