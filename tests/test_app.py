from pathlib import Path

import re
from html import unescape

import pytest
from werkzeug.security import generate_password_hash

from app import create_app
from models.database import db, Student, Course, Enrollment
from recommender.quiz_data import QUIZ_BANK


@pytest.fixture()
def client(tmp_path):
    database_path = (tmp_path / "test_learning.db").resolve()

    test_app = create_app(
        {
            "TESTING": True,
                        "WTF_CSRF_ENABLED": False,
            "SECRET_KEY": "test-secret-not-for-production",
            "SQLALCHEMY_DATABASE_URI": (
                f"sqlite:///{database_path.as_posix()}"
            ),
        }
    )

    with test_app.app_context():
        active_database = db.engine.url.database

        assert active_database is not None
        assert Path(active_database).resolve() == database_path

        db.create_all()

        student = Student(
            name="Test Student",
            email="student@example.com",
            password_hash=generate_password_hash("password123"),
            interests="python",
            skills="python",
        )

        admin = Student(
            name="Test Admin",
            email="admin@example.com",
            password_hash=generate_password_hash("password123"),
            is_admin=True,
        )

        course = Course(
            title="Python Test Course",
            category="Programming",
            level="Beginner",
            skills="python",
            description="A course for tests.",
        )

        db.session.add_all([student, admin, course])
        db.session.commit()

    try:
        with test_app.test_client() as test_client:
            yield test_client
    finally:
        with test_app.app_context():
            db.session.remove()
            db.engine.dispose()


def login(client, email="student@example.com"):
    return client.post(
        "/login",
        data={
            "email": email,
            "password": "password123",
        },
        follow_redirects=True,
    )


def course_id_for(client):
    with client.application.app_context():
        return Course.query.one().id


def test_homepage_loads(client):
    assert client.get("/").status_code == 200


def test_registration_page_loads(client):
    assert client.get("/register").status_code == 200


def test_courses_requires_login(client):
    assert client.get("/courses").status_code in (302, 401)


def test_login_opens_dashboard(client):
    response = login(client)

    assert response.status_code == 200
    assert b"Test" in response.data


def test_student_cannot_open_admin_pages(client):
    login(client)

    for path in (
        "/admin",
        "/admin/student-reports",
        "/admin/student-reports/export",
    ):
        assert client.get(path).status_code == 403


def test_admin_can_open_reports_and_export(client):
    login(client, "admin@example.com")

    assert client.get("/admin").status_code == 200
    assert client.get("/admin/student-reports").status_code == 200

    response = client.get("/admin/student-reports/export")

    assert response.status_code == 200
    assert b"Student Name" in response.data


def test_registration_normalizes_email(client):
    response = client.post(
        "/register",
        data={
            "name": "New Student",
            "email": "NEW@example.com",
            "password": "password123",
            "interests": "python",
            "skills": "",
        },
    )

    assert response.status_code == 302

    with client.application.app_context():
        student = Student.query.filter_by(
            email="new@example.com"
        ).one()

        assert student.name == "New Student"
        assert student.is_admin is False


def test_registration_rejects_short_password(client):
    response = client.post(
        "/register",
        data={
            "name": "New Student",
            "email": "new@example.com",
            "password": "short",
        },
    )

    assert response.status_code == 200

    with client.application.app_context():
        assert Student.query.filter_by(
            email="new@example.com"
        ).first() is None


def test_duplicate_email_is_rejected(client):
    client.post(
        "/register",
        data={
            "name": "Duplicate",
            "email": "STUDENT@example.com",
            "password": "password123",
        },
    )

    with client.application.app_context():
        assert Student.query.filter_by(
            email="student@example.com"
        ).count() == 1


def test_duplicate_enrollment_is_prevented(client):
    login(client)
    course_id = course_id_for(client)

    client.post(f"/enroll/{course_id}")
    client.post(f"/enroll/{course_id}")

    with client.application.app_context():
        student = Student.query.filter_by(
            email="student@example.com"
        ).one()

        assert Enrollment.query.filter_by(
            student_id=student.id,
            course_id=course_id,
        ).count() == 1


def test_quiz_requires_enrollment(client):
    login(client)
    course_id = course_id_for(client)

    response = client.get(f"/quiz/{course_id}")

    assert response.status_code == 302

    with client.application.app_context():
        assert Enrollment.query.count() == 0


