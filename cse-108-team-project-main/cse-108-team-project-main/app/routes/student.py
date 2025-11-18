from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
import importlib

student = Blueprint('student', __name__, url_prefix="/student")


class_mod = importlib.import_module('app.models.class')
Class = getattr(class_mod, 'Class')
Enrollment = getattr(class_mod, 'Enrollment')
from app.models.user import User


@student.route("/dashboard")
@login_required
def dashboard():
    # show student's enrolled classes (with grades) and all offered classes
    enrolled = current_user.enrollments  # list of Enrollment objects
    offered = Class.query.all()
    return render_template("student.html", user=current_user, enrolled=enrolled, offered=offered)


@student.route('/enroll/<int:class_id>', methods=['POST'])
@login_required
def enroll(class_id):
    if not current_user.is_authenticated or not current_user.is_student():
        flash('Only students can enroll in classes.')
        return redirect(url_for('auth.login'))

    cls = Class.query.get_or_404(class_id)
    # check if already enrolled
    existing = Enrollment.query.filter_by(student_id=current_user.id, class_id=cls.id).first()
    if existing:
        flash('Already enrolled in this class.')
        return redirect(url_for('student.dashboard'))

    if cls.seats_left() <= 0:
        flash('No seats available.')
        return redirect(url_for('student.dashboard'))

    enrollment = Enrollment(student_id=current_user.id, class_id=cls.id)
    db.session.add(enrollment)
    db.session.commit()
    flash('Enrolled successfully.')
    return redirect(url_for('student.dashboard'))
 