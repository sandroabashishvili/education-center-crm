import sqlite3
from functools import wraps

from flask import abort, flash, redirect, render_template, request, session, url_for

import database
from utils import is_valid_email, normalize_text, parse_float


def register_management_routes(app):
    def get_db_path():
        return app.config.get("DB_PATH", database.DB_PATH)

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

    @app.route("/courses/<int:course_id>", methods=["GET"])
    @roles_required("admin", "manager")
    def course_detail_page(course_id):
        conn = sqlite3.connect(get_db_path())
        course = conn.execute(
            "SELECT id, title, description, category, default_fee, status, created_at FROM courses WHERE id = ?",
            (course_id,),
        ).fetchone()
        groups = conn.execute(
            """
            SELECT g.id, g.name, COALESCE(t.full_name, 'Nicht zugewiesen'), g.capacity,
                   (SELECT COUNT(*) FROM group_students gs WHERE gs.group_id = g.id),
                   g.schedule_description, g.status
            FROM groups g
            LEFT JOIN teachers t ON g.teacher_id = t.id
            WHERE g.course_id = ? ORDER BY g.id DESC
            """,
            (course_id,),
        ).fetchall()
        conn.close()
        if not course:
            abort(404)
        return render_template("courses/detail.html", course=course, groups=groups)

    @app.route("/courses/<int:course_id>/edit", methods=["GET", "POST"])
    @roles_required("admin", "manager")
    def edit_course(course_id):
        conn = sqlite3.connect(get_db_path())
        course = conn.execute(
            "SELECT id, title, description, category, default_fee, status FROM courses WHERE id = ?",
            (course_id,),
        ).fetchone()
        if not course:
            conn.close()
            abort(404)
        if request.method == "POST":
            title = normalize_text(request.form.get("title", ""))
            description = normalize_text(request.form.get("description", ""))
            category = normalize_text(request.form.get("category", "")) or "Allgemein"
            fee = parse_float(request.form.get("default_fee"))
            status = normalize_text(request.form.get("status", "active"))
            if not title or fee < 0 or status not in {"active", "inactive", "archived"}:
                conn.close()
                flash("Bitte prüfen Sie Kursname, Gebühr und Status.", "danger")
                return redirect(url_for("edit_course", course_id=course_id))
            conn.execute(
                "UPDATE courses SET title = ?, description = ?, category = ?, default_fee = ?, status = ? WHERE id = ?",
                (title, description, category, fee, status, course_id),
            )
            conn.commit()
            conn.close()
            flash("Kurs wurde aktualisiert.", "success")
            return redirect(url_for("course_detail_page", course_id=course_id))
        conn.close()
        return render_template("courses/edit.html", course=course)

    @app.route("/teachers/<int:teacher_id>", methods=["GET"])
    @roles_required("admin", "manager")
    def teacher_detail_page(teacher_id):
        conn = sqlite3.connect(get_db_path())
        teacher = conn.execute(
            "SELECT id, full_name, email, phone, specialization, status, created_at, user_id FROM teachers WHERE id = ?",
            (teacher_id,),
        ).fetchone()
        groups = conn.execute(
            """
            SELECT g.id, g.name, c.title, g.capacity,
                   (SELECT COUNT(*) FROM group_students gs WHERE gs.group_id = g.id), g.status
            FROM groups g JOIN courses c ON c.id = g.course_id
            WHERE g.teacher_id = ? ORDER BY g.id DESC
            """,
            (teacher_id,),
        ).fetchall()
        conn.close()
        if not teacher:
            abort(404)
        return render_template("teachers/detail.html", teacher=teacher, groups=groups)

    @app.route("/teachers/<int:teacher_id>/edit", methods=["GET", "POST"])
    @roles_required("admin", "manager")
    def edit_teacher(teacher_id):
        conn = sqlite3.connect(get_db_path())
        teacher = conn.execute(
            "SELECT id, full_name, email, phone, specialization, status, user_id FROM teachers WHERE id = ?",
            (teacher_id,),
        ).fetchone()
        if not teacher:
            conn.close()
            abort(404)
        if request.method == "POST":
            full_name = normalize_text(request.form.get("full_name", ""))
            email = normalize_text(request.form.get("email", "")).lower()
            phone = normalize_text(request.form.get("phone", ""))
            specialization = normalize_text(request.form.get("specialization", ""))
            status = normalize_text(request.form.get("status", "active"))
            if not full_name or not is_valid_email(email) or status not in {"active", "inactive"}:
                conn.close()
                flash("Bitte prüfen Sie Name, E-Mail-Adresse und Status.", "danger")
                return redirect(url_for("edit_teacher", teacher_id=teacher_id))
            duplicate = conn.execute("SELECT id FROM teachers WHERE lower(email) = lower(?) AND id != ?", (email, teacher_id)).fetchone()
            if duplicate:
                conn.close()
                flash("Diese E-Mail-Adresse wird bereits verwendet.", "danger")
                return redirect(url_for("edit_teacher", teacher_id=teacher_id))
            conn.execute(
                "UPDATE teachers SET full_name = ?, email = ?, phone = ?, specialization = ?, status = ? WHERE id = ?",
                (full_name, email, phone, specialization, status, teacher_id),
            )
            if teacher[6]:
                conn.execute(
                    "UPDATE users SET full_name = ?, email = ?, phone = ?, status = ? WHERE id = ?",
                    (full_name, email, phone, status, teacher[6]),
                )
            conn.commit()
            conn.close()
            flash("Lehrkraft wurde aktualisiert.", "success")
            return redirect(url_for("teacher_detail_page", teacher_id=teacher_id))
        conn.close()
        return render_template("teachers/edit.html", teacher=teacher)

    @app.route("/teachers/<int:teacher_id>/delete", methods=["POST"])
    @roles_required("admin")
    def delete_teacher(teacher_id):
        conn = sqlite3.connect(get_db_path())
        teacher = conn.execute("SELECT user_id FROM teachers WHERE id = ?", (teacher_id,)).fetchone()
        if not teacher:
            conn.close()
            abort(404)
        conn.execute("UPDATE groups SET teacher_id = NULL WHERE teacher_id = ?", (teacher_id,))
        conn.execute("UPDATE lessons SET teacher_id = NULL WHERE teacher_id = ?", (teacher_id,))
        conn.execute("DELETE FROM teachers WHERE id = ?", (teacher_id,))
        if teacher[0]:
            conn.execute("UPDATE users SET status = 'inactive' WHERE id = ?", (teacher[0],))
        conn.commit()
        conn.close()
        flash("Lehrkraft wurde gelöscht. Zugeordnete Gruppen bleiben erhalten.", "success")
        return redirect(url_for("teachers_page"))
