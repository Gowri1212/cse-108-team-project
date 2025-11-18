import os
from flask import Flask
from flask_login import LoginManager
from .models import db, User, Role, Course, Enrollment 
from .routes import bp as routes_bp
from .admin import setup_admin

# Flask-Login setup
login_manager = LoginManager()

@login_manager.user_loader
def load_user(user_id):
    """Callback for Flask-Login to load a user from the database."""
    return db.session.get(User, int(user_id))

def init_db_data(app):
    """Helper function to initialize roles and test users."""
    with app.app_context():
        # add roles if they don't exist
        roles = ['Student', 'Teacher', 'Admin']
        for role_name in roles:
            if not Role.query.filter_by(name=role_name).first():
                db.session.add(Role(name=role_name))
        db.session.commit()

        # role ID
        student_role = Role.query.filter_by(name='Student').first()
        teacher_role = Role.query.filter_by(name='Teacher').first()
        admin_role = Role.query.filter_by(name='Admin').first()

        # backup test users
        test_users = [
            ('student', 'student@acme.edu', 'studentpass', student_role.id),
            ('teacher', 'teacher@acme.edu', 'teacherpass', teacher_role.id),
            ('admin', 'admin@acme.edu', 'adminpass', admin_role.id),
        ]
        for username, email, password, role_id in test_users:
            if not User.query.filter_by(username=username).first():
                new_user = User(username=username, email=email, role_id=role_id)
                new_user.set_password(password)
                db.session.add(new_user)
        db.session.commit()

        # back up courses and enrollments
        teacher_user = User.query.filter_by(username='teacher').first()
        student_user = User.query.filter_by(username='student').first()
        
        # check to see if teachers have been assigned courses
        if not Course.query.filter_by(teacher_id=teacher_user.id).first():
            course1 = Course(name='CS 101: Intro to CS', capacity=5, teacher=teacher_user)
            course2 = Course(name='Math 202: Advanced Calc', capacity=10, teacher=teacher_user)
            db.session.add_all([course1, course2])
            db.session.commit()

            #create an enrollment for the student when enrolling in courses
            db.session.add(Enrollment(student=student_user, course=course1, grade=88.5))
            db.session.add(Enrollment(student=student_user, course=course2, grade=None))
            db.session.commit()

def create_app(test_config=None):
    #path setup
    basedir = os.path.abspath(os.path.dirname(__file__))

    #configure app
    app = Flask(__name__, instance_relative_config=True)
    
    # application settings
    app.config.from_mapping(
        SECRET_KEY='dev', 
        SQLALCHEMY_DATABASE_URI='sqlite:////home/nsurender/ACME_Enrollment/site.db',
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )
    
    # intialize app with extensions and blueprints
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'routes.login' 

    # regiseter blueprints for the route
    app.register_blueprint(routes_bp)

    # flask set up admin panel
    setup_admin(app)

    # datatbase initialization with test data
    with app.app_context():
        db.create_all()
        init_db_data(app)

    return app