from app import app, db
import models as models
from datetime import date

def z_formularz():
    harmonogram = models.HarmonogramPraktyk(
        student_id=1,
        opiekun_zakladowy_id=3,
        firma_id=1,
        planowana_liczba_dni=120,
        planowana_data_rozpoczecia=date.fromisoformat('2026-07-01'),
        planowana_data_zakonczenia=date.fromisoformat('2027-02-01'),
        status='zaakceptowany',
    )
    models.db.session.add(harmonogram)
    models.db.session.commit()

    formularz = models.FormularzPraktyk(
        student_id=1, 
        opiekun_zakladowy_id=3, 
        firma_id=harmonogram.firma_id, 
        harmonogram_praktyk_id=harmonogram.id, 
        data_rozpoczecia=harmonogram.planowana_data_rozpoczecia,
        data_zakonczenia=harmonogram.planowana_data_zakonczenia,
        status = 'zaakceptowany',
        )
    models.db.session.add(formularz)
    models.db.session.commit()
    return

def z_temp_wpisy():
    wpis1 = models.DziennikWpis(
        student_id=1,
        nr_dnia=1,
        data=date.fromisoformat('2026-07-01'),
        liczba_godzin=8,
        opis="lorem ipsum"
        )
    models.db.session.add(wpis1)
    models.db.session.commit()

    wpis2 = models.DziennikWpis(
        student_id=1,
        nr_dnia=2,
        data=date.fromisoformat('2026-07-02'),
        liczba_godzin=7,
        opis="lorem ipsum dot amet"
        )
    models.db.session.add(wpis2)
    models.db.session.commit()

    return

with app.app_context():
    print(models.Uzytkownik.query.all())

    z_formularz()
    z_temp_wpisy()