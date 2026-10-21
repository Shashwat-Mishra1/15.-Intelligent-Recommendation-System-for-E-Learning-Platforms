import csv
import io
import os
from functools import wraps
from pathlib import Path

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
from werkzeug.security import check_password_hash, generate_password_hash

from models.database import db, Student, Course, Enrollment
from recommender.engine import recommend_courses
from recommender.quiz_data import QUIZ_BANK


BASE_DIR = Path(__file__).resolve().parent

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY", "change-this-development-secret-key"
)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL", f"sqlite:///{BASE_DIR / 'e_learning.db'}"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
login_manager.login_message_category = "info"


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
    """Add starter courses only when the courses table is empty."""
    if Course.query.count():
        return

    sample_courses = [
        (
            "Python Programming Fundamentals",
            "Programming",
            "Beginner",
            "python, programming, problem solving",
            "Learn variables, data types, conditionals, loops, functions, and core Python concepts.",
        ),
        (
            "Web Development with Flask",
            "Web Development",
            "Intermediate",
            "python, flask, html, css, web development",
            "Build web applications with Flask, templates, routing, forms, and databases.",
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
            "Learn JavaScript syntax, DOM manipulation, events, and browser fundamentals.",
        ),
        (
            "Machine Learning Basics",
            "Data Science",
            "Intermediate",
            "python, machine learning, data science, statistics",
            "Understand supervised learning, model evaluation, and basic machine-learning workflows.",
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
            "Learn relational databases, SELECT queries, joins, constraints, and schema design.",
        ),
        (
            "Introduction to Artificial Intelligence",
            "Artificial Intelligence",
            "Beginner",
            "ai, machine learning, algorithms",
            "Explore AI concepts, search, knowledge representation, and practical applications.",
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
            "Apply object-oriented programming, testing, and maintainable project design.",
        ),
    ]

    for title, category, level, skills, description in sample_courses:
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
    """Create missing tables and seed courses without deleting existing data.

    create_all() does not migrate existing tables. If an existing database has
    an outdated schema, use a migration or a careful schema repair instead.
    """
    db.create_all()
    seed_courses()


# Initialize tables and starter courses when this module is loaded.
# Existing tables and records are not deleted by create_all().
with app.app_context():
    initialize_database()


