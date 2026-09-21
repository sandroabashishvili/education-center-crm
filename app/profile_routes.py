from functools import wraps
import io
import mimetypes
from pathlib import Path
import sqlite3
from uuid import uuid4

from flask import abort, flash, redirect, render_template, request, session, url_for, send_file
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

import database
from utils import is_valid_email, normalize_text


ALLOWED_AVATAR_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
ROLE_LABELS = {
    "admin": "Administrator",
    "manager": "Verwaltung",
    "teacher": "Lehrkraft",
}


def register_profile_routes(app):
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

    def fetch_user(user_id):
        conn = sqlite3.connect(get_db_path())
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            """
            SELECT id, full_name, email, phone, role, status, avatar_filename, created_at, must_change_password
            FROM users
            WHERE id = ?
            """,
            (user_id,),
        ).fetchone()
        conn.close()
        return row

    def avatar_directory():
        path = Path(app.config["UPLOAD_DIR"]) if app.config.get("UPLOAD_DIR") else Path(app.static_folder) / "uploads" / "avatars"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def remove_avatar_file(filename):
        if not filename:
            return
        candidate = avatar_directory() / Path(filename).name
        if candidate.is_file():
            candidate.unlink()

    @app.context_processor
    def inject_current_user():
        user_id = session.get("user_id")
        if not session.get("logged_in") or not user_id:
            return {"current_user": None, "role_labels": ROLE_LABELS}
        return {
            "current_user": fetch_user(int(user_id)),
            "role_labels": ROLE_LABELS,
        }

    @app.route("/profile/avatar/<filename>")
    @login_required
    def profile_avatar(filename):
        user = fetch_user(int(session["user_id"]))
        if not user or filename != user["avatar_filename"] or filename != Path(filename).name:
            abort(404)
        path = avatar_directory() / filename
        if not path.is_file():
            abort(404)
        # Release the Windows file handle before another request replaces an avatar.
        response = send_file(io.BytesIO(path.read_bytes()), mimetype=mimetypes.guess_type(filename)[0] or 'application/octet-stream', download_name=filename)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Cache-Control"] = "private, no-store"
        return response

    @app.route("/profile", methods=["GET", "POST"])
    @login_required
    def profile_settings():
        user_id = int(session["user_id"])
        user = fetch_user(user_id)
        if not user:
            session.clear()
            return redirect(url_for("index"))

        if request.method == "POST":
            full_name = normalize_text(request.form.get("full_name", ""))
            email = normalize_text(request.form.get("email", "")).lower()
            phone = normalize_text(request.form.get("phone", ""))

            if not full_name or not is_valid_email(email):
                flash("Bitte geben Sie einen Namen und eine gültige E-Mail-Adresse ein.", "danger")
                return redirect(url_for("profile_settings"))

            conn = sqlite3.connect(get_db_path())
            duplicate = conn.execute(
                "SELECT 1 FROM users WHERE lower(email) = lower(?) AND id != ?",
                (email, user_id),
            ).fetchone()
            if duplicate:
                conn.close()
                flash("Diese E-Mail-Adresse wird bereits verwendet.", "danger")
                return redirect(url_for("profile_settings"))

            avatar_filename = user["avatar_filename"]
            upload = request.files.get("avatar")
            if upload and upload.filename:
                original_name = secure_filename(upload.filename)
                suffix = Path(original_name).suffix.lower()
                if suffix not in ALLOWED_AVATAR_EXTENSIONS:
                    conn.close()
                    flash("Profilbilder müssen PNG, JPG, JPEG oder WEBP sein.", "danger")
                    return redirect(url_for("profile_settings"))

                new_filename = f"user-{user_id}-{uuid4().hex}{suffix}"
                upload.save(avatar_directory() / new_filename)
                old_filename = avatar_filename
                avatar_filename = new_filename
                if old_filename and old_filename != new_filename:
                    remove_avatar_file(old_filename)

            conn.execute(
                """
                UPDATE users
                SET full_name = ?, email = ?, phone = ?, avatar_filename = ?
                WHERE id = ?
                """,
                (full_name, email, phone, avatar_filename, user_id),
            )

            if user["role"] == "teacher":
                conn.execute(
                    """
                    UPDATE teachers
                    SET full_name = ?, email = ?, phone = ?
                    WHERE user_id = ?
                    """,
                    (full_name, email, phone, user_id),
                )

            conn.commit()
            conn.close()
            session["user_name"] = full_name
            flash("Profil wurde gespeichert.", "success")
            return redirect(url_for("profile_settings"))

        return render_template("profile/settings.html", user=user)

    @app.route("/profile/password", methods=["POST"])
    @login_required
    def profile_password():
        user_id = int(session["user_id"])
        current_password = request.form.get("current_password", "")
        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")

        minimum = 8 if app.config['DEMO_MODE'] else 12
        if len(new_password) < minimum:
            flash(f"Das neue Passwort muss mindestens {minimum} Zeichen lang sein.", "danger")
            return redirect(url_for("profile_settings") + "#security")
        if new_password != confirm_password:
            flash("Die neuen Passwörter stimmen nicht überein.", "danger")
            return redirect(url_for("profile_settings") + "#security")

        conn = sqlite3.connect(get_db_path())
        row = conn.execute(
            "SELECT password_hash FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
        if not row or not check_password_hash(row[0], current_password):
            conn.close()
            flash("Das aktuelle Passwort ist nicht korrekt.", "danger")
            return redirect(url_for("profile_settings") + "#security")

        conn.execute(
            "UPDATE users SET password_hash = ?, must_change_password=0, auth_version=auth_version+1 WHERE id = ?",
            (generate_password_hash(new_password), user_id),
        )
        version = conn.execute("SELECT auth_version FROM users WHERE id=?", (user_id,)).fetchone()[0]
        conn.commit()
        conn.close()
        session["auth_version"] = version
        flash("Passwort wurde geändert.", "success")
        return redirect(url_for("profile_settings") + "#security")

    @app.route("/profile/avatar/remove", methods=["POST"])
    @login_required
    def remove_profile_avatar():
        user_id = int(session["user_id"])
        user = fetch_user(user_id)
        if not user:
            abort(404)

        remove_avatar_file(user["avatar_filename"])
        conn = sqlite3.connect(get_db_path())
        conn.execute(
            "UPDATE users SET avatar_filename = NULL WHERE id = ?",
            (user_id,),
        )
        conn.commit()
        conn.close()
        flash("Profilbild wurde entfernt.", "success")
        return redirect(url_for("profile_settings"))
