from flask import Flask, render_template, request, redirect, session, jsonify
import hashlib
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


def get_option_voters(subject_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT
            subject_options.id,
            subject_options.label,
            users.username
        FROM subject_options
        LEFT JOIN votes
            ON votes.option_id = subject_options.id
            AND votes.subject_id = subject_options.subject_id
        LEFT JOIN users
            ON users.id = CAST(votes.user_id AS UNSIGNED)
        WHERE subject_options.subject_id = %s
        ORDER BY subject_options.id, users.username;
    """,
        (subject_id,),
    )
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    voters_by_option = {}
    for row in rows:
        option_id = row["id"]
        if option_id not in voters_by_option:
            voters_by_option[option_id] = {
                "id": option_id,
                "label": row["label"],
                "voters": [],
            }

        if row["username"]:
            voters_by_option[option_id]["voters"].append(row["username"])

    return list(voters_by_option.values())


def get_form_text(name):
    return (request.form.get(name) or "").strip()


def normalize_chart_types(chart_types):
    normalized = []

    for chart_type in chart_types:
        if chart_type in AVAILABLE_CHART_TYPES and chart_type not in normalized:
            normalized.append(chart_type)

    return normalized


def get_selected_chart_types_from_form():
    return normalize_chart_types(request.form.getlist("allowed_chart_types"))


def parse_subject_chart_types(subject):
    chart_types = normalize_chart_types(
        (subject.get("allowed_chart_types") or "").split(",")
    )

    if chart_types:
        return chart_types

    return AVAILABLE_CHART_TYPES.copy()


def get_vote_user_id(subject, username, user_id):
    if subject.get("is_anonymous"):
        anonymous_source = f"{SECRET_KEY}:{subject['id']}:{username}"
        return hashlib.sha256(anonymous_source.encode("utf-8")).hexdigest()

    return str(user_id)


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
        username_input = get_form_text("username")
        password_input = request.form.get("password") or ""

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
        username = get_form_text("username").replace(" ", "")
        email = get_form_text("email").replace(" ", "")
        phone = get_form_text("phone").replace(" ", "")
        password = request.form.get("password") or ""
        confirm_password = request.form.get("confirm_password") or ""

        if not username or not email or not password:
            return render_template(
                "login.html",
                error="Brukernavn, e-post og passord er påkrevd.",
            )
        if password != confirm_password:
            return render_template(
                "login.html",
                error="Passordene samsvarer ikke.",
            )
        if len(password) < 6:
            return render_template(
                "login.html",
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
                "login.html",
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
            user_id = cursor.lastrowid
            conn.commit()
            cursor.close()
            conn.close()
        except mysql.connector.Error:
            cursor.close()
            conn.close()
            return render_template(
                "login.html",
                error="Kunne ikke opprette konto. Prøv igjen.",
            )

        session["user_id"] = user_id
        session["username"] = username
        session["is_admin"] = False
        return redirect("/main-menu")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# ---------
# Main menu
# ---------
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
        title = get_form_text("title")
        description = get_form_text("description")
        is_anonymous = 1 if request.form.get("is_anonymous") else 0
        allow_vote_changes = 1 if request.form.get("allow_vote_changes") else 0
        allowed_chart_types = get_selected_chart_types_from_form()
        options = [
            option.strip()
            for option in request.form.getlist("options")
            if option.strip()
        ]

        if not title:
            return render_template(
                "opprett_emne.html",
                error="Tittel er påkrevd.",
                title=title,
                description=description,
                options=options,
                is_anonymous=bool(is_anonymous),
                allow_vote_changes=bool(allow_vote_changes),
                selected_chart_types=allowed_chart_types,
                available_chart_types=AVAILABLE_CHART_TYPES,
            )
        if len(options) < 2:
            return render_template(
                "opprett_emne.html",
                error="Minst 2 alternativer er påkrevd.",
                title=title,
                description=description,
                options=options,
                is_anonymous=bool(is_anonymous),
                allow_vote_changes=bool(allow_vote_changes),
                selected_chart_types=allowed_chart_types,
                available_chart_types=AVAILABLE_CHART_TYPES,
            )
        if not allowed_chart_types:
            return render_template(
                "opprett_emne.html",
                error="Velg minst en diagramtype.",
                title=title,
                description=description,
                options=options,
                is_anonymous=bool(is_anonymous),
                allow_vote_changes=bool(allow_vote_changes),
                selected_chart_types=allowed_chart_types,
                available_chart_types=AVAILABLE_CHART_TYPES,
            )

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO subjects (
                title,
                description,
                is_anonymous,
                allow_vote_changes,
                allowed_chart_types,
                created_by
            )
            VALUES (%s, %s, %s, %s, %s, %s)
        """,
            (
                title,
                description,
                is_anonymous,
                allow_vote_changes,
                ",".join(allowed_chart_types),
                session["user_id"],
            ),
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

    return render_template(
        "opprett_emne.html",
        allow_vote_changes=False,
        available_chart_types=AVAILABLE_CHART_TYPES,
        selected_chart_types=AVAILABLE_CHART_TYPES,
    )


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
    if subject["created_by"] != session["user_id"] and not session.get("is_admin"):
        cursor.close()
        conn.close()
        return "Du har ikke tilgang til dette emnet.", 403

    cursor = conn.cursor()
    cursor.execute("DELETE FROM subjects WHERE id = %s", (subject_id,))
    conn.commit()
    cursor.close()
    conn.close()

    return redirect(request.referrer or "/main-menu")


# -----------
# Voting page
# -----------
@app.route("/vote/<int:subject_id>")
def vote_page(subject_id):
    if "user_id" not in session or "username" not in session:
        return redirect("/login")

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT subjects.*, users.username AS creator_username
        FROM subjects
        LEFT JOIN users ON users.id = subjects.created_by
        WHERE subjects.id = %s
    """,
        (subject_id,),
    )
    subject = cursor.fetchone()
    if not subject:
        cursor.close()
        conn.close()
        return "Emne ikke funnet", 404

    vote_user_id = get_vote_user_id(subject, session["username"], session["user_id"])

    cursor.execute(
        "SELECT id, label FROM subject_options WHERE subject_id = %s ORDER BY id",
        (subject_id,),
    )
    options = cursor.fetchall()
    cursor.execute(
        "SELECT option_id FROM votes WHERE subject_id = %s AND user_id = %s",
        (subject_id, vote_user_id),
    )
    user_vote = cursor.fetchone()
    cursor.close()
    conn.close()

    vote_stats, total_votes = get_option_statistics(subject_id)
    selected_option_id = user_vote["option_id"] if user_vote else None
    voter_lists = []
    show_voter_lists = bool(selected_option_id and not subject.get("is_anonymous"))
    allowed_chart_types = parse_subject_chart_types(subject)

    if show_voter_lists:
        voter_lists = get_option_voters(subject_id)

    return render_template(
        "avstemning.html",
        subject=subject,
        options=options,
        vote_stats=vote_stats,
        total_votes=total_votes,
        selected_option_id=selected_option_id,
        voter_lists=voter_lists,
        show_voter_lists=show_voter_lists,
        allowed_chart_types=allowed_chart_types,
    )


@app.route("/vote", methods=["POST"])
def vote():
    if "user_id" not in session or "username" not in session:
        return redirect("/login")
    subject_id = get_form_text("subject_id")
    option_id = get_form_text("option_id")

    if not subject_id or not option_id:
        return jsonify({"status": "error", "message": "Velg et alternativ."})

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT subjects.id, subjects.is_anonymous, subjects.allow_vote_changes
            FROM subjects
            JOIN subject_options ON subject_options.subject_id = subjects.id
            WHERE subjects.id = %s AND subject_options.id = %s
        """,
            (subject_id, option_id),
        )
        subject = cursor.fetchone()
        if not subject:
            cursor.close()
            conn.close()
            return jsonify({"status": "error", "message": "Ugyldig alternativ."})

        vote_user_id = get_vote_user_id(
            subject,
            session["username"],
            session["user_id"],
        )

        cursor.execute(
            "SELECT option_id FROM votes WHERE subject_id = %s AND user_id = %s",
            (subject_id, vote_user_id),
        )
        existing_vote = cursor.fetchone()

        if existing_vote and not subject.get("allow_vote_changes"):
            cursor.close()
            conn.close()
            return jsonify(
                {
                    "status": "error",
                    "message": "Denne avstemningen tillater ikke at du endrer stemmen din.",
                }
            )

        cursor = conn.cursor()
        if existing_vote:
            cursor.execute(
                """
                UPDATE votes
                SET option_id = %s, voted_at = CURRENT_TIMESTAMP
                WHERE subject_id = %s AND user_id = %s
            """,
                (option_id, subject_id, vote_user_id),
            )
        else:
            cursor.execute(
                """
                INSERT INTO votes (subject_id, user_id, option_id)
                VALUES (%s, %s, %s)
            """,
                (subject_id, vote_user_id, option_id),
            )
        conn.commit()
        cursor.close()
        conn.close()
    except mysql.connector.Error as e:
        return jsonify({"status": "error", "message": str(e)})

    vote_stats, total_votes = get_option_statistics(subject_id)
    voter_lists = []
    show_voter_lists = not subject.get("is_anonymous")
    allowed_chart_types = parse_subject_chart_types(subject)
    if show_voter_lists:
        voter_lists = get_option_voters(subject_id)

    return jsonify(
        {
            "status": "success",
            "total": total_votes,
            "options": vote_stats,
            "has_voted": True,
            "show_voter_lists": show_voter_lists,
            "voter_lists": voter_lists,
            "allow_vote_changes": bool(subject.get("allow_vote_changes")),
            "allowed_chart_types": allowed_chart_types,
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
        username = get_form_text("username")
        email = get_form_text("email")
        phone = get_form_text("phone")
        current_password = request.form.get("current_password") or ""
        new_password = request.form.get("new_password") or ""
        confirm_password = request.form.get("confirm_password") or ""

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
        (str(user_id),),
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
    app.run(host="0.0.0.0", port=5000, debug=True)
