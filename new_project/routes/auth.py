import os
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
import models as models
from app import microsoft
from flask import abort
from flask_login import login_user

auth_bp = Blueprint('auth', __name__)


# === REDIRECT ON ROLE ===
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


# === LOGIN ===
@auth_bp.route('/', methods=['GET', 'POST'])
def login_page():
    if current_user.is_authenticated:
        return redirect_based_on_role(current_user)
    if request.method == 'POST':
        return redirect(url_for('auth.login'))
    return render_template('login.html')


# === AUTH LOGIN ===
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    redirect_uri = os.getenv("MICROSOFT_REDIRECT_URI")
    return microsoft.authorize_redirect(redirect_uri)


# === LOGOUT ===
@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


# === AUTH CALLBACK ===
@auth_bp.route('/auth/callback')
def auth_callback():
    token = microsoft.authorize_access_token()
    resp = microsoft.get(
        "https://graph.microsoft.com/v1.0/me",
        token=token
    )
    msft_profil = resp.json()

    user_info = token["userinfo"]
    external_id = user_info["sub"]
    email = user_info.get("email") or user_info.get("preferred_username")
    given_name = msft_profil.get("givenName","")
    family_name = msft_profil.get("surname","")

    print(msft_profil)
    print(email)

    if not email:
        abort(400, "Brak adresu email")

    # Spr domeny
    student_domain = os.getenv("STUDENT_DOMAIN")
    employee_domain = os.getenv("EMPLOYEE_DOMAIN")
    domain = email.split("@")[-1].lower()
    if domain == student_domain:
        rola = "student"
        konto_aktywne = True
    elif domain == employee_domain:
        rola = "oczekuje_na_zatwierdzenie"
        konto_aktywne = False
    else:
        return "Brak dostępu dla tej domeny", 403

    # Czy uzytkownik istnieje
    user = models.Uzytkownik.query.filter_by(external_id=external_id).first()

    # Rejestracja nowego
    if not user:
        user = models.Uzytkownik(
            email=email,
            imie=given_name,
            nazwisko=family_name,
            external_id=external_id,
            auth_provider="microsoft",
            rola=rola,
            konto_aktywne=konto_aktywne
        )
        models.db.session.add(user)
        models.db.session.commit()
        if rola == 'student':
            profil = models.StudentProfil(uzytkownik_id=user.id, indeks=email[0:5])
            models.db.session.add(profil)
            models.db.session.commit()

    # Logowanie
    if not user.konto_aktywne:
        return "Konto oczekuje na zatwierdzenie"
    login_user(user)
    return redirect_based_on_role(user)