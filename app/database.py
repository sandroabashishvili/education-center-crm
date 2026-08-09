from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
import shutil
import sqlite3

from werkzeug.security import generate_password_hash

DB_PATH = Path(__file__).resolve().parent / "crm.db"
SCHEMA_VERSION = 1


def _connect(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _is_current_schema(path: Path) -> bool:
    if not path.exists():
        return True
    try:
        with _connect(path) as conn:
            return conn.execute("PRAGMA user_version").fetchone()[0] == SCHEMA_VERSION
    except sqlite3.DatabaseError:
        return False


def _archive_legacy_database(path: Path) -> Path:
    backup_dir = path.parent / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    backup_path = backup_dir / f"{path.stem}-legacy-{timestamp}{path.suffix}"
    shutil.copy2(path, backup_path)
    path.unlink()
    return backup_path


def init_db(db_path=None) -> None:
    path = Path(db_path or DB_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not _is_current_schema(path):
        _archive_legacy_database(path)

    with _connect(path) as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                phone TEXT,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL CHECK (role IN ('admin', 'manager', 'teacher')),
                status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'inactive')),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                email TEXT NOT NULL,
                phone TEXT,
                guardian_name TEXT,
                guardian_phone TEXT,
                status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'archived')),
                notes TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS courses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                category TEXT NOT NULL DEFAULT 'Allgemein',
                default_fee REAL NOT NULL DEFAULT 0 CHECK (default_fee >= 0),
                status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'archived')),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS teachers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE,
                full_name TEXT NOT NULL,
                email TEXT NOT NULL,
                phone TEXT,
                specialization TEXT,
                status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'inactive')),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
            );
            CREATE TABLE IF NOT EXISTS groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_id INTEGER NOT NULL,
                teacher_id INTEGER,
                name TEXT NOT NULL,
                capacity INTEGER NOT NULL DEFAULT 15 CHECK (capacity > 0),
                start_date TEXT,
                end_date TEXT,
                schedule_description TEXT,
                status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('planned', 'active', 'completed', 'archived')),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE RESTRICT,
                FOREIGN KEY (teacher_id) REFERENCES teachers(id) ON DELETE SET NULL
            );
            CREATE TABLE IF NOT EXISTS group_students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id INTEGER NOT NULL,
                student_id INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'enrolled' CHECK (status IN ('enrolled', 'paused', 'completed', 'cancelled')),
                joined_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (group_id, student_id),
                FOREIGN KEY (group_id) REFERENCES groups(id) ON DELETE CASCADE,
                FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS lessons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id INTEGER NOT NULL,
                teacher_id INTEGER,
                starts_at TEXT NOT NULL,
                ends_at TEXT NOT NULL,
                room_label TEXT,
                delivery_mode TEXT NOT NULL DEFAULT 'in_person' CHECK (delivery_mode IN ('in_person', 'online')),
                topic TEXT,
                status TEXT NOT NULL DEFAULT 'scheduled' CHECK (status IN ('scheduled', 'completed', 'cancelled')),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (group_id) REFERENCES groups(id) ON DELETE CASCADE,
                FOREIGN KEY (teacher_id) REFERENCES teachers(id) ON DELETE SET NULL
            );
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lesson_id INTEGER NOT NULL,
                student_id INTEGER NOT NULL,
                status TEXT NOT NULL CHECK (status IN ('present', 'absent', 'late', 'excused')),
                note TEXT,
                marked_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (lesson_id, student_id),
                FOREIGN KEY (lesson_id) REFERENCES lessons(id) ON DELETE CASCADE,
                FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                group_id INTEGER,
                amount_due REAL NOT NULL CHECK (amount_due > 0),
                amount_paid REAL NOT NULL DEFAULT 0 CHECK (amount_paid >= 0),
                due_date TEXT NOT NULL,
                paid_at TEXT,
                status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'partial', 'paid', 'overdue')),
                method TEXT NOT NULL DEFAULT 'cash' CHECK (method IN ('cash', 'bank_transfer', 'card', 'other')),
                note TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
                FOREIGN KEY (group_id) REFERENCES groups(id) ON DELETE SET NULL
            );
            CREATE INDEX IF NOT EXISTS idx_students_status ON students(status);
            CREATE INDEX IF NOT EXISTS idx_groups_teacher ON groups(teacher_id);
            CREATE INDEX IF NOT EXISTS idx_lessons_start ON lessons(starts_at);
            CREATE INDEX IF NOT EXISTS idx_payments_status_due ON payments(status, due_date);
            PRAGMA user_version = 1;
            """
        )
        _seed_demo_data(conn)


def _seed_demo_data(conn: sqlite3.Connection) -> None:
    if conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]:
        return

    users = [
        ("Administrator", "admin@bildungszentrum.de", "+49 561 000000", "admin123", "admin"),
        ("Mitarbeiter Demo", "manager@bildungszentrum.de", "+49 561 000001", "manager123", "manager"),
        ("Daniel Weber", "teacher@bildungszentrum.de", "+49 561 000002", "teacher123", "teacher"),
    ]
    for full_name, email, phone, password, role in users:
        conn.execute(
            "INSERT INTO users (full_name, email, phone, password_hash, role) VALUES (?, ?, ?, ?, ?)",
            (full_name, email, phone, generate_password_hash(password), role),
        )

    teacher_user_id = conn.execute(
        "SELECT id FROM users WHERE email = 'teacher@bildungszentrum.de'"
    ).fetchone()[0]
    conn.executemany(
        "INSERT INTO teachers (user_id, full_name, email, phone, specialization) VALUES (?, ?, ?, ?, ?)",
        [
            (teacher_user_id, "Daniel Weber", "teacher@bildungszentrum.de", "+49 151 111111", "Python und Webentwicklung"),
            (None, "Elena Koenig", "elena.koenig@example.de", "+49 152 222222", "Englisch"),
            (None, "Georg Meier", "georg.meier@example.de", "+49 155 333333", "UI/UX-Design"),
        ],
    )
    conn.executemany(
        "INSERT INTO students (full_name, email, phone, guardian_name, guardian_phone, notes) VALUES (?, ?, ?, ?, ?, ?)",
        [
            ("Jonas Becker", "jonas.becker@example.de", "+49 151 11223344", "Katrin Becker", "+49 151 11223345", "Sehr gute Lernfortschritte"),
            ("Lea Hoffmann", "lea.hoffmann@example.de", "+49 152 33445566", "Daniel Hoffmann", "+49 152 33445567", "Teilnahme am Englischkurs"),
            ("Noah Fischer", "noah.fischer@example.de", "+49 155 66778899", "Miriam Fischer", "+49 155 66778900", "Teilnahme am Python-Webkurs"),
        ],
    )
    conn.executemany(
        "INSERT INTO courses (title, description, category, default_fee) VALUES (?, ?, ?, ?)",
        [
            ("Python & Webentwicklung", "Praxisorientierter Kurs zu Python, Flask und SQLite", "Programmierung", 350.0),
            ("Englisch B2 - Aufbaukurs", "Intensiver Englischkurs mit Schwerpunkt Konversation", "Sprachen", 250.0),
            ("Grundlagen UI/UX-Design", "Grundlagen in Figma und interaktivem Prototyping", "Design", 300.0),
        ],
    )
    python_course = conn.execute("SELECT id FROM courses WHERE title = 'Python & Webentwicklung'").fetchone()[0]
    daniel = conn.execute("SELECT id FROM teachers WHERE user_id = ?", (teacher_user_id,)).fetchone()[0]
    conn.execute(
        "INSERT INTO groups (course_id, teacher_id, name, capacity, schedule_description) VALUES (?, ?, ?, ?, ?)",
        (python_course, daniel, "Python 2026 - Abendkurs", 15, "Montag und Mittwoch, 19:00 Uhr"),
    )
    group_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    student_ids = [row[0] for row in conn.execute("SELECT id FROM students ORDER BY id")]
    conn.executemany(
        "INSERT INTO group_students (group_id, student_id) VALUES (?, ?)",
        [(group_id, student_id) for student_id in student_ids],
    )
    starts_at = (datetime.now() + timedelta(hours=1)).replace(second=0, microsecond=0)
    ends_at = starts_at + timedelta(minutes=90)
    conn.execute(
        "INSERT INTO lessons (group_id, teacher_id, starts_at, ends_at, room_label, topic) VALUES (?, ?, ?, ?, ?, ?)",
        (group_id, daniel, starts_at.isoformat(sep=" "), ends_at.isoformat(sep=" "), "Raum 101", "Flask-Grundlagen"),
    )
    today = datetime.now().date()
    conn.executemany(
        "INSERT INTO payments (student_id, group_id, amount_due, amount_paid, due_date, paid_at, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
        [
            (student_ids[0], group_id, 350.0, 350.0, str(today), str(today), "paid"),
            (student_ids[1], group_id, 350.0, 150.0, str(today), str(today), "partial"),
            (student_ids[2], group_id, 350.0, 0.0, str(today - timedelta(days=7)), None, "overdue"),
        ],
    )
