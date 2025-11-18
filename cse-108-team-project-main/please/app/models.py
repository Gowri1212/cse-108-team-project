from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

# intialized __init__.py  with Global SQLAlchemy instance
db = SQLAlchemy()

# 3 roles in the system: Student, Teacher, Admin
class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    users = db.relationship('User', backref='role', lazy=True)

    def __repr__(self):
        return f'<Role {self.name}>'
    
    
    def __str__(self):
        return self.name

# user used for authentication and authorization
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)

    email = db.Column(db.String(120), index=True, unique=False, nullable=True)
    password_hash = db.Column(db.String(128))
    # 3 roles are student, teacher, admin
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'), default=1) 
    enrollments = db.relationship('Enrollment', backref='student', lazy='dynamic')
    teaching_courses = db.relationship('Course', backref='teacher', lazy='dynamic')
    #password hashing functions
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username} ({self.role.name})>'

#course model 
class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    capacity = db.Column(db.Integer, default=10)
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    enrollments = db.relationship('Enrollment', backref='course', lazy='dynamic')

    def __repr__(self):
        return f'<Course {self.name}>'
    
    @property
    def enrolled_students(self):
        return self.enrollments.count()

# Enrollment Model
class Enrollment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'))
    grade = db.Column(db.Float, nullable=True) 

    __table_args__ = (db.UniqueConstraint('user_id', 'course_id', name='unique_enrollment'),)

    def __repr__(self):
        return f'<Enrollment User:{self.user_id} Course:{self.course_id}>'