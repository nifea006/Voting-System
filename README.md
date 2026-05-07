# Voting System

## Digital Voting Platform with Flask and MySQL

### Development Skills

In this project, I built a digital voting platform where users can register, log in, create voting subjects, and cast votes through a web interface made with Flask, HTML, CSS, and JavaScript.

This is what I made:

- A Flask-based web application with separate routes for login, registration, profile pages, voting, and subject creation.
- A MySQL database structure for users, subjects, subject options, and votes.
- Session-based authentication in Flask to keep users logged in securely.
- A voting system where each user can vote once per subject, and update their vote if needed.
- A results system that calculates vote counts per option and returns live data with JSON.
- JavaScript with `fetch()` to send votes asynchronously and update the chart without reloading the page.

Example Flask route:

```python
@app.route('/vote', methods=['POST'])
def vote():
    if 'user_id' not in session or 'username' not in session:
        return redirect('/login')

    user_id = session['user_id']
    subject_id = request.form.get('subject_id', type=int)
    option_id = request.form.get('option_id', type=int)

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO votes (subject_id, user_id, option_id)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE option_id = VALUES(option_id), voted_at = CURRENT_TIMESTAMP
    """, (subject_id, user_id, option_id))
    conn.commit()
    cursor.close()
    conn.close()

    vote_stats, total_votes = get_option_statistics(subject_id)
    return jsonify({'status': 'success', 'total': total_votes, 'options': vote_stats, 'has_voted': True})
```

This function:

- Checks that the user is logged in
- Receives the selected subject and option
- Saves the vote in the database
- Updates the vote if the user has already voted on that subject
- Returns updated statistics as JSON so the frontend can refresh the results instantly

### Operation

I run the application locally with Flask during development.

The project uses:

- `Flask` for routing, templates, sessions, and backend logic
- `MySQL` for storing users, subjects, voting options, and votes
- `JavaScript` for sending votes and updating the results chart dynamically

The structure is kept simple and organized with separate folders for templates and static files:

```text
Voting-System/
├── app.py
├── .env
├── sample_subjects.sql
├── static/
│   ├── script.js
│   └── style.css
└── templates/
    ├── avstemning.html
    ├── login.html
    ├── hovedmeny.html
    ├── profil.html
    └── ...
```

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

### 1. Create and activate a virtual environment

```bash
//Windows:
python -m venv .venv
.venv\Scripts\Activate

//Linux / macOS:
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
//Windows:
pip install -r requirements.txt

//Linux / macOS:
pip3 install -r requirements.txt
```

Or use this if `requirements.txt` doesn't work:\
Windows:\
pip install flask mysql-connector-python python-dotenv werkzeug

Linux / macOS:\
pip3 install flask mysql-connector-python python-dotenv werkzeug

### 3. Fillout the database properties in the [`app.py`](/app.py#L24)

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

### 4. Start the application

```powershell
//Windows:
python app.py

//Linux / macOS:
python3 app.py
```

The app will start on:

[http://127.0.0.1:5000](/http://127.0.0.1:5000)

When the project starts:

- `create_tables()` creates the required tables if they do not already exist
- `seed_sample_subjects()` loads example subjects from `sample_subjects.sql` if the `subjects` table is empty
