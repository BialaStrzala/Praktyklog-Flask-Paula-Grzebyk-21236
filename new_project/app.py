# Importy
from flask import Flask
from flask_login import LoginManager

from models import db, Uzytkownik

app = Flask(__name__)

# === DB ===
app.config['SECRET_KEY'] = 'dev-secret-key-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///internships.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'

@login_manager.user_loader
def load_user(uzytkownik_id):
    return Uzytkownik.query.get(int(uzytkownik_id))

# === ROUTES ===
from routes.auth import auth_bp
from routes.student import student_bp
from routes.opiekun import opiekun_bp
from routes.dziekanat import dziekanat_bp
from routes.admin import admin_bp

app.register_blueprint(auth_bp)
app.register_blueprint(student_bp, url_prefix='/student')
app.register_blueprint(opiekun_bp, url_prefix='/opiekun')
app.register_blueprint(dziekanat_bp, url_prefix='/dziekanat')
app.register_blueprint(admin_bp, url_prefix='/admin')


# === MAIN ===
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)