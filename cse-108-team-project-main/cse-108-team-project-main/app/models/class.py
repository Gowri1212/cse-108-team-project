from app import db


# Use an association object so we can store a grade per enrollment
class Enrollment(db.Model):
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    class_id = db.Column(db.Integer, db.ForeignKey('class.id'), primary_key=True)
    grade = db.Column(db.Float, nullable=True)

    student = db.relationship('User', back_populates='enrollments')
    class_ = db.relationship('Class', back_populates='enrollments')


class Class(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    capacity = db.Column(db.Integer)
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    enrollments = db.relationship('Enrollment', back_populates='class_', cascade='all, delete-orphan')

    @property
    def students(self):
        return [e.student for e in self.enrollments]

    def seats_left(self):
        return self.capacity - len(self.enrollments)