def test_quiz_saves_score(client):
    login(client)
    course_id = course_id_for(client)
    client.post(f"/enroll/{course_id}")

    answers = {
        f"question_{index}": str(question["answer"])
        for index, question in enumerate(QUIZ_BANK["python"])
    }

    response = client.post(
        f"/quiz/{course_id}",
        data=answers,
    )

    assert response.status_code == 200

    with client.application.app_context():
        enrollment = Enrollment.query.one()

        assert enrollment.quiz_score == 100.0
        assert enrollment.completed is False


def test_invalid_quiz_answer_is_rejected(client):
    login(client)
    course_id = course_id_for(client)
    client.post(f"/enroll/{course_id}")

    response = client.post(
        f"/quiz/{course_id}",
        data={"question_0": "999"},
    )

    assert response.status_code == 400

    with client.application.app_context():
        assert Enrollment.query.one().quiz_score is None


def test_completion_requires_passing_score(client):
    login(client)
    course_id = course_id_for(client)
    client.post(f"/enroll/{course_id}")

    with client.application.app_context():
        enrollment = Enrollment.query.one()
        enrollment.quiz_score = 40
        db.session.commit()

    client.post(f"/courses/{course_id}/complete")

    with client.application.app_context():
        enrollment = Enrollment.query.one()
        assert enrollment.completed is False

        enrollment.quiz_score = 50
        db.session.commit()

    client.post(f"/courses/{course_id}/complete")

    with client.application.app_context():
        assert Enrollment.query.one().completed is True


def test_course_with_enrollments_cannot_be_deleted(client):
    login(client)
    course_id = course_id_for(client)
    client.post(f"/enroll/{course_id}")

    client.post("/logout")
    login(client, "admin@example.com")

    response = client.post(
        f"/admin/courses/{course_id}/delete"
    )

    assert response.status_code == 302

    with client.application.app_context():
        assert db.session.get(Course, course_id) is not None
        assert Enrollment.query.count() == 1

def test_login_requires_csrf_token(client):
    client.application.config["WTF_CSRF_ENABLED"] = True

    response = client.post(
        "/login",
        data={
            "email": "student@example.com",
            "password": "password123",
        },
    )

    assert response.status_code == 400


def test_login_accepts_valid_csrf_token(client):
    client.application.config["WTF_CSRF_ENABLED"] = True

    page = client.get("/login")

    match = re.search(
        r'name="csrf_token"\s+value="([^"]+)"',
        page.get_data(as_text=True),
    )

    assert match is not None

    response = client.post(
        "/login",
        data={
            "email": "student@example.com",
            "password": "password123",
            "csrf_token": unescape(match.group(1)),
        },
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/dashboard")

    with client.session_transaction() as session:
        assert "_user_id" in session


def test_logout_rejects_get_requests(client):
    login(client)

    assert client.get("/logout").status_code == 405


def test_logout_requires_csrf_token(client):
    login(client)
    client.application.config["WTF_CSRF_ENABLED"] = True

    response = client.post("/logout")

    assert response.status_code == 400

    with client.session_transaction() as session:
        assert "_user_id" in session
def test_course_detail_requires_login(client):
    course_id = course_id_for(client)

    response = client.get(f"/courses/{course_id}")

    assert response.status_code == 302


def test_course_notes_require_enrollment(client):
    login(client)

    with client.application.app_context():
        course = Course.query.one()
        course.title = "Python Programming Fundamentals"
        course_id = course.id
        db.session.commit()

    response = client.get(f"/courses/{course_id}")

    assert response.status_code == 200
    assert b"Enroll in course" in response.data
    assert b"Variables, values, and comments" not in response.data


def test_enrolled_student_can_read_course_notes(client):
    login(client)

    with client.application.app_context():
        course = Course.query.one()
        course.title = "Python Programming Fundamentals"
        course_id = course.id
        db.session.commit()

    client.post(f"/enroll/{course_id}")

    response = client.get(f"/courses/{course_id}")

    assert response.status_code == 200
    assert b"Variables, values, and comments" in response.data
    assert b"Practice task" in response.data


def test_unpublished_course_has_clear_message(client):
    login(client)
    course_id = course_id_for(client)

    response = client.get(f"/courses/{course_id}")

    assert response.status_code == 200
    assert b"Learning notes have not been published" in response.data