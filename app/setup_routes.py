"""One-time local organization bootstrap and live account validation."""
from contextlib import closing
import sqlite3

from flask import abort, flash, redirect, render_template, request, session, url_for
from werkzeug.security import generate_password_hash
from utils import is_valid_email, normalize_text


def register_setup_routes(app):
    def settings():
        with closing(sqlite3.connect(app.config['DB_PATH'])) as conn:
            return conn.execute('SELECT organization_name, setup_completed FROM app_settings WHERE id=1').fetchone()

    @app.before_request
    def setup_and_account_guard():
        if request.endpoint in ('static', 'favicon_ico', 'health'):
            return
        state = settings()
        if not state or not state[1]:
            if request.endpoint != 'setup':
                return redirect(url_for('setup'))
            return
        if session.get('logged_in'):
            with closing(sqlite3.connect(app.config['DB_PATH'])) as conn:
                user = conn.execute('SELECT role, status, full_name, auth_version, must_change_password FROM users WHERE id=?', (session.get('user_id'),)).fetchone()
                linked = user and (user[0] != 'teacher' or conn.execute(
                    "SELECT 1 FROM teachers WHERE user_id=? AND status='active'", (session.get('user_id'),)).fetchone())
            stale_storage = app.config.get('DATA_DIR') and session.get('storage_epoch') != app.config.get('STORAGE_EPOCH')
            if not user or user[1] != 'active' or not linked or session.get('auth_version') != user[3] or stale_storage:
                session.clear()
                abort(403)
            session.update(user_role=user[0], user_name=user[2])
            if user[4] and request.endpoint not in ('profile_settings','profile_password','logout'):
                return redirect(url_for('profile_settings') + '#security')

    @app.context_processor
    def organization_context():
        state = settings()
        return {'organization_name': state[0] if state else '', 'demo_mode': app.config['DEMO_MODE'], 'min_password_length': 8 if app.config['DEMO_MODE'] else 12, 'desktop_data': bool(app.config.get('DATA_DIR'))}

    @app.route('/setup', methods=['GET', 'POST'])
    def setup():
        state = settings()
        if state and state[1]:
            abort(404)
        if request.method == 'GET':
            return render_template('setup.html')
        organization = normalize_text(request.form.get('organization_name', ''))
        name = normalize_text(request.form.get('full_name', ''))
        email = normalize_text(request.form.get('email', '')).lower()
        password = request.form.get('password', '')
        if not organization or not name or len(organization) > 150 or len(name) > 150 or not is_valid_email(email) or len(email) > 254:
            flash('Bitte geben Sie Zentrum, Namen und eine gültige E-Mail-Adresse ein.', 'danger')
            return render_template('setup.html'), 400
        if len(password) < 12 or password != request.form.get('confirm_password', ''):
            flash('Passwörter müssen übereinstimmen und mindestens 12 Zeichen enthalten.', 'danger')
            return render_template('setup.html'), 400
        password_hash = generate_password_hash(password)
        with closing(sqlite3.connect(app.config['DB_PATH'])) as conn, conn:
            conn.execute('BEGIN IMMEDIATE')
            state = conn.execute('SELECT setup_completed FROM app_settings WHERE id=1').fetchone()
            if not state or state[0] or conn.execute('SELECT 1 FROM users LIMIT 1').fetchone():
                abort(409)
            conn.execute("INSERT INTO users(full_name,email,password_hash,role) VALUES (?,?,?,'admin')", (name,email,password_hash))
            conn.execute('UPDATE app_settings SET organization_name=?, setup_completed=1 WHERE id=1', (organization,))
        session.clear()
        flash('Ihr Zentrum wurde eingerichtet. Melden Sie sich mit Ihrem Konto an.', 'success')
        return redirect(url_for('index'))
