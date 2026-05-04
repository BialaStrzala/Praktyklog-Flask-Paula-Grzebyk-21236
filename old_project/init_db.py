from old_project.app import app, db
import old_project.models as models

with app.app_context():
    db.drop_all()
    db.create_all()

    # Admin
    admin_user = models.User(email='admin@admin.pl', role='admin')
    admin_user.set_password('admin')
    db.session.add(admin_user)
    db.session.commit()
    admin_profile = models.AdminProfile(user_id=admin_user.id, full_name='Administrator')
    db.session.add(admin_profile)

    # Student
    student_user = models.User(email='student@student.pl', role='student')
    student_user.set_password('student')
    db.session.add(student_user)
    db.session.commit()
    student_profile = models.StudentProfile(user_id=student_user.id, full_name='Jan Kowalski', student_id='21222', internship_place='Firma XYZ')
    db.session.add(student_profile)

    # Opiekun
    supervisor_user = models.User(email='supervisor@supervisor.pl', role='supervisor')
    supervisor_user.set_password('supervisor')
    db.session.add(supervisor_user)
    db.session.commit()
    supervisor_profile = models.SupervisorProfile(user_id=supervisor_user.id, full_name='Anna Nowak', type='workplace', workplace='Firma XYZ')
    db.session.add(supervisor_profile)
    db.session.commit()
    student_profile.workplace_supervisor_id = supervisor_profile.id
    db.session.commit()

    #Efekty uczenia
    confirmation_log = models.Confirmationlog(student_id=student_profile.id)
    db.session.add(confirmation_log)
    db.session.commit()
    learning_effects_1 = models.LearningEffects(number=1, description='loremipsum', confirmation_id=confirmation_log.id)
    db.session.add(learning_effects_1)
    db.session.commit()

    print("DB initialized")