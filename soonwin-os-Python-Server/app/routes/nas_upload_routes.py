"""QR-authorized, sequential chunk uploads directly to the mounted NAS."""
import json
import os
import queue
import re
import secrets
import threading
import time

import jwt
from flask import Blueprint, current_app, jsonify, request

from app.models.system_config import SystemConfig
from app.utils.auth_utils import get_user_role_from_token, require_auth, require_module_permission
from app.utils.nas_upload_utils import (
    DEFAULT_RELATIVE_DIR, MAX_FILE_SIZE, InvalidUploadPath, NasUnavailable,
    check_writable, clean_filename, clean_relative_path, open_target_dir,
)
from extensions import db

nas_upload_bp = Blueprint('nas_upload', __name__)
TOKEN_TTL_SECONDS = 30 * 60
TASK_TTL_SECONDS = 24 * 60 * 60
CHUNK_SIZE = 8 * 1024 * 1024
STATE_DIR_NAME = '.oa-upload-state'
_ID = re.compile(r'^[0-9a-f]{32}$')
_locks_guard = threading.Lock()
_task_locks = {}
_publish_queue = queue.Queue()
_queue_guard = threading.Lock()
_queued_tasks = set()
_publisher_started = False


def _error(message, status=400):
    return jsonify({'code': status, 'msg': message, 'data': None}), status


def _lock(upload_id):
    with _locks_guard:
        return _task_locks.setdefault(upload_id, threading.Lock())


def _admin_error():
    if get_user_role_from_token() != 'admin':
        return _error('仅管理员可执行此操作', 403)
    return None


def _configured_dir():
    return SystemConfig.get_config('nas_mobile_upload_dir', DEFAULT_RELATIVE_DIR)


def _key():
    key = current_app.config.get('NAS_UPLOAD_SIGNING_KEY', '')
    return key if isinstance(key, str) and len(key.encode()) >= 32 else None


def _decode(raw, purpose):
    key = _key()
    if not key:
        return None
    try:
        claims = jwt.decode(raw, key, algorithms=['HS256'])
        if claims.get('purpose') != purpose:
            return None
        if 'relative_dir' in claims:
            claims['relative_dir'] = clean_relative_path(claims['relative_dir'])
        return claims
    except (jwt.InvalidTokenError, InvalidUploadPath, TypeError, ValueError):
        return None


def _bearer(purpose):
    return _decode(request.headers.get('Authorization', '').removeprefix('Bearer ').strip(), purpose)


def _names(upload_id):
    if not isinstance(upload_id, str) or not _ID.fullmatch(upload_id):
        raise InvalidUploadPath('上传任务无效')
    return f'.oa-upload-{upload_id}.part', f'.oa-upload-{upload_id}.json'


def _open_state_dir(target_fd, create=False):
    """Open the module-owned state directory without following a NAS symlink."""
    flags = os.O_RDONLY | getattr(os, 'O_DIRECTORY', 0) | getattr(os, 'O_NOFOLLOW', 0)
    try:
        return os.open(STATE_DIR_NAME, flags, dir_fd=target_fd)
    except FileNotFoundError:
        if not create:
            return None
        try:
            os.mkdir(STATE_DIR_NAME, 0o700, dir_fd=target_fd)
        except FileExistsError:
            pass
        return os.open(STATE_DIR_NAME, flags, dir_fd=target_fd)


def _open_task_dir(target_fd, upload_id):
    """Resolve legacy root-level metadata first, then the new hidden state dir."""
    _, meta_name = _names(upload_id)
    try:
        os.stat(meta_name, dir_fd=target_fd, follow_symlinks=False)
        return os.dup(target_fd)
    except FileNotFoundError:
        pass
    state_fd = _open_state_dir(target_fd)
    if state_fd is not None:
        try:
            os.stat(meta_name, dir_fd=state_fd, follow_symlinks=False)
            return state_fd
        except FileNotFoundError:
            os.close(state_fd)
    raise FileNotFoundError(meta_name)


