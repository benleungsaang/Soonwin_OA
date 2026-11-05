"""Filesystem boundary for mobile uploads. The configured root must be a mountpoint."""
import os
import re
import secrets
import unicodedata

NAS_UPLOAD_ROOT = os.environ.get('OA_NAS_UPLOAD_ROOT', '/nas-upload')
EXPECTED_NAS_SOURCE = os.environ.get('OA_NAS_UPLOAD_SOURCE', '//192.168.110.229/美工资料')
DEFAULT_RELATIVE_DIR = '临时中转'
MAX_FILE_SIZE = 2048 * 1024 * 1024
_COMPONENT = re.compile(r'^[^/\\\x00]+$')


class NasUnavailable(Exception):
    pass


class InvalidUploadPath(Exception):
    pass


def ensure_mount():
    root = os.path.abspath(NAS_UPLOAD_ROOT)
    try:
        # The container bind mount itself is not proof that the SMB mount is live:
        # require the actual CIFS filesystem/source in mountinfo to prevent local fallback.
        found = False
        with open('/proc/self/mountinfo', 'r', encoding='utf-8') as mounts:
            for line in mounts:
                left, separator, right = line.rstrip('\n').partition(' - ')
                if not separator:
                    continue
                fields = left.split()
                details = right.split()
                if len(fields) < 5 or len(details) < 2:
                    continue
                mountpoint = fields[4]
                for encoded, decoded in (('\\040', ' '), ('\\011', '\t'), ('\\012', '\n'), ('\\134', '\\')):
                    mountpoint = mountpoint.replace(encoded, decoded)
                source = details[1]
                for encoded, decoded in (('\\040', ' '), ('\\011', '\t'), ('\\012', '\n'), ('\\134', '\\')):
                    source = source.replace(encoded, decoded)
                if mountpoint == root and details[0] == 'cifs' and source == EXPECTED_NAS_SOURCE:
                    found = True
                    break
        if not found or not os.path.isdir(root):
            raise NasUnavailable('授权 NAS CIFS 挂载不可用')
    except OSError as exc:
        raise NasUnavailable('无法确认 NAS CIFS 挂载状态') from exc
    return root


def clean_relative_path(value):
    if not isinstance(value, str) or not value or len(value) > 1024:
        raise InvalidUploadPath('请输入有效的共享内相对目录')
    value = unicodedata.normalize('NFC', value.strip()).replace('\\', '/')
    parts = value.split('/')
    if any(not p or p in ('.', '..') or not _COMPONENT.fullmatch(p) or ':' in p for p in parts):
        raise InvalidUploadPath('目录只能是授权共享根目录下的相对路径')
    return '/'.join(parts)


def open_target_dir(relative_dir):
    root = ensure_mount()
    relative_dir = clean_relative_path(relative_dir)
    flags = os.O_RDONLY | getattr(os, 'O_DIRECTORY', 0) | getattr(os, 'O_NOFOLLOW', 0)
    try:
        fd = os.open(root, flags)
    except OSError as exc:
        raise NasUnavailable('授权 NAS CIFS 挂载不可访问') from exc
    try:
        for component in relative_dir.split('/'):
            next_fd = os.open(component, flags, dir_fd=fd)
            os.close(fd)
            fd = next_fd
        return fd
    except (OSError, InvalidUploadPath) as exc:
        os.close(fd)
        if isinstance(exc, InvalidUploadPath):
            raise
        raise NasUnavailable('NAS 目标目录不可访问') from exc


def check_writable(relative_dir):
    fd = open_target_dir(relative_dir)
    name = f'.oa-write-check-{secrets.token_hex(16)}'
    file_fd = None
    try:
        file_fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, 'O_NOFOLLOW', 0), 0o600, dir_fd=fd)
        if os.write(file_fd, b'oa-nas-write-check') != 18:
            raise NasUnavailable('NAS 写入检测失败')
        os.fsync(file_fd)
    except OSError as exc:
        raise NasUnavailable('NAS 目标目录不可写') from exc
    finally:
        if file_fd is not None:
            os.close(file_fd)
        try:
            os.unlink(name, dir_fd=fd)
        except OSError:
            pass
        finally:
            os.close(fd)


def clean_filename(value):
    if not isinstance(value, str):
        raise InvalidUploadPath('文件名无效')
    name = unicodedata.normalize('NFC', value.strip())
    if not name or name in ('.', '..') or '/' in name or '\\' in name or '\x00' in name:
        raise InvalidUploadPath('文件名无效')
    name = ''.join('_' if ord(c) < 32 or c in '<>:"|?*' else c for c in name)
    name = name.strip(' .')
    if not name or len(name.encode('utf-8')) > 240:
        raise InvalidUploadPath('文件名为空或过长')
    return name
