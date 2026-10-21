
from sqlalchemy import inspect, text

from app import app
from models.database import db


def migrate_admin():
    with app.app_context():
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()

        print("Database:", app.config["SQLALCHEMY_DATABASE_URI"])
        print("Tables found:", tables)

        if "students" not in tables:
            print("ERROR: The 'students' table was not found.")
            print("No database changes were made.")
            return

        columns = {
            column["name"]
            for column in inspector.get_columns("students")
        }

        if "is_admin" in columns:
            print("The 'is_admin' column already exists.")
            print("Migration is not needed.")
            return

        try:
            with db.engine.begin() as connection:
                connection.execute(
                    text(
                        "ALTER TABLE students "
                        "ADD COLUMN is_admin BOOLEAN NOT NULL DEFAULT 0"
                    )
                )

            print("SUCCESS: Added the is_admin column.")
            print("Existing student records have been preserved.")

        except Exception as error:
            print("Migration failed:", error)
            raise


if __name__ == "__main__":
    migrate_admin()
