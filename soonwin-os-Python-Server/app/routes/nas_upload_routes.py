"""QR-authorized whole-file uploads directly to the mounted NAS."""
import hashlib
import json
import os
import queue
import re
import secrets
import threading
import time
from datetime import datetime

import jwt
from flask import Blueprint, current_app, jsonify, request

from app.models.employee import Employee
from app.models.nas_upload_log import NasUploadLog
from app.models.system_config import SystemConfig
from app.utils.auth_utils import get_user_id_from_token, get_user_role_from_token, require_admin, require_auth, require_module_permission
from app.utils.nas_upload_utils import (
    DEFAULT_RELATIVE_DIR, MAX_FILE_SIZE, InvalidUploadPath, NasUnavailable,
    check_writable, clean_filename, clean_relative_path, open_target_dir,
)
from extensions import db

nas_upload_bp = Blueprint('nas_upload', __name__)
TOKEN_TTL_SECONDS = 30 * 60
TASK_TTL_SECONDS = 24 * 60 * 60
LEGACY_CHUNK_SIZE = 8 * 1024 * 1024
DEFAULT_STATE_DIR_NAME = '.oa-upload-state'
# Keep the default name available to existing callers and tests.
STATE_DIR_NAME = DEFAULT_STATE_DIR_NAME
_STATE_DIR_NAME = re.compile(r'^[A-Za-z0-9._-]{1,64}$')
_ID = re.compile(r'^[0-9a-f]{32}$')
_QR_MAPPING_KEY = re.compile(r'^nas_upload_qr_([0-9a-f]{64})$')
_QR_ACTIVE_KEY = 'nas_upload_qr_active'
_locks_guard = threading.Lock()
_qr_state_lock = threading.RLock()
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


def _qr_token_digest(raw):
    if not isinstance(raw, str) or not raw or len(raw) > 4096:
        return None
    return hashlib.sha256(raw.encode()).hexdigest()


def _qr_mapping_key(raw):
    digest = _qr_token_digest(raw)
    return f'nas_upload_qr_{digest}' if digest else None


def _read_qr_mapping(digest):
    if not isinstance(digest, str) or not re.fullmatch(r'[0-9a-f]{64}', digest):
        return None
    try:
        value = SystemConfig.get_config(f'nas_upload_qr_{digest}', '')
        mapping = json.loads(value) if value else None
        if not isinstance(mapping, dict) or mapping.get('purpose') != 'nas-mobile-upload':
            return None
        if int(mapping.get('exp', 0)) <= int(time.time()):
            return None
        mapping['relative_dir'] = clean_relative_path(mapping.get('relative_dir'))
        return mapping
    except (TypeError, ValueError, json.JSONDecodeError, InvalidUploadPath):
        return None


def _write_qr_config(key, value, description=''):
    row = SystemConfig.query.filter_by(key=key).first()
    if row is None:
        row = SystemConfig(key=key)
    row.value = value
    if description:
        row.description = description
    db.session.add(row)


def _initialize_legacy_qr_pointer(raw, signed_claims):
    """Keep a single pre-upgrade QR usable when it can be identified safely."""
    with _qr_state_lock:
        active = SystemConfig.get_config(_QR_ACTIVE_KEY, '')
        if active:
            return active
        now = int(time.time())
        candidates = []
        for row in SystemConfig.query.filter(SystemConfig.key.startswith('nas_upload_qr_', autoescape=True)).all():
            match = _QR_MAPPING_KEY.fullmatch(row.key)
            if not match:
                continue
            mapping = _read_qr_mapping(match.group(1))
            if mapping:
                candidates.append((match.group(1), mapping))
            else:
                db.session.delete(row)
        if len(candidates) == 1:
            active = candidates[0][0]
            _write_qr_config(_QR_ACTIVE_KEY, active)
            db.session.commit()
            return active
        if candidates:
            # Multiple pre-upgrade opaque links have no reliable ordering when
            # issued in the same second. Fail closed until the user generates one.
            db.session.commit()
            return ''
        if not signed_claims:
            db.session.commit()
            return ''
        digest = _qr_token_digest(raw)
        mapping = {key: signed_claims[key] for key in ('purpose', 'relative_dir', 'iat', 'exp')}
        mapping['scanned'] = False
        _write_qr_config(f'nas_upload_qr_{digest}', json.dumps(mapping, separators=(',', ':')),
                         '兼容的 NAS 手机上传二维码令牌映射')
        _write_qr_config(_QR_ACTIVE_KEY, digest)
        db.session.commit()
        return digest