def _open_task_dirs(relative_dir, upload_id):
    target_fd = open_target_dir(relative_dir)
    try:
        return target_fd, _open_task_dir(target_fd, upload_id)
    except Exception:
        os.close(target_fd)
        raise


def _read_meta(dir_fd, meta_name):
    fd = os.open(meta_name, os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0), dir_fd=dir_fd)
    try:
        chunks = []
        while True:
            block = os.read(fd, 65536)
            if not block:
                break
            chunks.append(block)
            if sum(map(len, chunks)) > 1024 * 1024:
                raise ValueError('上传任务元数据无效')
        return json.loads(b''.join(chunks))
    finally:
        os.close(fd)


def _write_meta(dir_fd, meta_name, meta):
    temp = f".oa-upload-{meta['upload_id']}.meta-{secrets.token_hex(8)}.tmp"
    fd = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, 'O_NOFOLLOW', 0), 0o600, dir_fd=dir_fd)
    try:
        raw = json.dumps(meta, ensure_ascii=False, separators=(',', ':')).encode()
        view = memoryview(raw)
        while view:
            n = os.write(fd, view)
            if n <= 0:
                raise OSError('元数据写入失败')
            view = view[n:]
        os.fsync(fd)
    finally:
        os.close(fd)
    os.replace(temp, meta_name, src_dir_fd=dir_fd, dst_dir_fd=dir_fd)


def _task_claims():
    claims = _bearer('nas-upload-task')
    if not claims:
        return None
    try:
        _names(claims.get('upload_id'))
        claims['relative_dir'] = clean_relative_path(claims.get('relative_dir'))
        claims['filename'] = clean_filename(claims.get('filename'))
        size = int(claims.get('file_size'))
        if size < 0 or size > MAX_FILE_SIZE:
            return None
        claims['file_size'] = size
        return claims
    except (InvalidUploadPath, TypeError, ValueError):
        return None


def _assert_meta(meta, claims):
    for field in ('upload_id', 'relative_dir', 'filename', 'file_size', 'expires_at'):
        if meta.get(field) != claims.get(field):
            raise ValueError('上传任务授权与状态不匹配')
    if int(meta.get('expires_at', 0)) < int(time.time()):
        raise TimeoutError('上传任务已过期，请重新生成二维码')


def _clean_expired(dir_fd, now=None):
    """Opportunistically remove only expired module-owned task files."""
    now = now or int(time.time())
    try:
        names = os.listdir(dir_fd)
    except OSError:
        return
    for name in names:
        match = re.fullmatch(r'\.oa-upload-([0-9a-f]{32})\.(?:json|part|meta-[0-9a-f]{16}\.tmp)', name)
        if not match:
            continue
        upload_id = match.group(1)
        lock = _lock(upload_id)
        if not lock.acquire(blocking=False):
            continue
        try:
            part_name, meta_name = _names(upload_id)
            try:
                meta = _read_meta(dir_fd, meta_name)
                expired = int(meta.get('expires_at', 0)) < now
            except (OSError, ValueError, TypeError, json.JSONDecodeError):
                try:
                    expired = now - int(os.stat(name, dir_fd=dir_fd, follow_symlinks=False).st_mtime) > TASK_TTL_SECONDS
                except OSError:
                    expired = False
            if expired:
                for child in (part_name, meta_name):
                    try:
                        os.unlink(child, dir_fd=dir_fd)
                    except OSError:
                        pass
                # A process crash while atomically writing sidecar metadata can leave
                # only this uniquely named staging file. It is removed after the task TTL.
                for child in names:
                    if child.startswith(f'.oa-upload-{upload_id}.meta-') and child.endswith('.tmp'):
                        try:
                            os.unlink(child, dir_fd=dir_fd)
                        except OSError:
                            pass
        finally:
            lock.release()


def _chunk_count(meta):
    size = int(meta.get('file_size', 0))
    return (size + CHUNK_SIZE - 1) // CHUNK_SIZE


def _is_complete(meta):
    return (meta.get('next_chunk') == _chunk_count(meta)
            and meta.get('received_bytes') == meta.get('file_size'))


