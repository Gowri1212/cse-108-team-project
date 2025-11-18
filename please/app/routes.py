from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import current_user, login_user, logout_user, login_required
from sqlalchemy import func
from .models import db, User, Course, Enrollment 

# Create a Blueprint named 'routes'
bp = Blueprint('routes', __name__)

@bp.route('/')
def index():
    if current_user.is_authenticated:
        # Redirect users to their respective dashboard
        if current_user.role_id == 1: # Student
            return redirect(url_for('routes.student_dashboard'))
        elif current_user.role_id == 2: # Teacher
            return redirect(url_for('routes.teacher_dashboard'))
        elif current_user.role_id == 3: # Admin
            return redirect(url_for('admin.index'))
        else:
            # Unknown Users: log them out and redirect to the index
            logout_user()
            flash("Session error: Unknown user role detected. Please log in again.")
            return redirect(url_for('routes.index'))

    # Default logged-out page
    return render_template_string("""
    <div style="font-family: Arial, sans-serif; padding: 20px; border: 1px solid #ccc; border-radius: 8px; max-width: 400px; margin: 50px auto; text-align: center;">
        <h1 style="color: #1e40af;">ACME University Enrollment</h1>
        {% with messages = get_flashed_messages() %}
            {% if messages %}
                <ul style="list-style: none; padding: 10px; background-color: #fce3e3; color: #cc0000; border: 1px solid #ffcccc; border-radius: 4px; margin-bottom: 15px;">
                    {% for message in messages %}
                        <li>{{ message }}</li>
                    {% endfor %}
                </ul>
            {% endif %}
        {% endwith %}
        <p>Please sign in to access your dashboard.</p>
        <p style="margin-top: 20px;">
            <a href="{{ url_for('routes.login') }}" style="padding: 10px 20px; background-color: #3b82f6; color: white; border-radius: 5px; text-decoration: none; display: inline-block;">Log In</a>
        </p>
        <p style="margin-top: 15px; font-size: 0.8em; color: #666;">
            Admins: <a href="{{ url_for('admin.index') }}" style="color: #666;">Admin Dashboard</a>
        </p>
    </div>
    """)


# USER LOGIN
@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('routes.index'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('routes.index'))
        else:
            flash("Invalid username or password.")
            return redirect(url_for('routes.login'))

    # HTML form for login
    return render_template_string("""
    <div style="font-family: Arial, sans-serif; padding: 20px; border: 1px solid #ccc; border-radius: 8px; max-width: 400px; margin: 50px auto;">
        <h1 style="color: #1e40af;">Sign In</h1>
        {% with messages = get_flashed_messages() %}
            {% if messages %}
                <ul style="list-style: none; padding: 10px; background-color: #fce3e3; color: #cc0000; border: 1px solid #ffcccc; border-radius: 4px; margin-bottom: 15px;">
                    {% for message in messages %}
                        <li>{{ message }}</li>
                    {% endfor %}
                </ul>
            {% endif %}
        {% endwith %}
        <form method="POST">
            <label for="username" style="display: block; margin-top: 10px;">Username:</label>
            <input type="text" id="username" name="username" required style="width: 100%; padding: 8px; margin-top: 5px; border: 1px solid #ccc; border-radius: 4px;"><br>
            <label for="password" style="display: block; margin-top: 10px;">Password:</label>
            <input type="password" id="password" name="password" required style="width: 100%; padding: 8px; margin-top: 5px; border: 1px solid #ccc; border-radius: 4px;"><br><br>
            <button type="submit" style="width: 100%; padding: 10px; background-color: #3b82f6; color: white; border: none; border-radius: 4px; cursor: pointer;">Sign In</button>
        </form>
        <hr style="border-top: 1px solid #e0e0e0; margin: 20px 0;">
        <p><a href="/" style="color: #3b82f6; text-decoration: none;">Go Home</a></p>
    </div>
    """)

# USER LOGOUT
@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash("You have been logged out.")
    return redirect(url_for('routes.index'))