def _resolve_qr_token(raw, signed_claims=None):
    """Resolve and validate the currently active short or legacy QR token."""
    digest = _qr_token_digest(raw)
    if not digest:
        return None
    try:
        active = SystemConfig.get_config(_QR_ACTIVE_KEY, '')
        if not active:
            active = _initialize_legacy_qr_pointer(raw, signed_claims)
        if not active or active != digest:
            return None
        mapping = _read_qr_mapping(digest)
        if not mapping:
            return None
        if signed_claims and (
            mapping.get('exp') != signed_claims.get('exp')
            or mapping.get('relative_dir') != signed_claims.get('relative_dir')
        ):
            return None
        mapping['qr_token_hash'] = digest
        return mapping
    except Exception:
        current_app.logger.exception('NAS upload QR token lookup failed')
        return None


def _bearer(purpose):
    raw = request.headers.get('Authorization', '').removeprefix('Bearer ').strip()
    claims = _decode(raw, purpose)
    if purpose != 'nas-mobile-upload':
        return claims
    return _resolve_qr_token(raw, claims)


def _replace_active_qr_token(raw, mapping):
    """Atomically revoke all previous QR mappings and activate the new token."""
    digest = _qr_token_digest(raw)
    if not digest:
        raise ValueError('上传二维码令牌无效')
    with _qr_state_lock:
        rows = SystemConfig.query.filter(SystemConfig.key.startswith('nas_upload_qr_', autoescape=True)).all()
        for row in rows:
            if _QR_MAPPING_KEY.fullmatch(row.key):
                db.session.delete(row)
        mapping = {**mapping, 'scanned': False}
        _write_qr_config(f'nas_upload_qr_{digest}', json.dumps(mapping, separators=(',', ':')),
                         '短期 NAS 手机上传二维码令牌映射')
        _write_qr_config(_QR_ACTIVE_KEY, digest)
        db.session.commit()


def _mark_qr_scanned(digest):
    with _qr_state_lock:
        if SystemConfig.get_config(_QR_ACTIVE_KEY, '') != digest:
            return False
        row = SystemConfig.query.filter_by(key=f'nas_upload_qr_{digest}').first()
        if row is None:
            return False
        mapping = json.loads(row.value or '')
        if int(mapping.get('exp', 0)) <= int(time.time()):
            return False
        mapping['scanned'] = True
        row.value = json.dumps(mapping, separators=(',', ':'))
        db.session.commit()
        return True


def _active_qr_digest(digest):
    return bool(digest and SystemConfig.get_config(_QR_ACTIVE_KEY, '') == digest
                and _read_qr_mapping(digest))


def _names(upload_id):
    if not isinstance(upload_id, str) or not _ID.fullmatch(upload_id):
        raise InvalidUploadPath('上传任务无效')
    return f'.oa-upload-{upload_id}.part', f'.oa-upload-{upload_id}.json'


def _configured_state_dir_name():
    """Return a single safe child-directory name for NAS task state."""
    name = current_app.config.get('NAS_UPLOAD_STATE_DIR', DEFAULT_STATE_DIR_NAME)
    if (not isinstance(name, str) or not _STATE_DIR_NAME.fullmatch(name)
            or name in ('.', '..') or '..' in name):
        raise ValueError('NAS_UPLOAD_STATE_DIR must be a safe single directory name')
    return name


def _open_state_dir(target_fd, create=False):
    """Open the module-owned state directory without following a NAS symlink."""
    state_dir_name = _configured_state_dir_name()
    flags = os.O_RDONLY | getattr(os, 'O_DIRECTORY', 0) | getattr(os, 'O_NOFOLLOW', 0)
    try:
        return os.open(state_dir_name, flags, dir_fd=target_fd)
    except FileNotFoundError:
        if not create:
            return None
        try:
            os.mkdir(state_dir_name, 0o700, dir_fd=target_fd)
        except FileExistsError:
            pass
        return os.open(state_dir_name, flags, dir_fd=target_fd)


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
    if meta.get('qr_token_hash') != claims.get('qr_token_hash'):
        raise ValueError('上传任务二维码授权与状态不匹配')
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


