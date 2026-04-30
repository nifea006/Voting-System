from flask import Flask, render_template, request, redirect, session, jsonify
import mysql.connector
from dotenv import load_dotenv
import os
from pathlib import Path
from werkzeug.security import generate_password_hash, check_password_hash

load_dotenv()

app = Flask(__name__)

DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_VOTING_SYSTEM = os.getenv("DB_VOTING_SYSTEM")
SECRET_KEY = os.getenv("SECRET_KEY") or "a_super_secret_key"

app.secret_key = SECRET_KEY
BASE_DIR = Path(__file__).resolve().parent
SAMPLE_SUBJECTS_SQL = BASE_DIR / "sample_subjects.sql"


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
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(255) NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            phone VARCHAR(20) UNIQUE,
            is_admin BOOLEAN DEFAULT FALSE
        );
    """
    )
    # Subjects Table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS subjects (
            id INT AUTO_INCREMENT PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            description TEXT,
            is_anonymous BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by INT,
            FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
        );
    """
    )
    # Subject Options Table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS subject_options (
            id INT AUTO_INCREMENT PRIMARY KEY,
            subject_id INT NOT NULL,
            label VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE
        );
    """
    )
    # Votes Table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS votes (
            id INT AUTO_INCREMENT PRIMARY KEY,
            subject_id INT NOT NULL,
            user_id INT NOT NULL,
            option_id INT NOT NULL,
            voted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (option_id) REFERENCES subject_options(id) ON DELETE CASCADE,
            UNIQUE (subject_id, user_id)
        );
    """
    )
    conn.commit()
    cursor.close()
    conn.close()


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


# ----------------
# Helper Functions
# ----------------
def get_option_statistics(subject_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT subject_options.id, subject_options.label, COUNT(votes.id) AS vote_count
        FROM subject_options
        LEFT JOIN votes ON votes.option_id = subject_options.id
        WHERE subject_options.subject_id = %s
        GROUP BY subject_options.id
        ORDER BY subject_options.id;
    """,
        (subject_id,),
    )
    options = cursor.fetchall()
    total_votes = sum(option["vote_count"] for option in options)
    cursor.close()
    conn.close()

    return options, total_votes


# --------------
#    Routes
# --------------
@app.route("/")
def home():
    if "user_id" not in session or "username" not in session:
        return redirect("/login")
    return redirect("/main-menu")


# --------------
# Authentication
# --------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username_input = request.form.get("username").strip()
        password_input = request.form.get("password")

        if not username_input or not password_input:
            return render_template(
                "login.html", error="Brukernavn og passord er påkrevd."
            )

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM users WHERE username = %s OR email = %s",
            (username_input, username_input),
        )
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user and check_password_hash(user["password_hash"], password_input):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["is_admin"] = bool(user.get("is_admin"))
            return redirect("/main-menu")

        return render_template("login.html", error="Ugyldig brukernavn eller passord.")

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username").strip()
        email = request.form.get("email").strip()
        phone = request.form.get("phone").strip()
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        if not username or not email or not password:
            return render_template(
                "manage_subject.html",
                page="register",
                error="Brukernavn, e-post og passord er påkrevd.",
            )
        if password != confirm_password:
            return render_template(
                "manage_subject.html",
                page="register",
                error="Passordene samsvarer ikke.",
            )
        if len(password) < 6:
            return render_template(
                "manage_subject.html",
                page="register",
                error="Passordet må være minst 6 tegn.",
            )

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT id FROM users WHERE username = %s OR email = %s", (username, email)
        )
        existing = cursor.fetchone()
        if existing:
            cursor.close()
            conn.close()
            return render_template(
                "manage_subject.html",
                page="register",
                error="Brukernavn eller e-post er allerede i bruk.",
            )

        password_hash = generate_password_hash(password)

        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO users (username, password_hash, email, phone)
                VALUES (%s, %s, %s, %s)
            """,
                (username, password_hash, email, phone),
            )
            conn.commit()
            cursor.close()
            conn.close()
        except mysql.connector.Error:
            cursor.close()
            conn.close()
            return render_template(
                "manage_subject.html",
                page="register",
                error="Kunne ikke opprette konto. Prøv igjen.",
            )

        return redirect("/login")

    return render_template("manage_subject.html", page="register")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# -------------
