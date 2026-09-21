from contextlib import closing
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from database import init_db
from services import get_dashboard_metrics
from app_factory import create_app


class DashboardRateTests(unittest.TestCase):
    def test_missing_zero_and_complete_are_distinct(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'test.db'
            init_db(path,seed_demo=True)
            with closing(sqlite3.connect(path)) as conn,conn:
                conn.execute('DELETE FROM payments')
                conn.execute('DELETE FROM attendance')
                empty=get_dashboard_metrics(conn)
                self.assertIsNone(empty['collection_rate'])
                self.assertIsNone(empty['attendance_rate'])
                student=conn.execute('SELECT id FROM students LIMIT 1').fetchone()[0]
                lesson=conn.execute('SELECT id FROM lessons LIMIT 1').fetchone()[0]
                conn.execute("INSERT INTO payments(student_id,amount_due,amount_paid,due_date) VALUES (?,10,0,'2026-09-15')",(student,))
                conn.execute("INSERT INTO attendance(lesson_id,student_id,status) VALUES (?,?,'absent')",(lesson,student))
                zero=get_dashboard_metrics(conn)
                self.assertEqual(zero['collection_rate'],0.0)
                self.assertEqual(zero['attendance_rate'],0.0)
                conn.execute('UPDATE payments SET amount_paid=amount_due')
                conn.execute("UPDATE attendance SET status='present'")
                complete=get_dashboard_metrics(conn)
                self.assertEqual(complete['collection_rate'],100.0)
                self.assertEqual(complete['attendance_rate'],100.0)
                conn.execute('DELETE FROM payments')
                conn.execute('DELETE FROM attendance')
            app=create_app({'DB_PATH':path,'DEMO_MODE':True,'TESTING':True})
            client=app.test_client()
            with client.session_transaction() as session:
                session.update(logged_in=True,user_id=1,user_role='admin',auth_version=1)
            html=client.get('/').text
            self.assertEqual(html.count('Noch keine Daten'),2)
            self.assertNotIn('100.0%',html)
