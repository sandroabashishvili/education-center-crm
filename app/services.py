import sqlite3
import hashlib
from datetime import date
from typing import List, Tuple, Dict, Any, Optional

import database
from models import (
    User, Student, Course, Teacher, Group, Lesson, Attendance, Payment, Enrollment
)


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


# --- AUTH SERVICES ---

def verify_user_login(conn: sqlite3.Connection, email: str, password: str) -> Optional[User]:
    pass_hash = hash_password(password)
    row = conn.execute(
        "SELECT id, full_name, email, phone, role, status, created_at FROM users WHERE email = ? AND password_hash = ?",
        (email, pass_hash)
    ).fetchone()
    if row:
        return User(
            id=row[0], full_name=row[1], email=row[2], phone=row[3], role=row[4], status=row[5], created_at=row[6]
        )
    return None


def get_user_by_id(conn: sqlite3.Connection, user_id: int) -> Optional[User]:
    row = conn.execute(
        "SELECT id, full_name, email, phone, role, status, created_at FROM users WHERE id = ?",
        (user_id,)
    ).fetchone()
    if row:
        return User(
            id=row[0], full_name=row[1], email=row[2], phone=row[3], role=row[4], status=row[5], created_at=row[6]
        )
    return None


# --- STUDENT SERVICES ---

def get_students(conn: sqlite3.Connection, query: str = "", sort_mode: str = "latest", status_filter: str = "all") -> List[Tuple]:
    sql = "SELECT id, COALESCE(full_name, name) as display_name, email, phone, guardian_name, guardian_phone, status, notes, created_at FROM students WHERE 1=1"
    params = []

    if status_filter and status_filter != "all":
        sql += " AND status = ?"
        params.append(status_filter)

    if query:
        sql += " AND (full_name LIKE ? OR name LIKE ? OR email LIKE ? OR phone LIKE ?)"
        params.extend([f"%{query}%", f"%{query}%", f"%{query}%", f"%{query}%"])

    if sort_mode == "name_asc":
        sql += " ORDER BY display_name ASC"
    else:
        sql += " ORDER BY id DESC"

    return conn.execute(sql, params).fetchall()


def add_student(conn: sqlite3.Connection, student: Student) -> int:
    name_val = student.full_name or student.name
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO students (full_name, name, email, phone, guardian_name, guardian_phone, status, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            name_val,
            name_val,
            student.email,
            student.phone,
            student.guardian_name,
            student.guardian_phone,
            student.status or "active",
            student.notes
        )
    )
    return cur.lastrowid


def update_student(conn: sqlite3.Connection, student_id: int, student: Student) -> None:
    name_val = student.full_name or student.name
    conn.execute(
        """
        UPDATE students
        SET full_name = ?, name = ?, email = ?, phone = ?, guardian_name = ?, guardian_phone = ?, status = ?, notes = ?
        WHERE id = ?
        """,
        (
            name_val,
            name_val,
            student.email,
            student.phone,
            student.guardian_name,
            student.guardian_phone,
            student.status or "active",
            student.notes,
            student_id
        )
    )


def delete_student_with_enrollments(conn: sqlite3.Connection, student_id: int) -> None:
    conn.execute("DELETE FROM group_students WHERE student_id = ?", (student_id,))
    conn.execute("DELETE FROM payments WHERE student_id = ?", (student_id,))
    conn.execute("DELETE FROM attendance WHERE student_id = ?", (student_id,))
    conn.execute("DELETE FROM enrollments WHERE student_id = ?", (student_id,))
    conn.execute("DELETE FROM students WHERE id = ?", (student_id,))


