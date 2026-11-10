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


def ensure_mount(business=False, art_share=False):
    if business:
        root = os.path.abspath(os.environ.get('OA_NAS_BUSINESS_ROOT', '/mnt/oa-dev-business'))
        expected_source = '//192.168.110.229/业务资料'
    elif art_share:
        root = os.path.abspath(os.environ.get('OA_NAS_ART_ROOT', '/mnt/nas-recovery'))
        expected_source = '//192.168.110.229/美工资料'
    else:
        root = os.path.abspath(NAS_UPLOAD_ROOT)
        expected_source = EXPECTED_NAS_SOURCE
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
                if mountpoint == root and details[0] == 'cifs' and source == expected_source:
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
    # The public address is an interface prefix; filesystem access uses the
    # separately verified CIFS mounts, never an arbitrary network path.
    for host in ('//192.168.110.229/',):
        if value.startswith(host):
            value = value[len(host):]
            break
    if value == '业务资料' or value.startswith('业务资料/'):
        value = '@business' + value[len('业务资料'):]
    elif value == '美工资料' or value.startswith('美工资料/'):
        value = '@art' + value[len('美工资料'):]
    parts = value.split('/')
    if any(not p or p in ('.', '..') or not _COMPONENT.fullmatch(p) or ':' in p for p in parts):
        raise InvalidUploadPath('目录只能是授权共享根目录下的相对路径')
    return '/'.join(parts)


def open_target_dir(relative_dir):
    relative_dir = clean_relative_path(relative_dir)
    business = relative_dir == '@business' or relative_dir.startswith('@business/')
    art_share = relative_dir == '@art' or relative_dir.startswith('@art/') or relative_dir == '@art-root'
    root = ensure_mount(business, art_share)
    if art_share:
        relative_dir = '' if relative_dir == '@art-root' else relative_dir[len('@art'):].lstrip('/')
    if business:
        relative_dir = relative_dir[len('@business'):].lstrip('/')
    flags = os.O_RDONLY | getattr(os, 'O_DIRECTORY', 0) | getattr(os, 'O_NOFOLLOW', 0)
    try:
        fd = os.open(root, flags)
    except OSError as exc:
        raise NasUnavailable('授权 NAS CIFS 挂载不可访问') from exc
    try:
        for component in filter(None, relative_dir.split('/')):
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
