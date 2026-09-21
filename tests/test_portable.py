from contextlib import closing
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'app'))
from app_factory import create_app
from desktop.runtime import app_config, default_data_dir
from desktop.portable import create_portable_backup
from desktop.storage import digest, restore_backup, create_backup


class PortableTests(unittest.TestCase):
    def test_frozen_path_uses_executable_not_user_or_working_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / 'Moved CRM'
            exe = root / 'application' / 'EducationCenterCRM.exe'
            with patch.object(sys, 'frozen', True, create=True), patch.object(sys, 'executable', str(exe)):
                self.assertEqual(default_data_dir(), root.resolve() / 'data')
                self.assertEqual(app_config(default_data_dir())['PORTABLE_ROOT'], root.resolve())
                self.assertIsNone(app_config(Path(temp) / 'isolated')['PORTABLE_ROOT'])

    def test_complete_backup_runs_from_extracted_directory_and_excludes_old_backups(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / 'original'
            application = root / 'application'
            application.mkdir(parents=True)
            (application / 'EducationCenterCRM.exe').write_bytes(b'test executable')
            (application / '_internal').mkdir()
            (application / '_internal' / 'base_library.zip').write_bytes(b'test dependency')
            config = app_config(root / 'data')
            app = create_app({**config, 'TESTING': True, 'PORTABLE_ROOT': root})
            from werkzeug.security import generate_password_hash
            with closing(sqlite3.connect(config['DB_PATH'])) as conn, conn:
                conn.execute("UPDATE app_settings SET organization_name='Portable',setup_completed=1 WHERE id=1")
                conn.execute("INSERT INTO users(full_name,email,password_hash,role) VALUES (?,?,?,'admin')", ('Admin','a@example.test',generate_password_hash('test-admin-password')))
                conn.execute("INSERT INTO students(full_name,email) VALUES ('Student','s@example.test')")
            old = create_backup(app.config)
            restore_backup(app.config, old)  # active data need not be root/crm.db
            complete = create_portable_backup(app.config)
            self.assertEqual(complete.parent, root / 'data' / 'backups')
            moved = Path(temp) / 'other machine'
            with zipfile.ZipFile(complete) as archive:
                names = archive.namelist()
                self.assertIn('application/_internal/base_library.zip', names)
                self.assertIn('Start.cmd', names)
                self.assertFalse(any('backups/' in name or 'generations/' in name or name.endswith('app.lock') for name in names))
                archive.extractall(moved)  # trusted, freshly generated test archive only
            manifest = json.loads((moved / 'portable-manifest.json').read_text())
            for name, checksum in manifest['files'].items():
                self.assertEqual(digest(moved / name), checksum)
            restored = create_app({**app_config(moved / 'data'), 'TESTING':True})
            with closing(sqlite3.connect(restored.config['DB_PATH'])) as conn:
                self.assertEqual(conn.execute('SELECT full_name FROM students').fetchall(), [('Student',)])
            self.assertNotEqual(restored.config['SECRET_KEY'], app.config['SECRET_KEY'])
            self.assertEqual(restored.test_client().get('/').status_code, 200)
            self.assertIn('%~dp0application', (moved / 'Start.cmd').read_text())
