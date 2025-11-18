import os
from flask import Flask
from flask_login import LoginManager
from .models import db # Only import the db instance
from .routes import bp as routes_bp
from .admin import setup_admin

# Initialize login manager
login_manager = LoginManager()

# Helper function for initial user data 
def init_db_data(app):
    """Helper function to initialize roles, users, and courses."""
    # import inside the function to ensure models are loaded
    from .models import User, Role, Course, Enrollment 
    
    with app.app_context():
        # Check if Roles exist. If they do, we assume data is initialized.
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

        # 3. Create admin
        test_users = [
            ('admin', 'adminpass', admin_role.id),
        ]
        new_user = User(username='admin', role_id=admin_role.id)
        new_user.set_password('adminpass')
        db.session.add(new_user)
        db.session.commit() # commit the admin



def create_app(test_config=None):
    # path for the database file
    basedir = os.path.abspath(os.path.dirname(__file__))

    # Configure DB URI for local SQLite 
    DB_URI = 'sqlite:///' + os.path.join(basedir, '../site.db')

    # Create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    
    # Configure the application settings
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'default-dev-key'), 
        SQLALCHEMY_DATABASE_URI=DB_URI,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )
    
    # Load models
    from .models import User, Role, Course, Enrollment 
    
    # Initialize Extensions with the app
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'routes.login' 

    # Register Blueprints (for routes)
    app.register_blueprint(routes_bp)
    
    # Setup Flask-Admin
    setup_admin(app)

    # Initialize Database Data (inside app context)
    with app.app_context():
        db.create_all()
        init_db_data(app)

    return app

# Login Manager User Loader (Needs User Model)
@login_manager.user_loader
def load_user(user_id):
    from .models import User
    return db.session.get(User, int(user_id))