# Control Panel
# -------------
@app.route("/main-menu")
def main_menu():
    if "user_id" not in session or "username" not in session:
        return redirect("/login")

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM subjects ORDER BY created_at DESC;")
    subjects = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template("hovedmeny.html", subjects=subjects)


# --------------
# Create Subject
# --------------
@app.route("/create-subject", methods=["GET", "POST"])
def create_subject():
    if "user_id" not in session or "username" not in session:
        return redirect("/login")

    if request.method == "POST":
        title = request.form.get("title").strip()
        description = request.form.get("description").strip()
        is_anonymous = 1 if request.form.get("is_anonymous") else 0
        options = [
            option.strip()
            for option in request.form.getlist("options")
            if option.strip()
        ]

        if not title:
            return render_template(
                "manage_subject.html", page="create_subject", error="Tittel er påkrevd."
            )
        if len(options) < 2:
            return render_template(
                "manage_subject.html",
                page="create_subject",
                error="Minst 2 alternativer er påkrevd.",
                title=title,
                description=description,
                options=options,
            )

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO subjects (title, description, is_anonymous, created_by)
            VALUES (%s, %s, %s, %s)
        """,
            (title, description, is_anonymous, session["user_id"]),
        )
        subject_id = cursor.lastrowid
        option_rows = [(subject_id, option) for option in options]
        cursor.executemany(
            """
            INSERT INTO subject_options (subject_id, label)
            VALUES (%s, %s)
        """,
            option_rows,
        )
        conn.commit()
        cursor.close()
        conn.close()

        return redirect("/main-menu")

    return render_template("manage_subject.html", page="create_subject")


# --------------
# Delete Subject
# --------------
@app.route("/subject/<int:subject_id>/delete", methods=["POST"])
def delete_subject(subject_id):
    if "user_id" not in session or "username" not in session:
        return redirect("/login")

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, created_by FROM subjects WHERE id = %s", (subject_id,))
    subject = cursor.fetchone()
    if not subject:
        cursor.close()
        conn.close()
        return "Emne ikke funnet", 404
    if ["created_by"] != session["user_id"] and not session.get("is_admin"):
        cursor.close()
        conn.close()
        return "Du har ikke tilgang til dette emnet.", 403

    cursor = conn.cursor()
    cursor.execute("DELETE FROM subjects WHERE id = %s", (subject_id,))
    conn.commit()
    cursor.close()
    conn.close()

    return redirect(request.referrer)


# -----------
# Voting page
# -----------
@app.route("/vote/<int:subject_id>")
def vote_page(subject_id):
    if "user_id" not in session or "username" not in session:
        return redirect("/login")

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM subjects WHERE id = %s", (subject_id,))
    subject = cursor.fetchone()
    if not subject:
        return "Emne ikke funnet", 404
    cursor.execute(
        "SELECT id, label FROM subject_options WHERE subject_id = %s ORDER BY id",
        (subject_id,),
    )
    options = cursor.fetchall()
    cursor.execute(
        "SELECT option_id FROM votes WHERE subject_id = %s AND user_id = %s",
        (subject_id, session["user_id"]),
    )
    user_vote = cursor.fetchone()
    cursor.close()
    conn.close()

    vote_stats, total_votes = get_option_statistics(subject_id)
    selected_option_id = user_vote["option_id"] if user_vote else None

    return render_template(
        "avstemning.html",
        subject=subject,
        options=options,
        vote_stats=vote_stats,
        total_votes=total_votes,
        selected_option_id=selected_option_id,
    )


@app.route("/vote", methods=["POST"])
def vote():
    if "user_id" not in session or "username" not in session:
        return redirect("/login")
    user_id = session["user_id"]
    subject_id = request.form.get("subject_id")
    option_id = request.form.get("option_id")

    if not option_id:
        return jsonify({"status": "error", "message": "Velg et alternativ."})

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT id FROM subject_options WHERE id = %s AND subject_id = %s",
            (option_id, subject_id),
        )
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({"status": "error", "message": "Ugyldig alternativ."})

        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO votes (subject_id, user_id, option_id)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE option_id = VALUES(option_id), voted_at = CURRENT_TIMESTAMP
        """,
            (subject_id, user_id, option_id),
        )
        conn.commit()
        cursor.close()
        conn.close()
    except mysql.connector.Error as e:
        return jsonify({"status": "error", "message": str(e)})

    vote_stats, total_votes = get_option_statistics(subject_id)

    return jsonify(
        {
            "status": "success",
            "total": total_votes,
            "options": vote_stats,
            "has_voted": True,
        }
    )


