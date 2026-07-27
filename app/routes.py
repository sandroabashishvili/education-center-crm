import csv
from datetime import date
from functools import wraps
import io
import sqlite3

from flask import Response, flash, jsonify, redirect, render_template_string, request, session, url_for

import database
from models import Student, Course, Teacher, Group, Lesson, Payment, Enrollment
from services import (
    get_dashboard_metrics,
    get_students as get_students_service,
    add_student as add_student_service,
    update_student as update_student_service,
    delete_student_with_enrollments as delete_student_with_enrollments_service,
    get_student_detail as get_student_detail_service,
    get_courses as get_courses_service,
    add_course as add_course_service,
    update_course as update_course_service,
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
    get_enrollment_counts as get_enrollment_counts_service,
    add_enrollment as add_enrollment_service,
)
from templates import (
    DASHBOARD_HTML, STUDENTS_HTML, STUDENT_DETAIL_HTML, COURSES_HTML,
    GROUPS_HTML, GROUP_DETAIL_HTML, LESSONS_HTML, ATTENDANCE_HTML,
    PAYMENTS_HTML, TEACHERS_HTML, EDIT_HTML
)
from utils import normalize_text, parse_float, parse_int


def register_routes(app):
    def get_db_path():
        return app.config.get("DB_PATH", database.DB_PATH)

    def login_required(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if not session.get("logged_in"):
                flash("ცვლილების შესატანად გაიარეთ ავტორიზაცია.", "warning")
                return redirect(url_for("index"))
            return view(*args, **kwargs)
        return wrapped

    # --- AUTH ROUTES ---
    @app.route("/login", methods=["POST"])
    def login():
        email = normalize_text(request.form.get("username", ""))
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
            flash(f"მოგესალმებით, {user.full_name}.", "success")
        else:
            flash("ელ-ფოსტა ან პაროლი არასწორია.", "danger")
        return redirect(url_for("index"))

    @app.route("/logout", methods=["POST"])
    @login_required
    def logout():
        session.clear()
        flash("სესიიდან გამოხვედით.", "success")
        return redirect(url_for("index"))

    @app.route("/health", methods=["GET"])
    def health():
        return jsonify(service="education-center-crm", status="ok")

    # --- DASHBOARD ROUTE ---
    @app.route("/", methods=["GET"])
    def index():
        database.init_db(get_db_path())
        conn = sqlite3.connect(get_db_path())
        metrics = get_dashboard_metrics(conn)
        conn.close()
        return render_template_string(DASHBOARD_HTML, metrics=metrics)


    @app.route("/exports/students.csv", methods=["GET"])
    @login_required
    def export_students_csv():
        conn = sqlite3.connect(get_db_path())
        rows = get_students_service(conn)
        conn.close()
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["ID", "Full name", "Email", "Phone", "Guardian", "Guardian phone", "Status", "Notes", "Created at"])
        writer.writerows(rows)
        return Response(
            "\ufeff" + output.getvalue(),
            mimetype="text/csv; charset=utf-8",
            headers={"Content-Disposition": "attachment; filename=education-crm-students.csv"},
        )

    @app.route("/exports/payments.csv", methods=["GET"])
    @login_required
    def export_payments_csv():
        conn = sqlite3.connect(get_db_path())
        rows = get_payments_service(conn)
        conn.commit()
        conn.close()
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["ID", "Student", "Group", "Amount due", "Amount paid", "Due date", "Paid at", "Status", "Method", "Note"])
        writer.writerows(rows)
        return Response(
            "\ufeff" + output.getvalue(),
            mimetype="text/csv; charset=utf-8",
            headers={"Content-Disposition": "attachment; filename=education-crm-payments.csv"},
        )

    # --- STUDENTS ROUTES ---
    @app.route("/students", methods=["GET"])
    def students_page():
        database.init_db(get_db_path())
        conn = sqlite3.connect(get_db_path())
        query = normalize_text(request.args.get("q", ""))
        status_filter = request.args.get("status", "all")
        students = get_students_service(conn, query=query, status_filter=status_filter)
        conn.close()
        return render_template_string(STUDENTS_HTML, students=students, query=query, status_filter=status_filter)

    @app.route("/students/add", methods=["POST"])
    @login_required
    def add_student_route():
        full_name = normalize_text(request.form.get("full_name") or request.form.get("name", ""))
        email = normalize_text(request.form.get("email", ""))
        phone = normalize_text(request.form.get("phone", ""))
        guardian_name = normalize_text(request.form.get("guardian_name", ""))
        guardian_phone = normalize_text(request.form.get("guardian_phone", ""))
        notes = normalize_text(request.form.get("notes", ""))

        if full_name and email:
            conn = sqlite3.connect(get_db_path())
            add_student_service(conn, Student(
                full_name=full_name, name=full_name, email=email, phone=phone,
                guardian_name=guardian_name, guardian_phone=guardian_phone, notes=notes
            ))
            conn.commit()
            conn.close()
        return redirect(url_for("students_page"))

    @app.route("/students/<int:student_id>")
    def student_detail_page(student_id):
        conn = sqlite3.connect(get_db_path())
        student, groups, payments, enrollments = get_student_detail_service(conn, student_id)
        conn.close()
        if not student:
            return "Student not found", 404
        return render_template_string(STUDENT_DETAIL_HTML, student=student, groups=groups, payments=payments, enrollments=enrollments)

    @app.route("/students/<int:student_id>/delete", methods=["POST"])
    @login_required
    def delete_student(student_id):
        conn = sqlite3.connect(get_db_path())
        delete_student_with_enrollments_service(conn, student_id)
        conn.commit()
        conn.close()
        return redirect(url_for("students_page"))

    @app.route("/students/<int:student_id>/edit", methods=["GET", "POST"])
    @login_required
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
            if name and email:
                update_student_service(
                    conn,
                    student_id,
                    Student(
                        full_name=name,
                        name=name,
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
            "SELECT id, COALESCE(full_name, name), email, phone, guardian_name, guardian_phone, status, notes FROM students WHERE id = ?",
            (student_id,),
        ).fetchone()
        conn.close()
        if not student:
            return "Student not found", 404
        return render_template_string(EDIT_HTML, student=student)

    # --- COURSES ROUTES ---
    @app.route("/courses", methods=["GET"])
    def courses_page():
        conn = sqlite3.connect(get_db_path())
        query = normalize_text(request.args.get("q", ""))
        courses = get_courses_service(conn, query=query)
        conn.close()
        return render_template_string(COURSES_HTML, courses=courses, query=query)

    @app.route("/courses/add", methods=["POST"])
    @login_required
    def add_course_route():
        name = normalize_text(request.form.get("name") or request.form.get("title", ""))
        category = normalize_text(request.form.get("category", "General"))
        default_fee = parse_float(request.form.get("default_fee"))
        teacher = normalize_text(request.form.get("teacher", ""))
        description = normalize_text(request.form.get("description", ""))

        if name:
            conn = sqlite3.connect(get_db_path())
            add_course_service(conn, Course(
                name=name, title=name, category=category, default_fee=default_fee, teacher=teacher, description=description
            ))
            conn.commit()
            conn.close()
        return redirect(url_for("courses_page"))

    @app.route("/courses/<int:course_id>/delete", methods=["POST"])
    @login_required
    def delete_course(course_id):
        conn = sqlite3.connect(get_db_path())
        delete_course_service(conn, course_id)
        conn.commit()
        conn.close()
        return redirect(url_for("courses_page"))

    # --- TEACHERS ROUTES ---
    @app.route("/teachers", methods=["GET"])
    def teachers_page():
        conn = sqlite3.connect(get_db_path())
        query = normalize_text(request.args.get("q", ""))
        teachers = get_teachers_service(conn, query=query)
        conn.close()
        return render_template_string(TEACHERS_HTML, teachers=teachers, query=query)

    @app.route("/teachers/add", methods=["POST"])
    @login_required
    def add_teacher_route():
        full_name = normalize_text(request.form.get("full_name", ""))
        email = normalize_text(request.form.get("email", ""))
        phone = normalize_text(request.form.get("phone", ""))
        specialization = normalize_text(request.form.get("specialization", ""))

        if full_name and email:
            conn = sqlite3.connect(get_db_path())
            add_teacher_service(conn, Teacher(full_name=full_name, email=email, phone=phone, specialization=specialization))
            conn.commit()
            conn.close()
        return redirect(url_for("teachers_page"))

    # --- GROUPS ROUTES ---
    @app.route("/groups", methods=["GET"])
    def groups_page():
        conn = sqlite3.connect(get_db_path())
        query = normalize_text(request.args.get("q", ""))
        groups = get_groups_service(conn, query=query)
        courses = get_courses_service(conn)
        teachers = get_teachers_service(conn)
        conn.close()
        return render_template_string(GROUPS_HTML, groups=groups, courses=courses, teachers=teachers, query=query)

    @app.route("/groups/add", methods=["POST"])
    @login_required
    def add_group_route():
        course_id = parse_int(request.form.get("course_id"))
        teacher_id = parse_int(request.form.get("teacher_id"))
        name = normalize_text(request.form.get("name", ""))
        capacity = parse_int(request.form.get("capacity"), 15)
        schedule_description = normalize_text(request.form.get("schedule_description", ""))

        if name and course_id:
            conn = sqlite3.connect(get_db_path())
            add_group_service(conn, Group(
                course_id=course_id, teacher_id=teacher_id, name=name, capacity=capacity, schedule_description=schedule_description
            ))
            conn.commit()
            conn.close()
        return redirect(url_for("groups_page"))

    @app.route("/groups/<int:group_id>")
    def group_detail_page(group_id):
        conn = sqlite3.connect(get_db_path())
        group, members, lessons = get_group_detail_service(conn, group_id)
        all_students = get_students_service(conn)
        conn.close()
        if not group:
            return "Group not found", 404
        return render_template_string(GROUP_DETAIL_HTML, group=group, members=members, lessons=lessons, all_students=all_students)

    @app.route("/groups/<int:group_id>/enroll", methods=["POST"])
    @login_required
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
    def lessons_page():
        conn = sqlite3.connect(get_db_path())
        lessons = get_lessons_service(conn)
        groups = get_groups_service(conn)
        conn.close()
        return render_template_string(LESSONS_HTML, lessons=lessons, groups=groups)

    @app.route("/lessons/add", methods=["POST"])
    @login_required
    def add_lesson_route():
        group_id = parse_int(request.form.get("group_id"))
        starts_at = request.form.get("starts_at", "").replace("T", " ")
        ends_at = request.form.get("ends_at", "").replace("T", " ")
        room_label = normalize_text(request.form.get("room_label", "Room 101"))
        topic = normalize_text(request.form.get("topic", ""))

        if group_id and starts_at:
            conn = sqlite3.connect(get_db_path())
            add_lesson_service(conn, Lesson(
                group_id=group_id, starts_at=starts_at, ends_at=ends_at, room_label=room_label, topic=topic
            ))
            conn.commit()
            conn.close()
        return redirect(url_for("lessons_page"))

    @app.route("/lessons/<int:lesson_id>/attendance", methods=["GET"])
    def attendance_page(lesson_id):
        conn = sqlite3.connect(get_db_path())
        lesson, records = get_lesson_attendance(conn, lesson_id)
        conn.close()
        if not lesson:
            return "Lesson not found", 404
        return render_template_string(ATTENDANCE_HTML, lesson=lesson, records=records)

    @app.route("/lessons/<int:lesson_id>/attendance/save", methods=["POST"])
    @login_required
    def save_attendance_route(lesson_id):
        conn = sqlite3.connect(get_db_path())
        for key, value in request.form.items():
            if key.startswith("status_"):
                student_id = parse_int(key.split("_")[1])
                if student_id is None:
                    continue
                status = value
                note = request.form.get(f"note_{student_id}", "")
                mark_attendance(conn, lesson_id, student_id, status, note)
        conn.commit()
        conn.close()
        return redirect(url_for("lessons_page"))

    # --- PAYMENTS ROUTES ---
    @app.route("/payments", methods=["GET"])
    def payments_page():
        conn = sqlite3.connect(get_db_path())
        status_filter = request.args.get("status", "all")
        payments = get_payments_service(conn, status_filter=status_filter)
        students = get_students_service(conn)
        groups = get_groups_service(conn)
        today_date = str(date.today())
        conn.close()
        return render_template_string(PAYMENTS_HTML, payments=payments, students=students, groups=groups, status_filter=status_filter, today_date=today_date)

    @app.route("/payments/add", methods=["POST"])
    @login_required
    def add_payment_route():
        student_id = parse_int(request.form.get("student_id"))
        group_id = parse_int(request.form.get("group_id"))
        amount_due = parse_float(request.form.get("amount_due"))
        due_date = request.form.get("due_date", str(date.today()))
        note = normalize_text(request.form.get("note", ""))

        if student_id and amount_due > 0:
            conn = sqlite3.connect(get_db_path())
            add_payment_service(conn, Payment(
                student_id=student_id, group_id=group_id, amount_due=amount_due, due_date=due_date, note=note
            ))
            conn.commit()
            conn.close()
        return redirect(url_for("payments_page"))

    @app.route("/payments/record", methods=["POST"])
    @login_required
    def record_payment_route():
        payment_id = parse_int(request.form.get("payment_id"))
        amount_paid = parse_float(request.form.get("amount_paid"))
        paid_at = request.form.get("paid_at", str(date.today()))

        if payment_id and amount_paid > 0:
            conn = sqlite3.connect(get_db_path())
            record_payment_receipt(conn, payment_id, amount_paid, paid_at)
            conn.commit()
            conn.close()
        return redirect(url_for("payments_page"))

    # Legacy alias route
    @app.route("/enrollments/add", methods=["POST"])
    @login_required
    def add_enrollment():
        student_id = parse_int(request.form.get("student_id"))
        course_id = parse_int(request.form.get("course_id"))
        status = request.form.get("status", "Active")
        payment_status = request.form.get("payment_status", "Pending")
        amount_paid = request.form.get("amount_paid", "0")

        if student_id and course_id:
            conn = sqlite3.connect(get_db_path())
            add_enrollment_service(
                conn,
                Enrollment(
                    student_id=student_id,
                    course_id=course_id,
                    status=status or "Active",
                    payment_status=payment_status or "Pending",
                    amount_paid=parse_float(amount_paid),
                ),
            )
            conn.commit()
            conn.close()
        return redirect(url_for("index"))
