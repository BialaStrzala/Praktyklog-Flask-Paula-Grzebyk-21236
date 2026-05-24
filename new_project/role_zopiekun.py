from app import app, db
import models as models

with app.app_context():
    me = models.Uzytkownik.query.filter_by(id=3).first()
    me.rola = 'opiekun'
    opiekun_profil = models.OpiekunProfil(uzytkownik_id=me.id, firma_id=1, typ_opiekuna='zakladowy')
    db.session.add(opiekun_profil)
    models.db.session.add(me)
    models.db.session.commit()
    print('Changed current user role to opiekun_zakladowy')