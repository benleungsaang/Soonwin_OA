#!/usr/bin/env python3
"""Safe, cross-platform status/verify/upgrade entry point for Soonwin OA SQLite."""

from __future__ import annotations

import argparse
import ast
import contextlib
import importlib.util
import os
import sqlite3
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
BACKEND_ROOT = REPO_ROOT / "soonwin-os-Python-Server"
ALEMBIC_INI = BACKEND_ROOT / "migrations" / "alembic.ini"
MIGRATIONS_DIR = BACKEND_ROOT / "migrations"
LEGACY_DIR = MIGRATIONS_DIR / "archive" / "legacy_versions"
BASELINE_REVISION = "baseline_20261006"
CANONICAL_SCHEMA = REPO_ROOT / "docs" / "database" / "schema_baseline_20261006.json"


class OADatabaseError(RuntimeError):
    pass


def _dependencies() -> tuple[Any, Any, Any, Any]:
    try:
        from alembic import command
        from alembic.config import Config
        from alembic.script import ScriptDirectory
        from sqlalchemy.engine import URL, make_url
    except ModuleNotFoundError as exc:
        raise OADatabaseError(
            f"Missing Python dependency {exc.name!r}. Use the OA backend Python "
            "environment; this command will not install packages."
        ) from exc
    return command, Config, ScriptDirectory, (URL, make_url)


def _schema_verifier():
    tools_dir = BACKEND_ROOT / "tools"
    if str(tools_dir) not in sys.path:
        sys.path.insert(0, str(tools_dir))
    try:
        from verify_schema import _differences, capture_schema
    except ModuleNotFoundError as exc:
        raise OADatabaseError(f"Cannot load schema verifier: {exc}") from exc
    return _differences, capture_schema


