from app import app, db
import models as models

with app.app_context():
    me_uzytkownik = models.Uzytkownik.query.filter_by(imie='Paula').first()
    me_uzytkownik.rola = 'admin'
    models.db.session.commit()
    print('Changed current user role to admin')