def get_student_detail(conn: sqlite3.Connection, student_id: int):
    student = conn.execute(
        "SELECT id, COALESCE(full_name, name), email, phone, guardian_name, guardian_phone, status, notes, created_at FROM students WHERE id = ?",
        (student_id,)
    ).fetchone()

    # Groups
    groups = conn.execute(
        """
        SELECT g.id, g.name, c.name, gs.status, gs.joined_at
        FROM group_students gs
        JOIN groups g ON gs.group_id = g.id
        JOIN courses c ON g.course_id = c.id
        WHERE gs.student_id = ?
        """,
        (student_id,)
    ).fetchall()

    # Payments
    payments = conn.execute(
        """
        SELECT id, amount_due, amount_paid, due_date, status, paid_at
        FROM payments
        WHERE student_id = ?
        ORDER BY id DESC
        """,
        (student_id,)
    ).fetchall()

    # Legacy enrollments fallback
    enrollments = conn.execute(
        "SELECT e.id, c.name, e.status, e.payment_status, e.amount_paid FROM enrollments e JOIN courses c ON e.course_id = c.id WHERE e.student_id = ? ORDER BY e.id DESC",
        (student_id,)
    ).fetchall()

    return student, groups, payments, enrollments


# --- COURSE SERVICES ---

def get_courses(conn: sqlite3.Connection, query: str = "") -> List[Tuple]:
    if query:
        return conn.execute(
            "SELECT id, COALESCE(name, title) as display_name, description, category, default_fee, teacher, status FROM courses WHERE name LIKE ? OR title LIKE ? OR category LIKE ? ORDER BY id DESC",
            (f"%{query}%", f"%{query}%", f"%{query}%"),
        ).fetchall()
    return conn.execute("SELECT id, COALESCE(name, title) as display_name, description, category, default_fee, teacher, status FROM courses ORDER BY id DESC").fetchall()


def add_course(conn: sqlite3.Connection, course: Course) -> int:
    name_val = course.name or course.title
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO courses (name, title, description, category, default_fee, teacher, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (name_val, name_val, course.description, course.category, course.default_fee, course.teacher, course.status or "active")
    )
    return cur.lastrowid


def update_course(conn: sqlite3.Connection, course_id: int, course: Course) -> None:
    name_val = course.name or course.title
    conn.execute(
        "UPDATE courses SET name = ?, title = ?, description = ?, category = ?, default_fee = ?, teacher = ?, status = ? WHERE id = ?",
        (name_val, name_val, course.description, course.category, course.default_fee, course.teacher, course.status or "active", course_id),
    )


def delete_course(conn: sqlite3.Connection, course_id: int) -> None:
    conn.execute("DELETE FROM enrollments WHERE course_id = ?", (course_id,))
    conn.execute("DELETE FROM groups WHERE course_id = ?", (course_id,))
    conn.execute("DELETE FROM courses WHERE id = ?", (course_id,))


def get_course_detail(conn: sqlite3.Connection, course_id: int):
    course = conn.execute("SELECT id, COALESCE(name, title), description, category, default_fee, teacher, status FROM courses WHERE id = ?", (course_id,)).fetchone()
    groups = conn.execute("SELECT g.id, g.name, t.full_name, g.capacity, g.status FROM groups g LEFT JOIN teachers t ON g.teacher_id = t.id WHERE g.course_id = ?", (course_id,)).fetchall()
    enrollments = conn.execute(
        "SELECT e.id, s.full_name, e.status, e.payment_status, e.amount_paid FROM enrollments e JOIN students s ON e.student_id = s.id WHERE e.course_id = ? ORDER BY e.id DESC",
        (course_id,),
    ).fetchall()
    return course, groups, enrollments


# --- TEACHER SERVICES ---

def get_teachers(conn: sqlite3.Connection, query: str = "") -> List[Tuple]:
    if query:
        return conn.execute(
            "SELECT id, full_name, email, phone, specialization, status FROM teachers WHERE full_name LIKE ? OR email LIKE ? OR specialization LIKE ? ORDER BY id DESC",
            (f"%{query}%", f"%{query}%", f"%{query}%")
        ).fetchall()
    return conn.execute("SELECT id, full_name, email, phone, specialization, status FROM teachers ORDER BY id DESC").fetchall()