def _legacy_chunk_count(meta):
    size = int(meta.get('file_size', 0))
    return (size + LEGACY_CHUNK_SIZE - 1) // LEGACY_CHUNK_SIZE


def _is_complete(meta):
    received = meta.get('received_bytes') == meta.get('file_size')
    if meta.get('whole_file_received') is True:
        return received
    # Allow the publisher to recover tasks completed by the previous DEV chunk
    # protocol while all new sessions use a single HTTP request.
    return (received and meta.get('next_chunk') == _legacy_chunk_count(meta))


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
        dequeued_at_ns = time.time_ns()
        try:
            with app.app_context():
                _publish_task(upload_id, relative_dir, dequeued_at_ns)
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
        state_write_started = time.perf_counter()
        _write_meta(dir_fd, f".oa-upload-{meta['upload_id']}.json", meta)
        _log_publish_timing(meta['upload_id'], 'pending_json_write', state_write_started)
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


def _log_publish_timing(upload_id, stage, started_at):
    current_app.logger.info(
        'NAS upload publish timing upload_id=%s stage=%s elapsed_ms=%.1f',
        upload_id, stage, (time.perf_counter() - started_at) * 1000,
    )


def _record_upload_log(meta, status):
    """Persist only outcomes the server has confirmed, idempotently per task."""
    try:
        row = NasUploadLog.query.filter_by(upload_id=meta['upload_id']).first()
        if row is None:
            row = NasUploadLog(upload_id=meta['upload_id'])
        row.uploaded_at = datetime.fromtimestamp(
            int(meta.get('completed_at') or time.time())
        )
        row.operator_id = meta.get('creator_id')
        row.operator_name = meta.get('creator_name') or '未知账号'
        row.filename = meta['filename']
        row.file_size = int(meta['file_size'])
        row.status = status
        row.target_dir = meta['relative_dir']
        db.session.add(row)
        db.session.commit()
    except Exception:
        db.session.rollback()
        current_app.logger.exception('NAS upload audit record failed upload_id=%s', meta.get('upload_id'))