# STUDENT DASHBOARD AND ENROLLMENT
@bp.route('/student')
@login_required
def student_dashboard():
    if current_user.role_id != 1:
        flash("Access denied: You must be a Student.")
        return redirect(url_for('routes.index'))

    # 1. My Classes: Courses the student is currently enrolled in
    my_enrollments = current_user.enrollments.join(Course).all()

    # 2. Classes Offered: All courses that the student is NOT enrolled in
    enrolled_course_ids = [e.course_id for e in my_enrollments]
    
    # Query for all courses not in the student's enrollments
    classes_offered = Course.query.filter(Course.id.notin_(enrolled_course_ids)).all()
    
    # Merge and display all data from above on webpage
    return render_template_string(STUDENT_DASHBOARD_HTML, 
                                  current_user=current_user,
                                  my_enrollments=my_enrollments, 
                                  classes_offered=classes_offered,
                                  url_for=url_for,
                                  get_flashed_messages=lambda: flash(request.args.get('flash_message')) if request.args.get('flash_message') else get_flashed_messages())

# Student Enrollment Action
@bp.route('/enroll/<int:course_id>', methods=['POST'])
@login_required
# Make sure role is student
def enroll_course(course_id):
    if current_user.role_id != 1:
        flash("Access denied.")
        return redirect(url_for('routes.index'))
    # Get the course
    course = db.session.get(Course, course_id)
    if not course:
        flash("Error: Course not found.")
        return redirect(url_for('routes.student_dashboard'))

    # Check if already registered
    if Enrollment.query.filter_by(user_id=current_user.id, course_id=course_id).first():
        flash(f"You are already registered for {course.name}.")
        return redirect(url_for('routes.student_dashboard'))
    
    # Check if course capacity is reached
    if course.enrolled_students >= course.capacity:
        flash(f"Enrollment failed: {course.name} is full (Capacity {course.capacity}).")
        return redirect(url_for('routes.student_dashboard'))

    # If yes, create new enrollment record
    new_enrollment = Enrollment(user_id=current_user.id, course_id=course_id)
    db.session.add(new_enrollment)
    db.session.commit()
    flash(f"Successfully enrolled in {course.name}!")
    return redirect(url_for('routes.student_dashboard'))


# TEACHER DASHBOARD AND GRADE MANAGEMENT

@bp.route('/teacher')
@login_required
# Make sure role is teacher
def teacher_dashboard():
    if current_user.role_id != 2:
        flash("Access denied: You must be a Teacher.")
        return redirect(url_for('routes.index'))

    # Courses taught by the current teacher
    my_courses = current_user.teaching_courses.all()
    
    # Merge and display all data from above on webpage
    return render_template_string(TEACHER_DASHBOARD_HTML, 
                                  current_user=current_user,
                                  my_courses=my_courses,
                                  url_for=url_for,
                                  get_flashed_messages=lambda: flash(request.args.get('flash_message')) if request.args.get('flash_message') else get_flashed_messages())

@bp.route('/teacher/course/<int:course_id>')
@login_required
# View class roster and grades
def view_class_roster(course_id):
    # Make sure role is teacher
    if current_user.role_id != 2:
        flash("Access denied.")
        return redirect(url_for('routes.index'))
    # Get the course
    course = db.session.get(Course, course_id)
    
    # Make sure the teacher actually teaches this course
    if not course or course.teacher_id != current_user.id:
        flash("Course not found or you are not the assigned teacher.")
        return redirect(url_for('routes.teacher_dashboard'))

    # Get all enrollments (students and their grades) for this course
    enrollments = Enrollment.query.filter_by(course_id=course_id).join(User).all()
    
    # Show the roster view of enrollment data
    return render_template_string(ROSTER_VIEW_HTML, 
                                  course=course,
                                  enrollments=enrollments,
                                  url_for=url_for,
                                  get_flashed_messages=lambda: flash(request.args.get('flash_message')) if request.args.get('flash_message') else get_flashed_messages())