def _enqueue_publish(upload_id, relative_dir):
    """Queue a ready task once; a single daemon worker publishes tasks FIFO."""
    global _publisher_started
    app = current_app._get_current_object()
    with _queue_guard:
        if upload_id in _queued_tasks:
            return False
        if not _publisher_started:
            threading.Thread(target=_publisher_worker, args=(app,), daemon=True,
                             name='nas-upload-publisher').start()
            _publisher_started = True
        _queued_tasks.add(upload_id)
        try:
            _publish_queue.put((upload_id, relative_dir))
        except Exception:
            # A failed queue registration must remain retryable by reconciliation.
            _queued_tasks.discard(upload_id)
            raise
    return True


def _publisher_worker(app):
    while True:
        upload_id, relative_dir = _publish_queue.get()
        try:
            with app.app_context():
                _publish_task(upload_id, relative_dir)
        except Exception:
            app.logger.exception('NAS upload publisher crashed for task %s', upload_id)
        finally:
            with _queue_guard:
                _queued_tasks.discard(upload_id)
            _publish_queue.task_done()


def _reconcile_task(dir_fd, meta):
    """Promote a fully received task and enqueue pending work idempotently."""
    status = meta.get('status', 'uploading')
    if status in ('completed', 'failed') or not _is_complete(meta):
        return meta
    if status == 'uploading':
        meta.update(status='pending', pending_at=time.time_ns())
        _write_meta(dir_fd, f".oa-upload-{meta['upload_id']}.json", meta)
    if meta.get('status') in ('pending', 'processing'):
        _enqueue_publish(meta['upload_id'], meta['relative_dir'])
    return meta


def _recover_ready_tasks(dir_fds):
    """On new work, recover complete module tasks left by a service restart."""
    ready = []
    for dir_fd in dir_fds:
        for name in os.listdir(dir_fd):
            match = re.fullmatch(r'\.oa-upload-([0-9a-f]{32})\.json', name)
            if not match:
                continue
            try:
                meta = _read_meta(dir_fd, name)
                if (meta.get('upload_id') == match.group(1)
                        and int(meta.get('expires_at', 0)) >= int(time.time())
                        and meta.get('status', 'uploading') not in ('completed', 'failed')
                        and _is_complete(meta)):
                    ready.append((meta, os.dup(dir_fd)))
            except (OSError, ValueError, TypeError, json.JSONDecodeError):
                continue
    for meta, dir_fd in sorted(ready, key=lambda pair: (int(pair[0].get('pending_at', pair[0].get('created_at', 0))), pair[0]['upload_id'])):
        lock = _lock(meta['upload_id'])
        try:
            if not lock.acquire(blocking=False):
                continue
            try:
                current = _read_meta(dir_fd, f".oa-upload-{meta['upload_id']}.json")
                _reconcile_task(dir_fd, current)
            except (OSError, ValueError, TypeError, json.JSONDecodeError):
                continue
            finally:
                lock.release()
        finally:
            os.close(dir_fd)