@app.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        interests = request.form.get("interests", "").strip()
        skills = request.form.get("skills", "").strip()

        if not all([name, email, password]):
            flash("Name, email, and password are required.", "error")
        elif len(password) < 8:
            flash("Use a password with at least 8 characters.", "error")
        elif Student.query.filter_by(email=email).first():
            flash("An account with that email already exists.", "error")
        else:
            student = Student(
                name=name,
                email=email,
                password_hash=generate_password_hash(password),
                interests=interests,
                skills=skills,
            )
            db.session.add(student)
            db.session.commit()
            login_user(student)
            flash("Account created successfully.", "success")
            return redirect(url_for("dashboard"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        student = Student.query.filter_by(email=email).first()

        if student and check_password_hash(student.password_hash, password):
            login_user(student)
            flash("Welcome back!", "success")

            next_url = request.args.get("next", "")
            if next_url.startswith("/") and not next_url.startswith("//"):
                return redirect(next_url)

            return redirect(url_for("dashboard"))

        flash("Invalid email or password.", "error")

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("index"))


@app.route("/dashboard")
@login_required
def dashboard():
    courses = Course.query.order_by(Course.title.asc()).all()
    enrollments = Enrollment.query.filter_by(student_id=current_user.id).all()
    enrolled_ids = {enrollment.course_id for enrollment in enrollments}
    completed_ids = {
        enrollment.course_id
        for enrollment in enrollments
        if enrollment.completed
    }
    scores = [
        float(enrollment.quiz_score)
        for enrollment in enrollments
        if enrollment.quiz_score is not None
    ]
    average_score = round(sum(scores) / len(scores), 1) if scores else None

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


@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        interests = request.form.get("interests", "").strip()
        skills = request.form.get("skills", "").strip()

        if not name:
            flash("Name cannot be empty.", "error")
        else:
            current_user.name = name
            current_user.interests = interests
            current_user.skills = skills
            db.session.commit()
            flash("Profile updated.", "success")
            return redirect(url_for("profile"))

    return render_template("profile.html")


@app.route("/courses")
@login_required
def courses():
    query = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()
    level = request.args.get("level", "").strip()

    course_query = Course.query

    if query:
        like = f"%{query}%"
        course_query = course_query.filter(
            db.or_(
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
        enrollment.course_id
        for enrollment in Enrollment.query.filter_by(
            student_id=current_user.id
        ).all()
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


@app.route("/enroll/<int:course_id>", methods=["POST"])
@login_required
def enroll(course_id):
    course = db.session.get(Course, course_id)
    if course is None:
        abort(404)

    existing = Enrollment.query.filter_by(
        student_id=current_user.id,
        course_id=course_id,
    ).first()

    if existing:
        flash("You are already enrolled in this course.", "info")
    else:
        db.session.add(
            Enrollment(student_id=current_user.id, course_id=course_id)
        )
        db.session.commit()
        flash("Successfully enrolled in the course.", "success")

    return redirect(request.referrer or url_for("courses"))


@app.route("/quiz/<int:course_id>", methods=["GET", "POST"])
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

    course_text = (course.title + " " + (course.skills or "")).lower()
    if "python" in course_text:
        bank_key = "python"
    elif any(
        word in course_text
        for word in ["web", "html", "css", "flask", "javascript"]
    ):
        bank_key = "web development"
    else:
        bank_key = "general"

    questions = QUIZ_BANK[bank_key]

    if request.method == "POST":
        correct = 0
        for index, question in enumerate(questions):
            answer = request.form.get(f"question_{index}", "")
            if answer.isdigit() and int(answer) == question["answer"]:
                correct += 1

        score = round(correct / len(questions) * 100, 1) if questions else 0
        enrollment.quiz_score = score
        db.session.commit()

        return render_template(
            "quiz_result.html",
            course=course,
            score=score,
            correct=correct,
            total=len(questions),
        )

    return render_template("quiz.html", course=course, questions=questions)


@app.route("/courses/<int:course_id>/complete", methods=["POST"])
@login_required
def complete_course(course_id):
    enrollment = Enrollment.query.filter_by(
        student_id=current_user.id,
        course_id=course_id,
    ).first()

    if enrollment is None:
        flash("You must enroll before marking a course complete.", "error")
    elif (
        enrollment.quiz_score is None
        or enrollment.quiz_score < 50
    ):
        flash(
            "Pass the course quiz with at least 50% before marking this course complete.",
            "error",
        )
    else:
        enrollment.completed = True
        db.session.commit()
        flash("Congratulations! Course marked as completed.", "success")

    return redirect(url_for("dashboard"))


@app.route("/analytics")
@login_required
def analytics():
    enrollments = Enrollment.query.filter_by(
        student_id=current_user.id
    ).all()
    scored = [
        enrollment
        for enrollment in enrollments
        if enrollment.quiz_score is not None
    ]
    scores = [float(enrollment.quiz_score) for enrollment in scored]
    average_score = round(sum(scores) / len(scores), 1) if scores else None

    return render_template(
        "analytics.html",
        enrollments=enrollments,
        total_enrolled=len(enrollments),
        total_completed=sum(
            1 for enrollment in enrollments if enrollment.completed
        ),
        quiz_attempts=len(scored),
        average_score=average_score,
    )


@app.route("/admin")
@admin_required
def admin_dashboard():
    students = Student.query.order_by(Student.id.desc()).all()
    courses = Course.query.order_by(Course.id.desc()).all()
    enrollments = Enrollment.query.all()
    quiz_scores = [
        float(enrollment.quiz_score)
        for enrollment in enrollments
        if enrollment.quiz_score is not None
    ]

    return render_template(
        "admin_dashboard.html",
        students=students,
        courses=courses,
        total_students=Student.query.count(),
        total_courses=Course.query.count(),
        total_enrollments=len(enrollments),
        completed_enrollments=sum(
            1 for enrollment in enrollments if enrollment.completed
        ),
        average_quiz_score=(
            round(sum(quiz_scores) / len(quiz_scores), 1)
            if quiz_scores
            else None
        ),
    )


@app.route("/admin/courses/add", methods=["POST"])
@admin_required
def admin_add_course():
    title = request.form.get("title", "").strip()
    category = request.form.get("category", "").strip()
    level = request.form.get("level", "").strip()
    skills = request.form.get("skills", "").strip()
    description = request.form.get("description", "").strip()

    if not all([title, category, level, skills, description]):
        flash("Please fill in every course field.", "error")
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


@app.route("/admin/courses/<int:course_id>/delete", methods=["POST"])
@admin_required
def admin_delete_course(course_id):
    course = db.session.get(Course, course_id)
    if course is None:
        abort(404)

    if Enrollment.query.filter_by(course_id=course_id).first():
        flash(
            "This course has enrollments and cannot be deleted because student progress must be preserved.",
            "error",
        )
    else:
        db.session.delete(course)
        db.session.commit()
        flash("Course deleted.", "success")

    return redirect(url_for("admin_dashboard"))


def build_student_reports():
    student_reports = []
    students = Student.query.order_by(Student.name.asc()).all()

    for student in students:
        enrollments = Enrollment.query.filter_by(
            student_id=student.id
        ).all()
        scores = [
            float(enrollment.quiz_score)
            for enrollment in enrollments
            if enrollment.quiz_score is not None
        ]
        completed = sum(
            1 for enrollment in enrollments if enrollment.completed
        )
        total = len(enrollments)

        student_reports.append(
            {
                "id": student.id,
                "name": student.name,
                "email": student.email,
                "is_admin": student.is_admin,
                "total_enrolled": total,
                "completed_count": completed,
                "quiz_attempts": len(scores),
                "average_score": (
                    round(sum(scores) / len(scores), 1) if scores else None
                ),
                "completion_rate": (
                    round(completed / total * 100, 1) if total else 0
                ),
            }
        )

    return student_reports


@app.route("/admin/student-reports")
@admin_required
def admin_student_reports():
    reports = build_student_reports()
    return render_template(
        "admin_student_reports.html",
        student_reports=reports,
        total_students=len(reports),
    )


@app.route("/admin/student-reports/export")
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
            "Quiz Attempts",
            "Average Quiz Score",
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


@app.errorhandler(403)
def forbidden(_error):
    return (
        render_template(
            "error.html",
            code=403,
            message="You do not have permission to access this page.",
        ),
        403,
    )


@app.errorhandler(404)
def not_found(_error):
    return (
        render_template(
            "error.html",
            code=404,
            message="The requested page was not found.",
        ),
        404,
    )


if __name__ == "__main__":
    app.run(debug=True)
