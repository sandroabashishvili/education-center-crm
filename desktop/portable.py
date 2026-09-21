"""Self-contained program + active data archives; never recurse into old backups."""
from datetime import datetime, timezone
from pathlib import Path
import json
import os
import secrets
import tempfile
import uuid
import zipfile
from .storage import BackupError, create_backup, unpack_backup, digest

START_CMD = '@echo off\r\nstart "" "%~dp0application\\EducationCenterCRM.exe"\r\n'
INSTRUCTIONS = """Education Center CRM — portable
Start: Start.cmd oder application/EducationCenterCRM.exe.
Programm: application/; Daten: data/; Sicherungen: data/backups/.
Zum Umziehen die App schließen und den ganzen Ordner kopieren.
Komplettsicherung: ZIP in einen neuen leeren Ordner entpacken, Start.cmd öffnen.
Bestehende Ordner nicht überschreiben. Windows x64 mit WebView2 erforderlich.
Die Komplettsicherung enthält das Programm und den aktiven Datenstand, aber keine
älteren Sicherungen, alten Wiederherstellungsstände oder technischen Logs.
Eine Sicherung auf demselben Datenträger schützt nicht vor dessen Verlust.
"""


def create_portable_backup(config):
    portable = config.get('PORTABLE_ROOT')
    if not portable:
        raise BackupError('Komplettsicherungen sind nur in der portablen Version verfügbar.')
    root = Path(portable)
    application = root / 'application'
    if not (application / 'EducationCenterCRM.exe').is_file():
        raise BackupError('Der Programmordner ist unvollständig.')
    output = Path(config['DATA_DIR']) / 'backups'
    output.mkdir(parents=True, exist_ok=True)
    destination = output / f'crm-portable-{datetime.now(timezone.utc):%Y%m%d-%H%M%S}-{uuid.uuid4().hex}.zip'
    with tempfile.TemporaryDirectory(dir=config['DATA_DIR'], prefix='portable-stage-') as temp:
        stage = Path(temp)
        snapshot = create_backup(config, directory=stage)
        data = stage / 'data'
        unpack_backup(snapshot, data)
        # New session secret: preserve accounts, not browser sessions.
        (data / 'session.key').write_text(secrets.token_hex(32), encoding='ascii')
        paths = {}
        for base, prefix in ((application, 'application'), (data, 'data')):
            for path in base.rglob('*'):
                if path.is_symlink() or (hasattr(path, 'is_junction') and path.is_junction()):
                    raise BackupError('Verknüpfte Dateien können nicht vollständig gesichert werden.')
                if path.is_file():
                    paths[prefix + '/' + path.relative_to(base).as_posix()] = path
        if len(paths)>20000 or sum(path.stat().st_size for path in paths.values())>2*1024**3:
            raise BackupError('Die Komplettsicherung überschreitet 2 GB oder 20000 Dateien.')
        pending = stage / 'complete.zip'
        with zipfile.ZipFile(pending, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
            checksums = {}
            for name, path in paths.items():
                archive.write(path, name)
                checksums[name] = digest(path)
            archive.writestr('Start.cmd', START_CMD)
            archive.writestr('README.txt', INSTRUCTIONS)
            archive.writestr('portable-manifest.json', json.dumps({'format': 'crm-portable-1', 'files': checksums}))
        os.replace(pending, destination)
    return destination
