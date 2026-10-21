from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import UniqueConstraint

db = SQLAlchemy()


class Student(UserMixin, db.Model):
    __tablename__ = "students"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    interests = db.Column(db.String(300), default="")
    skills = db.Column(db.String(300), default="")
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    enrollments = db.relationship("Enrollment", back_populates="student", cascade="all, delete-orphan")


class Course(db.Model):
    __tablename__ = "courses"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    level = db.Column(db.String(50), nullable=False)
    skills = db.Column(db.String(300), default="")
    description = db.Column(db.Text, default="")
    enrollments = db.relationship("Enrollment", back_populates="course")


class Enrollment(db.Model):
    __tablename__ = "enrollments"
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=False)
    completed = db.Column(db.Boolean, default=False, nullable=False)
    quiz_score = db.Column(db.Float, nullable=True)
    student = db.relationship("Student", back_populates="enrollments")
    course = db.relationship("Course", back_populates="enrollments")
    __table_args__ = (UniqueConstraint("student_id", "course_id", name="unique_student_course"),)