def _publish_task(upload_id, relative_dir):
    part_name, meta_name = _names(upload_id)
    target_fd = open_target_dir(relative_dir)
    try:
        directory_fd = _open_task_dir(target_fd, upload_id)
    except Exception:
        os.close(target_fd)
        raise
    published = False
    try:
        lock = _lock(upload_id)
        with lock:
            meta = _read_meta(directory_fd, meta_name)
            if meta.get('relative_dir') != relative_dir:
                raise ValueError('上传任务目标目录不匹配')
            if meta.get('status') == 'completed' or meta.get('status') == 'failed':
                return
            if int(meta.get('expires_at', 0)) < int(time.time()):
                meta.update(status='failed', error='上传任务已过期')
                _write_meta(directory_fd, meta_name, meta)
                return
            if not _is_complete(meta):
                return
            meta.update(status='processing', error=None)
            _write_meta(directory_fd, meta_name, meta)

        try:
            part_fd = os.open(part_name, os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0), dir_fd=directory_fd)
            try:
                part_stat = os.fstat(part_fd)
                if part_stat.st_size != int(meta['file_size']):
                    raise ValueError('临时文件大小校验失败')
                os.fsync(part_fd)
            finally:
                os.close(part_fd)

            filename = clean_filename(meta['filename'])
            stem, suffix = os.path.splitext(filename)
            final_name = None
            for serial in range(10000):
                candidate = filename if serial == 0 else f'{stem} ({serial}){suffix}'
                try:
                    existing = os.stat(candidate, dir_fd=target_fd, follow_symlinks=False)
                except FileNotFoundError:
                    continue
                if (part_stat.st_ino and existing.st_ino == part_stat.st_ino
                        and existing.st_dev == part_stat.st_dev):
                    final_name = candidate
                    published = True
                    break
            if final_name is None:
                for serial in range(10000):
                    candidate = filename if serial == 0 else f'{stem} ({serial}){suffix}'
                    try:
                        os.link(part_name, candidate, src_dir_fd=directory_fd,
                                dst_dir_fd=target_fd, follow_symlinks=False)
                        final_name = candidate
                        published = True
                        break
                    except FileExistsError:
                        continue
            if final_name is None:
                raise OSError('无法分配不冲突的文件名')

            with lock:
                meta = _read_meta(directory_fd, meta_name)
                if meta.get('status') != 'completed':
                    meta.update(status='completed', published_filename=final_name,
                                completed_at=int(time.time()), error=None)
                    _write_meta(directory_fd, meta_name, meta)
            try:
                os.unlink(part_name, dir_fd=directory_fd)
            except OSError:
                current_app.logger.warning('Published NAS upload left module temp %s', part_name)
        except Exception as exc:
            current_app.logger.error('NAS upload publication failed for task %s: %s', upload_id, exc)
            with lock:
                try:
                    meta = _read_meta(directory_fd, meta_name)
                    if meta.get('status') != 'completed' and not published:
                        meta.update(status='failed', error='文件校验或发布失败，请重新上传')
                        _write_meta(directory_fd, meta_name, meta)
                except (OSError, ValueError, TypeError, json.JSONDecodeError):
                    pass
    finally:
        os.close(directory_fd)
        os.close(target_fd)


@nas_upload_bp.route('/settings', methods=['GET'])
@require_module_permission('nas_mobile_upload_manage')
@require_auth
def get_settings():
    return jsonify({'code': 200, 'data': {'relative_dir': _configured_dir()}})


@nas_upload_bp.route('/check', methods=['POST'])
@require_module_permission('nas_mobile_upload_manage')
@require_auth
def check_connection():
    denied = _admin_error()
    if denied:
        return denied
    data = request.get_json(silent=True) or {}
    try:
        path = clean_relative_path(data.get('relative_dir', _configured_dir()))
        check_writable(path)
        return jsonify({'code': 200, 'data': {'relative_dir': path, 'writable': True}})
    except InvalidUploadPath as exc:
        return _error(str(exc))
    except NasUnavailable as exc:
        return _error(str(exc), 503)


@nas_upload_bp.route('/settings', methods=['PUT'])
@require_module_permission('nas_mobile_upload_manage')
@require_auth
def update_settings():
    denied = _admin_error()
    if denied:
        return denied
    data = request.get_json(silent=True) or {}
    try:
        path = clean_relative_path(data.get('relative_dir'))
        check_writable(path)
        if not SystemConfig.set_config('nas_mobile_upload_dir', path,
                                       'NAS 手机上传目标子目录（共享根相对路径）', db_session=db.session):
            return _error('保存目录配置失败', 500)
        return jsonify({'code': 200, 'data': {'relative_dir': path}})
    except InvalidUploadPath as exc:
        return _error(str(exc))
    except NasUnavailable as exc:
        return _error(str(exc), 503)