def add_teacher(conn: sqlite3.Connection, teacher: Teacher) -> int:
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO teachers (user_id, full_name, email, phone, specialization, status) VALUES (?, ?, ?, ?, ?, ?)",
        (teacher.user_id, teacher.full_name, teacher.email, teacher.phone, teacher.specialization, teacher.status or "active")
    )
    return cur.lastrowid


# --- GROUP SERVICES ---

def get_groups(conn: sqlite3.Connection, query: str = "") -> List[Tuple]:
    sql = """
        SELECT g.id, g.name, c.name as course_name, COALESCE(t.full_name, 'Unassigned') as teacher_name,
               g.capacity, (SELECT COUNT(*) FROM group_students gs WHERE gs.group_id = g.id) as student_count,
               g.schedule_description, g.status
        FROM groups g
        JOIN courses c ON g.course_id = c.id
        LEFT JOIN teachers t ON g.teacher_id = t.id
    """
    if query:
        sql += " WHERE g.name LIKE ? OR c.name LIKE ? OR t.full_name LIKE ? ORDER BY g.id DESC"
        return conn.execute(sql, (f"%{query}%", f"%{query}%", f"%{query}%")).fetchall()
    sql += " ORDER BY g.id DESC"
    return conn.execute(sql).fetchall()


def add_group(conn: sqlite3.Connection, group: Group) -> int:
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO groups (course_id, teacher_id, name, capacity, start_date, end_date, schedule_description, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (group.course_id, group.teacher_id, group.name, group.capacity, group.start_date, group.end_date, group.schedule_description, group.status or "active")
    )
    return cur.lastrowid


def enroll_student_in_group(conn: sqlite3.Connection, group_id: int, student_id: int) -> None:
    conn.execute(
        "INSERT OR IGNORE INTO group_students (group_id, student_id, status) VALUES (?, ?, 'enrolled')",
        (group_id, student_id)
    )


def get_group_detail(conn: sqlite3.Connection, group_id: int):
    group = conn.execute(
        """
        SELECT g.id, g.name, c.name, COALESCE(t.full_name, 'Unassigned'), g.capacity, g.start_date, g.end_date, g.schedule_description, g.status
        FROM groups g
        JOIN courses c ON g.course_id = c.id
        LEFT JOIN teachers t ON g.teacher_id = t.id
        WHERE g.id = ?
        """,
        (group_id,)
    ).fetchone()

    members = conn.execute(
        """
        SELECT s.id, COALESCE(s.full_name, s.name), s.email, s.phone, gs.joined_at, gs.status
        FROM group_students gs
        JOIN students s ON gs.student_id = s.id
        WHERE gs.group_id = ?
        ORDER BY s.id DESC
        """,
        (group_id,)
    ).fetchall()

    lessons = conn.execute(
        "SELECT id, starts_at, ends_at, room_label, topic, status FROM lessons WHERE group_id = ? ORDER BY starts_at DESC",
        (group_id,)
    ).fetchall()

    return group, members, lessons


# --- LESSON & ATTENDANCE SERVICES ---

def get_lessons(conn: sqlite3.Connection, group_id: Optional[int] = None) -> List[Tuple]:
    sql = """
        SELECT l.id, g.name as group_name, COALESCE(t.full_name, 'Unassigned') as teacher_name,
               l.starts_at, l.ends_at, l.room_label, l.topic, l.status
        FROM lessons l
        JOIN groups g ON l.group_id = g.id
        LEFT JOIN teachers t ON l.teacher_id = t.id
    """
    params = []
    if group_id:
        sql += " WHERE l.group_id = ? ORDER BY l.starts_at DESC"
        params.append(group_id)
    else:
        sql += " ORDER BY l.starts_at DESC"
    return conn.execute(sql, params).fetchall()


