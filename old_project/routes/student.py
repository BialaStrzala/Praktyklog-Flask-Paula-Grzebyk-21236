from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
import old_project.models as models
from datetime import datetime
from functools import wraps

student_bp = Blueprint('student', __name__)

def role_required(role):
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            if current_user.role != role:
                flash('Access denied.')
                return redirect(url_for('auth.login'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


@student_bp.route('/dashboard')
@role_required('student')
def dashboard():
    profile = models.StudentProfile.query.filter_by(user_id=current_user.id).first()
    college_supervisor = models.SupervisorProfile.query.filter_by(id=profile.college_supervisor_id).first() if profile and profile.college_supervisor_id else None
    workplace_supervisor = models.SupervisorProfile.query.filter_by(id=profile.workplace_supervisor_id).first() if profile and profile.workplace_supervisor_id else None
    return render_template('student/dashboard.html', profile=profile, college_supervisor=college_supervisor, workplace_supervisor=workplace_supervisor) #<- tu dodac


@student_bp.route('/profil-studenta', methods=['GET', 'POST'])
@role_required('student')
def profil_studenta():
    profile = models.StudentProfile.query.filter_by(user_id=current_user.id).first()
    if request.method == 'POST':
        if not profile:
            profile = models.StudentProfile(user_id=current_user.id)
        profile.full_name = request.form.get('full_name')
        profile.student_id = request.form.get('student_id')
        start_date_str = request.form.get('internship_start_date')
        end_date_str = request.form.get('internship_end_date')
        if start_date_str:
            profile.internship_start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        if end_date_str:
            profile.internship_end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        models.db.session.add(profile)
        models.db.session.commit()
        flash('Profile updated.')
        return redirect(url_for('student.dashboard'))
    return render_template('student/profil_studenta.html', profile=profile)

@student_bp.route('/profil-studenta/edytuj', methods=['GET', 'POST'])
@role_required('student')
def profil_studenta_edytuj():
    return render_template('student/profil_studenta_edytuj.html')

@student_bp.route('/dziennik', methods=['GET', 'POST'])
@role_required('student')
def dziennik():
    profile = models.StudentProfile.query.filter_by(user_id=current_user.id).first()

    if request.method == 'POST':
        date_str = request.form.get('date')
        description = request.form.get('description')
        hours = request.form.get('hours_worked')
        if date_str and description:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
            log = models.InternshipLog(
                student_id=profile.id,
                date=date,
                description=description,
                hours_worked=float(hours) if hours else None
            )
            models.db.session.add(log)
            models.db.session.commit()
            flash('Entry added.')
        return redirect(url_for('student.dziennik'))

    logs = models.InternshipLog.query.filter_by(student_id=profile.id).order_by(models.InternshipLog.date.asc()).all()
    total_working_days = len(logs)
    total_hours_worked = 0
    for log in logs:
        total_hours_worked += log.hours_worked
    return render_template('student/dziennik.html', profile=profile, logs=logs, total_working_days=total_working_days, total_hours_worked=total_hours_worked)


@student_bp.route('/dziennik/usun/<int:log_id>', methods=['POST'])
@role_required('student')
def dziennik_usun(log_id):
    profile = models.StudentProfile.query.filter_by(user_id=current_user.id).first()
    log = models.InternshipLog.query.get_or_404(log_id)
    if log.student_id != profile.id:
        flash('Brak dostępu.')
        return redirect(url_for('student.dziennik'))
    models.db.session.delete(log)
    models.db.session.commit()
    return redirect(url_for('student.dziennik'))


@student_bp.route('/dziennik/edytuj', methods=['POST'])
@role_required('student')
def dziennik_edytuj():
    profile = models.StudentProfile.query.filter_by(user_id=current_user.id).first()

    log_ids = request.form.getlist('log_id[]')
    dates = request.form.getlist('date[]')
    descriptions = request.form.getlist('description[]')
    hours_list = request.form.getlist('hours_worked[]')

    for i in range(len(log_ids)):
        log = models.InternshipLog.query.get(log_ids[i])

        if log and log.student_id == profile.id:
            log.date = datetime.strptime(dates[i], '%Y-%m-%d').date()
            log.description = descriptions[i]
            log.hours_worked = float(hours_list[i]) if hours_list[i] else None

    models.db.session.commit()
    flash('Wszystkie zmiany zapisane.')

    return redirect(url_for('student.dziennik'))


@student_bp.route('/efekty-nauki')
@role_required('student')
def efekty_nauki():
    profile = models.StudentProfile.query.filter_by(user_id=current_user.id).first()
    confirmation = models.Confirmationlog.query.filter_by(student_id=profile.id).first()
    
    if confirmation.student_id != profile.id:
        flash('Access denied.')
        return redirect(url_for('student.dashboard'))
    
    effects = models.LearningEffects.query.filter_by(confirmation_id=confirmation.id).order_by(models.LearningEffects.number).all()
    return render_template('student/efekty_nauki.html', profile=profile, confirmation=confirmation, effects=effects)

@student_bp.route('/efekty-nauki-pdf')
@role_required('student')
def efekty_nauki_pdf():
    return 'PDF generation not implemented yet'