def _publish_task(upload_id, relative_dir, dequeued_at_ns):
    publish_started = time.perf_counter()
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
            pending_at = meta.get('pending_at')
            if isinstance(pending_at, int) and pending_at > 0:
                fifo_wait_ms = max(0, dequeued_at_ns - pending_at) / 1_000_000
                current_app.logger.info(
                    'NAS upload publish timing upload_id=%s stage=fifo_wait elapsed_ms=%.1f',
                    upload_id, fifo_wait_ms,
                )
            meta.update(status='processing', error=None)
            state_write_started = time.perf_counter()
            _write_meta(directory_fd, meta_name, meta)
            _log_publish_timing(upload_id, 'processing_json_write', state_write_started)

        try:
            part_fd = os.open(part_name, os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0), dir_fd=directory_fd)
            try:
                part_stat = os.fstat(part_fd)
                if part_stat.st_size != int(meta['file_size']):
                    raise ValueError('临时文件大小校验失败')
                fsync_started = time.perf_counter()
                os.fsync(part_fd)
                _log_publish_timing(upload_id, 'publish_fsync', fsync_started)
            finally:
                os.close(part_fd)

            filename = clean_filename(meta['filename'])
            stem, suffix = os.path.splitext(filename)
            final_name = None
            if meta.get('naming_scheme') == 'task_id':
                # The 12-hex suffix keeps even a 240-byte source name within
                # common 255-byte filesystem component limits.
                candidate = f'{stem}_{upload_id[:12]}{suffix}'
                link_started = time.perf_counter()
                try:
                    os.link(part_name, candidate, src_dir_fd=directory_fd,
                            dst_dir_fd=target_fd, follow_symlinks=False)
                    final_name = candidate
                    published = True
                except FileExistsError:
                    existing = os.stat(candidate, dir_fd=target_fd, follow_symlinks=False)
                    if not (part_stat.st_ino and existing.st_ino == part_stat.st_ino
                            and existing.st_dev == part_stat.st_dev):
                        raise OSError('目标文件名已被占用，请重新上传')
                    final_name = candidate
                    published = True
                _log_publish_timing(upload_id, 'os_link', link_started)
            else:
                # Preserve recovery of previously created DEV tasks which did
                # not use the task ID in the final filename.
                name_check_started = time.perf_counter()
                checked_names = 0
                existing_names = 0
                for serial in range(10000):
                    candidate = filename if serial == 0 else f'{stem} ({serial}){suffix}'
                    checked_names += 1
                    try:
                        existing = os.stat(candidate, dir_fd=target_fd, follow_symlinks=False)
                    except FileNotFoundError:
                        continue
                    existing_names += 1
                    if (part_stat.st_ino and existing.st_ino == part_stat.st_ino
                            and existing.st_dev == part_stat.st_dev):
                        final_name = candidate
                        published = True
                        break
                _log_publish_timing(upload_id, 'name_check', name_check_started)
                current_app.logger.info(
                    'NAS upload name scan upload_id=%s checked=%s existing=%s recovered=%s',
                    upload_id, checked_names, existing_names, published,
                )
                if final_name is None:
                    link_started = time.perf_counter()
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
                    _log_publish_timing(upload_id, 'os_link', link_started)
            if final_name is None:
                raise OSError('无法分配不冲突的文件名')

            # The final NAS entry already exists at this point; record the
            # server-confirmed success even if the sidecar update later fails.
            meta.update(completed_at=int(time.time()))
            _record_upload_log(meta, 'success')

            with lock:
                meta = _read_meta(directory_fd, meta_name)
                if meta.get('status') != 'completed':
                    meta.update(status='completed', published_filename=final_name,
                                completed_at=int(time.time()), error=None)
                    state_write_started = time.perf_counter()
                    _write_meta(directory_fd, meta_name, meta)
                    _log_publish_timing(upload_id, 'completed_json_write', state_write_started)
            try:
                unlink_started = time.perf_counter()
                os.unlink(part_name, dir_fd=directory_fd)
                _log_publish_timing(upload_id, 'temporary_unlink', unlink_started)
            except OSError:
                current_app.logger.warning('Published NAS upload left module temp %s', part_name)
        except Exception as exc:
            current_app.logger.error('NAS upload publication failed for task %s: %s', upload_id, exc)
            with lock:
                try:
                    meta = _read_meta(directory_fd, meta_name)
                    if meta.get('status') != 'completed' and not published:
                        meta.update(status='failed', error='文件校验或发布失败，请重新上传')
                        state_write_started = time.perf_counter()
                        _write_meta(directory_fd, meta_name, meta)
                        _log_publish_timing(upload_id, 'failed_json_write', state_write_started)
                        _record_upload_log(meta, 'failed')
                except (OSError, ValueError, TypeError, json.JSONDecodeError):
                    pass
    finally:
        os.close(directory_fd)
        os.close(target_fd)
        _log_publish_timing(upload_id, 'worker_total', publish_started)


@nas_upload_bp.route('/settings', methods=['GET'])
@require_module_permission('nas_mobile_upload_manage')
@require_auth
def get_settings():
    return jsonify({'code': 200, 'data': {'relative_dir': _configured_dir()}})