@nas_upload_bp.route('/tokens', methods=['POST'])
@require_module_permission('nas_mobile_upload_manage')
@require_auth
def create_token():
    relative_dir = _configured_dir()
    try:
        relative_dir = clean_relative_path(relative_dir)
        check_writable(relative_dir)
    except (InvalidUploadPath, NasUnavailable) as exc:
        return _error(f'NAS 连接或真实写入检测失败：{exc}', 503)
    key = _key()
    if not key:
        return _error('上传令牌签名密钥未配置，请联系管理员', 503)
    now = int(time.time())
    signed = jwt.encode({'purpose': 'nas-mobile-upload', 'relative_dir': relative_dir,
                         'iat': now, 'exp': now + TOKEN_TTL_SECONDS,
                         'nonce': secrets.token_urlsafe(12)}, key, algorithm='HS256')
    return jsonify({'code': 200, 'data': {'token': signed, 'expires_at': now + TOKEN_TTL_SECONDS,
                                         'relative_dir': relative_dir}})


@nas_upload_bp.route('/public', methods=['GET'])
def validate_public_token():
    claims = _bearer('nas-mobile-upload')
    if not claims:
        response, status = _error('上传二维码已过期或无效', 410)
        response.headers['Cache-Control'] = 'no-store'
        response.headers['Pragma'] = 'no-cache'
        return response, status
    # Mobile wall clocks are not authoritative. Return a server-computed lifetime
    # for a monotonic client countdown; session creation still verifies JWT expiry.
    remaining = max(0, int(claims['exp']) - int(time.time()))
    response = jsonify({'code': 200, 'data': {'expires_at': claims['exp'],
                                              'remaining_seconds': remaining}})
    response.headers['Cache-Control'] = 'no-store'
    response.headers['Pragma'] = 'no-cache'
    return response


@nas_upload_bp.route('/sessions', methods=['POST'])
def create_session():
    qr = _bearer('nas-mobile-upload')
    if not qr:
        return _error('上传二维码已过期或无效，不能创建新上传任务', 410)
    data = request.get_json(silent=True) or {}
    try:
        filename = clean_filename(data.get('filename', ''))
        size = int(data.get('file_size'))
        if size < 0 or size > MAX_FILE_SIZE:
            return _error('单文件最大为 2048 MB', 413)
        directory_fd = open_target_dir(qr['relative_dir'])
        try:
            _clean_expired(directory_fd)
            state_fd = _open_state_dir(directory_fd, create=True)
            try:
                _clean_expired(state_fd)
                _recover_ready_tasks((directory_fd, state_fd))
            finally:
                os.close(state_fd)
            state_fd = _open_state_dir(directory_fd)
            if state_fd is None:
                raise OSError('上传状态目录不可用')
            upload_id = secrets.token_hex(16)
            part_name, meta_name = _names(upload_id)
            try:
                fd = os.open(part_name, os.O_RDWR | os.O_CREAT | os.O_EXCL | getattr(os, 'O_NOFOLLOW', 0),
                             0o600, dir_fd=state_fd)
                try:
                    os.ftruncate(fd, size)
                    os.fsync(fd)
                finally:
                    os.close(fd)
                now = int(time.time())
                meta = {'upload_id': upload_id, 'relative_dir': qr['relative_dir'], 'filename': filename,
                        'file_size': size, 'next_chunk': 0, 'received_bytes': 0,
                        'created_at': now, 'last_activity': now, 'expires_at': now + TASK_TTL_SECONDS,
                        'status': 'uploading'}
                try:
                    _write_meta(state_fd, meta_name, meta)
                except Exception:
                    os.unlink(part_name, dir_fd=state_fd)
                    raise
                upload_token = jwt.encode({'purpose': 'nas-upload-task', **meta,
                                           'iat': now, 'exp': meta['expires_at']}, _key(), algorithm='HS256')
                return jsonify({'code': 200, 'data': {'upload_id': upload_id, 'upload_token': upload_token,
                                                      'chunk_size': CHUNK_SIZE, 'next_chunk': 0,
                                                      'expires_at': meta['expires_at']}})
            finally:
                os.close(state_fd)
        finally:
            os.close(directory_fd)
    except (InvalidUploadPath, ValueError, TypeError) as exc:
        return _error(str(exc))
    except (NasUnavailable, OSError) as exc:
        current_app.logger.error('NAS upload task init failed: %s', exc)
        return _error('NAS 不可用，无法开始上传', 503)


