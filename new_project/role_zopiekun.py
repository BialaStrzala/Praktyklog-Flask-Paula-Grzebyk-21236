from app import app, db
import models as models

with app.app_context():
    me_uzytkownik = models.Uzytkownik.query.filter_by(imie='Paula').first()

    me_uzytkownik.rola = 'opiekun'
    opiekun_profil = models.OpiekunProfil(uzytkownik_id=me_uzytkownik.id, firma_id=1, typ_opiekuna='zakladowy')
    db.session.add(opiekun_profil)
    models.db.session.commit()
    print('Changed current user role to opiekun_zakladowy')