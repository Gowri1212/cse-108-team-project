from flask import redirect, url_for, request, flash
from flask_admin import Admin, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from flask_admin.menu import MenuLink
from flask_login import current_user
from wtforms.fields import PasswordField
from .models import db, User, Role, Course, Enrollment 

# Admin Authentication Setup

class CustomAdminIndexView(AdminIndexView):
    """
    Custom view to restrict access to the /admin page.
    """
    def is_accessible(self):
        # check for Admin role (role_id 3)
        return current_user.is_authenticated and current_user.role_id == 3

    def inaccessible_callback(self, name, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('routes.login', next=request.url))
        return "Access denied: You must be an Admin.", 403

# Custom Model View Base Setup

class CustomModelView(ModelView):
    """
    Base class for views in Flask-Admin to restrict access to Admins.
    """
    def is_accessible(self):
        return current_user.is_authenticated and current_user.role_id == 3

    def inaccessible_callback(self, name, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('routes.login', next=request.url))
        return "Access denied: You must be an Admin.", 403

# Specialized Views
class CustomUserView(CustomModelView):
    column_list = ('id', 'username', 'role')
    form_columns = ('username', 'password', 'role')
    form_extra_fields = {
        'password': PasswordField('Password (Will be Hashed)')
    }
    column_exclude_list = ('password_hash', 'email', 'enrollments', 'teaching_courses') 
    
    def on_model_change(self, form, model, is_created):
        if 'password' in form and form.password.data:
            model.set_password(form.password.data)
        elif is_created and not form.password.data:
             raise ValueError('Password is required for new users.')

# Management > Classes & Teachers View
class CourseView(CustomModelView):
    column_list = ('id', 'name', 'capacity', 'teacher')
    column_searchable_list = ['name']
    column_filters = ['teacher.username']
    column_formatters = {
        'teacher': lambda v, c, m, p: m.teacher.username if m.teacher else 'N/A'
    }
    
    # Restrict the 'teacher' dropdown AND set the label to 'username'
    form_args = {
        'teacher': {
            'query_factory': lambda: User.query.filter(User.role_id == 2),
            'get_label': lambda u: u.username 
        }
    }
    form_excluded_columns = ('enrollments',)
    
    def on_model_change(self, form, model, is_created):
        # Check for Duplicate Name
        if is_created or model.name != db.session.get(Course, model.id).name:
            # Look for another course with the same name, excluding the one we are editing
            existing_course = Course.query.filter(
                Course.name == model.name,
                Course.id != model.id if model.id else 0
            ).first()

            if existing_course:
                # error message
                flash(f"Creation/Update failed: A course named '{model.name}' already exists.", 'error')
                return False

        # If it's a success or if the name didn't change, proceed with the save.
        return True
    
    

# Management > Enrollment Records View
class EnrollmentView(CustomModelView):
    column_editable_list = ('grade',)
    column_list = ('id', 'student', 'course', 'grade')
    column_searchable_list = ['student.username', 'course.name']
    column_filters = ['course.name', 'student.username']

    column_formatters = {
        'student': lambda v, c, m, p: m.student.username,
        'course': lambda v, c, m, p: m.course.name
    }

    # Restrict 'student' dropdown AND set the label to 'username'
    form_args = {
        'student': {
            'query_factory': lambda: User.query.filter(User.role_id == 1),
            'get_label': lambda u: u.username 
        },
        'course': {
            'get_label': lambda c: c.name 
        }
    }
    
    # logic to prevent duplicate enrollments or enrollments over capacity
    def create_model(self, form):
        course = form.course.data
        student = form.student.data
        
        # Check for Duplicate Enrollment
        if Enrollment.query.filter_by(user_id=student.id, course_id=course.id).first():
            flash(f"Enrollment failed: Student {student.username} is ALREADY enrolled in {course.name}.", 'error')
            return False
        
        # Check for Full Capacity
        if course.enrolled_students >= course.capacity:
            flash(f"Enrollment failed: Class {course.name} is FULL (Capacity {course.capacity}).", 'error')
            return False

        # If all checks pass, proceed with creation
        return super(EnrollmentView, self).create_model(form)

def setup_admin(app):
    """Configure Flask-Admin with custom views."""
    admin = Admin(
        app, 
        index_view=CustomAdminIndexView(name='Admin Dashboard', url='/admin'),
        name='ACME University Admin'
    )
    
    # Add the Admin-only views to the dashboard
    admin.add_view(CustomUserView(User, db.session, name='Users & Roles', category='Management'))
    admin.add_view(CourseView(Course, db.session, name='Classes & Teachers', category='Management'))
    admin.add_view(EnrollmentView(Enrollment, db.session, name='Enrollment Records', category='Management'))
    
    # Link to log out and go to the main page
    admin.add_link(MenuLink(name='Logout & Main Page', url='/logout'))