@nas_upload_bp.route('/sessions/<upload_id>', methods=['GET'])
def session_status(upload_id):
    claims = _task_claims()
    if not claims or claims.get('upload_id') != upload_id:
        return _error('上传授权无效或已过期', 410)
    try:
        _, meta_name = _names(upload_id)
        target_fd, directory_fd = _open_task_dirs(claims['relative_dir'], upload_id)
        try:
            with _lock(upload_id):
                meta = _read_meta(directory_fd, meta_name)
                _assert_meta(meta, claims)
                meta = _reconcile_task(directory_fd, meta)
                return jsonify({'code': 200, 'data': {'next_chunk': meta['next_chunk'],
                                                      'received_bytes': meta['received_bytes'],
                                                      'file_size': meta['file_size'],
                                                      'chunk_size': CHUNK_SIZE,
                                                      'status': meta.get('status', 'uploading'),
                                                      'error': meta.get('error'),
                                                      'published_filename': meta.get('published_filename')}})
        finally:
            os.close(directory_fd)
            os.close(target_fd)
    except TimeoutError as exc:
        return _error(str(exc), 410)
    except (OSError, ValueError, NasUnavailable) as exc:
        return _error('上传任务不可用或 NAS 已断开', 503)


@nas_upload_bp.route('/sessions/status', methods=['POST'])
def batch_session_status():
    data = request.get_json(silent=True) or {}
    tasks = data.get('tasks')
    if not isinstance(tasks, list) or len(tasks) > 100:
        return _error('查询任务列表无效')
    results = []
    for item in tasks:
        if not isinstance(item, dict):
            results.append({'upload_id': None, 'status': 'failed', 'error': '任务授权无效'})
            continue
        upload_id = item.get('upload_id')
        claims = _decode(item.get('upload_token', ''), 'nas-upload-task')
        if not claims or claims.get('upload_id') != upload_id:
            results.append({'upload_id': upload_id, 'status': 'failed', 'error': '上传授权无效或已过期'})
            continue
        try:
            _names(upload_id)
            relative_dir = clean_relative_path(claims.get('relative_dir'))
            target_fd, directory_fd = _open_task_dirs(relative_dir, upload_id)
            try:
                with _lock(upload_id):
                    meta = _read_meta(directory_fd, f'.oa-upload-{upload_id}.json')
                    _assert_meta(meta, claims)
                    meta = _reconcile_task(directory_fd, meta)
                    results.append({'upload_id': upload_id,
                                    'status': meta.get('status', 'uploading'),
                                    'error': meta.get('error'),
                                    'published_filename': meta.get('published_filename')})
            finally:
                os.close(directory_fd)
                os.close(target_fd)
        except TimeoutError as exc:
            results.append({'upload_id': upload_id, 'status': 'failed', 'error': str(exc)})
        except NasUnavailable:
            return _error('NAS 当前不可用，稍后可重新查询任务状态', 503)
        except (InvalidUploadPath, OSError, ValueError) as exc:
            results.append({'upload_id': upload_id, 'status': 'failed',
                            'error': '上传任务不可用或 NAS 已断开'})
    return jsonify({'code': 200, 'data': {'tasks': results}})


