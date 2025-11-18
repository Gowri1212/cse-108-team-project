from flask import Blueprint, render_template
from flask_login import login_required, current_user

# rename blueprint to avoid collision with Flask-Admin's blueprint named 'admin'
admin_bp = Blueprint('admin_bp', __name__, url_prefix="/admin")


@admin_bp.route("/dashboard")
@login_required
def dashboard():
    # Admin UI is available at /flask-admin (Flask-Admin integration)
    return render_template("admin.html", admin_url='/flask-admin')
