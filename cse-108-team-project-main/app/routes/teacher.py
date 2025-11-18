from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
import importlib

teacher = Blueprint('teacher', __name__, url_prefix="/teacher")

class_mod = importlib.import_module('app.models.class')
Class = getattr(class_mod, 'Class')
Enrollment = getattr(class_mod, 'Enrollment')


@teacher.route("/dashboard")
@login_required
def dashboard():
    # show classes taught by teacher and enrolled students
    if not current_user.is_teacher():
        flash('Access restricted to teachers.')
        return redirect(url_for('auth.login'))

    classes = Class.query.filter_by(teacher_id=current_user.id).all()
    return render_template("teacher.html", user=current_user, classes=classes)


@teacher.route('/grade', methods=['POST'])
@login_required
def edit_grade():
    if not current_user.is_teacher():
        flash('Access restricted to teachers.')
        return redirect(url_for('auth.login'))

    student_id = request.form.get('student_id')
    class_id = request.form.get('class_id')
    grade = request.form.get('grade')

    enrollment = Enrollment.query.filter_by(student_id=student_id, class_id=class_id).first()
    if not enrollment:
        flash('Enrollment not found.')
        return redirect(url_for('teacher.dashboard'))

    try:
        enrollment.grade = float(grade)
    except (TypeError, ValueError):
        enrollment.grade = None

    db.session.commit()
    flash('Grade updated.')
    return redirect(url_for('teacher.dashboard'))
