"""Explicit no-backup reset, completed under the process lock before opening storage."""
import json
import shutil
from pathlib import Path
from .storage import durable_json

MARKER = 'reset-pending.json'
# Only application-owned state; never remove unrelated files or the process lock.
TARGETS = ('crm.db', 'crm.db-wal', 'crm.db-shm', 'crm.db-journal',
           'session.key', 'uploads', 'backups', 'restore_uploads',
           'generations', 'current.json', 'logs')


def schedule_reset(root):
    durable_json(Path(root) / MARKER, {'reset': 1})


def finish_pending_reset(root):
    root = Path(root)
    marker = root / MARKER
    if not marker.exists():
        return
    if json.loads(marker.read_text(encoding='utf-8')) != {'reset': 1}:
        raise ValueError('Ungültiger Auftrag zum Zurücksetzen. Daten wurden nicht gelöscht.')
    # Keep the marker until every deletion succeeds. A failed launch retries;
    # it must never initialize a partially erased database.
    for name in TARGETS:
        path = root / name
        if path.is_symlink():
            path.unlink()
        elif path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink(missing_ok=True)
    marker.unlink()
