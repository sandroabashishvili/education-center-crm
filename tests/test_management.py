import re
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1] / "app"
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))
import main  # noqa: E402


class ManagementTests(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmpdir.name) / "test.db"
        main.DB_PATH = self.db_path
        main.app.config.update(DB_PATH=self.db_path, TESTING=True, WTF_CSRF_ENABLED=True, SECRET_KEY="test-secret")
        main.database.DB_PATH = self.db_path
        main.database.init_db(self.db_path)

    def tearDown(self):
        self.tmpdir.cleanup()

    def token(self, client, path="/"):
        html = client.get(path).get_data(as_text=True)
        match = re.search(r'name="csrf_token" value="([^"]+)"', html)
        self.assertIsNotNone(match)
        return match.group(1)

    def login(self, client, role="admin"):
        credentials = {
            "admin": ("admin@bildungszentrum.de", "admin123"),
            "manager": ("manager@bildungszentrum.de", "manager123"),
        }
        email, password = credentials[role]
        token = self.token(client)
        return client.post("/login", data={"username": email, "password": password, "csrf_token": token})

    def test_course_detail_and_edit(self):
        with main.app.test_client() as client:
            self.login(client)
            self.assertEqual(client.get("/courses/1").status_code, 200)
            token = self.token(client, "/courses/1/edit")
            response = client.post("/courses/1/edit", data={"title": "Python Pro", "category": "Programmierung", "default_fee": "399", "description": "Aktualisiert", "status": "active", "csrf_token": token})
            self.assertEqual(response.status_code, 302)
            with sqlite3.connect(self.db_path) as conn:
                self.assertEqual(conn.execute("SELECT title FROM courses WHERE id=1").fetchone()[0], "Python Pro")

    def test_teacher_detail_edit_and_delete(self):
        with main.app.test_client() as client:
            self.login(client)
            self.assertEqual(client.get("/teachers/1").status_code, 200)
            token = self.token(client, "/teachers/1/edit")
            response = client.post("/teachers/1/edit", data={"full_name": "Daniel Weber Neu", "email": "teacher@bildungszentrum.de", "phone": "+49 1", "specialization": "Python", "status": "active", "csrf_token": token})
            self.assertEqual(response.status_code, 302)
            with sqlite3.connect(self.db_path) as conn:
                self.assertEqual(conn.execute("SELECT full_name FROM teachers WHERE id=1").fetchone()[0], "Daniel Weber Neu")

    def test_group_detail_edit_and_delete(self):
        with main.app.test_client() as client:
            self.login(client)
            self.assertEqual(client.get("/groups/1").status_code, 200)
            self.assertEqual(client.get("/groups/1/edit").status_code, 200)
            token = self.token(client, "/groups/1/edit")
            response = client.post(
                "/groups/1/edit",
                data={
                    "course_id": "1",
                    "teacher_id": "1",
                    "name": "Python Abendgruppe Neu",
                    "capacity": "18",
                    "start_date": "2026-08-01",
                    "end_date": "2026-12-20",
                    "schedule_description": "Montag, 19:00 Uhr",
                    "status": "active",
                    "csrf_token": token,
                },
            )
            self.assertEqual(response.status_code, 302)
            with sqlite3.connect(self.db_path) as conn:
                row = conn.execute("SELECT name, capacity FROM groups WHERE id=1").fetchone()
                self.assertEqual(row, ("Python Abendgruppe Neu", 18))

            with sqlite3.connect(self.db_path) as conn:
                conn.execute("INSERT INTO groups (course_id, teacher_id, name, capacity, status) VALUES (1, 1, 'Delete me', 10, 'active')")
                group_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
                conn.commit()
            token = self.token(client, "/groups")
            self.assertEqual(client.post(f"/groups/{group_id}/delete", data={"csrf_token": token}).status_code, 302)
            with sqlite3.connect(self.db_path) as conn:
                self.assertIsNone(conn.execute("SELECT id FROM groups WHERE id = ?", (group_id,)).fetchone())

    def test_manager_cannot_delete_teacher_or_group(self):
        with main.app.test_client() as client:
            self.login(client, "manager")
            token = self.token(client, "/teachers")
            self.assertEqual(client.post("/teachers/1/delete", data={"csrf_token": token}).status_code, 403)
            token = self.token(client, "/groups")
            self.assertEqual(client.post("/groups/1/delete", data={"csrf_token": token}).status_code, 403)


if __name__ == "__main__":
    unittest.main()