@nas_upload_bp.route('/logs', methods=['GET'])
@require_admin
def get_upload_logs():
    try:
        page = max(1, int(request.args.get('page', 1)))
        page_size = min(100, max(1, int(request.args.get('page_size', 10))))
    except (TypeError, ValueError):
        return _error('分页参数无效')
    keyword = (request.args.get('keyword') or '').strip()
    query = NasUploadLog.query
    if keyword:
        query = query.filter(NasUploadLog.filename.contains(keyword))
    total = query.count()
    rows = query.order_by(NasUploadLog.uploaded_at.desc(), NasUploadLog.id.desc()) \
        .offset((page - 1) * page_size).limit(page_size).all()
    return jsonify({'code': 200, 'data': {
        'items': [{
            'id': row.id,
            'uploaded_at': row.uploaded_at.strftime('%Y-%m-%d %H:%M:%S') if row.uploaded_at else None,
            'operator_id': row.operator_id,
            'operator_name': row.operator_name,
            'filename': row.filename,
            'file_size': row.file_size,
            'status': row.status,
            'target_dir': row.target_dir,
        } for row in rows],
        'total': total,
        'page': page,
        'page_size': page_size,
    }})


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
    try:
        creator_id = get_user_id_from_token()
        creator = Employee.query.filter_by(emp_id=creator_id).first() if creator_id else None
        if not creator:
            return _error('无法识别二维码生成账号，请重新登录', 401)
        token = secrets.token_urlsafe(16)
        mapping = {'purpose': 'nas-mobile-upload', 'relative_dir': relative_dir,
                   'iat': now, 'exp': now + TOKEN_TTL_SECONDS,
                   'creator_id': creator.emp_id, 'creator_name': creator.name}
        _replace_active_qr_token(token, mapping)
    except Exception:
        db.session.rollback()
        current_app.logger.exception('NAS upload QR token mapping could not be saved')
        return _error('上传二维码生成失败，请稍后重试', 503)
    return jsonify({'code': 200, 'data': {'token': token, 'expires_at': now + TOKEN_TTL_SECONDS,
                                         'relative_dir': relative_dir}})


@nas_upload_bp.route('/public', methods=['GET'])
def validate_public_token():
    claims = _bearer('nas-mobile-upload')
    if not claims:
        response, status = _error('上传二维码已过期或无效', 410)
        response.headers['Cache-Control'] = 'no-store'
        response.headers['Pragma'] = 'no-cache'
        return response, status
    if not _mark_qr_scanned(claims['qr_token_hash']):
        response, status = _error('上传二维码已失效或无效', 410)
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


