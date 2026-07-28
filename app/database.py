from datetime import datetime, timedelta
from pathlib import Path
import sqlite3
import hashlib

DB_PATH = Path(__file__).resolve().parent / "crm.db"


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def init_db(db_path=None):
    path = Path(db_path or DB_PATH)
    conn = sqlite3.connect(path)
    cur = conn.cursor()

    # Enable foreign keys
    cur.execute("PRAGMA foreign_keys = ON;")

    # 1. Users table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'admin',
            status TEXT NOT NULL DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 2. Students table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT,
            name TEXT,
            email TEXT NOT NULL,
            phone TEXT,
            guardian_name TEXT,
            guardian_phone TEXT,
            status TEXT NOT NULL DEFAULT 'active',
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Ensure all columns exist in students for backward compatibility
    cur.execute("PRAGMA table_info(students);")
    student_cols = [col[1] for col in cur.fetchall()]
    for col_name, col_type in [
        ("full_name", "TEXT"),
        ("name", "TEXT"),
        ("guardian_name", "TEXT"),
        ("guardian_phone", "TEXT"),
        ("status", "TEXT DEFAULT 'active'"),
        ("notes", "TEXT"),
        ("created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
    ]:
        if col_name not in student_cols:
            try:
                cur.execute(f"ALTER TABLE students ADD COLUMN {col_name} {col_type};")
            except sqlite3.OperationalError:
                pass

    cur.execute("UPDATE students SET full_name = name WHERE (full_name IS NULL OR full_name = '') AND name IS NOT NULL;")
    cur.execute("UPDATE students SET name = full_name WHERE (name IS NULL OR name = '') AND full_name IS NOT NULL;")

    # 3. Courses table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            title TEXT,
            description TEXT,
            category TEXT DEFAULT 'Allgemein',
            default_fee REAL DEFAULT 0.0,
            teacher TEXT,
            status TEXT NOT NULL DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute("PRAGMA table_info(courses);")
    course_cols = [col[1] for col in cur.fetchall()]
    for col_name, col_type in [
        ("name", "TEXT"),
        ("title", "TEXT"),
        ("description", "TEXT"),
        ("category", "TEXT DEFAULT 'Allgemein'"),
        ("default_fee", "REAL DEFAULT 0.0"),
        ("teacher", "TEXT"),
        ("status", "TEXT DEFAULT 'active'"),
        ("created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
    ]:
        if col_name not in course_cols:
            try:
                cur.execute(f"ALTER TABLE courses ADD COLUMN {col_name} {col_type};")
            except sqlite3.OperationalError:
                pass

    cur.execute("UPDATE courses SET name = title WHERE (name IS NULL OR name = '') AND title IS NOT NULL;")
    cur.execute("UPDATE courses SET title = name WHERE (title IS NULL OR title = '') AND name IS NOT NULL;")


    # 4. Teachers table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS teachers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            full_name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT,
            specialization TEXT,
            status TEXT NOT NULL DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE SET NULL
        )
    """)

    # 5. Groups table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id INTEGER NOT NULL,
            teacher_id INTEGER,
            name TEXT NOT NULL,
            capacity INTEGER DEFAULT 15,
            start_date TEXT,
            end_date TEXT,
            schedule_description TEXT,
            status TEXT NOT NULL DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(course_id) REFERENCES courses(id) ON DELETE CASCADE,
            FOREIGN KEY(teacher_id) REFERENCES teachers(id) ON DELETE SET NULL
        )
    """)

    # 6. Group Students (enrollment junction table)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS group_students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id INTEGER NOT NULL,
            student_id INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'enrolled',
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(group_id, student_id),
            FOREIGN KEY(group_id) REFERENCES groups(id) ON DELETE CASCADE,
            FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE
        )
    """)

    # 7. Lessons table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS lessons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id INTEGER NOT NULL,
            teacher_id INTEGER,
            starts_at TEXT NOT NULL,
            ends_at TEXT NOT NULL,
            room_label TEXT DEFAULT 'Raum 101',
            delivery_mode TEXT DEFAULT 'in_person',
            topic TEXT,
            status TEXT NOT NULL DEFAULT 'scheduled',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(group_id) REFERENCES groups(id) ON DELETE CASCADE,
            FOREIGN KEY(teacher_id) REFERENCES teachers(id) ON DELETE SET NULL
        )
    """)

    # 8. Attendance table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lesson_id INTEGER NOT NULL,
            student_id INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'present',
            note TEXT,
            marked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(lesson_id, student_id),
            FOREIGN KEY(lesson_id) REFERENCES lessons(id) ON DELETE CASCADE,
            FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE
        )
    """)

    # 9. Payments table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            group_id INTEGER,
            amount_due REAL NOT NULL DEFAULT 0.0,
            amount_paid REAL NOT NULL DEFAULT 0.0,
            due_date TEXT NOT NULL,
            paid_at TEXT,
            status TEXT NOT NULL DEFAULT 'pending',
            method TEXT DEFAULT 'cash',
            note TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE,
            FOREIGN KEY(group_id) REFERENCES groups(id) ON DELETE SET NULL
        )
    """)

    # 10. Notification Logs table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS notification_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recipient_type TEXT NOT NULL DEFAULT 'student',
            recipient_id INTEGER NOT NULL,
            channel TEXT NOT NULL DEFAULT 'sms',
            subject TEXT,
            body TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'sent',
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Legacy enrollments table (for backward compatibility)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS enrollments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            course_id INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'Active',
            payment_status TEXT NOT NULL DEFAULT 'Pending',
            amount_paid REAL DEFAULT 0,
            FOREIGN KEY(student_id) REFERENCES students(id),
            FOREIGN KEY(course_id) REFERENCES courses(id)
        )
    """)

    # Seed default Admin user if empty
    cur.execute("SELECT COUNT(*) FROM users;")
    if cur.fetchone()[0] == 0:
        admin_pass = hash_password("admin123")
        cur.execute("""
            INSERT INTO users (full_name, email, phone, password_hash, role, status)
            VALUES ('Administrator', 'admin@bildungszentrum.de', '+49 561 000000', ?, 'admin', 'active')
        """, (admin_pass,))

    # Seed default sample data if empty
    cur.execute("SELECT COUNT(*) FROM students;")
    if cur.fetchone()[0] == 0:
        cur.execute("""
            INSERT INTO students (full_name, name, email, phone, guardian_name, guardian_phone, status, notes)
            VALUES
            ('Jonas Becker', 'Jonas Becker', 'jonas.becker@example.de', '+49 151 11223344', 'Katrin Becker', '+49 151 11223345', 'active', 'Sehr gute Lernfortschritte'),
            ('Lea Hoffmann', 'Lea Hoffmann', 'lea.hoffmann@example.de', '+49 152 33445566', 'Daniel Hoffmann', '+49 152 33445567', 'active', 'Teilnahme am Englischkurs'),
            ('Noah Fischer', 'Noah Fischer', 'noah.fischer@example.de', '+49 155 66778899', 'Miriam Fischer', '+49 155 66778900', 'active', 'Teilnahme am Python-Webkurs')
        """)

    cur.execute("SELECT COUNT(*) FROM courses;")
    if cur.fetchone()[0] == 0:
        cur.execute("""
            INSERT INTO courses (name, title, description, category, default_fee, teacher, status)
            VALUES
            ('Python & Webentwicklung', 'Python & Webentwicklung', 'Praxisorientierter Kurs zu Python, Flask, SQLite und Web-Grundlagen', 'Programmierung', 350.0, 'Daniel Weber', 'active'),
            ('Englisch B2 - Aufbaukurs', 'Englisch B2 - Aufbaukurs', 'Intensiver Englischkurs mit Schwerpunkt Konversation', 'Sprachen', 250.0, 'Elena König', 'active'),
            ('Grundlagen UI/UX-Design', 'Grundlagen UI/UX-Design', 'Grundlagen in Figma und interaktivem Prototyping', 'Design', 300.0, 'Georg Meier', 'active')
        """)

    cur.execute("SELECT COUNT(*) FROM teachers;")
    if cur.fetchone()[0] == 0:
        cur.execute("""
            INSERT INTO teachers (full_name, email, phone, specialization, status)
            VALUES
            ('Daniel Weber', 'daniel.weber@example.de', '+49 151 44556677', 'Python, Backend, Datenbanken', 'active'),
            ('Elena König', 'elena.koenig@example.de', '+49 152 55667788', 'Englisch, IELTS', 'active'),
            ('Georg Meier', 'georg.meier@example.de', '+49 155 66778899', 'UI/UX-Design', 'active')
        """)

    cur.execute("SELECT COUNT(*) FROM groups;")
    if cur.fetchone()[0] == 0:
        course_rows = cur.execute("SELECT id FROM courses ORDER BY id ASC").fetchall()
        teacher_rows = cur.execute("SELECT id FROM teachers ORDER BY id ASC").fetchall()
        group_specs = [
            ("Python 2026 – Gruppe A", 12, "Montag / Mittwoch, 19:00 Uhr"),
            ("Englisch B2 – Abendkurs", 14, "Dienstag / Donnerstag, 18:30 Uhr"),
            ("UI/UX – Wochenendkurs", 10, "Samstag, 11:00 Uhr"),
        ]
        for index, course_row in enumerate(course_rows[:3]):
            teacher_id = teacher_rows[index][0] if index < len(teacher_rows) else None
            name, capacity, schedule = group_specs[index]
            cur.execute(
                """
                INSERT INTO groups (
                    course_id, teacher_id, name, capacity, start_date, end_date,
                    schedule_description, status
                )
                VALUES (?, ?, ?, ?, date('now', '-14 days'), date('now', '+90 days'), ?, 'active')
                """,
                (course_row[0], teacher_id, name, capacity, schedule),
            )

    cur.execute("SELECT COUNT(*) FROM group_students;")
    if cur.fetchone()[0] == 0:
        group_rows = cur.execute("SELECT id FROM groups ORDER BY id ASC").fetchall()
        student_rows = cur.execute("SELECT id FROM students ORDER BY id ASC").fetchall()
        for index, student_row in enumerate(student_rows):
            if group_rows:
                group_id = group_rows[index % len(group_rows)][0]
                cur.execute(
                    "INSERT INTO group_students (group_id, student_id, status) VALUES (?, ?, 'enrolled')",
                    (group_id, student_row[0]),
                )
        if len(group_rows) > 1 and student_rows:
            cur.execute(
                "INSERT OR IGNORE INTO group_students (group_id, student_id, status) VALUES (?, ?, 'enrolled')",
                (group_rows[1][0], student_rows[0][0]),
            )

    cur.execute("SELECT COUNT(*) FROM lessons;")
    if cur.fetchone()[0] == 0:
        now = datetime.now().replace(second=0, microsecond=0)
        group_rows = cur.execute("SELECT id, teacher_id FROM groups ORDER BY id ASC").fetchall()
        for index, (group_id, teacher_id) in enumerate(group_rows):
            starts_at = now.replace(hour=10 + index * 2, minute=0)
            ends_at = starts_at + timedelta(minutes=90)
            cur.execute(
                """
                INSERT INTO lessons (
                    group_id, teacher_id, starts_at, ends_at, room_label,
                    delivery_mode, topic, status
                )
                VALUES (?, ?, ?, ?, ?, 'in_person', ?, 'scheduled')
                """,
                (
                    group_id,
                    teacher_id,
                    starts_at.strftime("%Y-%m-%d %H:%M"),
                    ends_at.strftime("%Y-%m-%d %H:%M"),
                    f"Raum {101 + index}",
                    ("Python-Funktionen", "Konversationstraining", "Figma-Komponenten")[index],
                ),
            )

    cur.execute("SELECT COUNT(*) FROM attendance;")
    if cur.fetchone()[0] == 0:
        lesson_rows = cur.execute("SELECT id, group_id FROM lessons ORDER BY id ASC").fetchall()
        for lesson_id, group_id in lesson_rows:
            member_rows = cur.execute(
                "SELECT student_id FROM group_students WHERE group_id = ? ORDER BY student_id",
                (group_id,),
            ).fetchall()
            for member_index, (student_id,) in enumerate(member_rows):
                status = ("present", "late", "absent")[member_index % 3]
                cur.execute(
                    "INSERT INTO attendance (lesson_id, student_id, status, note) VALUES (?, ?, ?, ?)",
                    (lesson_id, student_id, status, "Demo-Anwesenheitseintrag"),
                )

    cur.execute("SELECT COUNT(*) FROM payments;")
    if cur.fetchone()[0] == 0:
        student_rows = cur.execute("SELECT id FROM students ORDER BY id ASC").fetchall()
        group_rows = cur.execute("SELECT id FROM groups ORDER BY id ASC").fetchall()
        payment_specs = [
            (350.0, 350.0, 5, "paid", "bank_transfer", "Kursgebühr für den aktuellen Monat"),
            (250.0, 100.0, -2, "overdue", "cash", "Teilzahlung"),
            (300.0, 0.0, -5, "overdue", "cash", "Offene Rechnung"),
        ]
        today = datetime.now().date()
        for index, student_row in enumerate(student_rows):
            due, paid, offset, status, method, note = payment_specs[index % len(payment_specs)]
            due_date = today + timedelta(days=offset)
            paid_at = today.isoformat() if paid > 0 else None
            group_id = group_rows[index % len(group_rows)][0] if group_rows else None
            cur.execute(
                """
                INSERT INTO payments (
                    student_id, group_id, amount_due, amount_paid, due_date,
                    paid_at, status, method, note
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    student_row[0], group_id, due, paid, due_date.isoformat(),
                    paid_at, status, method, note,
                ),
            )

    conn.commit()
    conn.close()
    return path