@bp.route('/teacher/update_grade/<int:enrollment_id>', methods=['POST'])
@login_required
# Update a student's grade
def update_grade(enrollment_id):
    # Make sure role is teacher
    if current_user.role_id != 2:
        flash("Access denied.")
        return redirect(url_for('routes.index'))
    
    # Get the enrollment record, get grade from form
    enrollment = db.session.get(Enrollment, enrollment_id)
    new_grade = request.form.get('grade', type=float)
    
    # Make sure the teacher teaches this course
    if not enrollment or enrollment.course.teacher_id != current_user.id:
        flash("Enrollment record not found or you are not the course teacher.")
        return redirect(url_for('routes.teacher_dashboard'))

    # Update the grade
    try:
        if new_grade is not None and 0 <= new_grade <= 100:
            enrollment.grade = new_grade
            db.session.commit()
            flash(f"Grade updated for {enrollment.student.username} in {enrollment.course.name}.")
        else:
            flash("Invalid grade value (must be between 0 and 100).")
    except Exception as e:
        db.session.rollback()
        flash(f"An error occurred while updating the grade: {e}")

    # Go back to class roster
    return redirect(url_for('routes.view_class_roster', course_id=enrollment.course_id))

# HTML Templates

# Function to mimic Flask's render_template behavior without requiring separate template files
from flask import render_template_string, get_flashed_messages

STUDENT_DASHBOARD_HTML = """
<div style="font-family: Arial, sans-serif; padding: 20px;">
    <h1 style="color: #1e40af;">Welcome, {{ current_user.username }} (Student)!</h1>
    <p><a href="{{ url_for('routes.logout') }}" style="color: #dc2626;">Log Out</a></p>
    
    {% with messages = get_flashed_messages() %}
        {% if messages %}
            <ul style="list-style: none; padding: 10px; background-color: #d1e7dd; color: #0f5132; border: 1px solid #badbcc; border-radius: 4px;">
                {% for message in messages %}
                    <li>{{ message }}</li>
                {% endfor %}
            </ul>
        {% endif %}
    {% endwith %}

    <h2>My Classes</h2>
    <table border="1" style="width: 100%; border-collapse: collapse; margin-bottom: 30px;">
        <thead style="background-color: #f0f8ff;">
            <tr>
                <th style="padding: 10px;">Course Name</th>
                <th style="padding: 10px;">Teacher</th>
                <th style="padding: 10px;">Time</th>
                <th style="padding: 10px;">My Grade</th>
            </tr>
        </thead>
        <tbody>
            {% for enrollment in my_enrollments %}
            <tr>
                <td style="padding: 10px;">{{ enrollment.course.name }}</td>
                <td style="padding: 10px;">{{ enrollment.course.teacher.username }}</td>
                <td style="padding: 10px;">MWF 10:00-10:50 AM</td> <!-- Mock Time -->
                <td style="padding: 10px;">{{ enrollment.grade | default('N/A', True) }}</td>
            </tr>
            {% else %}
            <tr><td colspan="4" style="text-align: center; padding: 10px;">You are not currently enrolled in any classes.</td></tr>
            {% endfor %}
        </tbody>
    </table>

    <h2>Classes Offered (Enroll)</h2>
    <table border="1" style="width: 100%; border-collapse: collapse;">
        <thead style="background-color: #f0f8ff;">
            <tr>
                <th style="padding: 10px;">Course Name</th>
                <th style="padding: 10px;">Teacher</th>
                <th style="padding: 10px;">Enrollment</th>
                <th style="padding: 10px;">Action</th>
            </tr>
        </thead>
        <tbody>
            {% for course in classes_offered %}
            <tr>
                <td style="padding: 10px;">{{ course.name }}</td>
                <td style="padding: 10px;">{{ course.teacher.username }}</td>
                <td style="padding: 10px;">{{ course.enrolled_students }}/{{ course.capacity }}</td>
                <td style="padding: 10px;">
                    {% if course.enrolled_students < course.capacity %}
                    <form method="POST" action="{{ url_for('routes.enroll_course', course_id=course.id) }}" style="display: inline;">
                        <button type="submit" style="background-color: #22c55e; color: white; border: none; padding: 5px 10px; cursor: pointer; border-radius: 4px;">Enroll +</button>
                    </form>
                    {% else %}
                    <span style="color: red;">FULL</span>
                    {% endif %}
                </td>
            </tr>
            {% else %}
            <tr><td colspan="4" style="text-align: center; padding: 10px;">No other classes are currently offered.</td></tr>
            {% endfor %}
        </tbody>
    </table>
</div>
"""

