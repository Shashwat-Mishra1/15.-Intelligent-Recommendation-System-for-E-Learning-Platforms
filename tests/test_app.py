import os
import tempfile

import pytest
from werkzeug.security import generate_password_hash

from app import app
from models.database import db, Student, Course, Enrollment


@pytest.fixture()
def client():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI=f"sqlite:///{path}",
        SECRET_KEY="test-secret",
        WTF_CSRF_ENABLED=False,
    )
    app.extensions.pop("learning_app_db_initialized", None)
    with app.app_context():
        db.session.remove()
        db.engines[app].dispose()
        db.drop_all()
        db.create_all()
        student = Student(name="Test Student", email="student@example.com",
                          password_hash=generate_password_hash("password123"),
                          interests="python", skills="python")
        admin = Student(name="Test Admin", email="admin@example.com",
                        password_hash=generate_password_hash("password123"),
                        is_admin=True)
        course = Course(title="Python Test Course", category="Programming",
                        level="Beginner", skills="python",
                        description="A course for tests.")
        db.session.add_all([student, admin, course])
        db.session.commit()
    with app.test_client() as test_client:
        yield test_client
    with app.app_context():
        db.session.remove()
        db.drop_all()
        db.engines[app].dispose()
    app.extensions.pop("learning_app_db_initialized", None)
    os.unlink(path)


def login(client, email):
    return client.post("/login", data={"email": email, "password": "password123"}, follow_redirects=True)


def test_homepage_loads(client):
    assert client.get("/").status_code == 200


def test_registration_page_loads(client):
    assert client.get("/register").status_code == 200


def test_courses_requires_login(client):
    response = client.get("/courses")
    assert response.status_code in (302, 401)


def test_student_cannot_open_admin_reports(client):
    login(client, "student@example.com")
    assert client.get("/admin/student-reports").status_code == 403
    assert client.get("/admin/student-reports/export").status_code == 403


def test_admin_can_open_reports_and_export(client):
    login(client, "admin@example.com")
    assert client.get("/admin/student-reports").status_code == 200
    response = client.get("/admin/student-reports/export")
    assert response.status_code == 200
    assert b"Student Name" in response.data
