# LearnWise — Intelligent Recommendation System for E-Learning Platforms

A Flask-based final-year project that recommends courses using student interests, skills, and quiz performance. It includes authentication, course search and filtering, enrollments, quizzes, saved scores, completion tracking, learning analytics, admin management, student performance reports, and CSV export.

## Features

- Student registration, login, logout, and profile preferences
- Course catalog with keyword, category, and level filters
- Enrollment tracking with one enrollment per student/course
- Course quizzes with persisted scores
- Completion marking requires a quiz score of at least 50%
- Personalized course ranking using TF-IDF and cosine similarity, profile overlap, and quiz performance
- Student learning analytics
- Admin dashboard with platform metrics and course management
- Student performance reports with enrollment, completion, quiz, average-score, and completion-rate metrics
- Admin-only CSV export
- Responsive HTML/CSS design
- Basic automated tests

## Requirements

- Windows 10/11
- Python 3.10 or newer
- VS Code recommended

## Setup on Windows

1. Extract the ZIP file to a folder such as `C:\Users\Lenovo\Documents\e_learning_recommender`.
2. Open that folder in VS Code.
3. Open **Terminal → New Terminal**.
4. Create a virtual environment:

   ```powershell
   python -m venv .venv
   ```

5. Activate it:

   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```

   If PowerShell blocks activation, use Command Prompt and run:

   ```bat
   .venv\Scripts\activate.bat
   ```

6. Install dependencies:

   ```powershell
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```

7. Start the application:

   ```powershell
   python app.py
   ```

8. Open `http://127.0.0.1:5000` in your browser and register an account.

The SQLite database (`e_learning.db`) is created automatically on first run, and sample courses are inserted automatically. The database is intentionally not included in the ZIP so you get a clean database and do not accidentally overwrite any existing student records.

## Make your account an administrator

1. Register and log in once, using the email address you want as the admin account.
2. Stop the server with `Ctrl+C`.
3. Run the following command, replacing the email with your registered email:

   ```powershell
   python -c "from app import app; from models.database import db, Student; ctx=app.app_context(); ctx.push(); email='YOUR_EMAIL@example.com'.lower(); s=Student.query.filter_by(email=email).first(); print('Account found:', bool(s)); s.is_admin=True if s else False; db.session.commit() if s else None; print('Admin status:', s.is_admin if s else 'Account not found')"
   ```

4. Start the server again with `python app.py`, log out, and log back in.
5. Open `/admin`.

Do not leave the example `SECRET_KEY` unchanged if you deploy this application publicly. Set a long random `SECRET_KEY` environment variable for deployment. The development server is for local development only.

## Main project structure

```text
e_learning_recommender/
├── app.py
├── requirements.txt
├── README.md
├── models/
│   ├── __init__.py
│   └── database.py
├── recommender/
│   ├── __init__.py
│   ├── engine.py
│   └── quiz_data.py
├── data/
│   └── courses.csv
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   ├── courses.html
│   ├── quiz.html
│   ├── quiz_result.html
│   ├── analytics.html
│   ├── profile.html
│   ├── admin_dashboard.html
│   ├── admin_student_reports.html
│   └── error.html
├── static/
│   └── css/
│       └── style.css
└── tests/
    └── test_app.py
```

## Run tests

Install dependencies, then run:

```powershell
python -m pytest -q
```

## Important note if you already have a project folder

This ZIP is a complete standalone project package, not a patch that merges automatically into your existing database. Keep a copy of your existing `e_learning.db` and existing project folder before replacing any files. The database schema is created automatically for a fresh database; it does not automatically migrate older databases. If you need to preserve the exact database and records from your existing project, do not overwrite your existing database with a new one.

## Troubleshooting

- **`ModuleNotFoundError`**: activate `.venv` and run `pip install -r requirements.txt`.
- **PowerShell activation blocked**: use Command Prompt activation, or run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` for the current PowerShell session only.
- **Admin page returns 403**: promote the account using the command above, then log out and back in.
- **Port 5000 is busy**: stop the other Flask process, or change the port in the final `app.run(...)` line.
- **CSV export**: log in as admin, open `/admin/student-reports`, then select **Download CSV report**.
