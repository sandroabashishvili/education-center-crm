"""Validated full backups and atomic selection of a restored data generation."""
from contextlib import closing
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import sqlite3
import tempfile
import uuid
import zipfile

MAX_ARCHIVE_BYTES = 128 * 1024 * 1024
MAX_FILES = 5000
TOKEN = re.compile(r'^[0-9a-f]{32}$')
AVATAR = re.compile(r'^avatars/[A-Za-z0-9_-]+\.(png|jpg|jpeg|webp)$', re.I)


class BackupError(ValueError):
    pass


def digest(path):
    with Path(path).open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def durable_json(path, value):
    path = Path(path)
    temporary = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    try:
        with temporary.open('w', encoding='utf-8') as handle:
            json.dump(value, handle)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def active_folder(root):
    root = Path(root)
    pointer = root / 'current.json'
    if not pointer.exists():
        return root
    try:
        token = json.loads(pointer.read_text(encoding='utf-8'))['generation']
        if not isinstance(token, str) or not TOKEN.fullmatch(token):
            raise ValueError('invalid generation')
        folder = root / 'generations' / token
        if not (folder / 'crm.db').is_file() or not (folder / 'session.key').is_file():
            raise ValueError('missing restored data')
        return folder
    except (ValueError, KeyError, OSError, TypeError) as exc:
        raise BackupError('Der aktive Datenstand ist beschädigt. Die vorhandenen Daten wurden nicht ersetzt.') from exc


def inspect_database(path):
    from database import SCHEMA_VERSION
    with closing(sqlite3.connect(Path(path).as_uri() + '?mode=ro', uri=True)) as conn:
        version = conn.execute('PRAGMA user_version').fetchone()[0]
        if version not in (1,2,SCHEMA_VERSION):
            raise BackupError('Diese Datenbankversion wird nicht unterstützt.')
        objects = conn.execute("SELECT type,name FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'").fetchall()
        required = {'users','students','courses','teachers','groups','group_students','lessons','attendance','payments'}
        if required - {name for kind,name in objects if kind=='table'} or any(kind in ('trigger','view') for kind,name in objects):
            raise BackupError('Die Sicherung enthält kein unterstütztes CRM-Schema.')
        if conn.execute('PRAGMA quick_check').fetchone()[0]!='ok' or conn.execute('PRAGMA foreign_key_check').fetchone():
            raise BackupError('Die Datenbankprüfung ist fehlgeschlagen.')
        if not conn.execute("SELECT 1 FROM users WHERE role='admin' AND status='active'").fetchone():
            raise BackupError('Die Sicherung enthält kein aktives Admin-Konto.')
        organization = conn.execute('SELECT organization_name,setup_completed FROM app_settings WHERE id=1').fetchone() if version>=2 else None
        if version>=2 and (not organization or organization[1]!=1):
            raise BackupError('Die Einrichtung dieser Sicherung ist nicht abgeschlossen.')
        return {'organization': organization[0] if organization else 'Education Center CRM',
                'users': conn.execute('SELECT COUNT(*) FROM users').fetchone()[0],
                'students': conn.execute('SELECT COUNT(*) FROM students').fetchone()[0],
                'schema': version}


