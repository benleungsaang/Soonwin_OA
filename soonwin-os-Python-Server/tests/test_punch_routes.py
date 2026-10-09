"""QR device binding isolated tests; temporary SQLite only."""
import os, sys, tempfile, unittest
from datetime import datetime, timedelta
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import jwt, config
from sqlalchemy import event
from sqlalchemy.orm import Session
TEST_DB = tempfile.NamedTemporaryFile(suffix='.db', delete=False); TEST_DB.close()
config.get_database_uri = lambda port=5000: f'sqlite:///{TEST_DB.name}'
from app import create_app
from extensions import db
from app.models.employee import Employee
from app.models.punch_record import PunchRecord
from app.models.device_binding_session import DeviceBindingSession

UA='Mozilla/5.0 (Linux; Android 14; Mobile) AppleWebKit/537.36 Chrome/120.0 Safari/537.36 MicroMessenger/8.0'
FAIL_PUNCH_RECORD_FLUSH = False
def fail_punch_record_flush(session, flush_context, instances):
 if FAIL_PUNCH_RECORD_FLUSH and any(isinstance(obj, PunchRecord) for obj in session.new):
  raise RuntimeError('simulated PunchRecord write failure')
event.listen(Session, 'before_flush', fail_punch_record_flush)
class TestQrBinding(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.app=create_app(); cls.app.config.update(TESTING=True)
  with cls.app.app_context():
   db.create_all(); db.session.add_all([Employee(name='New',emp_id='NEW',dept='T',inner_ip='1',user_role='sales',status='active'),Employee(name='Bound',emp_id='BOUND',dept='T',inner_ip='2',user_role='sales',status='active',device_id='bound'),Employee(name='Other',emp_id='OTHER',dept='T',inner_ip='3',user_role='sales',status='active',device_id='other'),Employee(name='Admin',emp_id='ADMIN',dept='T',inner_ip='4',user_role='admin',status='active')]); db.session.commit()
 @classmethod
 def tearDownClass(cls): os.unlink(TEST_DB.name)
 def setUp(self):
  self.c=self.app.test_client()
  with self.app.app_context():
   DeviceBindingSession.query.delete(); PunchRecord.query.delete(); Employee.query.filter_by(emp_id='NEW').first().device_id=None; Employee.query.filter_by(emp_id='BOUND').first().device_id='bound'; db.session.commit()
 def h(self, emp, device=None, ua=UA):
  t=jwt.encode({'emp_id':emp,'name':'T','user_role':'admin' if emp=='ADMIN' else 'sales','exp':datetime.now()+timedelta(hours=1)},config.Config.JWT_SECRET_KEY,algorithm='HS256')
  h={'Authorization':'Bearer '+t,'User-Agent':ua}
  if device: h['X-Device-ID']=device
  return h
 def create(self, emp='NEW'):
  r=self.c.post('/api/device-binding-sessions',json={'emp_id':emp},headers=self.h('ADMIN')); self.assertEqual(r.status_code,200); return r.get_json()['data']['token']
 def test_admin_generates_and_employee_scans_then_submits_and_approves(self):
  token=self.create(); self.assertEqual(self.c.post(f'/api/device-binding-sessions/{token}/scan',headers=self.h('NEW')).get_json()['data']['status'],'scanned')
  self.assertEqual(self.c.post(f'/api/device-binding-sessions/{token}/submit',headers=self.h('NEW','candidate')).get_json()['data']['status'],'pending')
  self.assertEqual(self.c.post(f'/api/device-binding-sessions/{token}/approve',headers=self.h('ADMIN')).status_code,200)
  self.assertEqual(self.c.get(f'/api/device-binding-sessions/{token}/status',headers=self.h('NEW')).get_json()['data']['status'],'approved')
  with self.app.app_context():
   employee=Employee.query.filter_by(emp_id='NEW').first(); self.assertEqual(employee.device_id,'candidate')
   rows=PunchRecord.query.all(); self.assertEqual(len(rows),1)
   record=rows[0]; self.assertEqual(record.emp_id,'NEW'); self.assertEqual(record.name,'New')
   self.assertEqual(record.punch_type,'设备绑定已批准'); self.assertEqual(record.device_id,'candidate')
   self.assertEqual(record.login_device,'移动设备/Android 14/微信')
   self.assertEqual(record.punch_time,record.last_login_time); self.assertIsNone(record.inner_ip)
  visible=self.c.get('/api/punch-records?page=1&size=20',headers=self.h('ADMIN')).get_json()['data']['list']
  self.assertTrue(any(r['punch_type']=='设备绑定已批准' and r['emp_id']=='NEW' for r in visible))
 def test_replacement_approval_logs_legacy_type_and_duplicate_is_idempotent(self):
  token=self.create('BOUND')
  self.c.post(f'/api/device-binding-sessions/{token}/scan',headers=self.h('BOUND'))
  self.c.post(f'/api/device-binding-sessions/{token}/submit',headers=self.h('BOUND','replacement-device'))
  first=self.c.post(f'/api/device-binding-sessions/{token}/approve',headers=self.h('ADMIN'))
  second=self.c.post(f'/api/device-binding-sessions/{token}/approve',headers=self.h('ADMIN'))
  self.assertEqual(first.status_code,200); self.assertEqual(second.status_code,409)
  with self.app.app_context():
   rows=PunchRecord.query.all(); self.assertEqual(len(rows),1); self.assertEqual(rows[0].punch_type,'设备更换已批准')
   self.assertEqual(rows[0].emp_id,'BOUND'); self.assertEqual(rows[0].device_id,'replacement-device')
 def test_rejection_does_not_write_approval_record(self):
  token=self.create(); self.c.post(f'/api/device-binding-sessions/{token}/scan',headers=self.h('NEW'))
  self.c.post(f'/api/device-binding-sessions/{token}/submit',headers=self.h('NEW','candidate'))
  self.assertEqual(self.c.post(f'/api/device-binding-sessions/{token}/reject',headers=self.h('ADMIN')).status_code,200)
  with self.app.app_context(): self.assertEqual(PunchRecord.query.count(),0); self.assertIsNone(Employee.query.filter_by(emp_id='NEW').first().device_id)
 def test_record_failure_rolls_back_binding_and_approval(self):
  global FAIL_PUNCH_RECORD_FLUSH
  token=self.create(); self.c.post(f'/api/device-binding-sessions/{token}/scan',headers=self.h('NEW'))
  self.c.post(f'/api/device-binding-sessions/{token}/submit',headers=self.h('NEW','candidate'))
  FAIL_PUNCH_RECORD_FLUSH=True
  try: response=self.c.post(f'/api/device-binding-sessions/{token}/approve',headers=self.h('ADMIN'))
  finally: FAIL_PUNCH_RECORD_FLUSH=False
  self.assertEqual(response.status_code,500)
  with self.app.app_context():
   self.assertIsNone(Employee.query.filter_by(emp_id='NEW').first().device_id)
   self.assertEqual(DeviceBindingSession.query.filter_by(token=token).first().status,'pending')
   self.assertEqual(PunchRecord.query.count(),0)
 def test_login_mismatch_and_direct_legacy_request_are_rejected(self):
  token=self.create(); self.assertEqual(self.c.post(f'/api/device-binding-sessions/{token}/scan',headers=self.h('BOUND')).status_code,403)
  self.assertEqual(self.c.post('/api/request-device-change',json={'emp_id':'BOUND','new_device_id':'x'},headers=self.h('BOUND')).status_code,410)
 def test_unbound_cannot_auto_bind_and_correct_bound_can_punch(self):
  r=self.c.post('/api/device-clock-in',json={'emp_id':'NEW','device_id':'candidate'},headers=self.h('NEW','candidate'))
  self.assertEqual(r.status_code,403); self.assertEqual(r.get_json()['code'],403); self.assertEqual(r.get_json()['data']['status'],'device_binding_required')
  with self.app.app_context(): self.assertIsNone(Employee.query.filter_by(emp_id='NEW').first().device_id)
  response=self.c.post('/api/device-clock-in',json={'emp_id':'BOUND','device_id':'bound'},headers=self.h('BOUND','bound'))
  self.assertEqual(response.status_code,200)
  result=response.get_json()['data']
  self.assertEqual(result['emp_id'],'BOUND'); self.assertEqual(result['name'],'Bound')
  self.assertIn(result['punch_type'],('上班打卡','下班打卡','非打卡时间打卡'))
  self.assertTrue(result['punch_time']); self.assertGreater(result['record_id'],0); self.assertEqual(result['status'],'created')
  with self.app.app_context():
   record=PunchRecord.query.filter_by(id=result['record_id']).first()
   self.assertIsNotNone(record); self.assertEqual(record.name,result['name'])
   self.assertEqual(record.punch_type,result['punch_type'])
   self.assertEqual(record.punch_time.strftime('%Y-%m-%d %H:%M:%S'),result['punch_time'])
  visible=self.c.get('/api/punch-records?page=1&size=20',headers=self.h('ADMIN')).get_json()['data']['list']
  self.assertTrue(any(r['id']==result['record_id'] and r['emp_id']=='BOUND' for r in visible))
  with self.app.app_context(): self.assertEqual(PunchRecord.query.count(),1)

 def test_bound_employee_rejects_different_device_without_record(self):
  response=self.c.post('/api/device-clock-in',json={'emp_id':'BOUND','device_id':'new-browser-candidate'},headers=self.h('BOUND','new-browser-candidate'))
  self.assertEqual(response.status_code,403); self.assertEqual(response.get_json()['code'],403)
  self.assertEqual(response.get_json()['data']['status'],'device_binding_required')
  # A correct fallback header cannot override a different body ID.
  fallback=self.c.post('/api/device-clock-in',json={'emp_id':'BOUND','device_id':'another-candidate'},headers=self.h('BOUND','bound'))
  self.assertEqual(fallback.status_code,403); self.assertEqual(fallback.get_json()['data']['status'],'device_binding_required')
  with self.app.app_context():
   self.assertEqual(Employee.query.filter_by(emp_id='BOUND').first().device_id,'bound')
   self.assertEqual(PunchRecord.query.count(),0)

 def test_bound_employee_rejects_missing_and_empty_device_id_without_record(self):
  missing=self.c.post('/api/device-clock-in',json={'emp_id':'BOUND'},headers=self.h('BOUND'))
  empty=self.c.post('/api/device-clock-in',json={'emp_id':'BOUND','device_id':''},headers=self.h('BOUND'))
  for response in (missing,empty):
   self.assertEqual(response.status_code,403); self.assertEqual(response.get_json()['code'],403)
   self.assertEqual(response.get_json()['data']['status'],'device_binding_required')
  with self.app.app_context():
   self.assertEqual(Employee.query.filter_by(emp_id='BOUND').first().device_id,'bound')
   self.assertEqual(PunchRecord.query.count(),0)
 def test_expired_old_token_repeat_and_occupied_device(self):
  old=self.create(); new=self.create(); self.assertEqual(self.c.post(f'/api/device-binding-sessions/{old}/scan',headers=self.h('NEW')).status_code,410)
  self.assertEqual(self.c.post(f'/api/device-binding-sessions/{new}/scan',headers=self.h('NEW')).status_code,200)
  self.assertEqual(self.c.post(f'/api/device-binding-sessions/{new}/submit',headers=self.h('NEW','other')).status_code,409)
  with self.app.app_context(): DeviceBindingSession.query.filter_by(token=new).first().expires_at=datetime.now()-timedelta(seconds=1); db.session.commit()
  self.assertEqual(self.c.get(f'/api/device-binding-sessions/{new}/status',headers=self.h('NEW')).get_json()['data']['status'],'scanned')
 def test_reject_admin_scope_and_pc_block(self):
  token=self.create(); self.c.post(f'/api/device-binding-sessions/{token}/scan',headers=self.h('NEW')); self.c.post(f'/api/device-binding-sessions/{token}/submit',headers=self.h('NEW','candidate'))
  self.assertEqual(self.c.post(f'/api/device-binding-sessions/{token}/approve',headers=self.h('NEW')).status_code,403)
  self.assertEqual(self.c.post(f'/api/device-binding-sessions/{token}/reject',headers=self.h('ADMIN')).status_code,200)
  self.assertEqual(self.c.get(f'/api/device-binding-sessions/{token}/status',headers=self.h('NEW')).get_json()['data']['status'],'rejected')
  self.assertEqual(self.c.post('/api/device-clock-in',json={'emp_id':'BOUND'},headers=self.h('BOUND','bound','Mozilla/5.0 (Windows NT 10.0) Chrome/120')).status_code,403)
if __name__=='__main__': unittest.main()
