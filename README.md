# Voting System

## Digital Voting Platform

### Development Skills

In this project, I built a digital voting platform where users can register, log in, create voting subjects, and cast votes through a web interface made with Flask, HTML, CSS, and JavaScript.

This is what I made:

- A Flask-based web application with separate routes for login, registration, profile pages, voting, and subject creation.
- A MySQL database structure for users, subjects, subject options, and votes.
- Session-based authentication in Flask to keep users logged in securely.
- A voting system where each user can vote once per subject.
- A results system that calculates vote counts per option and returns live data with JSON.
- JavaScript using `chart.js` to display voting data in various chart types..

### Operation

I run the application locally with Flask during development.

The project uses:

- `Flask` for routing, templates, sessions, and backend logic
- `MariaDB` for storing users, subjects, voting options, and votes
- `JavaScript` for sending votes and updating the results chart dynamically

### User Support

The user gets a simple and structured experience:

- A login page at `/login`
- A registration page at `/register`
- A main menu for available voting subjects at `/main-menu`
- A voting page at `/vote/<the subject ID>` for each subject
- A profile page at `/profile` showing user information, created subjects, and voted subjects

Flask validates input such as username, email, password, and phone number, and shows error messages when something is wrong.

I also use `session` in Flask to handle authentication and protect pages that require login.

## How to Run the Project

### 1. Create and activate a virtual environment and install the dependencies

```bash
//Windows:
python -m venv .venv
.venv\Scripts\Activate
pip install -r requirements.txt
```

### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Database Setup

Fill out the database properties in [`app.py`](/app.py#L26). It must be a MySQL-type database such as MySQL or MariaDB.

```python
# -------------------
# Database Connection
# -------------------
def get_db_connection():
    return mysql.connector.connect(
        host=DB_HOST or 'localhost',
        user=DB_USER or 'your_user_name',
        password=DB_PASSWORD or 'your_password',
        database=DB_VOTING_SYSTEM or 'your_database_name'
    )
```

Alternatively, you can create and use a .env file to store the database properties:

```text
    DB_HOST = "localhost"
    DB_USER = "your_user_name"
    DB_PASSWORD = "your_password"
    DB_VOTING_SYSTEM = "your_database_name"
```

### 3. Run the App

After the database has been set up:

```powershell
    python app.py
```

The app runs at:

```text
    http://127.0.0.1:5000
```

## Example Data Notes

Example data is loaded from [`sample_subjects.sql`](/sample_subjects.sql).

It includes:

- 10 users
- Multiple example voting subjects
- Subject options
- Example votes

Use example data on a clean database for best results. If your database already contains conflicting users or subjects, the sample inserts may fail.
You cannot log in as any of the example users.

To become an admin, register on the website and grant yourself admin privileges through the database:

```sql
UPDATE users 
SET is_admin = 1 
WHERE username = 'your_username';
```
