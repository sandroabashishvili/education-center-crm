from contextlib import closing
import io
import json
from pathlib import Path
import re
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

sys.path.insert(0,str(Path(__file__).resolve().parents[1] / 'app'))
from app_factory import create_app
from desktop.runtime import app_config
from desktop.storage import create_backup, restore_backup, unpack_backup, BackupError

PASSWORD='initial-admin-password'


class AccountBackupTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name)
        self.app=create_app({**app_config(self.root),'TESTING':True})
        self.client=self.app.test_client()
        self.post('/setup',{'organization_name':'Test Zentrum','full_name':'Admin','email':'admin@example.test','password':PASSWORD,'confirm_password':PASSWORD},token_path='/setup')
        self.login(self.client,'admin@example.test',PASSWORD)

    def tearDown(self):
        self.temp.cleanup()

    def sql(self,query,values=()):
        with closing(sqlite3.connect(self.app.config['DB_PATH'])) as conn,conn:
            return conn.execute(query,values).fetchall()

    def post(self,path,data=None,client=None,token_path='/admin/accounts'):
        client=client or self.client
        response=client.get(token_path,follow_redirects=True)
        token=re.search(r'name="csrf_token" value="([^"]+)"',response.text)[1]
        return client.post(path,data={**(data or {}),'csrf_token':token},buffered=True)

    def login(self,client,email,password):
        return self.post('/login',{'username':email,'password':password},client=client,token_path='/')

    def create(self,email='manager@example.test',role='manager',teacher_id=''):
        return self.post('/admin/accounts',{'full_name':'New User','email':email,'role':role,'teacher_id':teacher_id,'password':'new-user-password','confirm_password':'new-user-password'})

    def test_create_forced_change_and_disable_revokes_session(self):
        self.assertEqual(self.create().status_code,302)
        self.assertEqual(self.create(email='MANAGER@example.test').status_code,400)
        manager=self.app.test_client()
        self.login(manager,'manager@example.test','new-user-password')
        self.assertIn('/profile',manager.get('/students').location)
        self.post('/profile/password',{'current_password':'new-user-password','new_password':'changed-user-password','confirm_password':'changed-user-password'},client=manager,token_path='/profile')
        self.assertEqual(manager.get('/students').status_code,200)
        self.assertEqual(manager.get('/admin/accounts').status_code,403)
        self.assertEqual(manager.get('/admin/backups').status_code,403)
        self.assertEqual(self.post('/admin/accounts/2/status',{'status':'inactive'}).status_code,302)
        self.assertEqual(manager.get('/students').status_code,403)
        self.post('/admin/accounts/2/status',{'status':'active'})
        self.assertEqual(manager.get('/students').status_code,302)

    def test_teacher_requires_unique_active_link_and_can_relink(self):
        self.sql("INSERT INTO teachers(full_name,email) VALUES ('Teacher One','one@example.test')")
        self.sql("INSERT INTO teachers(full_name,email) VALUES ('Teacher Two','two@example.test')")
        self.assertEqual(self.create(role='teacher').status_code,400)
        self.assertEqual(self.create(role='teacher',teacher_id=1).status_code,302)
        self.assertEqual(self.create(email='other@example.test',role='teacher',teacher_id=1).status_code,400)
        self.assertEqual(self.post('/admin/accounts/2/teacher',{'teacher_id':2}).status_code,302)
        self.assertEqual(self.sql('SELECT user_id FROM teachers ORDER BY id'),[(None,),(2,)])
        self.assertEqual(self.post('/admin/accounts/1/status',{'status':'inactive'}).status_code,400)
        self.assertEqual(self.sql('SELECT status FROM users WHERE id=1')[0][0],'active')

    def test_role_change_requires_teacher_link_and_keeps_admin(self):
        self.create()
        self.assertEqual(self.post('/admin/accounts/1/role',{'role':'manager'}).status_code,400)
        self.assertEqual(self.post('/admin/accounts/2/role',{'role':'teacher'}).status_code,400)
        self.sql("INSERT INTO teachers(full_name,email) VALUES ('Teacher','teacher@example.test')")
        self.assertEqual(self.post('/admin/accounts/2/role',{'role':'teacher','teacher_id':1}).status_code,302)
        self.assertEqual(self.sql('SELECT user_id FROM teachers'),[(2,)])
        self.assertEqual(self.post('/admin/accounts/2/role',{'role':'manager'}).status_code,302)
        self.assertEqual(self.sql('SELECT user_id FROM teachers'),[(None,)])

    def test_password_reset_invalidates_other_sessions(self):
        self.create()
        user=self.app.test_client()
        self.login(user,'manager@example.test','new-user-password')
        bad=self.post('/admin/accounts/2/password',{'current_password':'wrong','password':'replacement-password','confirm_password':'replacement-password'})
        self.assertEqual(bad.status_code,400)
        self.assertEqual(self.post('/admin/accounts/2/password',{'current_password':PASSWORD,'password':'replacement-password','confirm_password':'replacement-password'}).status_code,302)
        self.assertEqual(user.get('/profile').status_code,403)

    def test_recovery_code_is_single_use_and_revokes_old_admin_session(self):
        response=self.post('/admin/accounts/recovery-code',{'current_password':PASSWORD})
        code=re.search(r'<code[^>]*>([^<]+)</code>',response.text)[1]
        self.assertNotIn(code,self.sql('SELECT recovery_hash FROM app_settings')[0][0])
        anonymous=self.app.test_client()
        data={'email':'admin@example.test','recovery_code':code,'password':'recovered-admin-password','confirm_password':'recovered-admin-password'}
        self.assertEqual(self.post('/recover',data,client=anonymous,token_path='/recover').status_code,302)
        self.assertEqual(self.client.get('/admin/accounts').status_code,403)
        self.assertEqual(self.post('/recover',data,client=anonymous,token_path='/recover').status_code,400)
        self.login(anonymous,'admin@example.test','recovered-admin-password')
        self.assertEqual(anonymous.get('/admin/accounts').status_code,200)

    def test_full_backup_preview_restore_and_restart(self):
        avatar=self.app.config['UPLOAD_DIR'] / 'user-1-test.png'
        avatar.write_bytes(b'original image')
        self.sql("UPDATE users SET avatar_filename='user-1-test.png' WHERE id=1")
        self.sql("INSERT INTO students(full_name,email) VALUES ('Before','before@example.test')")
        self.assertEqual(self.post('/admin/backups').status_code,302)
        archive=next((self.root/'backups').glob('crm-*.zip'))
        original_db=self.app.config['DB_PATH']
        original_key=self.app.config['SECRET_KEY']
        original_epoch=self.app.config['STORAGE_EPOCH']
        self.sql("INSERT INTO students(full_name,email) VALUES ('After','after@example.test')")
        avatar.write_bytes(b'changed image')
        response=self.post('/admin/backups/preview',{'backup':(io.BytesIO(archive.read_bytes()),'backup.zip')})
        self.assertEqual(response.status_code,200)
        self.assertIn('Test Zentrum',response.text)
        with self.client.session_transaction() as session:
            token=session['restore_token']
        self.assertEqual(len(self.sql('SELECT id FROM students')),2)
        rejected=self.post('/admin/backups/restore',{'token':token,'confirm':'yes','current_password':'wrong'})
        self.assertEqual(rejected.status_code,400)
        restored=self.post('/admin/backups/restore',{'token':token,'confirm':'yes','current_password':PASSWORD})
        self.assertEqual(restored.status_code,302,restored.text)
        self.assertNotEqual(self.app.config['SECRET_KEY'],original_key)
        self.assertEqual(self.sql('SELECT full_name FROM students'),[('Before',)])
        self.assertEqual((self.app.config['UPLOAD_DIR']/avatar.name).read_bytes(),b'original image')
        self.assertTrue(original_db.exists())
        self.assertEqual(len(list((self.root/'backups').glob('crm-*.zip'))),2)
        restarted=create_app({**app_config(self.root),'TESTING':True})
        self.assertEqual(restarted.config['DB_PATH'],self.app.config['DB_PATH'])
        self.assertEqual(restarted.config['SECRET_KEY'],self.app.config['SECRET_KEY'])
        self.assertEqual(self.client.get('/admin/accounts').status_code,302)
        with self.client.session_transaction() as session:
            session.update(logged_in=True,user_id=1,user_role='admin',auth_version=1,storage_epoch=original_epoch)
        self.assertEqual(self.client.get('/admin/accounts').status_code,403)

    def test_bad_archives_and_activation_failure_preserve_active_data(self):
        good=create_backup(self.app.config)
        for kind in ('traversal','checksum'):
            bad=self.root/(kind+'.zip')
            with zipfile.ZipFile(good) as source,zipfile.ZipFile(bad,'w') as target:
                for item in source.infolist():
                    content=source.read(item.filename)
                    if kind=='checksum' and item.filename=='crm.db':
                        content=b'broken'
                    target.writestr(item.filename,content)
                if kind=='traversal':
                    target.writestr('../outside.txt',b'bad')
            with self.assertRaises(BackupError):
                unpack_backup(bad,self.root/('stage-'+kind))
        before=self.app.config['DB_PATH']
        with patch('desktop.storage.durable_json',side_effect=OSError('simulated disk failure')):
            with self.assertRaises(OSError):
                restore_backup(self.app.config,good)
        self.assertEqual(self.app.config['DB_PATH'],before)
        self.assertFalse((self.root/'current.json').exists())
        self.assertEqual(self.sql('SELECT email FROM users'),[('admin@example.test',)])
        self.assertFalse((self.root/'outside.txt').exists())

    def test_missing_avatar_does_not_claim_complete_backup(self):
        self.sql("UPDATE users SET avatar_filename='missing.png' WHERE id=1")
        with self.assertRaises(BackupError):
            create_backup(self.app.config)
        self.assertEqual(list((self.root/'backups').glob('*.zip')),[])

    def test_delete_account_preserves_teacher_and_revokes_session(self):
        self.sql("INSERT INTO teachers(full_name,email) VALUES ('Teacher','teacher@example.test')")
        self.create(role='teacher',teacher_id=1)
        other=self.app.test_client()
        self.login(other,'manager@example.test','new-user-password')
        data={'confirmation':'manager@example.test','current_password':PASSWORD}
        self.assertEqual(self.post('/admin/accounts/2/delete',{**data,'current_password':'wrong'}).status_code,400)
        self.assertEqual(self.post('/admin/accounts/1/delete',data).status_code,400)
        self.assertEqual(self.post('/admin/accounts/2/delete',data).status_code,302)
        self.assertEqual(self.sql('SELECT user_id FROM teachers'),[(None,)])
        self.assertEqual(self.sql('SELECT id FROM users'),[(1,)])
        self.assertEqual(other.get('/profile').status_code,403)
        self.assertEqual(self.post('/admin/accounts/2/delete',data).status_code,404)

    def test_reset_requires_admin_password_confirmation_and_csrf(self):
        self.assertEqual(self.client.post('/admin/reset',data={'confirmation':'ALLES LÖSCHEN','current_password':PASSWORD}).status_code,400)
        self.assertEqual(self.post('/admin/reset',{'confirmation':'ALLES LÖSCHEN','current_password':'wrong'}).status_code,400)
        self.assertEqual(self.post('/admin/reset',{'confirmation':'wrong','current_password':PASSWORD}).status_code,400)
        self.assertFalse((self.root/'reset-pending.json').exists())
        self.create()
        self.sql('UPDATE users SET must_change_password=0 WHERE id=2')
        other=self.app.test_client()
        self.login(other,'manager@example.test','new-user-password')
        self.assertEqual(other.get('/admin/reset').status_code,403)
        self.assertEqual(self.post('/admin/reset',{'confirmation':'ALLES LÖSCHEN','current_password':'new-user-password'},client=other,token_path='/profile').status_code,403)
        self.assertEqual(self.post('/admin/accounts/1/delete',{'confirmation':'admin@example.test','current_password':'new-user-password'},client=other,token_path='/profile').status_code,403)

    def test_reset_erases_generations_and_backups_then_reopens_setup(self):
        old_key=self.app.config['SECRET_KEY']
        archive=create_backup(self.app.config)
        restore_backup(self.app.config,archive)
        self.login(self.client,'admin@example.test',PASSWORD)
        (self.root/'unrelated.txt').write_text('keep')
        response=self.post('/admin/reset',{'confirmation':'ALLES LÖSCHEN','current_password':PASSWORD})
        self.assertEqual(response.status_code,302)
        self.assertTrue((self.root/'reset-pending.json').exists())
        self.assertTrue(archive.exists())  # no deletion while the server is running
        self.assertEqual(self.client.get('/students').status_code,503)
        self.assertEqual(self.client.post('/setup').status_code,503)
        restarted=create_app({**app_config(self.root),'TESTING':True})
        self.assertNotEqual(restarted.config['SECRET_KEY'],old_key)
        self.assertEqual(list((self.root/'backups').iterdir()),[])
        self.assertFalse((self.root/'generations').exists())
        self.assertFalse((self.root/'current.json').exists())
        self.assertFalse((self.root/'reset-pending.json').exists())
        self.assertEqual((self.root/'unrelated.txt').read_text(),'keep')
        with closing(sqlite3.connect(restarted.config['DB_PATH'])) as conn:
            self.assertEqual(conn.execute('SELECT count(*) FROM users').fetchone()[0],0)
        fresh=restarted.test_client()
        self.assertEqual(fresh.get('/setup').status_code,200)
        self.assertEqual(self.post('/setup',{'organization_name':'Fresh','full_name':'New Admin','email':'new@example.test','password':PASSWORD,'confirm_password':PASSWORD},client=fresh,token_path='/setup').status_code,302)
        self.assertEqual(self.login(fresh,'new@example.test',PASSWORD).status_code,302)
        self.assertEqual(fresh.get('/admin/accounts').status_code,200)

    def test_reset_failure_keeps_marker_and_retries_before_initialization(self):
        from desktop.reset import schedule_reset
        schedule_reset(self.root)
        with patch('desktop.reset.shutil.rmtree',side_effect=PermissionError('locked')):
            with self.assertRaises(PermissionError):
                app_config(self.root)
        self.assertTrue((self.root/'reset-pending.json').exists())
        config=app_config(self.root)
        self.assertFalse(Path(config['DB_PATH']).exists())
        self.assertFalse((self.root/'reset-pending.json').exists())
