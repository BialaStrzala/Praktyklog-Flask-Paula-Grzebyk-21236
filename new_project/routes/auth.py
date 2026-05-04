from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
import models as models

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect_based_on_role(current_user)

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = models.Uzytkownik.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect_based_on_role(user)
        else:
            flash('Niepoprawny email lub haslo')

    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

def redirect_based_on_role(user):
    if user.rola == 'student':
        return redirect(url_for('student.dashboard'))
    elif user.rola == 'opiekun_zakladowy' or user.rola == 'opiekun_uczelniany':
        return redirect(url_for('opiekun.dashboard'))
    elif user.rola == 'dziekanat':
        return redirect(url_for('dziekanat.dashboard'))
    elif user.rola == 'admin':
        return redirect(url_for('admin.dashboard'))
    return redirect(url_for('auth.login'))