TEACHER_DASHBOARD_HTML = """
<div style="font-family: Arial, sans-serif; padding: 20px;">
    <h1 style="color: #1e40af;">Welcome, {{ current_user.username }} (Teacher)!</h1>
    <p><a href="{{ url_for('routes.logout') }}" style="color: #dc2626;">Log Out</a></p>

    {% with messages = get_flashed_messages() %}
        {% if messages %}
            <ul style="list-style: none; padding: 10px; background-color: #d1e7dd; color: #0f5132; border: 1px solid #badbcc; border-radius: 4px;">
                {% for message in messages %}
                    <li>{{ message }}</li>
                {% endfor %}
            </ul>
        {% endif %}
    {% endwith %}

    <h2>My Teaching Courses</h2>
    <table border="1" style="width: 100%; border-collapse: collapse; margin-bottom: 30px;">
        <thead style="background-color: #f0f8ff;">
            <tr>
                <th style="padding: 10px;">Course Name</th>
                <th style="padding: 10px;">Students Enrolled</th>
                <th style="padding: 10px;">Action</th>
            </tr>
        </thead>
        <tbody>
            {% for course in my_courses %}
            <tr>
                <td style="padding: 10px;">{{ course.name }}</td>
                <td style="padding: 10px;">{{ course.enrolled_students }}/{{ course.capacity }}</td>
                <td style="padding: 10px;">
                    <a href="{{ url_for('routes.view_class_roster', course_id=course.id) }}" 
                       style="background-color: #3b82f6; color: white; text-decoration: none; padding: 5px 10px; border-radius: 4px;">View Roster</a>
                </td>
            </tr>
            {% else %}
            <tr><td colspan="3" style="text-align: center; padding: 10px;">You are not currently assigned to teach any courses.</td></tr>
            {% endfor %}
        </tbody>
    </table>
</div>
"""

ROSTER_VIEW_HTML = """
<div style="font-family: Arial, sans-serif; padding: 20px;">
    <h1 style="color: #1e40af;">Roster for {{ course.name }}</h1>
    <p><a href="{{ url_for('routes.teacher_dashboard') }}" style="color: #666;">&larr; Back to Dashboard</a> | 
       <a href="{{ url_for('routes.logout') }}" style="color: #dc2626;">Log Out</a></p>

    {% with messages = get_flashed_messages() %}
        {% if messages %}
            <ul style="list-style: none; padding: 10px; background-color: #d1e7dd; color: #0f5132; border: 1px solid #badbcc; border-radius: 4px;">
                {% for message in messages %}
                    <li>{{ message }}</li>
                {% endfor %}
            </ul>
        {% endif %}
    {% endwith %}

    <table border="1" style="width: 100%; border-collapse: collapse; margin-top: 20px;">
        <thead style="background-color: #f0f8ff;">
            <tr>
                <th style="padding: 10px;">Student Name</th>
                <th style="padding: 10px;">Current Grade</th>
                <th style="padding: 10px;">Update Grade</th>
            </tr>
        </thead>
        <tbody>
            {% for enrollment in enrollments %}
            <tr>
                <td style="padding: 10px;">{{ enrollment.student.username }}</td>
                <td style="padding: 10px;">{{ enrollment.grade | default('N/A', True) }}</td>
                <td style="padding: 10px;">
                    <form method="POST" action="{{ url_for('routes.update_grade', enrollment_id=enrollment.id) }}" style="display: flex; gap: 5px; justify-content: center;">
                        <input type="number" name="grade" step="0.1" min="0" max="100" placeholder="{{ enrollment.grade | default('0', True) }}" 
                               style="width: 60px; padding: 5px; border: 1px solid #ccc; border-radius: 4px;">
                        <button type="submit" style="background-color: #2563eb; color: white; border: none; padding: 5px 10px; cursor: pointer; border-radius: 4px;">Save</button>
                    </form>
                </td>
            </tr>
            {% else %}
            <tr><td colspan="3" style="text-align: center; padding: 10px;">No students are currently enrolled in this class.</td></tr>
            {% endfor %}
        </tbody>
    </table>
</div>
"""
