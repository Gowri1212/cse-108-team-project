from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user

db = SQLAlchemy()
login_manager = LoginManager()


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'devkey123'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    # Register blueprints
    from app.routes.auth import auth
    from app.routes.student import student
    from app.routes.teacher import teacher
    from app.routes.admin import admin_bp

    app.register_blueprint(auth)
    app.register_blueprint(student)
    app.register_blueprint(teacher)
    app.register_blueprint(admin_bp)

    # Import models and set up Flask-Admin
    from flask_admin import Admin
    from flask_admin.contrib.sqla import ModelView
    from app.models.user import User
    import importlib
    class_mod = importlib.import_module('app.models.class')
    Class = getattr(class_mod, 'Class')
    Enrollment = getattr(class_mod, 'Enrollment')

    class AdminModelView(ModelView):
        def is_accessible(self):
            return current_user.is_authenticated and getattr(current_user, 'role', None) == 'admin'

    # Custom User admin view: hash password on create/update and show role choices
    from werkzeug.security import generate_password_hash

    class UserAdminView(AdminModelView):
        column_list = ('id', 'username', 'role')
        form_excluded_columns = ('enrollments', 'taught_classes')
        form_choices = {
            'role': [
                ('student', 'student'),
                ('teacher', 'teacher'),
                ('admin', 'admin')
            ]
        }

        def on_model_change(self, form, model, is_created):
            # If password field present and not already hashed, hash it before saving
            pw = getattr(form, 'password', None)
            if pw is not None:
                raw = pw.data
                if raw:
                    model.password = generate_password_hash(raw)

    admin = Admin(name='Admin', url='/flask-admin')
    admin.init_app(app)

    # Add models to admin interface (protected via AdminModelView)
    admin.add_view(UserAdminView(User, db.session, name='Users'))
    admin.add_view(AdminModelView(Class, db.session, name='Classes'))
    admin.add_view(AdminModelView(Enrollment, db.session, name='Enrollments'))

    with app.app_context():
        db.create_all()

    return app