@nas_upload_bp.route('/qr-status', methods=['GET'])
def get_qr_status():
    claims = _bearer('nas-mobile-upload')
    if not claims:
        response, status = _error('上传二维码已失效或无效', 410)
        response.headers['Cache-Control'] = 'no-store'
        response.headers['Pragma'] = 'no-cache'
        return response, status
    response = jsonify({'code': 200, 'data': {'scanned': bool(claims.get('scanned')),
                                              'expires_at': claims['exp']}})
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
                        'qr_token_hash': qr['qr_token_hash'],
                        'creator_id': qr.get('creator_id'), 'creator_name': qr.get('creator_name'),
                        'file_size': size, 'received_bytes': 0, 'whole_file_received': False,
                        'naming_scheme': 'task_id',
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
                return jsonify({'code': 200, 'data': {'received_bytes': meta['received_bytes'],
                                                      'file_size': meta['file_size'],
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


@nas_upload_bp.route('/sessions/<upload_id>/ack', methods=['POST'])
def acknowledge_completed_session(upload_id):
    """Discard completed task metadata after the browser has observed success."""
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
                if meta.get('status') != 'completed':
                    return _error('上传尚未完成', 409)
                os.unlink(meta_name, dir_fd=directory_fd)
                current_app.logger.info('NAS upload completed metadata removed upload_id=%s', upload_id)
                return '', 204
        finally:
            os.close(directory_fd)
            os.close(target_fd)
    except FileNotFoundError:
        # Repeated acknowledgements are safe after successful cleanup.
        return '', 204
    except TimeoutError as exc:
        return _error(str(exc), 410)
    except (OSError, ValueError, NasUnavailable) as exc:
        current_app.logger.warning('NAS upload metadata cleanup failed upload_id=%s: %s', upload_id, exc)
        return _error('上传状态清理失败', 503)


@nas_upload_bp.route('/sessions/status', methods=['POST'])
def batch_session_status():
    request_started = time.perf_counter()
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
                    current_app.logger.info(
                        'NAS upload status observed upload_id=%s status=%s elapsed_ms=%.1f',
                        upload_id, meta.get('status', 'uploading'),
                        (time.perf_counter() - request_started) * 1000,
                    )
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


@nas_upload_bp.route('/sessions/<upload_id>/file', methods=['PUT'])
def upload_file(upload_id):
    """Receive one complete file body, stage it on NAS, then queue publication."""
    claims = _task_claims()
    if not claims or claims.get('upload_id') != upload_id:
        return _error('上传授权无效或已过期', 410)
    expected_size = claims['file_size']
    if request.content_length != expected_size:
        return _error('上传文件长度不正确', 413 if (request.content_length or 0) > expected_size else 400)
    # The normal OA request limit is 200 MB. This isolated endpoint is capped by
    # the NAS upload policy (2 GB) and reads the raw body incrementally.
    request.max_content_length = MAX_FILE_SIZE
    started = time.perf_counter()
    try:
        part_name, meta_name = _names(upload_id)
        target_fd, directory_fd = _open_task_dirs(claims['relative_dir'], upload_id)
        try:
            with _lock(upload_id):
                meta = _read_meta(directory_fd, meta_name)
                _assert_meta(meta, claims)
                if meta.get('status') in ('pending', 'processing', 'completed') and _is_complete(meta):
                    return jsonify({'code': 200, 'data': {'status': meta['status'],
                                                          'received_bytes': expected_size}})
                if meta.get('status') == 'failed':
                    return _error(meta.get('error') or '上传任务失败，请重新选择文件', 409)
                if _is_complete(meta):
                    meta = _reconcile_task(directory_fd, meta)
                    return jsonify({'code': 200, 'data': {'status': meta.get('status', 'pending'),
                                                          'received_bytes': expected_size}})
                # Serialize authorization with QR replacement in this process.
                # Once accepted, release the DB transaction and let this request
                # finish even if another QR is subsequently generated.
                with _qr_state_lock:
                    qr_is_current = _active_qr_digest(meta.get('qr_token_hash'))
                    db.session.commit()
                if not qr_is_current:
                    return _error('生成此上传任务的二维码已失效，请重新扫码后开始上传', 410)
                part_fd = os.open(part_name, os.O_WRONLY | getattr(os, 'O_NOFOLLOW', 0), dir_fd=directory_fd)
                received = 0
                body_started = time.perf_counter()
                try:
                    while received < expected_size:
                        block = request.stream.read(min(1024 * 1024, expected_size - received))
                        if not block:
                            raise ValueError('上传文件中断，未收到完整内容')
                        view = memoryview(block)
                        offset = received
                        while view:
                            written = os.pwrite(part_fd, view, offset)
                            if written <= 0:
                                raise OSError('NAS 写入未能推进')
                            offset += written
                            view = view[written:]
                        received += len(block)
                    _log_publish_timing(upload_id, 'body_receive_and_write', body_started)
                    sync_started = time.perf_counter()
                    os.fsync(part_fd)
                    _log_publish_timing(upload_id, 'receive_fsync', sync_started)
                finally:
                    os.close(part_fd)
                meta.update(received_bytes=received, whole_file_received=True,
                            last_activity=int(time.time()))
                meta_started = time.perf_counter()
                _write_meta(directory_fd, meta_name, meta)
                _log_publish_timing(upload_id, 'received_json_write', meta_started)
                meta = _reconcile_task(directory_fd, meta)
                current_app.logger.info(
                    'NAS whole-file upload received upload_id=%s bytes=%s elapsed_ms=%.1f',
                    upload_id, received, (time.perf_counter() - started) * 1000,
                )
                return jsonify({'code': 200, 'data': {'status': meta.get('status', 'pending'),
                                                      'received_bytes': received}})
        finally:
            os.close(directory_fd)
            os.close(target_fd)
    except TimeoutError as exc:
        return _error(str(exc), 410)
    except (InvalidUploadPath, ValueError) as exc:
        current_app.logger.warning('NAS whole-file upload rejected upload_id=%s: %s', upload_id, exc)
        return _error(str(exc), 400)
    except (OSError, NasUnavailable) as exc:
        current_app.logger.error('NAS whole-file upload failed upload_id=%s: %s', upload_id, exc)
        return _error('NAS 不可用或文件上传失败，可重试当前文件', 503)
