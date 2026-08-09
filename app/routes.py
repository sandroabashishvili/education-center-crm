import csv
from datetime import date
from functools import wraps
import io
import sqlite3

from flask import Response, abort, flash, jsonify, redirect, render_template, request, session, url_for

import database
from models import Student, Course, Teacher, Group, Lesson, Payment
from services import (
    get_dashboard_metrics,
    get_students as get_students_service,
    add_student as add_student_service,
    update_student as update_student_service,
    delete_student as delete_student_service,
    get_student_detail as get_student_detail_service,
    get_courses as get_courses_service,
    add_course as add_course_service,
    delete_course as delete_course_service,
    get_teachers as get_teachers_service,
    add_teacher as add_teacher_service,
    get_groups as get_groups_service,
    add_group as add_group_service,
    enroll_student_in_group,
    get_group_detail as get_group_detail_service,
    get_lessons as get_lessons_service,
    add_lesson as add_lesson_service,
    get_lesson_attendance,
    mark_attendance,
    get_payments as get_payments_service,
    add_payment as add_payment_service,
    record_payment_receipt,
    verify_user_login,
    get_teacher_id_for_user,
)
from utils import (
    is_valid_datetime_range, is_valid_email, is_valid_iso_date,
    normalize_text, parse_float, parse_int,
)


