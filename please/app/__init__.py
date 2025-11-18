import os
from flask import Flask
from flask_login import LoginManager
from .models import db # Only import the db instance
from .routes import bp as routes_bp
from .admin import setup_admin

# Initialize extensions (global instances)
login_manager = LoginManager()

# --- Helper Function for Initial User Data ---
def init_db_data(app):
    """Helper function to initialize roles, users, and courses."""
    # Local import inside the function to ensure models are loaded
    from .models import User, Role, Course, Enrollment 
    
    with app.app_context():
        # FIX: Check if Roles exist. If they do, we assume data is initialized.
        if Role.query.first():
            print("Database already initialized with roles and users.")
            return

        print("Initializing database with default roles, users, and courses...")
        
        # 1. Create Roles
        roles = ['Student', 'Teacher', 'Admin']
        for role_name in roles:
            db.session.add(Role(name=role_name))
        db.session.commit() # Commit roles first

        # 2. Get the role IDs
        student_role = Role.query.filter_by(name='Student').first()
        teacher_role = Role.query.filter_by(name='Teacher').first()
        admin_role = Role.query.filter_by(name='Admin').first()

        # 3. Create test users
        test_users = [
            ('student', 'student@acme.edu', 'studentpass', student_role.id),
            ('teacher', 'teacher@acme.edu', 'teacherpass', teacher_role.id),
            ('admin', 'admin@acme.edu', 'adminpass', admin_role.id),
        ]
        for username, email, password, role_id in test_users:
            new_user = User(username=username, email=email, role_id=role_id)
            new_user.set_password(password)
            db.session.add(new_user)
        db.session.commit() # Commit users next

        # 4. Create sample courses and enrollments
        teacher_user = User.query.filter_by(username='teacher').first()
        student_user = User.query.filter_by(username='student').first()
        
        # Add Courses (These must be unique)
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

    # Configure DB URI for local SQLite only
    # --------------------------------------------------------------------------
    DB_URI = 'sqlite:///' + os.path.join(basedir, '../site.db')
    # --------------------------------------------------------------------------

    # Create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    
    # Configure the application settings
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'default-dev-key'), # Use ENV var for security
        SQLALCHEMY_DATABASE_URI=DB_URI,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )
    
    # --- MODEL LOADING SEQUENCE ---
    from .models import User, Role, Course, Enrollment 
    
    # 2. Initialize Extensions with the app
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'routes.login' 

    # 3. Register Blueprints (for routes)
    app.register_blueprint(routes_bp)
    
    # 4. Setup Flask-Admin
    setup_admin(app)

    # 5. Initialize Database Data (inside app context)
    with app.app_context():
        db.create_all()
        init_db_data(app)

    return app

# --- Login Manager User Loader (Needs User Model) ---

@login_manager.user_loader
def load_user(user_id):
    """Callback for Flask-Login to load a user from the database."""
    from .models import User
    return db.session.get(User, int(user_id))
