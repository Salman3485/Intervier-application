# db.py
import sqlite3
import hashlib
from datetime import date

DB_NAME = "interview.db"


def get_conn():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row          # lets us use row["column_name"]
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    with get_conn() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS HR (
            hr_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS Candidate (
            candidate_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            resume_text TEXT
        );
        CREATE TABLE IF NOT EXISTS Interview_Field (
            field_id INTEGER PRIMARY KEY AUTOINCREMENT,
            field_name TEXT NOT NULL,
            category TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS Interview_Schedule (
            schedule_id INTEGER PRIMARY KEY AUTOINCREMENT,
            candidate_id INTEGER NOT NULL,
            hr_id INTEGER,
            field_id INTEGER NOT NULL,
            scheduled_date TEXT,
            status TEXT DEFAULT 'scheduled',
            FOREIGN KEY (candidate_id) REFERENCES Candidate(candidate_id),
            FOREIGN KEY (hr_id) REFERENCES HR(hr_id),
            FOREIGN KEY (field_id) REFERENCES Interview_Field(field_id)
        );
        CREATE TABLE IF NOT EXISTS Question (
            question_id INTEGER PRIMARY KEY AUTOINCREMENT,
            schedule_id INTEGER NOT NULL,
            question_text TEXT NOT NULL,
            answer_text TEXT,
            score INTEGER,
            feedback TEXT,
            FOREIGN KEY (schedule_id) REFERENCES Interview_Schedule(schedule_id)
        );
        CREATE TABLE IF NOT EXISTS Result (
            result_id INTEGER PRIMARY KEY AUTOINCREMENT,
            schedule_id INTEGER NOT NULL,
            candidate_id INTEGER NOT NULL,
            total_score INTEGER,
            strengths TEXT,
            weaknesses TEXT,
            result_date TEXT,
            FOREIGN KEY (schedule_id) REFERENCES Interview_Schedule(schedule_id),
            FOREIGN KEY (candidate_id) REFERENCES Candidate(candidate_id)
        );
        """)
        # Add default interview fields the first time
        if c.execute("SELECT COUNT(*) FROM Interview_Field").fetchone()[0] == 0:
            fields = [
                ("Python Developer", "Technical / Software"),
                ("Web Development", "Technical / Software"),
                ("Data Science", "Technical / Software"),
                ("Java Developer", "Technical / Software"),
                ("DBMS & SQL", "Technical / Software"),
                ("Marketing", "Business & Management"),
                ("Human Resources", "Business & Management"),
                ("Finance", "Business & Management"),
            ]
            c.executemany(
                "INSERT INTO Interview_Field(field_name, category) VALUES (?, ?)", fields
            )


# ---------- Authentication ----------
def hash_pw(password):
    return hashlib.sha256(password.encode()).hexdigest()


def ensure_admin_hr(name, email, password):
    """Create the single HR account from secrets.toml, or update it if it already exists."""
    email = email.strip().lower()
    with get_conn() as c:
        row = c.execute("SELECT hr_id FROM HR WHERE email=?", (email,)).fetchone()
        if row:
            c.execute("UPDATE HR SET name=?, password=? WHERE hr_id=?",
                      (name, hash_pw(password), row["hr_id"]))
        else:
            c.execute("INSERT INTO HR(name, email, password) VALUES (?, ?, ?)",
                      (name, email, hash_pw(password)))


def register(name, email, password):
    """Register a Candidate. HR accounts are not created here (see ensure_admin_hr)."""
    try:
        with get_conn() as c:
            c.execute(
                "INSERT INTO Candidate(name, email, password) VALUES (?, ?, ?)",
                (name.strip(), email.strip().lower(), hash_pw(password)),
            )
        return True
    except sqlite3.IntegrityError:      # email already exists
        return False


def login(role, email, password):
    table, id_col = ("HR", "hr_id") if role == "HR" else ("Candidate", "candidate_id")
    with get_conn() as c:
        row = c.execute(
            f"SELECT {id_col} AS id, name FROM {table} WHERE email=? AND password=?",
            (email.strip().lower(), hash_pw(password)),
        ).fetchone()
    if row:
        return {"id": row["id"], "name": row["name"], "role": role}
    return None


# ---------- Candidate / Resume ----------
def save_resume(candidate_id, text):
    with get_conn() as c:
        c.execute("UPDATE Candidate SET resume_text=? WHERE candidate_id=?",
                  (text, candidate_id))


def get_resume(candidate_id):
    with get_conn() as c:
        row = c.execute("SELECT resume_text FROM Candidate WHERE candidate_id=?",
                        (candidate_id,)).fetchone()
    return row["resume_text"] if row else None


def get_all_candidates():
    with get_conn() as c:
        return c.execute(
            "SELECT candidate_id, name, email, "
            "CASE WHEN resume_text IS NULL THEN 'No' ELSE 'Yes' END AS resume_uploaded "
            "FROM Candidate").fetchall()


# ---------- Fields & Scheduling ----------
def get_fields():
    with get_conn() as c:
        return c.execute("SELECT * FROM Interview_Field ORDER BY category").fetchall()


def create_schedule(candidate_id, hr_id, field_id, sched_date, status="scheduled"):
    with get_conn() as c:
        cur = c.execute(
            "INSERT INTO Interview_Schedule(candidate_id, hr_id, field_id, scheduled_date, status) "
            "VALUES (?, ?, ?, ?, ?)",
            (candidate_id, hr_id, field_id, sched_date, status),
        )
        return cur.lastrowid


def get_pending_schedules(candidate_id):
    with get_conn() as c:
        return c.execute("""
            SELECT s.schedule_id, s.scheduled_date, f.field_id, f.field_name
            FROM Interview_Schedule s JOIN Interview_Field f ON s.field_id = f.field_id
            WHERE s.candidate_id=? AND s.status='scheduled'
            ORDER BY s.scheduled_date
        """, (candidate_id,)).fetchall()


def get_all_schedules():
    with get_conn() as c:
        return c.execute("""
            SELECT s.schedule_id, c.name AS candidate, f.field_name,
                   s.scheduled_date, s.status
            FROM Interview_Schedule s
            JOIN Candidate c ON s.candidate_id = c.candidate_id
            JOIN Interview_Field f ON s.field_id = f.field_id
            WHERE s.status != 'practice'
            ORDER BY s.schedule_id DESC
        """).fetchall()


# ---------- Questions & Results ----------
def save_interview(candidate_id, schedule_id, field_id, qa_rows, total, strengths, weaknesses):
    """Save a finished interview in ONE transaction, so a crash never leaves half-saved data.

    schedule_id is None for a practice interview (a 'practice' schedule row is created here).
    qa_rows = list of (question, answer, score, feedback_json).
    Returns the schedule_id that was used.
    """
    today = str(date.today())
    with get_conn() as c:
        if schedule_id is None:
            schedule_id = c.execute(
                "INSERT INTO Interview_Schedule(candidate_id, hr_id, field_id, scheduled_date, status) "
                "VALUES (?, NULL, ?, ?, 'practice')",
                (candidate_id, field_id, today),
            ).lastrowid
        else:
            c.execute("UPDATE Interview_Schedule SET status='completed' WHERE schedule_id=?",
                      (schedule_id,))
        c.executemany(
            "INSERT INTO Question(schedule_id, question_text, answer_text, score, feedback) "
            "VALUES (?, ?, ?, ?, ?)",
            [(schedule_id, q, a, s, fb) for q, a, s, fb in qa_rows],
        )
        c.execute(
            "INSERT INTO Result(schedule_id, candidate_id, total_score, strengths, weaknesses, result_date) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (schedule_id, candidate_id, total, strengths, weaknesses, today),
        )
    return schedule_id


def get_questions(schedule_id):
    with get_conn() as c:
        return c.execute("SELECT * FROM Question WHERE schedule_id=? ORDER BY question_id",
                         (schedule_id,)).fetchall()


_RESULT_QUERY = """
    SELECT r.*, f.field_name, c.name AS candidate
    FROM Result r
    JOIN Interview_Schedule s ON r.schedule_id = s.schedule_id
    JOIN Interview_Field f ON s.field_id = f.field_id
    JOIN Candidate c ON r.candidate_id = c.candidate_id
"""


def get_results(candidate_id):
    with get_conn() as c:
        return c.execute(_RESULT_QUERY + " WHERE r.candidate_id=? ORDER BY r.result_id DESC",
                         (candidate_id,)).fetchall()


def get_all_results():
    with get_conn() as c:
        return c.execute(_RESULT_QUERY + " ORDER BY r.result_id DESC").fetchall()
