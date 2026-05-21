import mysql.connector
from dotenv import load_dotenv
import os
from pathlib import Path

load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_VOTING_SYSTEM = os.getenv("DB_VOTING_SYSTEM")
SECRET_KEY = os.getenv("SECRET_KEY") or "a_super_secret_key"

BASE_DIR = Path(__file__).resolve().parent
SAMPLE_SUBJECTS_SQL = BASE_DIR / "sample_subjects.sql"
AVAILABLE_CHART_TYPES = ["bar", "doughnut", "line", "polarArea", "radar"]


# -------------------
# Database Connection
# -------------------
def get_db_connection():
    return mysql.connector.connect(
        host=DB_HOST or "localhost",
        user=DB_USER or "your_user_name",
        password=DB_PASSWORD or "your_password",
        database=DB_VOTING_SYSTEM or "your_database_name",
    )


# -------------
# Create Tables
# -------------
def create_tables():
    conn = get_db_connection()
    cursor = conn.cursor()
    # Users Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(255) NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            phone VARCHAR(20) UNIQUE,
            is_admin BOOLEAN DEFAULT FALSE
        );
    """)
    # Subjects Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS subjects (
            id INT AUTO_INCREMENT PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            description TEXT,
            is_anonymous BOOLEAN DEFAULT FALSE,
            allow_vote_changes BOOLEAN DEFAULT FALSE,
            allowed_chart_types VARCHAR(255) DEFAULT 'bar,doughnut,line,polarArea,radar',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by INT,
            FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
        );
    """)
    # Subject Options Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS subject_options (
            id INT AUTO_INCREMENT PRIMARY KEY,
            subject_id INT NOT NULL,
            label VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE
        );
    """)
    # Votes Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS votes (
            id INT AUTO_INCREMENT PRIMARY KEY,
            subject_id INT NOT NULL,
            user_id VARCHAR(64) NOT NULL,
            option_id INT NOT NULL,
            voted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE,
            FOREIGN KEY (option_id) REFERENCES subject_options(id) ON DELETE CASCADE,
            UNIQUE (subject_id, user_id)
        );
    """)
    conn.commit()
    cursor.close()
    conn.close()


# Subject examples
def seed_sample_subjects():
    if not SAMPLE_SUBJECTS_SQL.exists():
        return

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT COUNT(*) AS total FROM subjects")
    subject_count = cursor.fetchone()["total"]
    cursor.close()

    if subject_count > 0:
        conn.close()
        return

    cursor = conn.cursor()
    with SAMPLE_SUBJECTS_SQL.open("r", encoding="utf-8") as sql_file:
        statement_lines = []
        for line in sql_file:
            stripped_line = line.strip()
            if not stripped_line or stripped_line.startswith("--"):
                continue

            statement_lines.append(line.rstrip())
            if stripped_line.endswith(";"):
                statement = " ".join(statement_lines).strip()
                cursor.execute(statement[:-1])
                statement_lines = []

    conn.commit()
    cursor.close()
    conn.close()

def main():
    setup = input("Do you want to setup the Database with 1 = tables only; or with 2 = example data also?\n")
    if setup == "1":
        create_tables()
        print("Tables created!")
    elif setup == "2":
        create_tables()
        print("Tables created!")
        seed_sample_subjects()
        print("Examples inserted!")


if __name__ == "__main__":
    main()