def create_backup(config, *, directory=None):
    """Caller holds the application's request lock, including avatar mutations."""
    root = Path(config['DATA_DIR'])
    directory = Path(directory) if directory is not None else root / 'backups'
    directory.mkdir(parents=True, exist_ok=True)
    token = uuid.uuid4().hex
    destination = directory / f'crm-{datetime.now(timezone.utc):%Y%m%d-%H%M%S}-{token}.zip'
    with tempfile.TemporaryDirectory(dir=root, prefix='backup-stage-') as temp:
        stage = Path(temp)
        database = stage / 'crm.db'
        with closing(sqlite3.connect(config['DB_PATH'])) as source, closing(sqlite3.connect(database)) as target:
            source.backup(target)
        info = inspect_database(database)
        paths = {'crm.db': database}
        with closing(sqlite3.connect(database)) as conn:
            avatars = {r[0] for r in conn.execute('SELECT avatar_filename FROM users WHERE avatar_filename IS NOT NULL') if r[0]}
        for name in avatars:
            if not AVATAR.fullmatch('avatars/' + name):
                raise BackupError('Ein Profilbild hat einen ungültigen Dateinamen.')
            path = Path(config['UPLOAD_DIR']) / name
            if not path.is_file() or path.is_symlink():
                raise BackupError('Ein gespeichertes Profilbild fehlt. Bitte das Profilbild vor der Sicherung korrigieren.')
            paths['avatars/' + name] = path
        if len(paths)>MAX_FILES or sum(p.stat().st_size for p in paths.values())>MAX_ARCHIVE_BYTES:
            raise BackupError('Diese Sicherung überschreitet die unterstützte Größe von 128 MB.')
        manifest = {'format': 1, 'created_at': datetime.now(timezone.utc).isoformat(),
                    'files': {name: digest(path) for name,path in paths.items()}, **info}
        pending = stage / 'backup.zip'
        with zipfile.ZipFile(pending, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr('manifest.json', json.dumps(manifest, ensure_ascii=False))
            for name,path in paths.items():
                archive.write(path,name)
        if pending.stat().st_size>MAX_ARCHIVE_BYTES:
            raise BackupError('Diese Sicherung überschreitet 128 MB.')
        # Move only a completed archive into the downloadable directory.
        os.replace(pending,destination)
    return destination


def unpack_backup(archive_path, destination):
    """Never extract arbitrary ZIP paths or trust declared organization metadata."""
    destination = Path(destination)
    try:
        if Path(archive_path).stat().st_size>MAX_ARCHIVE_BYTES:
            raise BackupError('Die Sicherung ist größer als 128 MB.')
        with zipfile.ZipFile(archive_path) as archive:
            infos = archive.infolist()
            names = [item.filename for item in infos]
            if len(names)>MAX_FILES+1 or len(names)!=len(set(names)) or 'manifest.json' not in names or 'crm.db' not in names:
                raise BackupError('Die Sicherung ist unvollständig oder enthält doppelte Dateien.')
            if sum(item.file_size for item in infos)>MAX_ARCHIVE_BYTES or archive.getinfo('manifest.json').file_size>1024*1024:
                raise BackupError('Die entpackte Sicherung ist zu groß.')
            if any(name not in ('crm.db','manifest.json') and not AVATAR.fullmatch(name) for name in names):
                raise BackupError('Die Sicherung enthält unerlaubte Dateipfade.')
            manifest = json.loads(archive.read('manifest.json'))
            if not isinstance(manifest,dict) or manifest.get('format')!=1 or not isinstance(manifest.get('files'),dict) or set(manifest['files'])!=set(names)-{'manifest.json'}:
                raise BackupError('Das Sicherungsmanifest ist ungültig.')
            destination.mkdir(parents=True, exist_ok=True)
            for name,expected_hash in manifest['files'].items():
                target = destination / ('crm.db' if name=='crm.db' else 'uploads/' + name)
                target.parent.mkdir(parents=True,exist_ok=True)
                with archive.open(name) as source, target.open('wb') as output:
                    shutil.copyfileobj(source,output,1024*1024)
                if digest(target)!=expected_hash:
                    raise BackupError('Die Prüfsumme einer Sicherungsdatei stimmt nicht.')
        info = inspect_database(destination / 'crm.db')
        with closing(sqlite3.connect(destination / 'crm.db')) as conn:
            avatars = {r[0] for r in conn.execute('SELECT avatar_filename FROM users WHERE avatar_filename IS NOT NULL') if r[0]}
        if {'avatars/' + name for name in avatars} != set(manifest['files'])-{'crm.db'}:
            raise BackupError('Profilbilder und Datenbank passen nicht zusammen.')
        return {**info, 'created_at': str(manifest.get('created_at','Unbekannt'))[:80], 'avatars': len(avatars)}
    except (zipfile.BadZipFile, sqlite3.DatabaseError, KeyError, TypeError, UnicodeError, json.JSONDecodeError, RuntimeError) as exc:
        raise BackupError('Die Datei ist keine gültige CRM-Sicherung.') from exc


def restore_backup(config, archive_path):
    """Build independently; pointer replacement is the only activation step."""
    from database import init_db
    root = Path(config['DATA_DIR'])
    generation = uuid.uuid4().hex
    target = root / 'generations' / generation
    target.mkdir(parents=True)
    activated = False
    try:
        info = unpack_backup(archive_path,target)
        init_db(target / 'crm.db', seed_demo=False)
        with (target / 'session.key').open('w',encoding='ascii') as handle:
            handle.write(secrets.token_hex(32))
            handle.flush()
            os.fsync(handle.fileno())
        (target / 'uploads/avatars').mkdir(parents=True,exist_ok=True)
        for file in target.rglob('*'):
            if file.is_file():
                with file.open('r+b') as handle:
                    os.fsync(handle.fileno())
        safety_backup = create_backup(config)
        # Validate the new config before changing the persistent pointer.
        new_config = {**config, 'DB_PATH': target / 'crm.db', 'UPLOAD_DIR': target / 'uploads/avatars',
                      'SECRET_KEY': (target / 'session.key').read_text()}
        new_config['STORAGE_EPOCH'] = hashlib.sha256(new_config['SECRET_KEY'].encode()).hexdigest()
        durable_json(root / 'current.json', {'generation': generation})
        activated = True
        config.update(new_config)
        return info, safety_backup
    finally:
        if not activated:
            shutil.rmtree(target,ignore_errors=True)