def register_routes(app):
    def get_db_path():
        return app.config.get("DB_PATH", database.DB_PATH)

    def login_required(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if not session.get("logged_in"):
                flash("Bitte melden Sie sich an.", "warning")
                return redirect(url_for("index"))
            return view(*args, **kwargs)
        return wrapped

    def current_teacher_id(conn):
        if session.get("user_role") != "teacher":
            return None
        return get_teacher_id_for_user(conn, int(session["user_id"]))

    def require_teacher_resource(conn, table, resource_id):
        teacher_id = current_teacher_id(conn)
        if teacher_id is None:
            return
        if table == "groups":
            row = conn.execute("SELECT teacher_id FROM groups WHERE id = ?", (resource_id,)).fetchone()
        else:
            row = conn.execute(
                "SELECT COALESCE(l.teacher_id, g.teacher_id) FROM lessons l JOIN groups g ON l.group_id = g.id WHERE l.id = ?",
                (resource_id,),
            ).fetchone()
        if not row or row[0] != teacher_id:
            abort(403)

    def roles_required(*allowed_roles):
        def decorator(view):
            @wraps(view)
            def wrapped(*args, **kwargs):
                if not session.get("logged_in"):
                    flash("Bitte melden Sie sich an.", "warning")
                    return redirect(url_for("index"))
                if session.get("user_role") not in allowed_roles:
                    abort(403)
                return view(*args, **kwargs)
            return wrapped
        return decorator

    # --- AUTH ROUTES ---
    @app.route("/login", methods=["POST"])
    def login():
        email = normalize_text(request.form.get("username", "")).lower()
        password = request.form.get("password", "")
        conn = sqlite3.connect(get_db_path())
        user = verify_user_login(conn, email, password)
        conn.close()
        if user and user.status == "active":
            session.clear()
            session.update(
                logged_in=True,
                user_id=user.id,
                user_name=user.full_name,
                user_role=user.role,
            )
            flash(f"Willkommen, {user.full_name}.", "success")
        else:
            flash("E-Mail-Adresse oder Passwort ist falsch.", "danger")
        return redirect(url_for("index"))

    @app.route("/logout", methods=["POST"])
    @login_required
    def logout():
        session.clear()
        flash("Sie wurden erfolgreich abgemeldet.", "success")
        return redirect(url_for("index"))

    @app.route("/health", methods=["GET"])
    def health():
        return jsonify(service="education-center-crm", status="ok")

    # --- DASHBOARD ROUTE ---
    @app.route("/", methods=["GET"])
    def index():
        if not session.get("logged_in"):
            return render_template("login.html")
        database.init_db(get_db_path())
        conn = sqlite3.connect(get_db_path())
        metrics = get_dashboard_metrics(conn)
        conn.close()
        return render_template("dashboard.html", metrics=metrics)


    @app.route("/exports/students.csv", methods=["GET"])
    @roles_required("admin", "manager")
    def export_students_csv():
        conn = sqlite3.connect(get_db_path())
        rows = get_students_service(conn)
        conn.close()
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["ID", "Name", "E-Mail", "Telefon", "Erziehungsberechtigte Person", "Telefon Erziehungsberechtigte", "Status", "Notizen", "Erstellt am"])
        writer.writerows(rows)
        return Response(
            "\ufeff" + output.getvalue(),
            mimetype="text/csv; charset=utf-8",
            headers={"Content-Disposition": "attachment; filename=education-crm-students.csv"},
        )

    @app.route("/exports/payments.csv", methods=["GET"])
    @roles_required("admin", "manager")
    def export_payments_csv():
        conn = sqlite3.connect(get_db_path())
        rows = get_payments_service(conn)
        conn.commit()
        conn.close()
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["ID", "Schüler", "Gruppe", "Fälliger Betrag", "Bezahlt", "Fällig am", "Bezahlt am", "Status", "Zahlungsart", "Notiz"])
        writer.writerows(rows)
        return Response(
            "\ufeff" + output.getvalue(),
            mimetype="text/csv; charset=utf-8",
            headers={"Content-Disposition": "attachment; filename=education-crm-payments.csv"},
        )

    # --- STUDENTS ROUTES ---
    @app.route("/students", methods=["GET"])
    @roles_required("admin", "manager")
    def students_page():
        database.init_db(get_db_path())
        conn = sqlite3.connect(get_db_path())
        query = normalize_text(request.args.get("q", ""))
        status_filter = request.args.get("status", "all")
        students = get_students_service(conn, query=query, status_filter=status_filter)
        conn.close()
        return render_template("students/index.html", students=students, query=query, status_filter=status_filter)

    @app.route("/students/add", methods=["POST"])
    @roles_required("admin", "manager")
    def add_student_route():
        full_name = normalize_text(request.form.get("full_name") or request.form.get("name", ""))
        email = normalize_text(request.form.get("email", ""))
        phone = normalize_text(request.form.get("phone", ""))
        guardian_name = normalize_text(request.form.get("guardian_name", ""))
        guardian_phone = normalize_text(request.form.get("guardian_phone", ""))
        notes = normalize_text(request.form.get("notes", ""))

        if not full_name or not is_valid_email(email):
            flash("Bitte geben Sie einen Namen und eine gueltige E-Mail-Adresse ein.", "danger")
            return redirect(url_for("students_page"))

        if full_name and email:
            conn = sqlite3.connect(get_db_path())
            add_student_service(conn, Student(
                full_name=full_name, email=email, phone=phone,
                guardian_name=guardian_name, guardian_phone=guardian_phone, notes=notes
            ))
            conn.commit()
            conn.close()
        return redirect(url_for("students_page"))

    @app.route("/students/<int:student_id>")
    @roles_required("admin", "manager")
    def student_detail_page(student_id):
        conn = sqlite3.connect(get_db_path())
        student, groups, payments = get_student_detail_service(conn, student_id)
        conn.close()
        if not student:
            return "Schüler nicht gefunden", 404
        return render_template("students/detail.html", student=student, groups=groups, payments=payments)

    @app.route("/students/<int:student_id>/delete", methods=["POST"])
    @roles_required("admin")
    def delete_student(student_id):
        conn = sqlite3.connect(get_db_path())
        delete_student_service(conn, student_id)
        conn.commit()
        conn.close()
        return redirect(url_for("students_page"))

    @app.route("/students/<int:student_id>/edit", methods=["GET", "POST"])
    @roles_required("admin", "manager")
    def edit_student(student_id):
        conn = sqlite3.connect(get_db_path())
        if request.method == "POST":
            name = normalize_text(request.form.get("name", ""))
            email = normalize_text(request.form.get("email", ""))
            phone = normalize_text(request.form.get("phone", ""))
            guardian_name = normalize_text(request.form.get("guardian_name", ""))
            guardian_phone = normalize_text(request.form.get("guardian_phone", ""))
            status = normalize_text(request.form.get("status", "active"))
            notes = normalize_text(request.form.get("notes", ""))
            if not name or not is_valid_email(email) or status not in {"active", "inactive", "archived"}:
                conn.close()
                flash("Bitte pruefen Sie Name, E-Mail-Adresse und Status.", "danger")
                return redirect(url_for("edit_student", student_id=student_id))
            if name and email:
                update_student_service(
                    conn,
                    student_id,
                    Student(
                        full_name=name,
                        email=email,
                        phone=phone,
                        guardian_name=guardian_name,
                        guardian_phone=guardian_phone,
                        status=status,
                        notes=notes,
                    ),
                )
                conn.commit()
            conn.close()
            return redirect(url_for("students_page"))

        student = conn.execute(
            "SELECT id, full_name, email, phone, guardian_name, guardian_phone, status, notes FROM students WHERE id = ?",
            (student_id,),
        ).fetchone()
        conn.close()
        if not student:
            return "Schüler nicht gefunden", 404
        return render_template("students/edit.html", student=student)

    # --- COURSES ROUTES ---
    @app.route("/courses", methods=["GET"])
    @roles_required("admin", "manager")
    def courses_page():
        conn = sqlite3.connect(get_db_path())
        query = normalize_text(request.args.get("q", ""))
        courses = get_courses_service(conn, query=query)
        conn.close()
        return render_template("courses/index.html", courses=courses, query=query)

    @app.route("/courses/add", methods=["POST"])
    @roles_required("admin", "manager")
    def add_course_route():
        name = normalize_text(request.form.get("name") or request.form.get("title", ""))
        category = normalize_text(request.form.get("category", "Allgemein"))
        default_fee = parse_float(request.form.get("default_fee"))
        description = normalize_text(request.form.get("description", ""))

        if not name or default_fee < 0:
            flash("Kursname und eine nicht negative Gebuehr sind erforderlich.", "danger")
            return redirect(url_for("courses_page"))

        if name:
            conn = sqlite3.connect(get_db_path())
            add_course_service(conn, Course(
                title=name, category=category, default_fee=default_fee, description=description
            ))
            conn.commit()
            conn.close()
        return redirect(url_for("courses_page"))

    @app.route("/courses/<int:course_id>/delete", methods=["POST"])
    @roles_required("admin")
    def delete_course(course_id):
        conn = sqlite3.connect(get_db_path())
        delete_course_service(conn, course_id)
        conn.commit()
        conn.close()
        return redirect(url_for("courses_page"))

    # --- TEACHERS ROUTES ---
    @app.route("/teachers", methods=["GET"])
    @roles_required("admin", "manager")
    def teachers_page():
        conn = sqlite3.connect(get_db_path())
        query = normalize_text(request.args.get("q", ""))
        teachers = get_teachers_service(conn, query=query)
        conn.close()
        return render_template("teachers/index.html", teachers=teachers, query=query)

    @app.route("/teachers/add", methods=["POST"])
    @roles_required("admin")
    def add_teacher_route():
        full_name = normalize_text(request.form.get("full_name", ""))
        email = normalize_text(request.form.get("email", ""))
        phone = normalize_text(request.form.get("phone", ""))
        specialization = normalize_text(request.form.get("specialization", ""))

        if not full_name or not is_valid_email(email):
            flash("Bitte geben Sie einen Namen und eine gueltige E-Mail-Adresse ein.", "danger")
            return redirect(url_for("teachers_page"))

        if full_name and email:
            conn = sqlite3.connect(get_db_path())
            add_teacher_service(conn, Teacher(full_name=full_name, email=email, phone=phone, specialization=specialization))
            conn.commit()
            conn.close()
        return redirect(url_for("teachers_page"))

    # --- GROUPS ROUTES ---
    @app.route("/groups", methods=["GET"])
    @login_required
    def groups_page():
        conn = sqlite3.connect(get_db_path())
        query = normalize_text(request.args.get("q", ""))
        teacher_id = current_teacher_id(conn)
        groups = get_groups_service(conn, query=query, teacher_id=teacher_id)
        courses = get_courses_service(conn) if teacher_id is None else []
        teachers = get_teachers_service(conn) if teacher_id is None else []
        conn.close()
        return render_template("groups/index.html", groups=groups, courses=courses, teachers=teachers, query=query)

    @app.route("/groups/add", methods=["POST"])
    @roles_required("admin", "manager")
    def add_group_route():
        course_id = parse_int(request.form.get("course_id"))
        teacher_id = parse_int(request.form.get("teacher_id"))
        name = normalize_text(request.form.get("name", ""))
        capacity = parse_int(request.form.get("capacity"), 15)
        schedule_description = normalize_text(request.form.get("schedule_description", ""))

        if not name or not course_id or not capacity or capacity < 1:
            flash("Gruppenname, Kurs und eine positive Kapazitaet sind erforderlich.", "danger")
            return redirect(url_for("groups_page"))

        if name and course_id:
            conn = sqlite3.connect(get_db_path())
            add_group_service(conn, Group(
                course_id=course_id, teacher_id=teacher_id, name=name, capacity=capacity, schedule_description=schedule_description
            ))
            conn.commit()
            conn.close()
        return redirect(url_for("groups_page"))

    @app.route("/groups/<int:group_id>")
    @login_required
    def group_detail_page(group_id):
        conn = sqlite3.connect(get_db_path())
        require_teacher_resource(conn, "groups", group_id)
        group, members, lessons = get_group_detail_service(conn, group_id)
        all_students = get_students_service(conn) if session.get("user_role") in {"admin", "manager"} else []
        conn.close()
        if not group:
            return "Gruppe nicht gefunden", 404
        return render_template("groups/detail.html", group=group, members=members, lessons=lessons, all_students=all_students)

    @app.route("/groups/<int:group_id>/enroll", methods=["POST"])
    @roles_required("admin", "manager")
    def enroll_student_route(group_id):
        student_id = parse_int(request.form.get("student_id"))
        if student_id:
            conn = sqlite3.connect(get_db_path())
            enroll_student_in_group(conn, group_id, int(student_id))
            conn.commit()
            conn.close()
        return redirect(url_for("group_detail_page", group_id=group_id))

    # --- LESSONS & ATTENDANCE ROUTES ---
    @app.route("/lessons", methods=["GET"])
    @login_required
    def lessons_page():
        conn = sqlite3.connect(get_db_path())
        teacher_id = current_teacher_id(conn)
        lessons = get_lessons_service(conn, teacher_id=teacher_id)
        groups = get_groups_service(conn, teacher_id=teacher_id)
        conn.close()
        return render_template("lessons/index.html", lessons=lessons, groups=groups)

    @app.route("/lessons/add", methods=["POST"])
    @roles_required("admin", "manager")
    def add_lesson_route():
        group_id = parse_int(request.form.get("group_id"))
        starts_at = request.form.get("starts_at", "").replace("T", " ")
        ends_at = request.form.get("ends_at", "").replace("T", " ")
        room_label = normalize_text(request.form.get("room_label", "Raum 101"))
        topic = normalize_text(request.form.get("topic", ""))

        if not group_id or not is_valid_datetime_range(starts_at, ends_at):
            flash("Bitte geben Sie einen gueltigen Zeitraum fuer den Unterricht ein.", "danger")
            return redirect(url_for("lessons_page"))

        if group_id and starts_at:
            conn = sqlite3.connect(get_db_path())
            add_lesson_service(conn, Lesson(
                group_id=group_id, starts_at=starts_at, ends_at=ends_at, room_label=room_label, topic=topic
            ))
            conn.commit()
            conn.close()
        return redirect(url_for("lessons_page"))

    @app.route("/lessons/<int:lesson_id>/attendance", methods=["GET"])
    @login_required
    def attendance_page(lesson_id):
        conn = sqlite3.connect(get_db_path())
        require_teacher_resource(conn, "lessons", lesson_id)
        lesson, records = get_lesson_attendance(conn, lesson_id)
        conn.close()
        if not lesson:
            return "Unterrichtstermin nicht gefunden", 404
        return render_template("lessons/attendance.html", lesson=lesson, records=records)

    @app.route("/lessons/<int:lesson_id>/attendance/save", methods=["POST"])
    @login_required
    def save_attendance_route(lesson_id):
        conn = sqlite3.connect(get_db_path())
        require_teacher_resource(conn, "lessons", lesson_id)
        for key, value in request.form.items():
            if key.startswith("status_"):
                student_id = parse_int(key.split("_")[1])
                if student_id is None:
                    continue
                status = value
                if status not in {"present", "absent", "late", "excused"}:
                    continue
                note = normalize_text(request.form.get(f"note_{student_id}", ""))
                mark_attendance(conn, lesson_id, student_id, status, note)
        conn.commit()
        conn.close()
        return redirect(url_for("lessons_page"))

    # --- PAYMENTS ROUTES ---
    @app.route("/payments", methods=["GET"])
    @roles_required("admin", "manager")
    def payments_page():
        conn = sqlite3.connect(get_db_path())
        status_filter = request.args.get("status", "all")
        payments = get_payments_service(conn, status_filter=status_filter)
        students = get_students_service(conn)
        groups = get_groups_service(conn)
        today_date = str(date.today())
        conn.close()
        return render_template("payments/index.html", payments=payments, students=students, groups=groups, status_filter=status_filter, today_date=today_date)

    @app.route("/payments/add", methods=["POST"])
    @roles_required("admin", "manager")
    def add_payment_route():
        student_id = parse_int(request.form.get("student_id"))
        group_id = parse_int(request.form.get("group_id"))
        amount_due = parse_float(request.form.get("amount_due"))
        due_date = request.form.get("due_date", str(date.today()))
        note = normalize_text(request.form.get("note", ""))

        if not student_id or amount_due <= 0 or not is_valid_iso_date(due_date):
            flash("Bitte pruefen Sie Schueler, Betrag und Faelligkeitsdatum.", "danger")
            return redirect(url_for("payments_page"))

        if student_id and amount_due > 0:
            conn = sqlite3.connect(get_db_path())
            add_payment_service(conn, Payment(
                student_id=student_id, group_id=group_id, amount_due=amount_due, due_date=due_date, note=note
            ))
            conn.commit()
            conn.close()
        return redirect(url_for("payments_page"))

    @app.route("/payments/record", methods=["POST"])
    @roles_required("admin", "manager")
    def record_payment_route():
        payment_id = parse_int(request.form.get("payment_id"))
        amount_paid = parse_float(request.form.get("amount_paid"))
        paid_at = request.form.get("paid_at", str(date.today()))

        if not payment_id or amount_paid <= 0 or not is_valid_iso_date(paid_at):
            flash("Bitte pruefen Sie Zahlung, Betrag und Zahlungsdatum.", "danger")
            return redirect(url_for("payments_page"))

        conn = sqlite3.connect(get_db_path())
        accepted = record_payment_receipt(conn, payment_id, amount_paid, paid_at)
        if accepted:
            conn.commit()
            flash("Zahlung wurde verbucht.", "success")
        else:
            flash("Der Betrag uebersteigt den offenen Saldo oder die Rechnung fehlt.", "danger")
        conn.close()
        return redirect(url_for("payments_page"))
