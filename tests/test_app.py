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


class CRMAppTests(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmpdir.name) / "test.db"
        main.DB_PATH = self.db_path
        main.app.config.update(DB_PATH=self.db_path, TESTING=True)
        main.database.DB_PATH = self.db_path
        main.database.init_db(self.db_path)

    def tearDown(self):
        self.tmpdir.cleanup()

    @staticmethod
    def login(client):
        return client.post(
            "/login",
            data={"username": "admin@education.ge", "password": "admin123"},
        )

    def test_health_and_dashboard(self):
        with main.app.test_client() as client:
            health = client.get("/health")
            self.assertEqual(health.status_code, 200)
            self.assertEqual(health.get_json()["status"], "ok")

            dashboard = client.get("/")
            self.assertEqual(dashboard.status_code, 200)
            self.assertIn("Education Center CRM", dashboard.get_data(as_text=True))
            self.assertIn("დღევანდელი გაკვეთილი", dashboard.get_data(as_text=True))

    def test_write_routes_require_login(self):
        with main.app.test_client() as client:
            response = client.post(
                "/students/add",
                data={"full_name": "Unauthorized", "email": "blocked@example.com"},
            )
            self.assertEqual(response.status_code, 302)
            with sqlite3.connect(self.db_path) as conn:
                count = conn.execute(
                    "SELECT COUNT(*) FROM students WHERE email = ?",
                    ("blocked@example.com",),
                ).fetchone()[0]
            self.assertEqual(count, 0)

    def test_login_add_edit_and_delete_student(self):
        with main.app.test_client() as client:
            self.login(client)
            response = client.post(
                "/students/add",
                data={
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
            self.assertEqual(edit_page.status_code, 200)
            self.assertIn("Ana Test", edit_page.get_data(as_text=True))

            client.post(
                f"/students/{student_id}/edit",
                data={
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
            self.assertIn("Updated in test", detail.get_data(as_text=True))

            delete_get = client.get(f"/students/{student_id}/delete")
            self.assertEqual(delete_get.status_code, 405)
            delete_post = client.post(f"/students/{student_id}/delete")
            self.assertEqual(delete_post.status_code, 302)

    def test_group_attendance_and_payment_workflows(self):
        with main.app.test_client() as client:
            self.login(client)
            client.post(
                "/students/add",
                data={"full_name": "Workflow Student", "email": "workflow@example.com"},
            )
            with sqlite3.connect(self.db_path) as conn:
                student_id = conn.execute(
                    "SELECT id FROM students WHERE email = ?",
                    ("workflow@example.com",),
                ).fetchone()[0]
                group_id = conn.execute("SELECT id FROM groups ORDER BY id LIMIT 1").fetchone()[0]

            client.post(f"/groups/{group_id}/enroll", data={"student_id": student_id})
            lesson_response = client.post(
                "/lessons/add",
                data={
                    "group_id": group_id,
                    "starts_at": "2026-07-27T10:00",
                    "ends_at": "2026-07-27T11:30",
                    "topic": "Regression Test",
                },
            )
            self.assertEqual(lesson_response.status_code, 302)

            with sqlite3.connect(self.db_path) as conn:
                lesson_id = conn.execute(
                    "SELECT id FROM lessons WHERE topic = ?",
                    ("Regression Test",),
                ).fetchone()[0]

            attendance = client.post(
                f"/lessons/{lesson_id}/attendance/save",
                data={f"status_{student_id}": "present", f"note_{student_id}": "On time"},
            )
            self.assertEqual(attendance.status_code, 302)

            payment = client.post(
                "/payments/add",
                data={
                    "student_id": student_id,
                    "group_id": group_id,
                    "amount_due": "250.00",
                    "due_date": "2020-01-01",
                },
            )
            self.assertEqual(payment.status_code, 302)
            overdue_page = client.get("/payments?status=overdue")
            self.assertIn("Workflow Student", overdue_page.get_data(as_text=True))

    def test_csv_exports(self):
        with main.app.test_client() as client:
            self.login(client)
            students = client.get("/exports/students.csv")
            self.assertEqual(students.status_code, 200)
            self.assertIn("education-crm-students.csv", students.headers["Content-Disposition"])
            self.assertIn("Full name", students.get_data(as_text=True))

            payments = client.get("/exports/payments.csv")
            self.assertEqual(payments.status_code, 200)
            self.assertIn("education-crm-payments.csv", payments.headers["Content-Disposition"])
            self.assertIn("Amount due", payments.get_data(as_text=True))


if __name__ == "__main__":
    unittest.main()
