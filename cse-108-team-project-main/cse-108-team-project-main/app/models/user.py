from app import db, login_manager
from flask_login import UserMixin


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(200))
    role = db.Column(db.String(10))  
    # "student", "teacher", or "admin"

    # relationships
    enrollments = db.relationship('Enrollment', back_populates='student', cascade='all, delete-orphan')
    taught_classes = db.relationship('Class', backref='teacher', foreign_keys='Class.teacher_id')

    @property
    def classes(self):
        # convenience: list of Class objects the user (student) is enrolled in
        return [e.class_ for e in self.enrollments]

    def is_student(self):
        return self.role == 'student'

    def is_teacher(self):
        return self.role == 'teacher'

    def is_admin(self):
        return self.role == 'admin'

    def __repr__(self):
        return f"<User {self.username}>"

    def __str__(self):
        return self.username
