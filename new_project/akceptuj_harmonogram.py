from app import app, db
import models as models

with app.app_context():
    me_uzytkownik = models.Uzytkownik.query.filter_by(imie='Paula').first()
    me_profil = models.StudentProfil.query.filter_by(uzytkownik_id=me_uzytkownik.id).first()
    harmonogram = models.HarmonogramPraktyk.query.filter_by(student_id=me_profil.id).first()

    harmonogram.status = 'zaakceptowany'
    formularz = models.FormularzPraktyk(
        student_id=me_profil.id, 
        opiekun_uczelniany_id=2, 
        opiekun_zakladowy_id=harmonogram.opiekun_zakladowy_id, 
        firma_id=harmonogram.firma_id,
        harmonogram_praktyk_id=harmonogram.id,
        data_rozpoczecia=harmonogram.planowana_data_rozpoczecia,
        data_zakonczenia=harmonogram.planowana_data_zakonczenia,
        )

    models.db.session.add(formularz)
    models.db.session.commit()
    print('Zaakceptowano harmonogram')