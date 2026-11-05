"""Isolated NAS mobile upload API tests; all writes target a temporary local directory."""
import os
import queue
import shutil
import sys
import tempfile
import time
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import jwt
import config

TEST_DB = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
TEST_DB.close()
config.get_database_uri = lambda port=5000: f'sqlite:///{TEST_DB.name}'
from app import create_app
from extensions import db
from app.models.employee import Employee
from app.models.simple_permission import SimpleRole, SimpleRolePermission
from app.models.system_config import SystemConfig
from app.routes import nas_upload_routes
from app.utils.nas_upload_utils import MAX_FILE_SIZE
from app.utils.nas_upload_utils import NasUnavailable, check_writable, ensure_mount
from app.utils import nas_upload_utils


class NasUploadApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config.update(TESTING=True, NAS_UPLOAD_SIGNING_KEY='t' * 48)
        cls.temp_dir = tempfile.TemporaryDirectory()
        cls.dir_fd = os.open(cls.temp_dir.name, os.O_RDONLY | os.O_DIRECTORY)
        cls.mount_patch = patch.object(nas_upload_routes, 'open_target_dir', lambda _path: os.dup(cls.dir_fd))
        cls.check_patch = patch.object(nas_upload_routes, 'check_writable', lambda _path: None)
        cls.mount_patch.start(); cls.check_patch.start()
        with cls.app.app_context():
            db.create_all()
            db.session.add_all([
                Employee(name='Sales', emp_id='NAS_SALES', dept='T', inner_ip='1', user_role='sales', status='active'),
                Employee(name='Admin', emp_id='NAS_ADMIN', dept='T', inner_ip='2', user_role='admin', status='active'),
                Employee(name='Unassigned', emp_id='NAS_UNASSIGNED', dept='T', inner_ip='3', user_role='user', status='active'),
            ])
            sales_role = SimpleRole(name='sales', remark='test sales role')
            db.session.add(sales_role)
            db.session.flush()
            db.session.add(SimpleRolePermission(role_id=sales_role.id, route_name='nas_mobile_upload_manage'))
            db.session.commit()

    @classmethod
    def tearDownClass(cls):
        nas_upload_routes._publish_queue.join()
        cls.mount_patch.stop(); cls.check_patch.stop()
        os.close(cls.dir_fd)
        cls.temp_dir.cleanup()
        os.unlink(TEST_DB.name)

    def setUp(self):
        nas_upload_routes._publish_queue.join()
        self.client = self.app.test_client()
        with self.app.app_context():
            SystemConfig.query.filter_by(key='nas_mobile_upload_dir').delete()
            db.session.commit()
        for entry in os.listdir(self.temp_dir.name):
            path = os.path.join(self.temp_dir.name, entry)
            if os.path.isdir(path) and not os.path.islink(path):
                shutil.rmtree(path)
            else:
                os.unlink(path)

    def task_state_path(self, upload_id, suffix='json'):
        return os.path.join(self.temp_dir.name, nas_upload_routes.STATE_DIR_NAME,
                            f'.oa-upload-{upload_id}.{suffix}')

    def auth(self, emp_id, role):
        token = jwt.encode({'emp_id': emp_id, 'user_role': role,
                            'exp': datetime.now() + timedelta(hours=1)},
                           config.Config.JWT_SECRET_KEY, algorithm='HS256')
        return {'Authorization': f'Bearer {token}'}

    def generated_token(self, user='NAS_SALES', role='sales'):
        response = self.client.post('/api/nas-upload/tokens', headers=self.auth(user, role))
        self.assertEqual(response.status_code, 200, response.get_json())
        return response.get_json()['data']['token']

    def task(self, token, filename, size):
        response = self.client.post('/api/nas-upload/sessions', json={'filename': filename, 'file_size': size},
                                    headers={'Authorization': f'Bearer {token}'})
        self.assertEqual(response.status_code, 200, response.get_json())
        return response.get_json()['data']

    def chunk(self, task, index, payload, terminated_input=False):
        return self.client.put(f"/api/nas-upload/sessions/{task['upload_id']}/chunks/{index}", data=payload,
                               headers={'Authorization': f"Bearer {task['upload_token']}",
                                        'Content-Type': 'application/octet-stream'},
                               environ_overrides={'wsgi.input_terminated': True} if terminated_input else None)

    def finish(self, task):
        response = self.client.post(f"/api/nas-upload/sessions/{task['upload_id']}/complete", json={},
                                    headers={'Authorization': f"Bearer {task['upload_token']}"})
        if response.status_code != 200:
            return response
        for _ in range(200):
            status = self.client.get(f"/api/nas-upload/sessions/{task['upload_id']}",
                                     headers={'Authorization': f"Bearer {task['upload_token']}"})
            if status.status_code != 200 or status.get_json()['data']['status'] in ('completed', 'failed'):
                return status
            time.sleep(0.01)
        return status

    def test_auth_isolated_and_admin_only_settings(self):
        self.assertEqual(self.client.get('/api/nas-upload/settings').status_code, 401)
        self.assertIn(self.client.get('/api/employees').status_code, (401, 403))
        permitted_settings = self.client.get('/api/nas-upload/settings', headers=self.auth('NAS_SALES', 'sales'))
        self.assertEqual(permitted_settings.status_code, 200)
        no_feature_permission = self.client.get('/api/nas-upload/settings',
                                                headers=self.auth('NAS_UNASSIGNED', 'user'))
        self.assertEqual(no_feature_permission.status_code, 403)
        no_feature_qr = self.client.post('/api/nas-upload/tokens',
                                         headers=self.auth('NAS_UNASSIGNED', 'user'))
        self.assertEqual(no_feature_qr.status_code, 403)
        denied = self.client.post('/api/nas-upload/check', json={'relative_dir': 'temp'},
                                  headers=self.auth('NAS_SALES', 'sales'))
        self.assertEqual(denied.status_code, 403)
        allowed = self.client.post('/api/nas-upload/check', json={'relative_dir': 'temp'},
                                   headers=self.auth('NAS_ADMIN', 'admin'))
        self.assertEqual(allowed.status_code, 200)

    def test_mount_validation_fails_closed_and_write_check_cleans_up(self):
        with patch.object(nas_upload_utils, 'NAS_UPLOAD_ROOT', self.temp_dir.name):
            with self.assertRaises(NasUnavailable):
                ensure_mount()
        with patch.object(nas_upload_utils, 'open_target_dir', lambda _path: os.dup(self.dir_fd)):
            check_writable('临时中转')
        self.assertEqual(os.listdir(self.temp_dir.name), [])

    def test_scoped_token_expiry_and_directory_binding(self):
        token = self.generated_token()
        info = self.client.get('/api/nas-upload/public', headers={'Authorization': f'Bearer {token}'})
        self.assertEqual(info.status_code, 200)
        self.assertGreater(info.get_json()['data']['remaining_seconds'], 0)
        claims = jwt.decode(token, self.app.config['NAS_UPLOAD_SIGNING_KEY'], algorithms=['HS256'])
        self.assertEqual(claims['relative_dir'], '临时中转')
        expired = jwt.encode({**claims, 'exp': int(datetime.utcnow().timestamp()) - 1},
                             self.app.config['NAS_UPLOAD_SIGNING_KEY'], algorithm='HS256')
        self.assertEqual(self.client.get('/api/nas-upload/public', headers={'Authorization': f'Bearer {expired}'}).status_code, 410)

    def test_admin_save_rechecks_and_old_token_keeps_its_directory(self):
        old = self.generated_token()
        saved = self.client.put('/api/nas-upload/settings', json={'relative_dir': 'next-folder'},
                                headers=self.auth('NAS_ADMIN', 'admin'))
        self.assertEqual(saved.status_code, 200)
        old_claims = jwt.decode(old, self.app.config['NAS_UPLOAD_SIGNING_KEY'], algorithms=['HS256'])
        new = self.generated_token()
        new_claims = jwt.decode(new, self.app.config['NAS_UPLOAD_SIGNING_KEY'], algorithms=['HS256'])
        self.assertEqual(old_claims['relative_dir'], '临时中转')
        self.assertEqual(new_claims['relative_dir'], 'next-folder')

    def test_nas_unavailable_never_generates_a_token(self):
        with patch.object(nas_upload_routes, 'check_writable', side_effect=NasUnavailable('offline')):
            response = self.client.post('/api/nas-upload/tokens', headers=self.auth('NAS_SALES', 'sales'))
        self.assertEqual(response.status_code, 503)
        self.assertNotIn('token', response.get_json().get('data') or {})

    def test_chunk_upload_tail_duplicate_order_and_completion(self):
        token = self.generated_token()
        payload = b'a' * nas_upload_routes.CHUNK_SIZE + b'tail'
        task = self.task(token, 'photo.jpg', len(payload))
        order = self.chunk(task, 1, b'tail')
        self.assertEqual(order.status_code, 409)
        first = self.chunk(task, 0, payload[:nas_upload_routes.CHUNK_SIZE], terminated_input=True)
        self.assertEqual(first.status_code, 200, first.get_json())
        duplicate = self.chunk(task, 0, payload[:nas_upload_routes.CHUNK_SIZE])
        self.assertTrue(duplicate.get_json()['data']['duplicate'])
        self.assertEqual(self.chunk(task, 1, b'tail').status_code, 200)
        completed = self.finish(task)
        self.assertEqual(completed.status_code, 200, completed.get_json())
        self.assertEqual(sorted(os.listdir(self.temp_dir.name)), [nas_upload_routes.STATE_DIR_NAME, 'photo.jpg'])
        self.assertEqual(sorted(os.listdir(os.path.join(self.temp_dir.name, nas_upload_routes.STATE_DIR_NAME))),
                         ['.oa-upload-' + task['upload_id'] + '.json'])
        with open(os.path.join(self.temp_dir.name, 'photo.jpg'), 'rb') as uploaded:
            self.assertEqual(uploaded.read(), payload)

    def test_qr_expiry_blocks_new_task_but_existing_grant_continues(self):
        token = self.generated_token()
        task = self.task(token, 'long.bin', 3)
        claims = jwt.decode(token, self.app.config['NAS_UPLOAD_SIGNING_KEY'], algorithms=['HS256'])
        expired = jwt.encode({**claims, 'exp': int(datetime.utcnow().timestamp()) - 1},
                             self.app.config['NAS_UPLOAD_SIGNING_KEY'], algorithm='HS256')
        self.assertEqual(self.client.post('/api/nas-upload/sessions', json={'filename': 'new', 'file_size': 1},
                                          headers={'Authorization': f'Bearer {expired}'}).status_code, 410)
        part = self.chunk(task, 0, b'abc')
        self.assertEqual(part.status_code, 200, part.get_json())
        self.assertEqual(self.finish(task).status_code, 200)

    def test_max_size_and_filename_collision(self):
        token = self.generated_token()
        too_big = self.client.post('/api/nas-upload/sessions', json={'filename': 'huge', 'file_size': MAX_FILE_SIZE + 1},
                                   headers={'Authorization': f'Bearer {token}'})
        self.assertEqual(too_big.status_code, 413)
        for payload in (b'first', b'second'):
            task = self.task(token, 'same.txt', len(payload))
            self.assertEqual(self.chunk(task, 0, payload).status_code, 200)
            self.assertEqual(self.finish(task).status_code, 200)
        self.assertEqual(sorted(name for name in os.listdir(self.temp_dir.name) if not name.startswith('.oa-upload-')),
                         ['same (1).txt', 'same.txt'])

    def test_failed_chunk_can_retry_and_nas_disconnect_fails_closed(self):
        token = self.generated_token()
        task = self.task(token, 'retry.bin', 4)
        with patch.object(nas_upload_routes.os, 'pwrite', side_effect=OSError('simulated NAS write failure')):
            failed = self.chunk(task, 0, b'data')
        self.assertEqual(failed.status_code, 503)
        self.assertEqual(self.client.get(f"/api/nas-upload/sessions/{task['upload_id']}",
                                         headers={'Authorization': f"Bearer {task['upload_token']}"})
                         .get_json()['data']['next_chunk'], 0)
        self.assertEqual(self.chunk(task, 0, b'data').status_code, 200)
        self.assertEqual(self.finish(task).status_code, 200)

        next_task = self.task(token, 'offline.bin', 1)
        with patch.object(nas_upload_routes, 'open_target_dir', side_effect=NasUnavailable('offline')):
            offline = self.chunk(next_task, 0, b'x')
        self.assertEqual(offline.status_code, 503)
        self.assertFalse(os.path.exists(os.path.join(self.temp_dir.name, 'offline.bin')))

    def test_upload_requires_qr_and_task_authorization_and_cleans_expired_task(self):
        token = self.generated_token()
        expired = jwt.encode({'purpose': 'nas-mobile-upload', 'relative_dir': '临时中转',
                              'exp': int(datetime.utcnow().timestamp()) - 1},
                             self.app.config['NAS_UPLOAD_SIGNING_KEY'], algorithm='HS256')
        self.assertEqual(self.client.post('/api/nas-upload/sessions', json={'filename': 'x', 'file_size': 1},
                                          headers={'Authorization': f'Bearer {expired}'}).status_code, 410)
        self.assertEqual(os.listdir(self.temp_dir.name), [])
        task = self.task(token, 'x', 5)
        unauthorized = self.client.put(f"/api/nas-upload/sessions/{task['upload_id']}/chunks/0", data=b'hello')
        self.assertEqual(unauthorized.status_code, 410)
        with open(self.task_state_path(task['upload_id']), encoding='utf-8') as meta_file:
            meta = __import__('json').load(meta_file)
        meta['expires_at'] = int(datetime.utcnow().timestamp()) - 10
        with open(self.task_state_path(task['upload_id']), 'w', encoding='utf-8') as meta_file:
            __import__('json').dump(meta, meta_file)
        business_file = os.path.join(self.temp_dir.name, 'business.txt')
        with open(business_file, 'wb') as handle:
            handle.write(b'keep')
        other = self.task(token, 'other', 1)  # initialization opportunistically cleans expired module-owned files
        self.assertFalse(os.path.exists(self.task_state_path(task['upload_id'], 'part')))
        self.assertFalse(os.path.exists(self.task_state_path(task['upload_id'])))
        self.assertTrue(os.path.exists(business_file))
        self.assertEqual(self.chunk(other, 0, b'z').status_code, 200)

    def test_concurrent_same_name_never_overwrites(self):
        token = self.generated_token()
        tasks = [self.task(token, 'same.bin', len(payload)) for payload in (b'alpha', b'beta')]
        for task, payload in zip(tasks, (b'alpha', b'beta')):
            self.assertEqual(self.chunk(task, 0, payload).status_code, 200)
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda task: self.finish(task).status_code, tasks))
        self.assertEqual(results, [200, 200])
        self.assertEqual(sorted(name for name in os.listdir(self.temp_dir.name) if not name.startswith('.oa-upload-')),
                         ['same (1).bin', 'same.bin'])
        contents = set()
        for name in os.listdir(self.temp_dir.name):
            if name.startswith('.oa-upload-'):
                continue
            with open(os.path.join(self.temp_dir.name, name), 'rb') as uploaded:
                contents.add(uploaded.read())
        self.assertEqual(contents, {b'alpha', b'beta'})

    def test_status_poll_recovers_ready_task_and_duplicate_polls_do_not_republish(self):
        token = self.generated_token()
        task = self.task(token, 'recovered.txt', 4)
        self.assertEqual(self.chunk(task, 0, b'data').status_code, 200)
        meta_path = self.task_state_path(task['upload_id'])
        with open(meta_path, encoding='utf-8') as handle:
            meta = __import__('json').load(handle)
        meta['status'] = 'processing'  # Simulate a complete task left by a backend restart.
        with open(meta_path, 'w', encoding='utf-8') as handle:
            __import__('json').dump(meta, handle)

        # New task creation performs the bounded module-only recovery scan.
        other = self.task(token, 'other.txt', 1)
        self.assertEqual(self.chunk(other, 0, b'x').status_code, 200)
        batch = {'tasks': [{'upload_id': task['upload_id'], 'upload_token': task['upload_token']}]}
        for _ in range(200):
            state = self.client.post('/api/nas-upload/sessions/status', json=batch).get_json()['data']['tasks'][0]
            if state['status'] in ('completed', 'failed'):
                break
            time.sleep(0.01)
        self.assertEqual(state['status'], 'completed')
        repeated = self.client.post('/api/nas-upload/sessions/status', json=batch).get_json()['data']['tasks'][0]
        self.assertEqual(repeated['status'], 'completed')
        self.assertEqual(os.listdir(self.temp_dir.name).count('recovered.txt'), 1)

    def test_legacy_root_level_task_is_resolved_and_recovered(self):
        token = self.generated_token()
        task = self.task(token, 'legacy.txt', 4)
        state_dir = os.path.join(self.temp_dir.name, nas_upload_routes.STATE_DIR_NAME)
        for suffix in ('part', 'json'):
            shutil.move(self.task_state_path(task['upload_id'], suffix),
                        os.path.join(self.temp_dir.name, f".oa-upload-{task['upload_id']}.{suffix}"))
        os.rmdir(state_dir)

        self.assertEqual(self.chunk(task, 0, b'data').status_code, 200)
        status = self.client.get(f"/api/nas-upload/sessions/{task['upload_id']}",
                                 headers={'Authorization': f"Bearer {task['upload_token']}"})
        self.assertEqual(status.status_code, 200, status.get_json())
        self.assertIn(status.get_json()['data']['status'], ('pending', 'processing', 'completed'))
        final = self.finish(task)
        self.assertEqual(final.status_code, 200, final.get_json())
        self.assertEqual(os.listdir(self.temp_dir.name).count('legacy.txt'), 1)
        self.assertTrue(os.path.exists(os.path.join(self.temp_dir.name, f".oa-upload-{task['upload_id']}.json")))

    def test_publisher_queue_is_fifo(self):
        nas_upload_routes._publish_queue.join()
        observed = []
        done = threading.Event()
        ids = [f'{i:032x}' for i in range(1, 4)]

        def record(upload_id, _relative_dir):
            observed.append(upload_id)
            if len(observed) == len(ids):
                done.set()

        with patch.object(nas_upload_routes, '_publish_task', side_effect=record):
            with self.app.app_context():
                for upload_id in ids:
                    nas_upload_routes._enqueue_publish(upload_id, '临时中转')
            self.assertTrue(done.wait(2), 'publisher queue did not drain')
        self.assertEqual(observed, ids)

    def test_publisher_thread_start_failure_does_not_poison_queue_registration(self):
        upload_id = 'f' * 32
        isolated_queue = queue.Queue()
        with patch.object(nas_upload_routes, '_publish_queue', isolated_queue), \
                patch.object(nas_upload_routes, '_queued_tasks', set()), \
                patch.object(nas_upload_routes, '_publisher_started', False), \
                patch.object(nas_upload_routes.threading.Thread, 'start',
                             side_effect=[RuntimeError('simulated thread start failure'), None]):
            with self.app.app_context():
                with self.assertRaisesRegex(RuntimeError, 'simulated thread start failure'):
                    nas_upload_routes._enqueue_publish(upload_id, '临时中转')
                self.assertNotIn(upload_id, nas_upload_routes._queued_tasks)
                self.assertFalse(nas_upload_routes._publisher_started)

                self.assertTrue(nas_upload_routes._enqueue_publish(upload_id, '临时中转'))
                self.assertIn(upload_id, nas_upload_routes._queued_tasks)
                self.assertTrue(nas_upload_routes._publisher_started)
                self.assertEqual(isolated_queue.get_nowait(), (upload_id, '临时中转'))
                isolated_queue.task_done()

    def test_complete_enqueues_without_waiting_for_publish(self):
        token = self.generated_token()
        first = self.task(token, 'first.bin', 1)
        with patch.object(nas_upload_routes, '_enqueue_publish', return_value=False):
            self.assertEqual(self.chunk(first, 0, b'a').status_code, 200)
            response = self.client.post(f"/api/nas-upload/sessions/{first['upload_id']}/complete", json={},
                                        headers={'Authorization': f"Bearer {first['upload_token']}"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()['data']['status'], 'pending')
        # Another upload can initialize while the first remains queued for publication.
        second = self.task(token, 'second.bin', 1)
        self.assertEqual(self.chunk(second, 0, b'b').status_code, 200)
        self.assertEqual(os.listdir(self.temp_dir.name).count('first.bin'), 0)

    def test_publish_failure_is_persisted_without_final_file(self):
        token = self.generated_token()
        task = self.task(token, 'publish-fail.bin', 4)
        with patch.object(nas_upload_routes, '_enqueue_publish', return_value=False):
            self.assertEqual(self.chunk(task, 0, b'data').status_code, 200)
        with patch.object(nas_upload_routes.os, 'link', side_effect=OSError('simulated publish failure')):
            with self.app.app_context():
                nas_upload_routes._publish_task(task['upload_id'], '临时中转')
        state = self.client.get(f"/api/nas-upload/sessions/{task['upload_id']}",
                                headers={'Authorization': f"Bearer {task['upload_token']}"}).get_json()['data']
        self.assertEqual(state['status'], 'failed')
        self.assertFalse(os.path.exists(os.path.join(self.temp_dir.name, 'publish-fail.bin')))


if __name__ == '__main__':
    unittest.main()
