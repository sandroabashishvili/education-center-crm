import re
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parents[1]
APP_DIR = APP_ROOT / "app"
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

import main  # noqa: E402


class ProfileSettingsTests(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmpdir.name) / "test.db"
        main.DB_PATH = self.db_path
        main.app.config.update(
            DB_PATH=self.db_path,
            TESTING=True,
            WTF_CSRF_ENABLED=True,
            SECRET_KEY="test-secret",
        )
        main.database.DB_PATH = self.db_path
        main.database.init_db(self.db_path)

    def tearDown(self):
        self.tmpdir.cleanup()

    @staticmethod
    def csrf_token(client, path="/"):
        response = client.get(path)
        match = re.search(
            r'name="csrf_token" value="([^"]+)"',
            response.get_data(as_text=True),
        )
        if not match:
            raise AssertionError(f"No CSRF token on {path}")
        return match.group(1)

    def post(self, client, path, data=None, token_path="/"):
        payload = dict(data or {})
        payload["csrf_token"] = self.csrf_token(client, token_path)
        return client.post(path, data=payload)

    def login(self, client):
        return self.post(
            client,
            "/login",
            {"username": "admin@bildungszentrum.de", "password": "admin123"},
        )

    def test_profile_page_and_personal_data_update(self):
        with main.app.test_client() as client:
            self.login(client)
            page = client.get("/profile")
            self.assertEqual(page.status_code, 200)
            self.assertIn("Mein Profil", page.get_data(as_text=True))

            response = self.post(
                client,
                "/profile",
                {
                    "full_name": "Sandro Admin",
                    "email": "sandro.admin@example.de",
                    "phone": "+49 561 123456",
                },
                token_path="/profile",
            )
            self.assertEqual(response.status_code, 302)

            with sqlite3.connect(self.db_path) as conn:
                row = conn.execute(
                    "SELECT full_name, email, phone FROM users WHERE role = 'admin'"
                ).fetchone()
            self.assertEqual(row, ("Sandro Admin", "sandro.admin@example.de", "+49 561 123456"))

    def test_password_change_requires_current_password(self):
        with main.app.test_client() as client:
            self.login(client)
            wrong = self.post(
                client,
                "/profile/password",
                {
                    "current_password": "wrong-password",
                    "new_password": "new-password-123",
                    "confirm_password": "new-password-123",
                },
                token_path="/profile",
            )
            self.assertEqual(wrong.status_code, 302)

            success = self.post(
                client,
                "/profile/password",
                {
                    "current_password": "admin123",
                    "new_password": "new-password-123",
                    "confirm_password": "new-password-123",
                },
                token_path="/profile",
            )
            self.assertEqual(success.status_code, 302)

            self.post(client, "/logout")
            relogin = self.post(
                client,
                "/login",
                {"username": "admin@bildungszentrum.de", "password": "new-password-123"},
            )
            self.assertEqual(relogin.status_code, 302)
            self.assertEqual(client.get("/").status_code, 200)

    def test_profile_requires_login(self):
        with main.app.test_client() as client:
            self.assertEqual(client.get("/profile").status_code, 302)


if __name__ == "__main__":
    unittest.main()
