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
BASELINE = REPO_ROOT / "docs/database/schema_baseline_20261006.json"


def main() -> int:
    config = Config(str(BACKEND_ROOT / "migrations/alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_ROOT / "migrations"))
    script = ScriptDirectory.from_config(config)
    heads = script.get_heads()
    if len(heads) != 1:
        print(f"FAIL: expected one active Alembic head, found {heads}")
        return 1

    expected = json.loads(BASELINE.read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory(prefix="oa-alembic-smoke-") as temp_dir:
        database = Path(temp_dir) / "fresh.sqlite"
        config.set_main_option("sqlalchemy.url", f"sqlite:///{database}")
        command.upgrade(config, "head")
        actual = capture_schema(database)
        differences = _differences(expected, actual)
        if differences:
            print("DRIFT")
            for difference in differences:
                print(f"- {difference}")
            return 1

    print(f"EXACT MATCH; active_head={heads[0]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
