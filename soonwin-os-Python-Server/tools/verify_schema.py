#!/usr/bin/env python3
"""Read-only SQLite schema snapshot and comparison for Soonwin OA.

No table rows are read. The JSON representation is normalized from SQLite
PRAGMA metadata; sqlite_schema SQL is retained as supplemental DDL evidence.
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
from pathlib import Path
from typing import Any


def _quote_identifier(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


def _check_expressions(sql: str | None) -> list[str]:
    expressions = []
    for match in re.finditer(r"\bCHECK\s*\(", sql or "", re.IGNORECASE):
        start, depth, quote = match.end(), 1, None
        i = start
        while i < len(sql) and depth:
            char = sql[i]
            if quote:
                if char == quote:
                    if i + 1 < len(sql) and sql[i + 1] == quote:
                        i += 1
                    else:
                        quote = None
            elif char in ('"', "'", "`"):
                quote = char
            elif char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
            i += 1
        if depth == 0:
            expressions.append(" ".join(sql[start:i - 1].split()))
    return expressions


def capture_schema(database: Path) -> dict[str, Any]:
    uri = database.resolve().as_uri() + "?mode=ro"
    connection = sqlite3.connect(uri, uri=True)
    connection.row_factory = sqlite3.Row
    try:
        rows = connection.execute(
            "SELECT type, name, tbl_name, sql FROM sqlite_schema "
            "WHERE name NOT LIKE 'sqlite_%' "
            "AND type IN ('table', 'view', 'trigger', 'index') "
            "ORDER BY type, name"
        ).fetchall()
        table_names = sorted(
            row["name"] for row in rows if row["type"] == "table"
        )
        schema: dict[str, Any] = {
            "format": "soonwin-oa-sqlite-schema-v1",
            "tables": {},
            "views": [],
            "triggers": [],
        }

        for table in table_names:
            qtable = _quote_identifier(table)
            columns_raw = connection.execute(
                f"PRAGMA table_xinfo({qtable})"
            ).fetchall()
            columns = []
            for col in columns_raw:
                columns.append({
                    "name": col["name"],
                    "type": " ".join((col["type"] or "").split()).upper(),
                    "nullable": not bool(col["notnull"]) and not bool(col["pk"]),
                    "default": col["dflt_value"],
                    "primary_key_position": int(col["pk"]),
                    "hidden": int(col["hidden"]),
                })

            foreign_keys: dict[int, list[sqlite3.Row]] = {}
            for fk in connection.execute(f"PRAGMA foreign_key_list({qtable})"):
                foreign_keys.setdefault(int(fk["id"]), []).append(fk)
            normalized_fks = []
            for fk_id, parts in sorted(foreign_keys.items()):
                parts.sort(key=lambda item: int(item["seq"]))
                normalized_fks.append({
                    "columns": [part["from"] for part in parts],
                    "referenced_table": parts[0]["table"],
                    "referenced_columns": [part["to"] for part in parts],
                    "on_update": parts[0]["on_update"],
                    "on_delete": parts[0]["on_delete"],
                    "match": parts[0]["match"],
                })
            normalized_fks.sort(key=lambda fk: (
                fk["columns"], fk["referenced_table"], fk["referenced_columns"],
                fk["on_update"], fk["on_delete"], fk["match"],
            ))

            indexes = []
            for idx in connection.execute(f"PRAGMA index_list({qtable})"):
                qidx = _quote_identifier(idx["name"])
                index_cols = []
                for part in connection.execute(f"PRAGMA index_xinfo({qidx})"):
                    if int(part["key"]):
                        index_cols.append({
                            "sequence": int(part["seqno"]),
                            "column": part["name"],
                            "descending": bool(part["desc"]),
                            "collation": part["coll"],
                        })
                index_cols.sort(key=lambda item: item["sequence"])
                indexes.append({
                    "name": idx["name"],
                    "unique": bool(idx["unique"]),
                    "origin": idx["origin"],
                    "partial": bool(idx["partial"]),
                    "columns": index_cols,
                })
            indexes.sort(key=lambda item: item["name"])

            ddl_row = connection.execute(
                "SELECT sql FROM sqlite_schema WHERE type='table' AND name=?",
                (table,),
            ).fetchone()
            schema["tables"][table] = {
                "columns": columns,
                "primary_key": [
                    col["name"] for col in sorted(
                        (c for c in columns if c["primary_key_position"]),
                        key=lambda c: c["primary_key_position"],
                    )
                ],
                "foreign_keys": normalized_fks,
                "indexes": indexes,
                "checks": _check_expressions(ddl_row["sql"] if ddl_row else None),
                "autoincrement": "AUTOINCREMENT" in (ddl_row["sql"] or "").upper() if ddl_row else False,
                "sql": ddl_row["sql"] if ddl_row else None,
            }

        for row in rows:
            if row["type"] in ("view", "trigger"):
                schema["views" if row["type"] == "view" else "triggers"].append({
                    "name": row["name"],
                    "table": row["tbl_name"],
                    "sql": row["sql"],
                })
        return schema
    finally:
        connection.close()


def _dump(schema: dict[str, Any]) -> str:
    return json.dumps(schema, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _differences(expected: dict[str, Any], actual: dict[str, Any]) -> list[str]:
    differences: list[str] = []
    expected_tables = set(expected["tables"])
    actual_tables = set(actual["tables"])
    for table in sorted(expected_tables - actual_tables):
        differences.append(f"missing table: {table}")
    for table in sorted(actual_tables - expected_tables):
        differences.append(f"extra table: {table}")
    scalar_fields = ("primary_key", "foreign_keys", "checks", "autoincrement")
    column_fields = ("type", "nullable", "default", "primary_key_position", "hidden")
    for table in sorted(expected_tables & actual_tables):
        exp_table, act_table = expected["tables"][table], actual["tables"][table]
        exp_cols = {item["name"]: item for item in exp_table["columns"]}
        act_cols = {item["name"]: item for item in act_table["columns"]}
        for name in sorted(set(exp_cols) - set(act_cols)):
            differences.append(f"missing column: {table}.{name}")
        for name in sorted(set(act_cols) - set(exp_cols)):
            differences.append(f"extra column: {table}.{name}")
        for name in sorted(set(exp_cols) & set(act_cols)):
            for field in column_fields:
                if exp_cols[name][field] != act_cols[name][field]:
                    differences.append(
                        f"column difference: {table}.{name} {field}: "
                        f"expected={exp_cols[name][field]!r}, actual={act_cols[name][field]!r}"
                    )
        for field in scalar_fields:
            if exp_table[field] != act_table[field]:
                differences.append(f"{field} difference: {table}")
        exp_indexes = {item["name"]: item for item in exp_table["indexes"]}
        act_indexes = {item["name"]: item for item in act_table["indexes"]}
        for name in sorted(set(exp_indexes) - set(act_indexes)):
            label = "unique index" if exp_indexes[name]["unique"] else "index"
            differences.append(f"missing {label}: {table}.{name}")
        for name in sorted(set(act_indexes) - set(exp_indexes)):
            label = "unique index" if act_indexes[name]["unique"] else "index"
            differences.append(f"extra {label}: {table}.{name}")
        for name in sorted(set(exp_indexes) & set(act_indexes)):
            if exp_indexes[name] != act_indexes[name]:
                differences.append(f"index definition difference: {table}.{name}")
    for field in ("views", "triggers"):
        if expected[field] != actual[field]:
            differences.append(f"{field} difference")
    return differences


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("database", type=Path, help="SQLite DB file (opened read-only)")
    parser.add_argument(
        "--baseline", type=Path,
        default=Path(__file__).resolve().parents[2] / "docs/database/schema_baseline_20261006.json",
        help="canonical schema JSON",
    )
    parser.add_argument("--write-snapshot", type=Path, help="write schema-only JSON artifact")
    args = parser.parse_args()
    if not args.database.is_file():
        parser.error(f"database file does not exist: {args.database}")
    try:
        actual = capture_schema(args.database)
        if args.write_snapshot:
            args.write_snapshot.parent.mkdir(parents=True, exist_ok=True)
            args.write_snapshot.write_text(_dump(actual), encoding="utf-8")
            print(f"WROTE schema-only snapshot: {args.write_snapshot}")
            return 0
        expected = json.loads(args.baseline.read_text(encoding="utf-8"))
        differences = _differences(expected, actual)
        if differences:
            print("DRIFT")
            for difference in differences:
                print(f"- {difference}")
            return 1
        print("EXACT MATCH")
        print(f"tables={len(actual['tables'])} views={len(actual['views'])} triggers={len(actual['triggers'])}")
        return 0
    except (OSError, sqlite3.Error, json.JSONDecodeError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
