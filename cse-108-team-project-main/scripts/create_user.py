import sys
from werkzeug.security import generate_password_hash

from app import create_app, db
from app.models.user import User


def create_user(username: str, password: str, role: str):
    app = create_app()
    with app.app_context():
        existing = User.query.filter_by(username=username).first()
        if existing:
            print(f"User '{username}' already exists (id={existing.id}, role={existing.role}).")
            return

        hashed = generate_password_hash(password)
        user = User(username=username, password=hashed, role=role)
        db.session.add(user)
        db.session.commit()
        print(f"Created user '{username}' (id={user.id}, role={role}).")


def usage():
    print("Usage: python create_user.py <username> <password> <role>")
    print("role must be one of: student, teacher, admin")


if __name__ == '__main__':
    if len(sys.argv) != 4:
        usage()
        sys.exit(1)

    username, password, role = sys.argv[1], sys.argv[2], sys.argv[3]
    if role not in ("student", "teacher", "admin"):
        print("Invalid role. Must be: student, teacher, admin")
        sys.exit(1)

    create_user(username, password, role)
