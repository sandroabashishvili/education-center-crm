"""Admin-only desktop backup, preview and confirmed restore."""
from contextlib import closing
from pathlib import Path
import sqlite3
import tempfile
import threading
import uuid

from flask import abort, flash, g, redirect, render_template, request, send_file, session, url_for
from werkzeug.security import check_password_hash
from account_routes import admin_required
from desktop.reset import MARKER, schedule_reset
from desktop.portable import create_portable_backup
from desktop.storage import BackupError, MAX_ARCHIVE_BYTES, TOKEN, create_backup, unpack_backup, restore_backup


def register_backup_routes(app):
    lock = threading.RLock()
    app.extensions['storage_lock'] = lock

    def storage_guard():
        if app.config.get('DATA_DIR'):
            lock.acquire()
            g.storage_lock_held = True
            if (Path(app.config['DATA_DIR']) / MARKER).exists():
                session.clear()
                return app.make_response(('''<!doctype html><html lang="de"><meta charset="utf-8"><title>Neustart erforderlich</title><body><h1>Zurücksetzen bestätigt</h1><p>Bitte schließen Sie die Anwendung vollständig und öffnen Sie sie erneut über dieselbe Verknüpfung. Beim nächsten Start werden die CRM-Daten und lokalen Sicherungen ohne Archiv gelöscht. Danach beginnt die Ersteinrichtung.</p></body></html>''', 503, {'Cache-Control': 'no-store'}))
        if request.endpoint == 'backup_preview':
            request.max_content_length = MAX_ARCHIVE_BYTES + 1024*1024
    # Before CSRF parsing, setup, account checks and all database mutations.
    app.before_request_funcs.setdefault(None,[]).insert(0,storage_guard)

    @app.teardown_request
    def release_storage(_error):
        if getattr(g,'storage_lock_held',False):
            g.storage_lock_held = False
            lock.release()

    def root():
        if not app.config.get('DATA_DIR'):
            abort(404)
        return Path(app.config['DATA_DIR'])

    def page(error=None,status=200,preview=None,token=None):
        directory = root() / 'backups'
        archives = sorted(directory.glob('crm-*.zip'),reverse=True) if directory.exists() else []
        return render_template('admin/backups.html',archives=[{'name':p.name,'size':round(p.stat().st_size/1024,1)} for p in archives],error=error,preview=preview,token=token,portable=bool(app.config.get('PORTABLE_ROOT'))),status

    @app.route('/admin/backups',methods=['GET','POST'])
    @admin_required
    def backups_page():
        root()
        if request.method=='POST':
            try:
                path = create_portable_backup(app.config) if app.config.get('PORTABLE_ROOT') else create_backup(app.config)
            except (BackupError,OSError) as exc:
                return page(str(exc),400)
            flash('Sicherung erstellt und im Datenordner unter backups gespeichert. Eine Komplettsicherung mit Programm entpacken Sie zur Wiederherstellung in einen neuen leeren Ordner.','success')
            return redirect(url_for('backups_page'))
        return page()

    @app.get('/admin/backups/download/<name>')
    @admin_required
    def backup_download(name):
        if Path(name).name!=name or not name.startswith('crm-') or not name.endswith('.zip'):
            abort(404)
        path = root() / 'backups' / name
        if not path.is_file():
            abort(404)
        response = send_file(path,as_attachment=True,download_name=name)
        response.headers['Cache-Control']='private, no-store'
        return response

    @app.post('/admin/backups/preview')
    @admin_required
    def backup_preview():
        incoming = root() / 'restore_uploads'
        incoming.mkdir(exist_ok=True)
        previous = session.pop('restore_token',None)
        if isinstance(previous,str) and TOKEN.fullmatch(previous):
            (incoming / (previous+'.zip')).unlink(missing_ok=True)
        upload = request.files.get('backup')
        if not upload or not upload.filename:
            return page('Bitte eine CRM-ZIP-Sicherung auswählen.',400)
        token = uuid.uuid4().hex
        archive = incoming / (token+'.zip')
        try:
            upload.save(archive)
            with tempfile.TemporaryDirectory(dir=incoming) as temporary:
                preview = unpack_backup(archive,Path(temporary))
        except (BackupError,OSError) as exc:
            archive.unlink(missing_ok=True)
            return page(str(exc),400)
        session['restore_token']=token
        return page(preview=preview,token=token)

    @app.post('/admin/backups/restore')
    @admin_required
    def backup_restore():
        token = request.form.get('token','')
        if not TOKEN.fullmatch(token) or token!=session.get('restore_token'):
            return page('Bitte die Sicherung erneut auswählen und prüfen.',400)
        with closing(sqlite3.connect(app.config['DB_PATH'])) as conn:
            password_hash = conn.execute('SELECT password_hash FROM users WHERE id=?',(session['user_id'],)).fetchone()[0]
        if request.form.get('confirm')!='yes' or not check_password_hash(password_hash,request.form.get('current_password','')):
            return page('Bestätigung und korrektes aktuelles Admin-Passwort sind erforderlich. Bitte die Sicherung erneut prüfen.',400)
        archive = root() / 'restore_uploads' / (token+'.zip')
        try:
            restore_backup(app.config,archive)
        except (BackupError,OSError,sqlite3.DatabaseError) as exc:
            return page('Wiederherstellung nicht aktiviert: '+str(exc),400)
        session.clear()
        archive.unlink(missing_ok=True)
        flash('Sicherung wiederhergestellt. Melden Sie sich mit einem Konto aus dieser Sicherung an. Der vorherige Datenstand wurde zusätzlich gesichert.','success')
        return redirect(url_for('index'))

    @app.route('/admin/reset', methods=['GET', 'POST'])
    @admin_required
    def application_reset():
        directory = root()
        error = None
        if request.method == 'POST':
            with closing(sqlite3.connect(app.config['DB_PATH'])) as conn:
                row = conn.execute('SELECT password_hash FROM users WHERE id=?', (session['user_id'],)).fetchone()
            if request.form.get('confirmation') != 'ALLES LÖSCHEN' or not row or not check_password_hash(row[0], request.form.get('current_password', '')):
                error = 'Geben Sie ALLES LÖSCHEN und Ihr korrektes aktuelles Admin-Passwort ein.'
            else:
                try:
                    schedule_reset(directory)
                except OSError:
                    return render_template('admin/reset.html', error='Zurücksetzen konnte nicht vorgemerkt werden. Es wurden keine Daten gelöscht.'), 500
                session.clear()
                return redirect(url_for('application_reset'))
        return render_template('admin/reset.html', error=error), 400 if error else 200

    @app.post('/admin/backups/data-only')
    @admin_required
    def backup_data_only():
        root()
        try:
            create_backup(app.config)
        except (BackupError, OSError) as exc:
            return page(str(exc), 400)
        flash('Datensicherung für die Wiederherstellung innerhalb der App erstellt.', 'success')
        return redirect(url_for('backups_page'))
