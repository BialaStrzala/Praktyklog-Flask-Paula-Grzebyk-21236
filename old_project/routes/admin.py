from flask import Blueprint, render_template, redirect, url_for, request
from flask_login import login_required, current_user
import old_project.models as models
from functools import wraps
from datetime import datetime

admin_bp = Blueprint('admin', __name__)

def role_required(role):
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            if current_user.role != role:
                return redirect(url_for('auth.login'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@admin_bp.route('/dashboard')
@role_required('admin')
def dashboard():
    profile = models.AdminProfile.query.filter_by(user_id=current_user.id).first()
    return render_template('admin/dashboard.html', profile=profile)

@admin_bp.route('/uzytkownicy')
@role_required('admin')
def uzytkownicy():
    profile = models.AdminProfile.query.filter_by(user_id=current_user.id).first()
    users = models.User.query.all()
    return render_template('admin/uzytkownicy.html', profile=profile,users=users)

@admin_bp.route('/profil-uzytkownika/<int:user_id>', methods=['GET', 'POST'])
@role_required('admin')
def profil_uzytkownika(user_id):
    profile = models.AdminProfile.query.filter_by(user_id=current_user.id).first()

    user = models.User.query.filter_by(id=user_id).first()
    if user.role == 'student':
        user_profile = models.StudentProfile.query.filter_by(user_id=user_id).first()
    elif user.role == 'supervisor':
        user_profile = models.SupervisorProfile.query.filter_by(user_id=user_id).first()
    else:
        user_profile = models.AdminProfile.query.filter_by(user_id=user_id).first()
    return render_template('admin/profil_uzytkownika.html', profile=profile, user=user, user_profile=user_profile)


@admin_bp.route('/profil-uzytkownika/edytuj', methods=['POST'])
@role_required('admin')
def profil_uzytkownika_edytuj():
    user_id = request.form.get('user_id')
    profile = models.AdminProfile.query.filter_by(user_id=current_user.id).first()
    user = models.User.query.filter_by(id=user_id).first()

    full_name = request.form.get('full_name')
    role = request.form.get('role')
    email = request.form.get('email')
    user.full_name = full_name
    user.role = role
    user.email = email

    if role == 'student':
        student_id = request.form.get('student_id')
        college_major = request.form.get('college_major')
        college_specialization = request.form.get('college_specialization')
        internship_start_date = request.form.get('internship_start_date')
        internship_end_date = request.form.get('internship_end_date')
        user_profile = models.StudentProfile.query.filter_by(user_id=user_id).first()
        user_profile.student_id = student_id
        user_profile.college_major = college_major
        user_profile.college_specialization = college_specialization
        if internship_start_date:
            user_profile.internship_start_date = datetime.strptime(internship_start_date, '%Y-%m-%d').date()
        if internship_end_date:
            user_profile.internship_end_date = datetime.strptime(internship_end_date, '%Y-%m-%d').date()
    
    elif role == 'supervisor':
        supervisor_type = request.form.get('supervisor_type')
        workplace = request.form.get('workplace')
        user_profile = models.SupervisorProfile.query.filter_by(user_id=user_id).first()
        user_profile.type = supervisor_type
        user_profile.workplace = workplace
    models.db.session.commit()
    return redirect(url_for('admin.profil_uzytkownika', user_id=user_id))
    

@admin_bp.route('/profil-uzytkownika/usun/<int:user_id>', methods=['POST'])
@role_required('admin')
def profil_uzytkownika_usun(user_id):
    return 'tbd'