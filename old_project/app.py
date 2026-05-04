# Importy
from flask import Flask
from flask_login import LoginManager

from old_project.models import db, User

app = Flask(__name__)

# === DB ===
app.config['SECRET_KEY'] = 'dev-secret-key-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///internships.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# === ROUTES ===
from old_project.routes.auth import auth_bp
from old_project.routes.student import student_bp
from old_project.routes.supervisor import supervisor_bp
from old_project.routes.admin import admin_bp

app.register_blueprint(auth_bp)
app.register_blueprint(student_bp, url_prefix='/student')
app.register_blueprint(supervisor_bp, url_prefix='/supervisor')
app.register_blueprint(admin_bp, url_prefix='/admin')


# === MAIN ===
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)