def _load_project_config():
    config_path = BACKEND_ROOT / "config.py"
    spec = importlib.util.spec_from_file_location("soonwin_oa_db_project_config", config_path)
    if spec is None or spec.loader is None:
        raise OADatabaseError(f"Cannot load project DB configuration: {config_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sqlite_path_from_url(value: str, make_url: Any) -> Path:
    try:
        url = make_url(value)
    except Exception as exc:
        raise OADatabaseError(f"Invalid SQLite database URL: {exc}") from exc
    if url.get_backend_name() != "sqlite" or not url.database:
        raise OADatabaseError("Only file-backed SQLite database URLs are supported.")
    path = Path(url.database).expanduser()
    if not path.is_absolute():
        path = REPO_ROOT / path
    return path.resolve()


def resolve_database(argument: str | None, make_url: Any) -> Path:
    if argument is not None:
        path = Path(argument).expanduser()
        if not path.is_absolute():
            # Relative --database values are always relative to the repository root.
            path = REPO_ROOT / path
        return path.resolve()

    explicit_url = os.environ.get("OA_DATABASE_URL")
    if explicit_url:
        return _sqlite_path_from_url(explicit_url, make_url)

    project_config = _load_project_config()
    # The project's port 5001 configuration is the explicit local/dev database.
    return _sqlite_path_from_url(project_config.get_database_uri(port=5001), make_url)


def _sqlite_uri(path: Path) -> str:
    return path.resolve().as_uri() + "?mode=ro"


def _legacy_revisions() -> set[str]:
    revisions: set[str] = set()
    if not LEGACY_DIR.is_dir():
        return revisions
    for file_path in LEGACY_DIR.glob("*.py"):
        try:
            tree = ast.parse(file_path.read_text(encoding="utf-8"), filename=str(file_path))
        except (OSError, SyntaxError):
            continue
        for node in tree.body:
            if isinstance(node, ast.Assign) and any(
                isinstance(target, ast.Name) and target.id == "revision"
                for target in node.targets
            ):
                try:
                    value = ast.literal_eval(node.value)
                except (ValueError, TypeError):
                    continue
                if isinstance(value, str):
                    revisions.add(value)
    return revisions


def migration_topology(Config: Any, ScriptDirectory: Any) -> dict[str, Any]:
    try:
        cfg = Config(str(ALEMBIC_INI))
        cfg.set_main_option("script_location", str(MIGRATIONS_DIR))
        script = ScriptDirectory.from_config(cfg)
        heads = script.get_heads()
        bases = script.get_bases()
        if len(heads) != 1 or len(bases) != 1 or bases[0] != BASELINE_REVISION:
            return {"valid": False, "heads": heads, "bases": bases, "lineage": set()}
        revisions = list(script.walk_revisions(heads[0]))
        lineage = {item.revision for item in revisions}
        if BASELINE_REVISION not in lineage:
            return {"valid": False, "heads": heads, "bases": bases, "lineage": lineage}
        return {"valid": True, "heads": heads, "bases": bases, "lineage": lineage}
    except Exception as exc:
        return {"valid": False, "heads": [], "bases": [], "lineage": set(), "error": str(exc)}


def classify_revision(current: str, topology: dict[str, Any], legacy: set[str]) -> str:
    if not topology.get("valid"):
        return "UNKNOWN"
    if current in topology["lineage"]:
        return "CURRENT" if current == topology["heads"][0] else "UPGRADE_AVAILABLE"
    return "LEGACY" if current in legacy else "UNKNOWN"


def inspect_database(database: Path, topology: dict[str, Any]) -> dict[str, Any]:
    if not topology.get("valid"):
        return {
            "state": "UNKNOWN", "exists": database.exists(), "revision": None,
            "error": topology.get("error", "active Alembic topology is invalid"),
            "topology": topology,
        }
    if not database.exists():
        if not database.parent.is_dir():
            return {"state": "INVALID / ERROR", "error": "database parent directory does not exist", "exists": False, "topology": topology}
        return {
            "state": "EMPTY", "exists": False, "revision": None,
            "application_tables": [], "integrity": "not applicable",
            "topology": topology,
        }
    if not database.is_file():
        return {"state": "INVALID / ERROR", "error": "database path is not a regular file", "exists": True, "topology": topology}

    try:
        connection = sqlite3.connect(_sqlite_uri(database), uri=True, timeout=10)
        try:
            integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
            objects = connection.execute(
                "SELECT type,name FROM sqlite_schema "
                "WHERE name NOT LIKE 'sqlite_%' ORDER BY type,name"
            ).fetchall()
            table_names = {name for kind, name in objects if kind == "table"}
            app_tables = sorted(table_names - {"alembic_version"})
            version_rows: list[str] | None = None
            if "alembic_version" in table_names:
                columns = {
                    row[1] for row in connection.execute('PRAGMA table_info("alembic_version")')
                }
                if "version_num" not in columns:
                    return {
                        "state": "INVALID / ERROR", "exists": True,
                        "integrity": integrity,
                        "error": "alembic_version has no version_num column",
                        "application_tables": app_tables,
                        "topology": topology,
                    }
                version_rows = [
                    row[0] for row in connection.execute(
                        'SELECT version_num FROM "alembic_version" ORDER BY version_num'
                    ) if row[0]
                ]
        finally:
            connection.close()
    except (sqlite3.Error, OSError) as exc:
        return {"state": "INVALID / ERROR", "exists": True, "error": str(exc), "topology": topology}

    result: dict[str, Any] = {
        "exists": True, "integrity": integrity,
        "application_tables": app_tables, "topology": topology,
    }
    if integrity != "ok":
        result.update(state="INVALID / ERROR", error=f"integrity_check returned {integrity!r}")
        return result
    if not topology.get("valid"):
        result.update(state="UNKNOWN", revision=None, error=topology.get("error", "active Alembic topology is invalid"))
        return result

    if version_rows is None or len(version_rows) == 0:
        result["revision"] = None
        result["state"] = "NONEMPTY_UNVERSIONED" if app_tables or any(
            kind in {"view", "trigger", "index"} for kind, _ in objects
        ) else "EMPTY"
        return result
    if len(version_rows) != 1:
        result.update(state="UNKNOWN", revision=version_rows, error="database has multiple Alembic revisions")
        return result

    current = version_rows[0]
    result["revision"] = current
    result["state"] = classify_revision(current, topology, _legacy_revisions())
    if result["state"] == "UNKNOWN":
        result["error"] = "current revision is not in the active or archived lineage"
    return result


def database_url(database: Path, URL: Any) -> str:
    return URL.create("sqlite", database=str(database.resolve())).render_as_string(hide_password=False)


@contextlib.contextmanager
def temporary_database_url(value: str):
    existed = "OA_DATABASE_URL" in os.environ
    previous = os.environ.get("OA_DATABASE_URL")
    os.environ["OA_DATABASE_URL"] = value
    try:
        yield
    finally:
        if existed:
            os.environ["OA_DATABASE_URL"] = previous or ""
        else:
            os.environ.pop("OA_DATABASE_URL", None)


def _print_status(database: Path, result: dict[str, Any]) -> None:
    topology = result.get("topology", {})
    heads = topology.get("heads", [])
    current = result.get("revision")
    state = result.get("state", "INVALID / ERROR")
    if state in {"EMPTY", "UPGRADE_AVAILABLE"}:
        required = "YES"
    elif state in {"LEGACY", "UNKNOWN", "NONEMPTY_UNVERSIONED", "INVALID / ERROR"}:
        required = "REFUSED"
    else:
        required = "NO"
    print(f"Database: {database}")
    print(f"Database state: {state}")
    print(f"Current revision: {current if current is not None else 'none'}")
    print(f"Alembic head: {', '.join(heads) if heads else 'INVALID TOPOLOGY'}")
    print(f"Migration required: {required}")
    if result.get("integrity"):
        print(f"Integrity check: {result['integrity']}")
    if result.get("error"):
        print(f"Details: {result['error']}")


def _verify_canonical(database: Path) -> bool:
    differences_fn, capture_fn = _schema_verifier()
    import json
    expected = json.loads(CANONICAL_SCHEMA.read_text(encoding="utf-8"))
    differences = differences_fn(expected, capture_fn(database))
    if differences:
        print("Canonical schema: DRIFT")
        for difference in differences:
            print(f"- {difference}")
        return False
    print("Canonical schema: EXACT MATCH")
    return True


def command_status(database: Path, topology: dict[str, Any]) -> int:
    result = inspect_database(database, topology)
    _print_status(database, result)
    return 0 if result.get("state") not in {"INVALID / ERROR", "UNKNOWN"} else 2


def command_verify(database: Path, topology: dict[str, Any]) -> int:
    result = inspect_database(database, topology)
    _print_status(database, result)
    state = result["state"]
    if state in {"INVALID / ERROR", "UNKNOWN", "LEGACY", "NONEMPTY_UNVERSIONED", "EMPTY"}:
        print("Verification: REFUSED for this database state")
        return 2
    if result.get("integrity") != "ok":
        print("Verification: FAIL (SQLite integrity check failed)")
        return 2
    if result["revision"] == BASELINE_REVISION:
        ok = _verify_canonical(database)
        print("Verification: PASS" if ok else "Verification: FAIL")
        return 0 if ok else 1
    print("Canonical schema: NOT APPLICABLE (database is beyond the baseline revision)")
    print("Verification: PASS (SQLite integrity and active revision topology only; no current-head schema snapshot exists)")
    return 0


def backup_database(database: Path) -> Path:
    if os.name == "nt":
        # Existing Windows OA backups live here; the root is already gitignored.
        backup_root = REPO_ROOT / "windows-backup" / "database"
    else:
        data_root = Path(os.environ.get("XDG_DATA_HOME") or (Path.home() / ".local" / "share"))
        backup_root = data_root / "soonwin-oa" / "db-backups"
    backup_root = backup_root.expanduser().resolve()
    backup_root.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().astimezone().strftime("%Y%m%d_%H%M%S_%f")
    final_path = backup_root / f"{database.stem}.pre-upgrade-{timestamp}{database.suffix or '.db'}"
    temp_path = backup_root / f".{final_path.name}.{uuid.uuid4().hex}.tmp"
    try:
        source = sqlite3.connect(_sqlite_uri(database), uri=True, timeout=30)
        destination = sqlite3.connect(temp_path, timeout=30)
        try:
            source.backup(destination, pages=256, sleep=0.1)
            destination.commit()
        finally:
            destination.close()
            source.close()
        check = sqlite3.connect(_sqlite_uri(temp_path), uri=True, timeout=10)
        try:
            integrity = check.execute("PRAGMA integrity_check").fetchone()[0]
        finally:
            check.close()
        if integrity != "ok":
            raise OADatabaseError(f"backup integrity_check returned {integrity!r}")
        temp_path.replace(final_path)
        return final_path
    except Exception:
        for candidate in (temp_path, Path(str(temp_path) + "-journal"), Path(str(temp_path) + "-wal"), Path(str(temp_path) + "-shm")):
            try:
                candidate.unlink(missing_ok=True)
            except OSError:
                pass
        raise


def command_upgrade(database: Path, topology: dict[str, Any], command: Any, Config: Any, URL: Any) -> int:
    if not topology.get("valid"):
        print(f"Database: {database}")
        print(f"REFUSED: active Alembic topology is invalid: {topology.get('error', topology)}")
        return 2
    if not database.parent.is_dir():
        print(f"Database: {database}")
        print(f"REFUSED: database parent directory does not exist: {database.parent}")
        return 2

    before = inspect_database(database, topology)
    _print_status(database, before)
    state = before.get("state")
    if state in {"LEGACY", "UNKNOWN", "NONEMPTY_UNVERSIONED", "INVALID / ERROR"}:
        print(f"REFUSED: {state}; reconciliation/adoption required. No stamp or automatic repair is performed.")
        return 2
    if state == "CURRENT":
        print("Database already up to date.")
        return 0

    if state == "UPGRADE_AVAILABLE" and before.get("revision") == BASELINE_REVISION:
        if not _verify_canonical(database):
            print("REFUSED: baseline database does not match canonical schema.")
            return 2

    target = topology["heads"][0]
    print(f"Target: {target}")
    backup_path = None
    if before.get("exists") and (before.get("application_tables") or before.get("revision")):
        try:
            backup_path = backup_database(database)
        except Exception as exc:
            print(f"FAILED at backup; migration was not run: {exc}")
            return 2
        print(f"Backup: {backup_path}")

    cfg = Config(str(ALEMBIC_INI))
    cfg.set_main_option("script_location", str(MIGRATIONS_DIR))
    try:
        with temporary_database_url(database_url(database, URL)):
            command.upgrade(cfg, "head")
    except Exception as exc:
        print(f"FAILED at migration execution: {exc}")
        if backup_path:
            print(f"Manual recovery point: {backup_path}")
        return 2

    after = inspect_database(database, topology)
    _print_status(database, after)
    if after.get("state") != "CURRENT" or after.get("revision") != target:
        print("FAILED at post-upgrade revision validation; database was not automatically restored.")
        if backup_path:
            print(f"Manual recovery point: {backup_path}")
        return 2
    if after.get("integrity") != "ok":
        print("FAILED at post-upgrade integrity_check; database was not automatically restored.")
        if backup_path:
            print(f"Manual recovery point: {backup_path}")
        return 2
    if target == BASELINE_REVISION and not _verify_canonical(database):
        print("FAILED at post-upgrade baseline verification; database was not automatically restored.")
        if backup_path:
            print(f"Manual recovery point: {backup_path}")
        return 2
    print("Upgrade and post-upgrade validation: PASS")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Cross-platform Soonwin OA SQLite migration manager. Relative --database "
            "paths are resolved from the Git repository root, never from the current directory. "
            "Database selection priority: --database, explicit OA_DATABASE_URL, then the "
            "backend's configured port-5001 development database; production is never a default."
        ),
        epilog=(
            "Examples:\n"
            "  Windows: python .\\soonwin-os-Python-Server\\migrations\\tools\\oa_db.py status\n"
            "  Windows: python .\\soonwin-os-Python-Server\\migrations\\tools\\oa_db.py verify --database D:\\OA\\test.db\n"
            "  Linux:   python3 ./soonwin-os-Python-Server/migrations/tools/oa_db.py upgrade\n"
            "  Linux:   python3 ./soonwin-os-Python-Server/migrations/tools/oa_db.py upgrade --database /tmp/test.db"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="action", required=True)
    for action, help_text in (
        ("status", "Read-only database state, revision, head and integrity status."),
        ("verify", "Verify baseline schema or future revision/integrity topology."),
        ("upgrade", "Safely upgrade an empty or active-lineage database to head."),
    ):
        sub = subparsers.add_parser(action, help=help_text, description=help_text)
        sub.add_argument(
            "--database", metavar="PATH",
            help="SQLite file path; absolute, or relative to the Git repository root.",
        )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        command, Config, ScriptDirectory, sqlalchemy_url = _dependencies()
        URL, make_url = sqlalchemy_url
        database = resolve_database(args.database, make_url)
        topology = migration_topology(Config, ScriptDirectory)
        if not topology.get("valid"):
            print(f"Active Alembic topology: INVALID ({topology.get('error', topology)})")
        if args.action == "status":
            return command_status(database, topology)
        if args.action == "verify":
            return command_verify(database, topology)
        return command_upgrade(database, topology, command, Config, URL)
    except OADatabaseError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:
        print(f"ERROR during {args.action}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
