"""Local account administration and one-use organization recovery codes."""
from contextlib import closing
from functools import wraps
import secrets
import sqlite3

from flask import abort, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from utils import is_valid_email, normalize_text


def admin_required(view):
    @wraps(view)
    def guarded(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('index'))
        if session.get('user_role') != 'admin':
            abort(403)
        return view(*args, **kwargs)
    return guarded


def register_account_routes(app):
    def connect():
        conn = sqlite3.connect(app.config['DB_PATH'])
        conn.row_factory = sqlite3.Row
        conn.execute('PRAGMA foreign_keys=ON')
        return conn

    def current_password_ok(conn):
        row = conn.execute('SELECT password_hash FROM users WHERE id=?', (session['user_id'],)).fetchone()
        return row and check_password_hash(row['password_hash'], request.form.get('current_password', ''))

    def listing(error=None, status=200, recovery_code=None):
        with closing(connect()) as conn:
            users = conn.execute('SELECT u.*,t.id AS teacher_id,t.full_name AS teacher_name FROM users u LEFT JOIN teachers t ON t.user_id=u.id ORDER BY u.id').fetchall()
            teachers = conn.execute("SELECT id,full_name,user_id FROM teachers WHERE status='active' ORDER BY full_name").fetchall()
            recovery_ready = bool(conn.execute('SELECT recovery_hash FROM app_settings WHERE id=1').fetchone()[0])
        response = app.make_response((render_template('admin/accounts.html', users=users, teachers=teachers, error=error, recovery_code=recovery_code, recovery_ready=recovery_ready), status))
        response.headers['Cache-Control'] = 'no-store'
        return response

    @app.route('/admin/accounts', methods=['GET', 'POST'])
    @admin_required
    def accounts():
        if request.method == 'GET':
            return listing()
        name = normalize_text(request.form.get('full_name', ''))
        email = normalize_text(request.form.get('email', '')).lower()
        role = request.form.get('role')
        password = request.form.get('password', '')
        if not name or len(name)>150 or not is_valid_email(email) or len(email)>254 or role not in ('admin','manager','teacher'):
            return listing('Bitte gültigen Namen, E-Mail-Adresse und Rolle angeben.', 400)
        if len(password)<12 or password != request.form.get('confirm_password'):
            return listing('Passwörter müssen übereinstimmen und mindestens 12 Zeichen enthalten.', 400)
        with closing(connect()) as conn, conn:
            conn.execute('BEGIN IMMEDIATE')
            if conn.execute('SELECT 1 FROM users WHERE lower(email)=?', (email,)).fetchone():
                return listing('Diese E-Mail-Adresse wird bereits verwendet.', 400)
            teacher = None
            if role == 'teacher':
                teacher = conn.execute("SELECT id FROM teachers WHERE id=? AND user_id IS NULL AND status='active'", (request.form.get('teacher_id'),)).fetchone()
                if not teacher:
                    return listing('Bitte eine aktive Lehrkraft ohne Benutzerkonto auswählen.', 400)
            user_id = conn.execute('INSERT INTO users(full_name,email,password_hash,role,must_change_password) VALUES (?,?,?,?,1)', (name,email,generate_password_hash(password),role)).lastrowid
            if teacher:
                conn.execute('UPDATE teachers SET user_id=? WHERE id=?', (user_id,teacher['id']))
        flash('Konto erstellt. Das Startpasswort muss bei der ersten Anmeldung geändert werden.', 'success')
        return redirect(url_for('accounts'))

    @app.post('/admin/accounts/<int:user_id>/status')
    @admin_required
    def account_status(user_id):
        status = request.form.get('status')
        if status not in ('active','inactive'):
            abort(400)
        with closing(connect()) as conn, conn:
            conn.execute('BEGIN IMMEDIATE')
            user = conn.execute('SELECT role,status FROM users WHERE id=?', (user_id,)).fetchone()
            if not user:
                abort(404)
            if user_id == session['user_id'] and status == 'inactive':
                return listing('Das eigene angemeldete Konto kann nicht deaktiviert werden.', 400)
            if user['role']=='admin' and status=='inactive' and not conn.execute("SELECT 1 FROM users WHERE role='admin' AND status='active' AND id!=?", (user_id,)).fetchone():
                return listing('Mindestens ein aktiver Administrator muss erhalten bleiben.', 400)
            if user['role']=='teacher' and status=='active' and not conn.execute("SELECT 1 FROM teachers WHERE user_id=? AND status='active'", (user_id,)).fetchone():
                return listing('Vor der Aktivierung muss eine aktive Lehrkraft mit dem Konto verknüpft sein.', 400)
            if status != user['status']:
                conn.execute('UPDATE users SET status=?,auth_version=auth_version+1 WHERE id=?', (status,user_id))
        flash('Kontostatus aktualisiert.', 'success')
        return redirect(url_for('accounts'))

    @app.post('/admin/accounts/<int:user_id>/role')
    @admin_required
    def account_role(user_id):
        role=request.form.get('role')
        if role not in ('admin','manager','teacher'):
            abort(400)
        with closing(connect()) as conn,conn:
            conn.execute('BEGIN IMMEDIATE')
            user=conn.execute('SELECT role FROM users WHERE id=?',(user_id,)).fetchone()
            if not user:
                abort(404)
            if user_id==session['user_id'] and role!='admin':
                return listing('Die eigene Admin-Rolle kann hier nicht entfernt werden.',400)
            if user['role']=='admin' and role!='admin' and not conn.execute("SELECT 1 FROM users WHERE role='admin' AND status='active' AND id!=?",(user_id,)).fetchone():
                return listing('Mindestens ein aktiver Administrator muss erhalten bleiben.',400)
            if role=='teacher':
                teacher=conn.execute("SELECT id FROM teachers WHERE id=? AND status='active' AND (user_id IS NULL OR user_id=?)",(request.form.get('teacher_id'),user_id)).fetchone()
                if not teacher:
                    return listing('Bitte eine aktive verfügbare Lehrkraft auswählen.',400)
                conn.execute('UPDATE teachers SET user_id=NULL WHERE user_id=?',(user_id,))
                conn.execute('UPDATE teachers SET user_id=? WHERE id=?',(user_id,teacher['id']))
            elif user['role']=='teacher':
                conn.execute('UPDATE teachers SET user_id=NULL WHERE user_id=?',(user_id,))
            conn.execute('UPDATE users SET role=?,auth_version=auth_version+1 WHERE id=?',(role,user_id))
        flash('Rolle aktualisiert. Das Konto muss sich neu anmelden.','success')
        return redirect(url_for('accounts'))

    @app.post('/admin/accounts/<int:user_id>/teacher')
    @admin_required
    def account_teacher(user_id):
        with closing(connect()) as conn, conn:
            conn.execute('BEGIN IMMEDIATE')
            user = conn.execute("SELECT id FROM users WHERE id=? AND role='teacher'", (user_id,)).fetchone()
            teacher = conn.execute("SELECT id FROM teachers WHERE id=? AND status='active' AND (user_id IS NULL OR user_id=?)", (request.form.get('teacher_id'),user_id)).fetchone()
            if not user or not teacher:
                return listing('Diese Zuordnung ist nicht möglich. Die Lehrkraft muss aktiv und verfügbar sein.', 400)
            conn.execute('UPDATE teachers SET user_id=NULL WHERE user_id=?', (user_id,))
            conn.execute('UPDATE teachers SET user_id=? WHERE id=?', (user_id,teacher['id']))
            conn.execute('UPDATE users SET auth_version=auth_version+1 WHERE id=?', (user_id,))
        flash('Lehrkraft zugeordnet. Das Konto muss sich neu anmelden.', 'success')
        return redirect(url_for('accounts'))

    @app.post('/admin/accounts/<int:user_id>/password')
    @admin_required
    def account_password(user_id):
        if user_id == session['user_id']:
            return redirect(url_for('profile_settings') + '#security')
        password = request.form.get('password','')
        with closing(connect()) as conn, conn:
            if not current_password_ok(conn):
                return listing('Ihr aktuelles Admin-Passwort ist nicht korrekt.',400)
            if len(password)<12 or password != request.form.get('confirm_password'):
                return listing('Neue Passwörter müssen übereinstimmen und mindestens 12 Zeichen enthalten.',400)
            if not conn.execute('SELECT 1 FROM users WHERE id=?',(user_id,)).fetchone():
                abort(404)
            conn.execute('UPDATE users SET password_hash=?,must_change_password=1,auth_version=auth_version+1 WHERE id=?',(generate_password_hash(password),user_id))
        flash('Startpasswort erneuert; bestehende Sitzungen sind ungültig.', 'success')
        return redirect(url_for('accounts'))

    @app.post('/admin/accounts/recovery-code')
    @admin_required
    def recovery_code():
        with closing(connect()) as conn, conn:
            if not current_password_ok(conn):
                return listing('Ihr aktuelles Admin-Passwort ist nicht korrekt.',400)
            code = secrets.token_urlsafe(32)
            conn.execute('UPDATE app_settings SET recovery_hash=? WHERE id=1',(generate_password_hash(code),))
        return listing(recovery_code=code)

    @app.route('/recover', methods=['GET','POST'])
    def recover_account():
        error = None
        if request.method == 'POST':
            password = request.form.get('password','')
            email = normalize_text(request.form.get('email','')).lower()
            with closing(connect()) as conn, conn:
                conn.execute('BEGIN IMMEDIATE')
                recovery = conn.execute('SELECT recovery_hash FROM app_settings WHERE id=1').fetchone()
                user = conn.execute("SELECT id FROM users WHERE lower(email)=? AND role='admin' AND status='active'",(email,)).fetchone()
                if not user or not recovery or not recovery[0] or not check_password_hash(recovery[0],request.form.get('recovery_code','')):
                    error = 'E-Mail-Adresse oder Wiederherstellungscode ist ungültig.'
                elif len(password)<12 or password != request.form.get('confirm_password'):
                    error = 'Passwörter müssen übereinstimmen und mindestens 12 Zeichen enthalten.'
                else:
                    conn.execute('UPDATE users SET password_hash=?,auth_version=auth_version+1,must_change_password=0 WHERE id=?',(generate_password_hash(password),user['id']))
                    conn.execute('UPDATE app_settings SET recovery_hash=NULL WHERE id=1')
                    session.clear()
                    flash('Passwort erneuert. Erstellen Sie nach der Anmeldung einen neuen Wiederherstellungscode.','success')
                    return redirect(url_for('index'))
        response = app.make_response((render_template('admin/recover.html',error=error),400 if error else 200))
        response.headers['Cache-Control']='no-store'
        return response

    @app.route('/admin/accounts/<int:user_id>/delete', methods=['GET', 'POST'])
    @admin_required
    def account_delete(user_id):
        with closing(connect()) as conn, conn:
            conn.execute('BEGIN IMMEDIATE')
            user = conn.execute('SELECT * FROM users WHERE id=?', (user_id,)).fetchone()
            if not user:
                abort(404)
            if user_id == session['user_id']:
                return listing('Das angemeldete Konto kann nicht gelöscht werden. Melden Sie sich mit einem anderen Administrator an.', 400)
            if user['role'] == 'admin' and not conn.execute("SELECT 1 FROM users WHERE role='admin' AND status='active' AND id!=?", (user_id,)).fetchone():
                return listing('Mindestens ein aktiver Administrator muss erhalten bleiben.', 400)
            error = None
            if request.method == 'POST':
                if request.form.get('confirmation') != user['email'] or not current_password_ok(conn):
                    error = 'Bestätigen Sie die E-Mail-Adresse und Ihr aktuelles Admin-Passwort.'
                else:
                    conn.execute('DELETE FROM users WHERE id=?', (user_id,))
                    flash('Benutzerkonto endgültig gelöscht. Lehrkraft und Unterrichtsdaten bleiben erhalten. Vorhandene Sicherungen wurden nicht verändert.', 'success')
                    return redirect(url_for('accounts'))
            return render_template('admin/delete_account.html', target=user, error=error), 400 if error else 200
