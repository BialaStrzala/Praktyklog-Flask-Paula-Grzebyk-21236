from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
import old_project.models as models
from functools import wraps

supervisor_bp = Blueprint('supervisor', __name__)

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

@supervisor_bp.route('/dashboard')
@role_required('supervisor')
def dashboard():
    profile = models.SupervisorProfile.query.filter_by(user_id=current_user.id).first()
    if profile.type == 'workplace':
        students = models.StudentProfile.query.filter_by(workplace_supervisor_id=profile.id).all()
    elif profile.type == 'college':
        students = models.StudentProfile.query.filter_by(college_supervisor_id=profile.id).all()
    else:
        students = []
    return render_template('supervisor/dashboard.html', profile=profile, students=students)

@supervisor_bp.route('/student/<int:student_id>')
@role_required('supervisor')
def student_detail(student_id):
    profile = models.SupervisorProfile.query.filter_by(user_id=current_user.id).first()
    student = models.StudentProfile.query.get_or_404(student_id)
    # Check assignment
    if (profile.type == 'workplace' and student.workplace_supervisor_id != profile.id) or \
       (profile.type == 'college' and student.college_supervisor_id != profile.id):
        flash('Access denied.')
        return redirect(url_for('supervisor.dashboard'))
    logs = models.InternshipLog.query.filter_by(student_id=student.id).order_by(models.InternshipLog.date.desc()).all()
    return render_template('supervisor/student_detail.html', student=student, logs=logs)

@supervisor_bp.route('/sign/<int:log_id>', methods=['POST'])
@role_required('supervisor')
def sign_log(log_id):
    profile = models.SupervisorProfile.query.filter_by(user_id=current_user.id).first()
    log = models.InternshipLog.query.get_or_404(log_id)
    student = models.StudentProfile.query.get(log.student_id)
    if (profile.type == 'workplace' and student.workplace_supervisor_id == profile.id):
        log.workplace_supervisor_signed = True
    elif (profile.type == 'college' and student.college_supervisor_id == profile.id):
        log.college_supervisor_signed = True
    else:
        flash('Cannot sign.')
        return redirect(url_for('supervisor.student_detail', student_id=student.id))
    models.db.session.commit()
    flash('Signed.')
    return redirect(url_for('supervisor.student_detail', student_id=student.id))

@supervisor_bp.route('/learning-effects/<int:confirmation_id>')
@role_required('supervisor')
def learning_effects(confirmation_id):
    supervisor = models.SupervisorProfile.query.filter_by(user_id=current_user.id).first()
    confirmation = models.Confirmationlog.query.get_or_404(confirmation_id)
    student = confirmation.student
    
    # Verify supervisor is assigned to this student
    if (supervisor.type == 'workplace' and student.workplace_supervisor_id != supervisor.id) or \
       (supervisor.type == 'college' and student.college_supervisor_id != supervisor.id):
        return 'bajo jajo brak dostepu'
        #return redirect(url_for('supervisor.dashboard'))
    
    effects = models.LearningEffects.query.filter_by(confirmation_id=confirmation_id).order_by(models.LearningEffects.number).all()
    return render_template('supervisor/learning_effects.html', confirmation=confirmation, student=student, effects=effects, supervisor=supervisor)

@supervisor_bp.route('/sign-confirmation/<int:confirmation_id>', methods=['POST'])
@role_required('supervisor')
def sign_confirmation(confirmation_id):
    from datetime import datetime
    supervisor = models.SupervisorProfile.query.filter_by(user_id=current_user.id).first()
    confirmation = models.Confirmationlog.query.get_or_404(confirmation_id)
    student = models.StudentProfile.query.get(confirmation.student_id)
    
    # Verify supervisor is assigned
    if (supervisor.type == 'workplace' and student.workplace_supervisor_id != supervisor.id) or \
       (supervisor.type == 'college' and student.college_supervisor_id != supervisor.id):
        flash('Cannot sign.')
        return redirect(url_for('supervisor.learning_effects', confirmation_id=confirmation_id))
    
    if supervisor.type == 'workplace':
        confirmation.workplace_supervisor_signed = True
        confirmation.workplace_supervisor_signed_date = datetime.now()
    elif supervisor.type == 'college':
        if request.form.get('opinion'):
            confirmation.college_supervisor_opinion = request.form.get('opinion')
        confirmation.college_supervisor_signed = True
        confirmation.college_supervisor_signed_date = datetime.now()
    
    models.db.session.commit()
    flash('Document signed.')
    return redirect(url_for('supervisor.learning_effects', confirmation_id=confirmation_id))

@supervisor_bp.route('/approve-effect/<int:effect_id>', methods=['POST'])
@role_required('supervisor')
def approve_effect(effect_id):
    supervisor = models.SupervisorProfile.query.filter_by(user_id=current_user.id).first()
    effect = models.LearningEffects.query.get_or_404(effect_id)
    confirmation = models.Confirmationlog.query.get(effect.confirmation_id)
    student = models.StudentProfile.query.get(confirmation.student_id)
    
    # Verify supervisor is assigned
    if (supervisor.type == 'workplace' and student.workplace_supervisor_id != supervisor.id) or \
       (supervisor.type == 'college' and student.college_supervisor_id != supervisor.id):
        flash('Cannot approve.')
        return redirect(url_for('supervisor.learning_effects', confirmation_id=confirmation.id))
    
    effect.is_approved = not effect.is_approved
    models.db.session.commit()
    return redirect(url_for('supervisor.learning_effects', confirmation_id=confirmation.id))