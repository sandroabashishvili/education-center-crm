import sqlite3
from datetime import date
from functools import wraps

from flask import abort, flash, redirect, render_template, request, session, url_for

import database
from utils import normalize_text, parse_float, parse_int


PAYMENT_METHODS = {"cash", "bank_transfer", "card", "other"}


def register_payment_routes(app):
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

    def payment_row(conn, payment_id):
        return conn.execute(
            """
            SELECT p.id, p.student_id, s.full_name, p.group_id,
                   COALESCE(g.name, 'Keine Gruppe'), p.amount_due, p.amount_paid,
                   p.due_date, p.paid_at, p.status, p.method, p.note, p.created_at
            FROM payments p
            JOIN students s ON s.id = p.student_id
            LEFT JOIN groups g ON g.id = p.group_id
            WHERE p.id = ?
            """,
            (payment_id,),
        ).fetchone()

    @app.route("/payments/<int:payment_id>", methods=["GET"])
    @roles_required("admin", "manager")
    def payment_detail_page(payment_id):
        conn = sqlite3.connect(get_db_path())
        payment = payment_row(conn, payment_id)
        conn.close()
        if not payment:
            abort(404)
        return render_template("payments/detail.html", payment=payment)

    @app.route("/payments/<int:payment_id>/edit", methods=["GET", "POST"])
    @roles_required("admin", "manager")
    def edit_payment(payment_id):
        conn = sqlite3.connect(get_db_path())
        payment = payment_row(conn, payment_id)
        if not payment:
            conn.close()
            abort(404)

        if request.method == "POST":
            student_id = parse_int(request.form.get("student_id"))
            group_id = parse_int(request.form.get("group_id")) or None
            amount_due = parse_float(request.form.get("amount_due"))
            due_date = normalize_text(request.form.get("due_date", ""))
            method = normalize_text(request.form.get("method", "cash"))
            note = normalize_text(request.form.get("note", ""))

            if not student_id or amount_due <= 0 or amount_due < payment[6] or not due_date or method not in PAYMENT_METHODS:
                conn.close()
                flash("Bitte prüfen Sie Schüler, Betrag, Fälligkeitsdatum und Zahlungsart. Der Rechnungsbetrag darf nicht unter dem bereits bezahlten Betrag liegen.", "danger")
                return redirect(url_for("edit_payment", payment_id=payment_id))
            if not conn.execute("SELECT 1 FROM students WHERE id = ?", (student_id,)).fetchone():
                conn.close()
                flash("Der ausgewählte Schüler existiert nicht.", "danger")
                return redirect(url_for("edit_payment", payment_id=payment_id))
            if group_id and not conn.execute("SELECT 1 FROM groups WHERE id = ?", (group_id,)).fetchone():
                conn.close()
                flash("Die ausgewählte Gruppe existiert nicht.", "danger")
                return redirect(url_for("edit_payment", payment_id=payment_id))

            if payment[6] >= amount_due:
                status = "paid"
            elif payment[6] > 0:
                status = "partial"
            elif due_date < date.today().isoformat():
                status = "overdue"
            else:
                status = "pending"

            conn.execute(
                """
                UPDATE payments
                SET student_id = ?, group_id = ?, amount_due = ?, due_date = ?,
                    status = ?, method = ?, note = ?
                WHERE id = ?
                """,
                (student_id, group_id, amount_due, due_date, status, method, note, payment_id),
            )
            conn.commit()
            conn.close()
            flash("Rechnung wurde aktualisiert.", "success")
            return redirect(url_for("payment_detail_page", payment_id=payment_id))

        students = conn.execute("SELECT id, full_name FROM students WHERE status != 'archived' ORDER BY full_name").fetchall()
        groups = conn.execute("SELECT id, name FROM groups ORDER BY name").fetchall()
        conn.close()
        return render_template("payments/edit.html", payment=payment, students=students, groups=groups)

    @app.route("/payments/<int:payment_id>/delete", methods=["POST"])
    @roles_required("admin")
    def delete_payment(payment_id):
        conn = sqlite3.connect(get_db_path())
        if not conn.execute("SELECT 1 FROM payments WHERE id = ?", (payment_id,)).fetchone():
            conn.close()
            abort(404)
        conn.execute("DELETE FROM payments WHERE id = ?", (payment_id,))
        conn.commit()
        conn.close()
        flash("Rechnung wurde gelöscht.", "success")
        return redirect(url_for("payments_page"))
