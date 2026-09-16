"""Windows-only SQLite backup helper for the production OA database."""

from __future__ import annotations

import re
import sqlite3
import threading
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
PRODUCTION_DB = ROOT_DIR / "soonwin-os-Python-Server" / "soonwin_oa.db"
BACKUP_DIR = ROOT_DIR / "windows-backup" / "database"
BACKUP_LOG = BACKUP_DIR / "database-backup.log"
BACKUP_PATTERN = re.compile(r"^soonwin_oa_(\d{8})_(\d{6})\.db$")
BACKUP_LOCK = threading.Lock()


@dataclass(frozen=True)
class BackupResult:
    success: bool
    path: Path | None
    message: str
    finished_at: datetime


def _write_log(message: str) -> None:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    with BACKUP_LOG.open("a", encoding="utf-8", buffering=1) as handle:
        handle.write(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {message}\n")


def _is_valid_backup_name(path: Path) -> bool:
    return BACKUP_PATTERN.fullmatch(path.name) is not None


def _cleanup_old_backups(now: datetime) -> None:
    cutoff = now - timedelta(days=14)
    if not BACKUP_DIR.exists():
        return
    for path in BACKUP_DIR.iterdir():
        if not path.is_file() or not _is_valid_backup_name(path):
            continue
        match = BACKUP_PATTERN.fullmatch(path.name)
        assert match is not None
        try:
            backup_time = datetime.strptime(
                f"{match.group(1)}{match.group(2)}", "%Y%m%d%H%M%S"
            )
        except ValueError:
            continue
        if backup_time < cutoff:
            try:
                path.unlink()
                _write_log(f"RETENTION deleted {path.name}")
            except OSError as exc:
                _write_log(f"RETENTION FAILED {path.name}: {exc}")


def backup_database(now: datetime | None = None) -> BackupResult:
    """Create and validate one SQLite backup using sqlite3.Connection.backup."""
    finished_at = now or datetime.now()
    if not BACKUP_LOCK.acquire(blocking=False):
        result = BackupResult(False, None, "backup already running", finished_at)
        _write_log(f"FAILED: {result.message}")
        return result

    source = None
    destination = None
    target: Path | None = None
    try:
        if not PRODUCTION_DB.exists():
            raise FileNotFoundError(f"production database not found: {PRODUCTION_DB}")

        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        target = BACKUP_DIR / f"soonwin_oa_{finished_at:%Y%m%d_%H%M%S}.db"
        source = sqlite3.connect(str(PRODUCTION_DB), timeout=30)
        destination = sqlite3.connect(str(target), timeout=30)
        source.backup(destination)
        destination.commit()
        destination.close()
        destination = None
        source.close()
        source = None

        if not target.exists() or target.stat().st_size <= 0:
            raise RuntimeError("backup file is missing or empty")

        with sqlite3.connect(str(target), timeout=10) as validation:
            check = validation.execute("PRAGMA quick_check").fetchone()
        if not check or check[0] != "ok":
            raise RuntimeError(f"SQLite quick_check failed: {check!r}")

        _write_log(f"SUCCESS {target.name} size={target.stat().st_size}")
        _cleanup_old_backups(finished_at)
        return BackupResult(True, target, "backup succeeded", finished_at)
    except Exception as exc:
        _write_log(f"FAILED {target.name if target else ''}: {exc}")
        return BackupResult(False, target, str(exc), finished_at)
    finally:
        if destination is not None:
            destination.close()
        if source is not None:
            source.close()
        BACKUP_LOCK.release()