# -------
# Profile
# -------
@app.route("/profile", methods=["GET", "POST"])
def profile():
    if "user_id" not in session or "username" not in session:
        return redirect("/login")
    user_id = session["user_id"]
    error = None
    message = None

    if request.method == "POST":
        username = request.form.get("username").strip()
        email = request.form.get("email").strip()
        phone = request.form.get("phone").strip()
        current_password = request.form.get("current_password")
        new_password = request.form.get("new_password")
        confirm_password = request.form.get("confirm_password")

        if not username or not email:
            error = "Brukernavn og e-post er påkrevd."
        elif new_password and new_password != confirm_password:
            error = "Nye passord samsvarer ikke."
        elif new_password and len(new_password) < 6:
            error = "Nytt passord må være minst 6 tegn."

        if error is None:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT id FROM users WHERE (username = %s OR email = %s) AND id != %s",
                (username, email, user_id),
            )
            conflict = cursor.fetchone()
            if conflict:
                error = "Brukernavn eller e-post er allerede i bruk."
            else:
                password_hash = None
                if new_password:
                    cursor.execute(
                        "SELECT password_hash FROM users WHERE id = %s", (user_id,)
                    )
                    user_row = cursor.fetchone()
                    if not user_row or not check_password_hash(
                        user_row["password_hash"], current_password
                    ):
                        error = "Nåværende passord er feil."
                    else:
                        password_hash = generate_password_hash(new_password)

                if error is None:
                    if password_hash:
                        cursor.execute(
                            """
                            UPDATE users
                            SET username = %s, email = %s, phone = %s, password_hash = %s
                            WHERE id = %s
                        """,
                            (username, email, phone, password_hash, user_id),
                        )
                    else:
                        cursor.execute(
                            """
                            UPDATE users
                            SET username = %s, email = %s, phone = %s
                            WHERE id = %s
                        """,
                            (username, email, phone, user_id),
                        )
                    conn.commit()
                    session["username"] = username
                    message = "Profil oppdatert."
            cursor.close()
            conn.close()

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT id, username, email, phone FROM users WHERE id = %s", (user_id,)
    )
    user = cursor.fetchone()
    # Subjects user created
    cursor.execute("SELECT * FROM subjects WHERE created_by = %s", (user_id,))
    created_subjects = cursor.fetchall()
    # Subjects user voted on
    cursor.execute(
        """
        SELECT subjects.*
        FROM subjects
        JOIN votes ON votes.subject_id = subjects.id
        WHERE votes.user_id = %s
    """,
        (user_id,),
    )
    voted_subjects = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template(
        "profil.html",
        user=user,
        created_subjects=created_subjects,
        voted_subjects=voted_subjects,
        error=error,
        message=message,
    )


if __name__ == "__main__":
    create_tables()
    seed_sample_subjects()
    app.run(host="0.0.0.0", port=5000, debug=True)
