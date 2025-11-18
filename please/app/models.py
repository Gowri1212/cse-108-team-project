from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

# Global SQLAlchemy instance
db = SQLAlchemy()

# Define the three distinct roles
class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    users = db.relationship('User', backref='role', lazy=True)

    def __repr__(self):
        return f'<Role {self.name}>'
    
    # Display role name
    def __str__(self):
        return self.name

# User Model for authentication and roles
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    # 1: Student, 2: Teacher, 3: Admin
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'), default=1) 
    enrollments = db.relationship('Enrollment', backref='student', lazy='dynamic')
    teaching_courses = db.relationship('Course', backref='teacher', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username} ({self.role.name})>'

# Course Model (for Teacher)
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

# Enrollment Model (Students enrolling in Courses)
class Enrollment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'))
    grade = db.Column(db.Float, nullable=True) 

    __table_args__ = (db.UniqueConstraint('user_id', 'course_id', name='unique_enrollment'),)

    def __repr__(self):
        return f'<Enrollment User:{self.user_id} Course:{self.course_id}>'
