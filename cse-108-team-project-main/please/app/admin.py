from flask import redirect, url_for, request
from flask_admin import Admin, AdminIndexView, BaseView, expose
from flask_admin.contrib.sqla import ModelView
from flask_admin.menu import MenuLink
from flask_login import current_user
from wtforms.fields import PasswordField
from .models import db, Role, User, Course, Enrollment # Relative import
from sqlalchemy.event import listen
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

#Admin check setup

class CustomAdminIndexView(AdminIndexView):
    """
    Custom index view to restrict access to the /admin page.
    """
    def is_accessible(self):
        #checks if the current user is an admin
        return current_user.is_authenticated and current_user.role_id == 3

    def inaccessible_callback(self, name, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('routes.login', next=request.url))
        return "Access denied: You must be an Admin.", 403

#class to restrict access to admin views

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

# class to manage users and roles

class CustomUserView(CustomModelView):
    column_list = ('id', 'username', 'role')
    form_columns = ('username', 'password', 'role')
    form_extra_fields = {
        'password': PasswordField('Password (Will be Hashed)')
    }
    column_exclude_list = ('password_hash', 'email', 'enrollments', 'teaching_courses') 
    
    #incrept password hashing when creating or updating a user
    def on_model_change(self, form, model, is_created):
        if 'password' in form and form.password.data:
            model.set_password(form.password.data)
        elif is_created and not form.password.data:
             raise ValueError('Password is required for new users.')

# shows courses and their teachers
class CourseView(CustomModelView):
    
    column_list = ('id', 'name', 'capacity', 'teacher')
    column_searchable_list = ['name']
    column_filters = ['teacher.username']
    column_formatters = {
        'teacher': lambda v, c, m, p: m.teacher.username if m.teacher else 'N/A'
    }
    
    #only teachers are shown in the teacher dropdown
    form_args = {
        'teacher': {
            'query_factory': lambda: User.query.filter(User.role_id == 2)
        }
    }
    # no enrollments shown in course view
    form_excluded_columns = ('enrollments',)
    

# Enrolement view to manage student enrollments and grades
class EnrollmentView(CustomModelView):
    column_editable_list = ('grade',)
    column_list = ('id', 'student', 'course', 'grade')
    column_searchable_list = ['student.username', 'course.name']
    column_filters = ['course.name', 'student.username']

    # display usernames and course names 
    column_formatters = {
        'student': lambda v, c, m, p: m.student.username,
        'course': lambda v, c, m, p: m.course.name
    }

    # only students shwon in student dropdown
    form_args = {
        'student': {
            'query_factory': lambda: User.query.filter(User.role_id == 1)
        },
        'course': {
            'get_label': lambda c: c.name # Use the course name for display
        }
    }
    
    # prevent duplicate enrollments and check capacity by overriding create_model
    def create_model(self, form):
        course = form.course.data
        student = form.student.data
        
        # capacity check
        if course.enrolled_students >= course.capacity:
            raise ValueError(f"Enrollment failed: {course.name} is full (Capacity {course.capacity}).")

        # duplicate enrollment check
        if Enrollment.query.filter_by(user_id=student.id, course_id=course.id).first():
            raise ValueError(f"Enrollment failed: {student.username} is already enrolled in {course.name}.")

        return super(EnrollmentView, self).create_model(form)

def setup_admin(app):
    """Initializes and configures Flask-Admin with custom views."""
    admin = Admin(
        app, 
        index_view=CustomAdminIndexView(name='Admin Dashboard', url='/admin'),
        name='ACME University Admin'
    )
    
    # admin only views shown on dashboard
    admin.add_view(CustomUserView(User, db.session, name='Users & Roles', category='Management'))
    admin.add_view(CourseView(Course, db.session, name='Classes & Teachers', category='Management'))
    admin.add_view(EnrollmentView(Enrollment, db.session, name='Enrollment Records', category='Management'))
    
    
    # add logout link to admin panel
    admin.add_link(MenuLink(name='Logout & Main Page', url='/logout'))