def add_lesson(conn: sqlite3.Connection, lesson: Lesson) -> int:
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO lessons (group_id, teacher_id, starts_at, ends_at, room_label, delivery_mode, topic, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (lesson.group_id, lesson.teacher_id, lesson.starts_at, lesson.ends_at, lesson.room_label, lesson.delivery_mode, lesson.topic, lesson.status or "scheduled")
    )
    return cur.lastrowid


def get_lesson_attendance(conn: sqlite3.Connection, lesson_id: int):
    lesson = conn.execute(
        """
        SELECT l.id, g.name, COALESCE(t.full_name, 'Unassigned'), l.starts_at, l.ends_at, l.room_label, l.topic, l.status, l.group_id
        FROM lessons l
        JOIN groups g ON l.group_id = g.id
        LEFT JOIN teachers t ON l.teacher_id = t.id
        WHERE l.id = ?
        """,
        (lesson_id,)
    ).fetchone()

    if not lesson:
        return None, []

    group_id = lesson[8]

    # Get all students enrolled in group with their attendance record for this lesson
    records = conn.execute(
        """
        SELECT s.id, COALESCE(s.full_name, s.name), COALESCE(a.status, 'unmarked'), COALESCE(a.note, '')
        FROM group_students gs
        JOIN students s ON gs.student_id = s.id
        LEFT JOIN attendance a ON a.lesson_id = ? AND a.student_id = s.id
        WHERE gs.group_id = ?
        """,
        (lesson_id, group_id)
    ).fetchall()

    return lesson, records


def mark_attendance(conn: sqlite3.Connection, lesson_id: int, student_id: int, status: str, note: str = "") -> None:
    conn.execute(
        """
        INSERT INTO attendance (lesson_id, student_id, status, note)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(lesson_id, student_id) DO UPDATE SET status = excluded.status, note = excluded.note, marked_at = CURRENT_TIMESTAMP
        """,
        (lesson_id, student_id, status, note)
    )


# --- PAYMENT SERVICES ---

def refresh_payment_statuses(conn: sqlite3.Connection) -> None:
    """Keep overdue status aligned with due dates and outstanding balances."""
    conn.execute(
        """
        UPDATE payments
        SET status = CASE
            WHEN amount_paid >= amount_due AND amount_due > 0 THEN 'paid'
            WHEN due_date < date('now') AND amount_paid < amount_due THEN 'overdue'
            WHEN amount_paid > 0 THEN 'partial'
            ELSE 'pending'
        END
        """
    )


def get_payments(conn: sqlite3.Connection, status_filter: str = "all") -> List[Tuple]:
    refresh_payment_statuses(conn)
    sql = """
        SELECT p.id, COALESCE(s.full_name, s.name) as student_name, COALESCE(g.name, 'N/A') as group_name,
               p.amount_due, p.amount_paid, p.due_date, p.paid_at, p.status, p.method, p.note
        FROM payments p
        JOIN students s ON p.student_id = s.id
        LEFT JOIN groups g ON p.group_id = g.id
    """
    if status_filter and status_filter != "all":
        sql += " WHERE p.status = ? ORDER BY p.id DESC"
        return conn.execute(sql, (status_filter,)).fetchall()
    sql += " ORDER BY p.id DESC"
    return conn.execute(sql).fetchall()


