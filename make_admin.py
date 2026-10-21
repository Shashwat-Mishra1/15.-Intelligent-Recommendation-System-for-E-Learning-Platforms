
from getpass import getpass

from app import app, db
from models.database import Student

with app.app_context():
    email = input("Enter your registered account email: ").strip().lower()
    student = Student.query.filter_by(email=email).first()

    if student is None:
        print("No account found for that email.")
    else:
        confirmation = input(
            f"Make {student.email} an administrator? Type YES: "
        ).strip()

        if confirmation == "YES":
            student.is_admin = True
            db.session.commit()
            print("SUCCESS: Administrator access enabled.")
        else:
            print("Cancelled. No changes made.")
