# Soonwin OA Schema Baseline

## Authority and active history

On 2026-10-06, the current production physical schema was captured as the
canonical baseline in `schema_baseline_20261006.json`. The standalone Alembic
revision is `baseline_20261006` (`down_revision = None`). Production adopted
that revision after an exact schema comparison; the stamp changed only the
Alembic bookkeeping value.

The old revisions are retained under
`soonwin-os-Python-Server/migrations/archive/legacy_versions/` for historical
audit. They are not part of the active Alembic chain. Do not restore them to
`migrations/versions/` or create a second active head.

Application startup does not call `db.create_all()` and does not migrate or
repair the database. Schema ownership belongs to explicit Alembic operations.

## Cross-platform entry point

For ordinary interactive use, run the script without a subcommand. It opens a
Chinese menu for the configured development database. You can also select a
database explicitly:

```text
Windows: python .\soonwin-os-Python-Server\migrations\tools\oa_db.py
Windows: python .\soonwin-os-Python-Server\migrations\tools\oa_db.py --database D:\OA\test.db

Linux:   python3 ./soonwin-os-Python-Server/migrations/tools/oa_db.py
Linux:   python3 ./soonwin-os-Python-Server/migrations/tools/oa_db.py --database /tmp/test.db
```

The menu offers status, verify and upgrade. Interactive upgrade requires an
explicit `y` confirmation after its normal safety preflight. Legacy, unknown
and nonempty unversioned databases remain refused.

For advanced or automated use, the existing CLI subcommands remain available
from any working directory:

```text
Windows: git pull
Windows: python .\soonwin-os-Python-Server\migrations\tools\oa_db.py status
Windows: python .\soonwin-os-Python-Server\migrations\tools\oa_db.py verify
Windows: python .\soonwin-os-Python-Server\migrations\tools\oa_db.py upgrade

Linux:   git pull
Linux:   python3 ./soonwin-os-Python-Server/migrations/tools/oa_db.py status
Linux:   python3 ./soonwin-os-Python-Server/migrations/tools/oa_db.py verify
Linux:   python3 ./soonwin-os-Python-Server/migrations/tools/oa_db.py upgrade
```

The default database follows the backend's local/development configuration
(`config.get_database_uri(port=5001)`). An explicitly set `OA_DATABASE_URL`
takes precedence; `--database PATH` takes precedence over both. The production
database is never inferred as the default. Relative `--database` paths are
resolved from the Git repository root, not the current working directory;
absolute paths are used as given. Every command prints the resolved absolute
path.

The repository's currently tracked development seed database may report
`LEGACY`; the tool will refuse to upgrade it automatically. Do not stamp it;
use the reviewed legacy reconciliation/adoption process.

For an explicitly selected database:

```text
Windows: python .\soonwin-os-Python-Server\migrations\tools\oa_db.py upgrade --database D:\OA\test.db
Linux:   python3 ./soonwin-os-Python-Server/migrations/tools/oa_db.py upgrade --database /tmp/test.db
```

The script constructs `OA_DATABASE_URL` for Alembic using SQLAlchemy URL
handling and restores the previous process environment when it exits. It
does not install dependencies. Run it in the existing OA backend Python
environment. Do not call `create_app()` as a schema bootstrap.

`status` distinguishes `EMPTY`, `CURRENT`, `UPGRADE_AVAILABLE`, `LEGACY`,
`UNKNOWN`, `NONEMPTY_UNVERSIONED`, and `INVALID / ERROR`. `upgrade` only runs
for a truly empty database or a revision on the current active lineage. It
refuses legacy, unknown, nonempty-unversioned, invalid databases and invalid
Alembic topology. It never stamps, purges, reconciles, restores a backup, or
runs archived revisions.

For an existing nonempty database that can safely upgrade, the script first
creates a consistent SQLite backup with `sqlite3.Connection.backup()` under
the local backup directory (`windows-backup/database/` on Windows, already
excluded by the repository's `.gitignore`; `$XDG_DATA_HOME/soonwin-oa/db-backups`
or `~/.local/share/soonwin-oa/db-backups` on Linux), validates its integrity,
and only then runs Alembic. A failed post-upgrade check leaves the backup
available for manual recovery and does not overwrite the database.

## Empty database and verification

The empty-database command path is:

```text
empty database -> python ./soonwin-os-Python-Server/migrations/tools/oa_db.py upgrade -> current head -> integrity check
```

At `baseline_20261006`, `verify` compares against the canonical snapshot and
requires `EXACT MATCH`. After a later active migration, that baseline snapshot
is no longer the expected head schema; `verify` reports SQLite integrity and
active revision/topology only until a reviewed current-head schema snapshot is
available.

The backend-environment smoke check creates its own temporary empty DB, runs
the active chain, and compares it to the canonical schema:

```text
python tools/migration_smoke_test.py
```

After an intentional schema migration, review and update the canonical schema
snapshot in the same change so this smoke check continues to assert the
expected head schema.

## Existing databases

Manual baseline adoption is a separate reviewed operation. Before stamping an
existing database, take a consistent SQLite backup and run the verifier
against both the target and backup. Only `EXACT MATCH` permits a baseline
stamp. For databases carrying an unknown/archived revision marker, the
operator-managed adoption procedure may use Alembic's purge option to replace
migration bookkeeping only:

```text
OA_DATABASE_URL=sqlite:////absolute/path/to/verified.db alembic -c migrations/alembic.ini stamp --purge baseline_20261006
```

Immediately verify schema and integrity again, and compare application table
row counts before and after. `stamp --purge` is not a schema repair tool; it
must never bypass a failed verifier. The `oa_db.py` script intentionally does
not expose stamp or purge.

Classify an older remote database before acting:

1. **Exact baseline match**: backup, verify, then reviewed adoption stamp.
2. **Known legacy schema**: use an explicitly reviewed reconciliation procedure.
3. **Unknown drift**: stop for manual investigation. Never blind-stamp or use
   `db.create_all()` to make it appear compatible.

## Future schema changes

Every schema change after `baseline_20261006` must be represented by a reviewed
Alembic revision whose `down_revision` points to the current active head.
Validate the migration from a truly empty database with
`soonwin-os-Python-Server/migrations/tools/oa_db.py upgrade`
and the schema verifier before adopting it to production. Application startup
must remain separate from schema migration.