def add_payment(conn: sqlite3.Connection, payment: Payment) -> int:
    cur = conn.cursor()
    # Auto status computation
    status = payment.status
    if payment.amount_paid >= payment.amount_due and payment.amount_due > 0:
        status = "paid"
    elif payment.due_date < date.today().isoformat():
        status = "overdue"
    elif payment.amount_paid > 0:
        status = "partial"

    cur.execute(
        """
        INSERT INTO payments (student_id, group_id, amount_due, amount_paid, due_date, paid_at, status, method, note)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (payment.student_id, payment.group_id, payment.amount_due, payment.amount_paid, payment.due_date, payment.paid_at, status, payment.method, payment.note)
    )
    return cur.lastrowid


def record_payment_receipt(conn: sqlite3.Connection, payment_id: int, paid_amount: float, paid_date: str) -> None:
    payment = conn.execute("SELECT amount_due, amount_paid FROM payments WHERE id = ?", (payment_id,)).fetchone()
    if not payment:
        return

    new_paid = payment[1] + paid_amount
    status = "paid" if new_paid >= payment[0] else "partial"

    conn.execute(
        "UPDATE payments SET amount_paid = ?, paid_at = ?, status = ? WHERE id = ?",
        (new_paid, paid_date, status, payment_id)
    )


# --- DASHBOARD & METRICS SERVICES ---

def get_dashboard_metrics(conn: sqlite3.Connection) -> Dict[str, Any]:
    refresh_payment_statuses(conn)
    total_students = conn.execute("SELECT COUNT(*) FROM students WHERE status = 'active'").fetchone()[0]
    total_courses = conn.execute("SELECT COUNT(*) FROM courses WHERE status = 'active'").fetchone()[0]
    active_groups = conn.execute("SELECT COUNT(*) FROM groups WHERE status = 'active'").fetchone()[0]

    overdue_payments = conn.execute("SELECT COUNT(*) FROM payments WHERE status = 'overdue' OR (status != 'paid' AND due_date < date('now'))").fetchone()[0]

    monthly_revenue = conn.execute(
        "SELECT COALESCE(SUM(amount_paid), 0) FROM payments WHERE substr(COALESCE(paid_at, created_at), 1, 7) = strftime('%Y-%m', 'now')"
    ).fetchone()[0]

    today_lessons = conn.execute(
        "SELECT COUNT(*) FROM lessons WHERE date(starts_at) = date('now') AND status != 'cancelled'"
    ).fetchone()[0]

    attendance_total = conn.execute("SELECT COUNT(*) FROM attendance").fetchone()[0]
    attendance_present = conn.execute("SELECT COUNT(*) FROM attendance WHERE status = 'present'").fetchone()[0]

    attendance_rate = round((attendance_present / attendance_total * 100), 1) if attendance_total > 0 else 100.0

    recent_students = conn.execute("SELECT id, COALESCE(full_name, name), email, created_at FROM students ORDER BY id DESC LIMIT 5").fetchall()
    recent_payments = conn.execute(
        "SELECT p.id, COALESCE(s.full_name, s.name), p.amount_paid, p.status, p.due_date FROM payments p JOIN students s ON p.student_id = s.id ORDER BY p.id DESC LIMIT 5"
    ).fetchall()

    return {
        "total_students": total_students,
        "total_courses": total_courses,
        "active_groups": active_groups,
        "today_lessons": today_lessons,
        "overdue_payments": overdue_payments,
        "monthly_revenue": monthly_revenue,
        "attendance_rate": attendance_rate,
        "recent_students": recent_students,
        "recent_payments": recent_payments
    }


def get_enrollment_counts(conn: sqlite3.Connection) -> Tuple[int, int, int]:
    student_count = conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]
    course_count = conn.execute("SELECT COUNT(*) FROM courses").fetchone()[0]
    enrollment_count = conn.execute("SELECT COUNT(*) FROM group_students").fetchone()[0]
    if enrollment_count == 0:
        enrollment_count = conn.execute("SELECT COUNT(*) FROM enrollments").fetchone()[0]
    return student_count, course_count, enrollment_count


def add_enrollment(conn: sqlite3.Connection, enrollment: Enrollment) -> None:
    conn.execute(
        "INSERT INTO enrollments (student_id, course_id, status, payment_status, amount_paid) VALUES (?, ?, ?, ?, ?)",
        (enrollment.student_id, enrollment.course_id, enrollment.status, enrollment.payment_status, enrollment.amount_paid),
    )
