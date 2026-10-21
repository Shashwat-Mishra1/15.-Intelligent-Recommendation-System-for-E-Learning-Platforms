
from sqlalchemy import inspect, text

from app import app, db

with app.app_context():
    inspector = inspect(db.engine)

    if "students" not in inspector.get_table_names():
        raise RuntimeError(
            "The students table was not found in the configured database."
        )

    columns = {
        column["name"]
        for column in inspector.get_columns("students")
    }

    if "is_admin" in columns:
        print("The is_admin column already exists. No changes needed.")
    else:
        with db.engine.begin() as connection:
            connection.execute(
                text(
                    "ALTER TABLE students "
                    "ADD COLUMN is_admin BOOLEAN NOT NULL DEFAULT 0"
                )
            )

        print("SUCCESS: Added is_admin to students.")
        print("Existing student records have been preserved.")
