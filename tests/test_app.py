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

import main
from tools.database_cli import backup_database, restore_database


class CRMAppTests(unittest.TestCase):
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

    def login(self, client, role="admin"):
        credentials = {
            "admin": ("admin@bildungszentrum.de", "admin123"),
            "manager": ("manager@bildungszentrum.de", "manager123"),
            "teacher": ("teacher@bildungszentrum.de", "teacher123"),
        }
        email, password = credentials[role]
        return self.post(
            client,
            "/login",
            {"username": email, "password": password},
        )

    def test_health_login_and_dashboard(self):
        with main.app.test_client() as client:
            health = client.get("/health")
            self.assertEqual(health.status_code, 200)
            self.assertEqual(health.get_json()["status"], "ok")

            login_page = client.get("/")
            self.assertIn("Sichere Demo-Anmeldung", login_page.get_data(as_text=True))
            self.assertEqual(self.login(client).status_code, 302)
            dashboard = client.get("/")
            self.assertEqual(dashboard.status_code, 200)
            self.assertIn("Heutiger Unterricht", dashboard.get_data(as_text=True))

    def test_csrf_and_private_pages_are_protected(self):
        with main.app.test_client() as client:
            self.assertEqual(client.get("/students").status_code, 302)
            response = client.post(
                "/students/add",
                data={"full_name": "Blocked", "email": "blocked@example.com"},
            )
            self.assertEqual(response.status_code, 400)
            with sqlite3.connect(self.db_path) as conn:
                count = conn.execute(
                    "SELECT COUNT(*) FROM students WHERE email = ?",
                    ("blocked@example.com",),
                ).fetchone()[0]
            self.assertEqual(count, 0)

    def test_password_hashes_and_seeded_roles(self):
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT password_hash, role FROM users ORDER BY id"
            ).fetchall()
        self.assertEqual({row[1] for row in rows}, {"admin", "manager", "teacher"})
        for password_hash, _ in rows:
            self.assertTrue(password_hash.startswith("scrypt:"))
            self.assertNotEqual(len(password_hash), 64)

    def test_role_permissions_and_teacher_scope(self):
        with sqlite3.connect(self.db_path) as conn:
            course_id = conn.execute("SELECT id FROM courses ORDER BY id LIMIT 1").fetchone()[0]
            other_teacher = conn.execute(
                "SELECT id FROM teachers WHERE user_id IS NULL ORDER BY id LIMIT 1"
            ).fetchone()[0]
            conn.execute(
                "INSERT INTO groups (course_id, teacher_id, name) VALUES (?, ?, ?)",
                (course_id, other_teacher, "Nicht sichtbare Gruppe"),
            )
            conn.commit()

        with main.app.test_client() as client:
            self.login(client, "manager")
            self.assertEqual(client.get("/students").status_code, 200)
            student_id = sqlite3.connect(self.db_path).execute(
                "SELECT id FROM students ORDER BY id LIMIT 1"
            ).fetchone()[0]
            self.assertEqual(
                self.post(client, f"/students/{student_id}/delete").status_code,
                403,
            )

        with main.app.test_client() as client:
            self.login(client, "teacher")
            self.assertEqual(client.get("/students").status_code, 403)
            self.assertEqual(client.get("/payments").status_code, 403)
            groups = client.get("/groups")
            body = groups.get_data(as_text=True)
            self.assertEqual(groups.status_code, 200)
            self.assertIn("Python 2026 - Abendkurs", body)
            self.assertNotIn("Nicht sichtbare Gruppe", body)

    def test_student_crud(self):
        with main.app.test_client() as client:
            self.login(client)
            response = self.post(
                client,
                "/students/add",
                {
                    "full_name": "Ana Test",
                    "email": "ana@example.com",
                    "phone": "123",
                    "guardian_name": "Nino Test",
                },
            )
            self.assertEqual(response.status_code, 302)
            with sqlite3.connect(self.db_path) as conn:
                student_id = conn.execute(
                    "SELECT id FROM students WHERE email = ?",
                    ("ana@example.com",),
                ).fetchone()[0]

            edit_page = client.get(f"/students/{student_id}/edit")
            self.assertIn("Ana Test", edit_page.get_data(as_text=True))
            self.post(
                client,
                f"/students/{student_id}/edit",
                {
                    "name": "Ana Updated",
                    "email": "ana@example.com",
                    "phone": "456",
                    "guardian_name": "Nino Updated",
                    "guardian_phone": "789",
                    "status": "inactive",
                    "notes": "Updated in test",
                },
            )
            detail = client.get(f"/students/{student_id}")
            self.assertIn("Ana Updated", detail.get_data(as_text=True))
            self.assertEqual(client.get(f"/students/{student_id}/delete").status_code, 405)
            self.assertEqual(
                self.post(client, f"/students/{student_id}/delete").status_code,
                302,
            )

    def test_group_attendance_and_partial_payment(self):
        with main.app.test_client() as client:
            self.login(client)
            self.post(
                client,
                "/students/add",
                {"full_name": "Workflow Student", "email": "workflow@example.com"},
            )
            with sqlite3.connect(self.db_path) as conn:
                student_id = conn.execute(
                    "SELECT id FROM students WHERE email = ?",
                    ("workflow@example.com",),
                ).fetchone()[0]
                group_id = conn.execute("SELECT id FROM groups ORDER BY id LIMIT 1").fetchone()[0]

            self.post(client, f"/groups/{group_id}/enroll", {"student_id": student_id})
            self.post(
                client,
                "/lessons/add",
                {
                    "group_id": group_id,
                    "starts_at": "2026-08-10T10:00",
                    "ends_at": "2026-08-10T11:30",
                    "topic": "Regression Test",
                },
            )
            with sqlite3.connect(self.db_path) as conn:
                lesson_id = conn.execute(
                    "SELECT id FROM lessons WHERE topic = ?",
                    ("Regression Test",),
                ).fetchone()[0]

            self.post(
                client,
                f"/lessons/{lesson_id}/attendance/save",
                {f"status_{student_id}": "present", f"note_{student_id}": "On time"},
            )
            self.post(
                client,
                "/payments/add",
                {
                    "student_id": student_id,
                    "group_id": group_id,
                    "amount_due": "250.00",
                    "due_date": "2026-08-20",
                },
            )
            with sqlite3.connect(self.db_path) as conn:
                payment_id = conn.execute(
                    "SELECT id FROM payments WHERE student_id = ? ORDER BY id DESC",
                    (student_id,),
                ).fetchone()[0]
            self.post(
                client,
                "/payments/record",
                {"payment_id": payment_id, "amount_paid": "100", "paid_at": "2026-08-09"},
            )
            with sqlite3.connect(self.db_path) as conn:
                amount, status = conn.execute(
                    "SELECT amount_paid, status FROM payments WHERE id = ?",
                    (payment_id,),
                ).fetchone()
            self.assertEqual(amount, 100)
            self.assertEqual(status, "partial")

    def test_invalid_forms_and_overpayment_are_rejected(self):
        with main.app.test_client() as client:
            self.login(client)
            self.post(
                client,
                "/students/add",
                {"full_name": "Bad Email", "email": "not-an-email"},
            )
            with sqlite3.connect(self.db_path) as conn:
                self.assertEqual(
                    conn.execute(
                        "SELECT COUNT(*) FROM students WHERE full_name = 'Bad Email'"
                    ).fetchone()[0],
                    0,
                )
                payment_id, due, paid = conn.execute(
                    "SELECT id, amount_due, amount_paid FROM payments WHERE status = 'partial' LIMIT 1"
                ).fetchone()
            self.post(
                client,
                "/payments/record",
                {
                    "payment_id": payment_id,
                    "amount_paid": str(due - paid + 1),
                    "paid_at": "2026-08-09",
                },
            )
            with sqlite3.connect(self.db_path) as conn:
                unchanged = conn.execute(
                    "SELECT amount_paid FROM payments WHERE id = ?",
                    (payment_id,),
                ).fetchone()[0]
            self.assertEqual(unchanged, paid)

    def test_csv_exports(self):
        with main.app.test_client() as client:
            self.login(client)
            students = client.get("/exports/students.csv")
            payments = client.get("/exports/payments.csv")
            self.assertEqual(students.status_code, 200)
            self.assertEqual(payments.status_code, 200)
            self.assertIn("education-crm-students.csv", students.headers["Content-Disposition"])
            self.assertIn("Betrag", payments.get_data(as_text=True))

    def test_database_backup_and_restore(self):
        backup_dir = Path(self.tmpdir.name) / "backups"
        backup = backup_database(self.db_path, backup_dir)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM students")
            conn.commit()
        restore_database(backup, self.db_path)
        with sqlite3.connect(self.db_path) as conn:
            self.assertGreater(conn.execute("SELECT COUNT(*) FROM students").fetchone()[0], 0)
            self.assertEqual(conn.execute("PRAGMA quick_check").fetchone()[0], "ok")


if __name__ == "__main__":
    unittest.main()
