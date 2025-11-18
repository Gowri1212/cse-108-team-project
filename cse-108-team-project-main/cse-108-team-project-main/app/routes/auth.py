from flask import Blueprint, render_template, redirect, request, url_for
from flask_login import login_user, logout_user, current_user
from werkzeug.security import check_password_hash
from app.models.user import User

auth = Blueprint('auth', __name__)

@auth.route("/")
def home():
    if current_user.is_authenticated:
        if current_user.role == "student":
            return redirect(url_for("student.dashboard"))
        elif current_user.role == "teacher":
            return redirect(url_for("teacher.dashboard"))
        elif current_user.role == "admin":
            return redirect(url_for("admin_bp.dashboard"))
    
    return redirect(url_for("auth.login"))

@auth.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)

            # Redirect based on role
            if user.role == "student":
                return redirect(url_for("student.dashboard"))
            elif user.role == "teacher":
                return redirect(url_for("teacher.dashboard"))
            elif user.role == "admin":
                return redirect(url_for("admin_bp.dashboard"))

        return render_template("login.html", error="Invalid username or password")

    return render_template("login.html")

@auth.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("auth.login"))
