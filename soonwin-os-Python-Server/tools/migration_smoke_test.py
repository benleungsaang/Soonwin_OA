#!/usr/bin/env python3
"""Run the active Alembic chain on an empty temporary SQLite database."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory

from verify_schema import _differences, capture_schema


REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = Path(__file__).resolve().parents[1]
PREVIOUS_BASELINE = REPO_ROOT / "docs/database/schema_baseline_20261009.json"
BASELINE = REPO_ROOT / "docs/database/schema_baseline_20261106.json"
PREVIOUS_HEAD = "device_binding_qr_sessions_20261009"


def verify(database: Path, expected: dict, stage: str) -> bool:
    differences = _differences(expected, capture_schema(database))
    if differences:
        print(f"DRIFT at {stage}")
        for difference in differences:
            print(f"- {difference}")
        return False
    return True


def main() -> int:
    config = Config(str(BACKEND_ROOT / "migrations/alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_ROOT / "migrations"))
    script = ScriptDirectory.from_config(config)
    heads = script.get_heads()
    if len(heads) != 1:
        print(f"FAIL: expected one active Alembic head, found {heads}")
        return 1

    expected = json.loads(BASELINE.read_text(encoding="utf-8"))
    previous = json.loads(PREVIOUS_BASELINE.read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory(prefix="oa-alembic-smoke-") as temp_dir:
        database = Path(temp_dir) / "fresh.sqlite"
        config.set_main_option("sqlalchemy.url", f"sqlite:///{database}")
        command.upgrade(config, PREVIOUS_HEAD)
        if not verify(database, previous, "previous revision"):
            return 1
        command.upgrade(config, "head")
        if not verify(database, expected, "upgrade"):
            return 1
        command.downgrade(config, PREVIOUS_HEAD)
        if not verify(database, previous, "downgrade"):
            return 1
        command.upgrade(config, "head")
        if not verify(database, expected, "re-upgrade"):
            return 1

    print(f"EXACT MATCH; upgrade, downgrade and re-upgrade; active_head={heads[0]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
