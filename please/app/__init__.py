import os
from flask import Flask
from flask_login import LoginManager
from .models import db, User, Role, Course, Enrollment # Relative imports
from .routes import bp as routes_bp
from .admin import setup_admin

# Initialize extensions (global instances)
login_manager = LoginManager()

@login_manager.user_loader
def load_user(user_id):
    """Callback for Flask-Login to load a user from the database."""
    return db.session.get(User, int(user_id))

def init_db_data(app):
    """Helper function to initialize roles and test users."""
    with app.app_context():
        # 1. Create Roles if they don't exist
        roles = ['Student', 'Teacher', 'Admin']
        for role_name in roles:
            if not Role.query.filter_by(name=role_name).first():
                db.session.add(Role(name=role_name))
        db.session.commit()

        # 2. Get the role IDs
        student_role = Role.query.filter_by(name='Student').first()
        teacher_role = Role.query.filter_by(name='Teacher').first()
        admin_role = Role.query.filter_by(name='Admin').first()

        # 3. Create test users if they don't exist
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

        # 4. Create sample courses and enrollments
        teacher_user = User.query.filter_by(username='teacher').first()
        student_user = User.query.filter_by(username='student').first()
        
        # Check if the teacher user has been assigned as a teacher for any course
        if not Course.query.filter_by(teacher_id=teacher_user.id).first():
            course1 = Course(name='CS 101: Intro to CS', capacity=5, teacher=teacher_user)
            course2 = Course(name='Math 202: Advanced Calc', capacity=10, teacher=teacher_user)
            db.session.add_all([course1, course2])
            db.session.commit()

            # Create an enrollment for the student
            db.session.add(Enrollment(student=student_user, course=course1, grade=88.5))
            db.session.add(Enrollment(student=student_user, course=course2, grade=None))
            db.session.commit()

def create_app(test_config=None):
    # Determine the absolute path for the database file
    basedir = os.path.abspath(os.path.dirname(__file__))

    # Create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    
    # Configure the application settings
    app.config.from_mapping(
        SECRET_KEY='dev', 
        SQLALCHEMY_DATABASE_URI='sqlite:////home/nsurender/ACME_Enrollment/site.db',
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )
    
    # 1. Initialize Extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'routes.login' 

    # 2. Register Blueprints (for routes)
    app.register_blueprint(routes_bp)

    # 3. Setup Flask-Admin
    setup_admin(app)

    # 4. Initialize Database Data (Roles and Test Users)
    with app.app_context():
        # WARNING: If you encounter issues where old data persists (e.g., deleted users still show up)
        # you may need to delete the 'site.db' file manually.
        db.create_all()
        init_db_data(app)

    return app