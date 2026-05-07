# Importy
import os
from flask import Flask
from flask_login import LoginManager
from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv
from models import db, Uzytkownik

load_dotenv()
app = Flask(__name__)

# === DB ===
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY"),
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///internships.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'
oauth = OAuth(app)

@login_manager.user_loader
def load_user(uzytkownik_id):
    return Uzytkownik.query.get(int(uzytkownik_id))

# === MSFT ===
microsoft = oauth.register(
    name="microsoft",

    client_id=os.getenv("MICROSOFT_CLIENT_ID"),

    client_secret=os.getenv("MICROSOFT_CLIENT_SECRET"),

    server_metadata_url=(
        f"https://login.microsoftonline.com/"
        f"{os.getenv('MICROSOFT_TENANT_ID')}"
        f"/v2.0/.well-known/openid-configuration"
    ),

    client_kwargs={
        "scope": "openid profile email User.Read"
    }
)

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