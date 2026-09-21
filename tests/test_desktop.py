"""Desktop foundations: isolated data, bootstrap, migration and local transport."""
from contextlib import closing
from pathlib import Path
import re
import io
import sqlite3
import sys
import tempfile
import unittest
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'app'))
from app_factory import create_app
from database import init_db, DatabaseVersionError
from desktop.runtime import app_config, instance_lock
from desktop.server import LocalServer


class DesktopTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.config = app_config(self.root)
        self.app = create_app({**self.config, 'TESTING': True})
        self.client = self.app.test_client()

    def tearDown(self):
        self.tmp.cleanup()

    def sql(self, query, values=()):
        with closing(sqlite3.connect(self.config['DB_PATH'])) as conn, conn:
            return conn.execute(query, values).fetchall()

    def setup_admin(self):
        page = self.client.get('/setup').text
        token = re.search(r'name="csrf_token" value="([^"]+)"', page)[1]
        return self.client.post('/setup', data={'csrf_token': token,
            'organization_name': 'Test Zentrum', 'full_name': 'Test Admin',
            'email': 'admin@example.test', 'password': 'long-test-password',
            'confirm_password': 'long-test-password'})

    def test_empty_setup_is_once_only_and_password_hashed(self):
        self.assertEqual(self.sql('SELECT COUNT(*) FROM users')[0][0], 0)
        self.assertEqual(self.sql('SELECT COUNT(*) FROM students')[0][0], 0)
        self.assertTrue(self.client.get('/').location.endswith('/setup'))
        self.assertEqual(self.client.post('/setup', data={}).status_code, 400)
        self.assertEqual(self.setup_admin().status_code, 302)
        self.assertNotEqual(self.sql('SELECT password_hash FROM users')[0][0], 'long-test-password')
        self.assertEqual(self.sql('SELECT organization_name FROM app_settings')[0][0], 'Test Zentrum')
        self.assertEqual(self.client.get('/setup').status_code, 404)
        self.sql('DELETE FROM users')
        self.assertEqual(self.client.get('/setup').status_code, 404)

    def test_customer_login_never_seeds_demo_records(self):
        self.setup_admin()
        token = re.search(r'name="csrf_token" value="([^"]+)"', self.client.get('/').text)[1]
        response = self.client.post('/login', data={'csrf_token': token,
            'username': 'admin@example.test', 'password': 'long-test-password'})
        self.assertEqual(response.status_code, 302)
        for path in ('/', '/students', '/groups'):
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200)
        self.assertEqual(self.sql('SELECT COUNT(*) FROM students')[0][0], 0)
        self.assertEqual(self.sql('SELECT COUNT(*) FROM users')[0][0], 1)
        self.assertNotIn('Demo-Konten', self.client.get('/').text)
        # A second app instance uses its own database and setup state.
        other = create_app({**app_config(self.root / 'other'), 'TESTING': True})
        self.assertTrue(other.test_client().get('/').location.endswith('/setup'))

    def test_avatar_uses_private_data_folder_and_owner_route(self):
        self.setup_admin()
        with self.client.session_transaction() as session:
            session.update(logged_in=True, auth_version=1, storage_epoch=self.app.config["STORAGE_EPOCH"], user_id=1, user_role='admin')
        token = re.search(r'name="csrf_token" value="([^"]+)"', self.client.get('/profile').text)[1]
        payload = b'\x89PNG\r\n\x1a\n'
        response = self.client.post('/profile', data={'csrf_token': token,
            'full_name': 'Test Admin', 'email': 'admin@example.test',
            'avatar': (io.BytesIO(payload), 'profile.png')})
        self.assertEqual(response.status_code, 302)
        filename = self.sql('SELECT avatar_filename FROM users')[0][0]
        self.assertEqual((self.config['UPLOAD_DIR'] / filename).read_bytes(), payload)
        with self.client.get('/profile/avatar/' + filename) as response:
            self.assertEqual(response.data, payload)
            self.assertEqual(response.headers['Cache-Control'], 'private, no-store')
        self.assertEqual(self.client.get('/profile/avatar/other.png').status_code, 404)
        self.assertEqual(self.app.test_client().get('/profile/avatar/' + filename).status_code, 302)

    def test_unsupported_or_corrupt_database_is_not_replaced(self):
        for name, content in [('newer.db', None), ('broken.db', b'not a sqlite database')]:
            path = self.root / name
            if content:
                path.write_bytes(content)
            else:
                with closing(sqlite3.connect(path)) as conn, conn:
                    conn.execute('PRAGMA user_version=99')
                    conn.execute('CREATE TABLE precious (value TEXT)')
            before = path.read_bytes()
            with self.assertRaises((DatabaseVersionError, sqlite3.DatabaseError)):
                init_db(path, seed_demo=False)
            self.assertEqual(path.read_bytes(), before)

    def test_v1_migration_keeps_data_and_creates_backup(self):
        self.setup_admin()
        self.sql('DROP TABLE app_settings')
        self.sql('PRAGMA user_version=1')
        init_db(self.config['DB_PATH'], seed_demo=False)
        self.assertEqual(self.sql('SELECT email FROM users')[0][0], 'admin@example.test')
        backups = list((self.root / 'backups').glob('pre-migration-*.db'))
        self.assertEqual(len(backups), 1)
        with closing(sqlite3.connect(backups[0])) as conn:
            self.assertEqual(conn.execute('PRAGMA user_version').fetchone()[0], 1)
        self.assertEqual(self.sql('PRAGMA user_version')[0][0], 3)

    def test_orphan_teacher_and_disabled_session_denied(self):
        self.setup_admin()
        self.sql("UPDATE users SET role='teacher'")
        with self.client.session_transaction() as session:
            session.update(logged_in=True, auth_version=1, storage_epoch=self.app.config["STORAGE_EPOCH"], user_id=1, user_role='teacher')
        self.assertEqual(self.client.get('/groups').status_code, 403)
        self.sql("UPDATE users SET role='admin',status='inactive'")
        with self.client.session_transaction() as session:
            session.update(logged_in=True, auth_version=1, storage_epoch=self.app.config["STORAGE_EPOCH"], user_id=1, user_role='admin')
        self.assertEqual(self.client.get('/').status_code, 403)

    def test_persistent_secret_and_exclusive_released_lock(self):
        self.assertEqual(app_config(self.root)['SECRET_KEY'], self.config['SECRET_KEY'])
        with instance_lock(self.root):
            with self.assertRaises(RuntimeError):
                with instance_lock(self.root):
                    pass
        with instance_lock(self.root):
            pass

    def test_local_transport_requires_token_and_stops(self):
        server = LocalServer(self.app)
        try:
            server.start()
            with self.assertRaises(HTTPError) as result:
                urlopen(server.base_url + '/health')
            self.assertEqual(result.exception.code, 403)
            headers = {'Cookie': 'crm_desktop_access=' + server.token}
            with urlopen(Request(server.base_url + '/health', headers=headers)) as response:
                self.assertEqual(response.status, 200)
            with self.assertRaises(HTTPError):
                urlopen(Request(server.base_url + '/health', headers={**headers, 'Origin': 'https://example.com'}))
        finally:
            server.close()
        self.assertFalse(server.thread.is_alive())
        with self.assertRaises(URLError):
            urlopen(server.base_url + '/health', timeout=.5)
