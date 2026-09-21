"""Per-user files and a cross-platform process lock, independent of the UI."""
from contextlib import contextmanager
from pathlib import Path
import hashlib
import os
import secrets
import sys


def default_data_dir():
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).resolve().parent.parent / 'data'
    if sys.platform == 'win32':
        root = Path(os.environ.get('LOCALAPPDATA', Path.home() / 'AppData/Local'))
    elif sys.platform == 'darwin':
        root = Path.home() / 'Library/Application Support'
    else:
        root = Path(os.environ.get('XDG_DATA_HOME', Path.home() / '.local/share'))
    return root / 'EducationCenterCRM'


@contextmanager
def instance_lock(data_dir):
    """OS releases the lock after a crash; do not unlink the shared lock file."""
    data_dir.mkdir(parents=True, exist_ok=True)
    handle = (data_dir / 'app.lock').open('a+b')
    try:
        handle.seek(0, 2)
        if handle.tell() == 0:
            handle.write(b'0')
            handle.flush()
        handle.seek(0)
        try:
            if sys.platform == 'win32':
                import msvcrt
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            raise RuntimeError('Education Center CRM läuft bereits für diesen Datenordner.') from exc
        yield
    finally:
        handle.close()


def app_config(data_dir):
    """Called after acquiring the instance lock; never includes packaged data."""
    from .reset import finish_pending_reset
    finish_pending_reset(data_dir)
    for subdir in ('uploads/avatars', 'logs', 'backups'):
        (data_dir / subdir).mkdir(parents=True, exist_ok=True)
    from .storage import active_folder
    active = active_folder(data_dir)
    key_path = active / 'session.key'
    if not key_path.exists():
        fd = os.open(key_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, 'w') as handle:
            handle.write(secrets.token_hex(32))
    key = key_path.read_text().strip()
    if len(key) != 64:
        raise ValueError('Der Sitzungsschlüssel ist beschädigt. Bitte den Datenordner prüfen.')
    portable = Path(sys.executable).resolve().parent.parent if getattr(sys, 'frozen', False) and data_dir.resolve() == default_data_dir() else None
    return {'PORTABLE_ROOT': portable, 'DATA_DIR': data_dir, 'DB_PATH': active / 'crm.db', 'UPLOAD_DIR': active / 'uploads/avatars',
            'SECRET_KEY': key, 'STORAGE_EPOCH': hashlib.sha256(key.encode()).hexdigest(), 'DEMO_MODE': False}
