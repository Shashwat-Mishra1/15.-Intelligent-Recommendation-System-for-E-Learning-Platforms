import csv
import io
import os
from functools import wraps
from pathlib import Path
from flask_wtf.csrf import CSRFProtect, CSRFError

from flask import (
    Flask,
    abort,
    flash,
    make_response,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash

from models.database import db, Student, Course, Enrollment
from recommender.engine import recommend_courses
from recommender.quiz_data import QUIZ_BANK
from recommender.learning_content import get_learning_content


BASE_DIR = Path(__file__).resolve().parent

login_manager = LoginManager()
csrf = CSRFProtect()
login_manager.login_view = "login"
login_manager.login_message_category = "info"

ALLOWED_LEVELS = {"Beginner", "Intermediate", "Advanced"}

STARTER_COURSES = [
    (
        "Python Programming Fundamentals",
        "Programming",
        "Beginner",
        "python, programming, problem solving",
        "Learn variables, data types, conditionals, loops, functions, "
        "and core Python concepts.",
    ),
    (
        "Web Development with Flask",
        "Web Development",
        "Intermediate",
        "python, flask, html, css, web development",
        "Build web applications with Flask, templates, routing, forms, "
        "and databases.",
    ),
    (
        "HTML and CSS Essentials",
        "Web Development",
        "Beginner",
        "html, css, frontend, web design",
        "Create accessible web pages with semantic HTML and responsive CSS.",
    ),
    (
        "JavaScript for Beginners",
        "Programming",
        "Beginner",
        "javascript, frontend, programming",
        "Learn JavaScript syntax, DOM manipulation, events, "
        "and browser fundamentals.",
    ),
    (
        "Machine Learning Basics",
        "Data Science",
        "Intermediate",
        "python, machine learning, data science, statistics",
        "Understand supervised learning, model evaluation, "
        "and basic machine-learning workflows.",
    ),
    (
        "Data Analysis with Pandas",
        "Data Science",
        "Intermediate",
        "python, pandas, data analysis, csv",
        "Clean, transform, analyze, and summarize datasets with Pandas.",
    ),
    (
        "SQL and Database Design",
        "Databases",
        "Beginner",
        "sql, database, data modeling",
        "Learn relational databases, SELECT queries, joins, "
        "constraints, and schema design.",
    ),
    (
        "Introduction to Artificial Intelligence",
        "Artificial Intelligence",
        "Beginner",
        "ai, machine learning, algorithms",
        "Explore AI concepts, search, knowledge representation, "
        "and practical applications.",
    ),
    (
        "Responsive UI Design",
        "Web Development",
        "Intermediate",
        "html, css, responsive design, ui",
        "Design usable responsive layouts for desktop and mobile screens.",
    ),
    (
        "Advanced Python Projects",
        "Programming",
        "Advanced",
        "python, oop, testing, software design",
        "Apply object-oriented programming, testing, "
        "and maintainable project design.",
    ),
]


@login_manager.user_loader
def load_user(user_id):
    try:
        return db.session.get(Student, int(user_id))
    except (TypeError, ValueError):
        return None


def admin_required(view_function):
    @wraps(view_function)
    @login_required
    def wrapped_view(*args, **kwargs):
        if not current_user.is_admin:
            abort(403)
        return view_function(*args, **kwargs)

    return wrapped_view


def seed_courses():
    """Seed the catalog only when it is empty."""
    if Course.query.first() is not None:
        return

    for title, category, level, skills, description in STARTER_COURSES:
        db.session.add(
            Course(
                title=title,
                category=category,
                level=level,
                skills=skills,
                description=description,
            )
        )

    db.session.commit()


def initialize_database():
    """Create missing tables; do not delete existing records."""
    db.create_all()
    seed_courses()


def average_score_for(enrollments):
    scores = [
        float(enrollment.quiz_score)
        for enrollment in enrollments
        if enrollment.quiz_score is not None
    ]

    return round(sum(scores) / len(scores), 1) if scores else None


def select_quiz_questions(course):
    """Preserve the existing course-to-bank selection behavior."""
    course_text = (
        f"{course.title} {course.skills or ''}"
    ).lower()

    if "python" in course_text:
        bank_key = "python"
    elif any(
        word in course_text
        for word in ("web", "html", "css", "flask", "javascript")
    ):
        bank_key = "web development"
    else:
        bank_key = "general"

    return QUIZ_BANK[bank_key]


def build_student_reports():
    reports = []

    students = (
        Student.query.options(
            db.selectinload(Student.enrollments)
        )
        .order_by(Student.name.asc())
        .all()
    )

    for student in students:
        enrollments = student.enrollments
        total = len(enrollments)
        completed = sum(
            1 for enrollment in enrollments if enrollment.completed
        )
        scored = sum(
            1
            for enrollment in enrollments
            if enrollment.quiz_score is not None
        )

        reports.append(
            {
                "id": student.id,
                "name": student.name,
                "email": student.email,
                "is_admin": student.is_admin,
                "total_enrolled": total,
                "completed_count": completed,
                # Legacy name retained for existing templates.
                # This counts scored enrollments, not all submissions.
                "quiz_attempts": scored,
                "average_score": average_score_for(enrollments),
                "completion_rate": (
                    round(completed / total * 100, 1) if total else 0
                ),
            }
        )

    return reports


def create_app(test_config=None):
    application = Flask(__name__)

    application.config.from_mapping(
        SECRET_KEY=os.environ.get(
            "SECRET_KEY",
            "change-this-development-secret-key",
        ),
        SQLALCHEMY_DATABASE_URI=os.environ.get(
            "DATABASE_URL",
            f"sqlite:///{(BASE_DIR / 'e_learning.db').as_posix()}",
        ),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        DEBUG=False,
    )

    if test_config is not None:
        application.config.update(test_config)

    db.init_app(application)
    login_manager.init_app(application)
    csrf.init_app(application)

    @application.route("/")
    def index():
        if current_user.is_authenticated:
            return redirect(url_for("dashboard"))

        return render_template("index.html")

    @application.route("/register", methods=["GET", "POST"])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for("dashboard"))

        if request.method == "POST":
            name = request.form.get("name", "").strip()
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")
            interests = request.form.get("interests", "").strip()
            skills = request.form.get("skills", "").strip()

            error = None

            if not all((name, email, password)):
                error = "Name, email, and password are required."
            elif len(name) > 100:
                error = "Name must be 100 characters or fewer."
            elif len(email) > 150:
                error = "Email must be 150 characters or fewer."
            elif len(password) < 8:
                error = "Use a password with at least 8 characters."
            elif len(interests) > 300:
                error = "Interests must be 300 characters or fewer."
            elif len(skills) > 300:
                error = "Skills must be 300 characters or fewer."
            elif Student.query.filter_by(email=email).first():
                error = "An account with that email already exists."

            if error:
                flash(error, "error")
            else:
                student = Student(
                    name=name,
                    email=email,
                    password_hash=generate_password_hash(password),
                    interests=interests,
                    skills=skills,
                )
                db.session.add(student)

                try:
                    db.session.commit()
                except IntegrityError:
                    db.session.rollback()
                    flash(
                        "The account could not be created. "
                        "That email may already be registered.",
                        "error",
                    )
                else:
                    login_user(student)
                    flash("Account created successfully.", "success")
                    return redirect(url_for("dashboard"))

        return render_template("register.html")

    @application.route("/login", methods=["GET", "POST"])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for("dashboard"))

        if request.method == "POST":
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")

            student = Student.query.filter_by(email=email).first()

            if student and check_password_hash(
                student.password_hash,
                password,
            ):
                login_user(student)
                flash("Welcome back!", "success")

                # Use a known internal destination in this first stage.
                return redirect(url_for("dashboard"))

            flash("Invalid email or password.", "error")

        return render_template("login.html")

    @application.route("/logout", methods=["POST"])
    @login_required
    def logout():
        logout_user()
        flash("You have been logged out.", "info")
        return redirect(url_for("index"))

    @application.route("/dashboard")
    @login_required
    def dashboard():
        courses = Course.query.order_by(Course.title.asc()).all()

        enrollments = (
            Enrollment.query.options(
                db.selectinload(Enrollment.course)
            )
            .filter_by(student_id=current_user.id)
            .all()
        )

        enrolled_ids = {
            enrollment.course_id for enrollment in enrollments
        }
        completed_ids = {
            enrollment.course_id
            for enrollment in enrollments
            if enrollment.completed
        }
        average_score = average_score_for(enrollments)

        recommendations = recommend_courses(
            courses=courses,
            interests=current_user.interests or "",
            skills=current_user.skills or "",
            quiz_average=average_score,
            completed_course_ids=completed_ids,
            enrolled_course_ids=enrolled_ids,
        )

        return render_template(
            "dashboard.html",
            enrollments=enrollments,
            total_enrolled=len(enrollments),
            total_completed=sum(
                1 for enrollment in enrollments if enrollment.completed
            ),
            average_score=average_score,
            recommendations=recommendations,
        )

    @application.route("/profile", methods=["GET", "POST"])
    @login_required
    def profile():
        if request.method == "POST":
            name = request.form.get("name", "").strip()
            interests = request.form.get("interests", "").strip()
            skills = request.form.get("skills", "").strip()

            error = None

            if not name:
                error = "Name cannot be empty."
            elif len(name) > 100:
                error = "Name must be 100 characters or fewer."
            elif len(interests) > 300:
                error = "Interests must be 300 characters or fewer."
            elif len(skills) > 300:
                error = "Skills must be 300 characters or fewer."

            if error:
                flash(error, "error")
            else:
                current_user.name = name
                current_user.interests = interests
                current_user.skills = skills
                db.session.commit()

                flash("Profile updated.", "success")
                return redirect(url_for("profile"))

        return render_template("profile.html")

    @application.route("/courses/<int:course_id>")
    @login_required
    def course_detail(course_id):
        course = db.session.get(Course, course_id)

        if course is None:
            abort(404)

        enrollment = Enrollment.query.filter_by(
            student_id=current_user.id,
            course_id=course_id,
        ).first()

        content = get_learning_content(course.title)

        return render_template(
            "course_detail.html",
            course=course,
            enrollment=enrollment,
            content=content,
        )


    @application.route("/courses")
    @login_required
    def courses():
        query = request.args.get("q", "").strip()
        category = request.args.get("category", "").strip()
        level = request.args.get("level", "").strip()

        course_query = Course.query

        if query:
            like = f"%{query}%"
            course_query = course_query.filter(
                or_(
                    Course.title.ilike(like),
                    Course.skills.ilike(like),
                    Course.description.ilike(like),
                )
            )

        if category:
            course_query = course_query.filter_by(category=category)

        if level:
            course_query = course_query.filter_by(level=level)

        all_courses = course_query.order_by(Course.title.asc()).all()

        categories = [
            row[0]
            for row in db.session.query(Course.category)
            .distinct()
            .order_by(Course.category)
            .all()
        ]

        enrolled_ids = {
            row[0]
            for row in db.session.query(Enrollment.course_id)
            .filter_by(student_id=current_user.id)
            .all()
        }

        return render_template(
            "courses.html",
            courses=all_courses,
            categories=categories,
            selected_query=query,
            selected_category=category,
            selected_level=level,
            enrolled_ids=enrolled_ids,
        )

    @application.route("/enroll/<int:course_id>", methods=["POST"])
    @login_required
    def enroll(course_id):
        if db.session.get(Course, course_id) is None:
            abort(404)

        existing = Enrollment.query.filter_by(
            student_id=current_user.id,
            course_id=course_id,
        ).first()

        if existing:
            flash("You are already enrolled in this course.", "info")
        else:
            db.session.add(
                Enrollment(
                    student_id=current_user.id,
                    course_id=course_id,
                )
            )

            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
                flash(
                    "Enrollment could not be saved. "
                    "You may already be enrolled.",
                    "error",
                )
            else:
                flash("Successfully enrolled in the course.", "success")

        return redirect(url_for("courses"))

    @application.route(
        "/quiz/<int:course_id>",
        methods=["GET", "POST"],
    )
    @login_required
    def take_quiz(course_id):
        course = db.session.get(Course, course_id)

        if course is None:
            abort(404)

        enrollment = Enrollment.query.filter_by(
            student_id=current_user.id,
            course_id=course_id,
        ).first()

        if enrollment is None:
            flash("Enroll in this course before taking its quiz.", "error")
            return redirect(url_for("courses"))

        questions = select_quiz_questions(course)

        if not questions:
            abort(404)

        if request.method == "POST":
            correct = 0

            for index, question in enumerate(questions):
                raw_answer = request.form.get(
                    f"question_{index}",
                    "",
                ).strip()

                if not raw_answer:
                    # Preserve existing behavior: unanswered = incorrect.
                    continue

                try:
                    answer = int(raw_answer)
                except ValueError:
                    abort(400)

                if not 0 <= answer < len(question["options"]):
                    abort(400)

                if answer == question["answer"]:
                    correct += 1

            score = round(correct / len(questions) * 100, 1)
            enrollment.quiz_score = score
            db.session.commit()

            return render_template(
                "quiz_result.html",
                course=course,
                score=score,
                correct=correct,
                total=len(questions),
            )

        return render_template(
            "quiz.html",
            course=course,
            questions=questions,
        )

    @application.route(
        "/courses/<int:course_id>/complete",
        methods=["POST"],
    )
    @login_required
    def complete_course(course_id):
        enrollment = Enrollment.query.filter_by(
            student_id=current_user.id,
            course_id=course_id,
        ).first()

        if enrollment is None:
            flash(
                "You must enroll before marking a course complete.",
                "error",
            )
        elif enrollment.quiz_score is None or enrollment.quiz_score < 50:
            flash(
                "Pass the course quiz with at least 50% "
                "before marking this course complete.",
                "error",
            )
        elif enrollment.completed:
            flash("This course is already completed.", "info")
        else:
            enrollment.completed = True
            db.session.commit()
            flash(
                "Congratulations! Course marked as completed.",
                "success",
            )

        return redirect(url_for("dashboard"))

    @application.route("/analytics")
    @login_required
    def analytics():
        enrollments = (
            Enrollment.query.options(
                db.selectinload(Enrollment.course)
            )
            .filter_by(student_id=current_user.id)
            .all()
        )

        scored = sum(
            1
            for enrollment in enrollments
            if enrollment.quiz_score is not None
        )

        return render_template(
            "analytics.html",
            enrollments=enrollments,
            total_enrolled=len(enrollments),
            total_completed=sum(
                1 for enrollment in enrollments if enrollment.completed
            ),
            quiz_attempts=scored,
            average_score=average_score_for(enrollments),
        )

    @application.route("/admin")
    @admin_required
    def admin_dashboard():
        students = Student.query.order_by(Student.id.desc()).all()

        courses = (
            Course.query.options(
                db.selectinload(Course.enrollments)
            )
            .order_by(Course.id.desc())
            .all()
        )

        enrollments = Enrollment.query.all()

        return render_template(
            "admin_dashboard.html",
            students=students,
            courses=courses,
            total_students=len(students),
            total_courses=len(courses),
            total_enrollments=len(enrollments),
            completed_enrollments=sum(
                1 for enrollment in enrollments if enrollment.completed
            ),
            average_quiz_score=average_score_for(enrollments),
        )

    @application.route("/admin/courses/add", methods=["POST"])
    @admin_required
    def admin_add_course():
        title = request.form.get("title", "").strip()
        category = request.form.get("category", "").strip()
        level = request.form.get("level", "").strip()
        skills = request.form.get("skills", "").strip()
        description = request.form.get("description", "").strip()

        error = None

        if not all((title, category, level, skills, description)):
            error = "Please fill in every course field."
        elif len(title) > 200:
            error = "Course title must be 200 characters or fewer."
        elif len(category) > 100:
            error = "Category must be 100 characters or fewer."
        elif level not in ALLOWED_LEVELS:
            error = "Choose Beginner, Intermediate, or Advanced."
        elif len(skills) > 300:
            error = "Skills must be 300 characters or fewer."

        if error:
            flash(error, "error")
        else:
            db.session.add(
                Course(
                    title=title,
                    category=category,
                    level=level,
                    skills=skills,
                    description=description,
                )
            )
            db.session.commit()
            flash("Course added successfully.", "success")

        return redirect(url_for("admin_dashboard"))

    @application.route(
        "/admin/courses/<int:course_id>/delete",
        methods=["POST"],
    )
    @admin_required
    def admin_delete_course(course_id):
        course = db.session.get(Course, course_id)

        if course is None:
            abort(404)

        if Enrollment.query.filter_by(course_id=course_id).first():
            flash(
                "This course has enrollments and cannot be deleted "
                "because student progress must be preserved.",
                "error",
            )
        else:
            db.session.delete(course)
            db.session.commit()
            flash("Course deleted.", "success")

        return redirect(url_for("admin_dashboard"))

    @application.route("/admin/student-reports")
    @admin_required
    def admin_student_reports():
        reports = build_student_reports()

        return render_template(
            "admin_student_reports.html",
            student_reports=reports,
            total_students=len(reports),
        )

    @application.route("/admin/student-reports/export")
    @admin_required
    def export_student_reports():
        output = io.StringIO()
        writer = csv.writer(output)

        writer.writerow(
            [
                "Student ID",
                "Student Name",
                "Email",
                "Admin Account",
                "Total Enrolled",
                "Completed Courses",
                "Scored Courses",
                "Average Latest Quiz Score",
                "Completion Rate (%)",
            ]
        )

        for report in build_student_reports():
            writer.writerow(
                [
                    report["id"],
                    report["name"],
                    report["email"],
                    "Yes" if report["is_admin"] else "No",
                    report["total_enrolled"],
                    report["completed_count"],
                    report["quiz_attempts"],
                    (
                        report["average_score"]
                        if report["average_score"] is not None
                        else ""
                    ),
                    report["completion_rate"],
                ]
            )

        response = make_response("\ufeff" + output.getvalue())
        response.headers["Content-Type"] = "text/csv; charset=utf-8"
        response.headers["Content-Disposition"] = (
            "attachment; filename=student_performance_reports.csv"
        )

        return response
    @application.errorhandler(CSRFError)
    def csrf_error(_error):
        return (
            render_template(
                "error.html",
                code=400,
                message=(
                    "This form could not be verified. "
                    "Reload the page and submit it again."
                ),
            ),
            400,
        )


    @application.errorhandler(400)
    def bad_request(_error):
        return (
            render_template(
                "error.html",
                code=400,
                message=(
                    "The submitted request was invalid. "
                    "Reload the page and try again."
                ),
            ),
            400,
        )

    @application.errorhandler(403)
    def forbidden(_error):
        return (
            render_template(
                "error.html",
                code=403,
                message="You do not have permission to access this page.",
            ),
            403,
        )

    @application.errorhandler(404)
    def not_found(_error):
        return (
            render_template(
                "error.html",
                code=404,
                message="The requested page was not found.",
            ),
            404,
        )

    @application.cli.command("init-db")
    def init_db_command():
        """Create missing tables and seed an empty course catalog."""
        initialize_database()
        print("Database initialized.")

    return application


# Keeps existing helper scripts using "from app import app" compatible.
# Importing this module does not create tables or seed courses.
app = create_app()


if __name__ == "__main__":
    with app.app_context():
        initialize_database()

    app.run(debug=False)