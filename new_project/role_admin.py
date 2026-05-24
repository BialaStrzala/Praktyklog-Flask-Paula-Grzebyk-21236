from app import app, db
import models as models

with app.app_context():
    me = models.Uzytkownik.query.filter_by(id=3).first()
    me.rola = 'admin'
    models.db.session.add(me)
    models.db.session.commit()
    print('Changed current user role to admin')