@nas_upload_bp.route('/sessions/<upload_id>/chunks/<int:index>', methods=['PUT'])
def upload_chunk(upload_id, index):
    claims = _task_claims()
    if not claims or claims.get('upload_id') != upload_id:
        return _error('上传授权无效或已过期', 410)
    if index < 0:
        return _error('分片序号无效')
    expected_count = (claims['file_size'] + CHUNK_SIZE - 1) // CHUNK_SIZE
    if index >= expected_count:
        return _error('分片序号超出文件范围')
    expected_len = min(CHUNK_SIZE, claims['file_size'] - index * CHUNK_SIZE)
    if request.content_length != expected_len:
        return _error('分片长度不正确', 413 if request.content_length and request.content_length > CHUNK_SIZE else 400)
    request.max_content_length = CHUNK_SIZE
    try:
        part_name, meta_name = _names(upload_id)
        target_fd, directory_fd = _open_task_dirs(claims['relative_dir'], upload_id)
        try:
            with _lock(upload_id):
                meta = _read_meta(directory_fd, meta_name)
                _assert_meta(meta, claims)
                if index < meta['next_chunk']:
                    return jsonify({'code': 200, 'data': {'next_chunk': meta['next_chunk'], 'duplicate': True}})
                if index != meta['next_chunk']:
                    return _error('分片顺序错误', 409)
                part_fd = os.open(part_name, os.O_WRONLY | getattr(os, 'O_NOFOLLOW', 0), dir_fd=directory_fd)
                try:
                    offset = index * CHUNK_SIZE
                    received = 0
                    while received < expected_len:
                        block = request.stream.read(min(1024 * 1024, expected_len - received))
                        if not block:
                            raise ValueError('分片上传中断')
                        written = 0
                        view = memoryview(block)
                        while view:
                            n = os.pwrite(part_fd, view, offset + received + written)
                            if n <= 0:
                                raise OSError('NAS 写入未能推进')
                            written += n
                            view = view[n:]
                        received += len(block)
                    # Content-Length has already been matched to the exact expected
                    # chunk size. Do not probe one byte past it: Waitress marks
                    # request bodies as input-terminated, and Werkzeug raises 413
                    # when that probe reaches the configured max_content_length.
                    os.fsync(part_fd)
                finally:
                    os.close(part_fd)
                meta.update(next_chunk=index + 1, received_bytes=meta['received_bytes'] + expected_len,
                            last_activity=int(time.time()))
                _write_meta(directory_fd, meta_name, meta)
                if _is_complete(meta):
                    meta = _reconcile_task(directory_fd, meta)
                return jsonify({'code': 200, 'data': {'next_chunk': meta['next_chunk'], 'duplicate': False}})
        finally:
            os.close(directory_fd)
            os.close(target_fd)
    except TimeoutError as exc:
        return _error(str(exc), 410)
    except (InvalidUploadPath, ValueError) as exc:
        return _error(str(exc))
    except (OSError, NasUnavailable) as exc:
        current_app.logger.error('NAS upload chunk failed: %s', exc)
        return _error('NAS 不可用或分片写入失败，可重试当前分片', 503)


@nas_upload_bp.route('/sessions/<upload_id>/complete', methods=['POST'])
def complete_session(upload_id):
    claims = _task_claims()
    if not claims or claims.get('upload_id') != upload_id:
        return _error('上传授权无效或已过期', 410)
    try:
        _, meta_name = _names(upload_id)
        target_fd, directory_fd = _open_task_dirs(claims['relative_dir'], upload_id)
        try:
            with _lock(upload_id):
                meta = _read_meta(directory_fd, meta_name)
                _assert_meta(meta, claims)
                if meta.get('status') == 'completed':
                    return jsonify({'code': 200, 'data': {'status': 'completed',
                                                          'filename': meta.get('published_filename'),
                                                          'size': claims['file_size']}})
                if meta.get('status') == 'failed':
                    return _error(meta.get('error') or '文件处理失败，请重新上传', 409)
                if not _is_complete(meta):
                    return _error('文件分片尚未完整接收', 409)
                meta = _reconcile_task(directory_fd, meta)
                return jsonify({'code': 200, 'data': {'status': meta.get('status', 'pending')}})
        finally:
            os.close(directory_fd)
            os.close(target_fd)
    except TimeoutError as exc:
        return _error(str(exc), 410)
    except (InvalidUploadPath, ValueError) as exc:
        return _error(str(exc))
    except (OSError, NasUnavailable) as exc:
        current_app.logger.error('NAS upload queue request failed: %s', exc)
        return _error('NAS 不可用，文件已暂存，稍后可查询状态', 503)
