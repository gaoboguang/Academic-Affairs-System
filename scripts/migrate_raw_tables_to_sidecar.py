"""Migrate raw gaokao tables out of data/app.db into the sidecar database.

Usage:
    python scripts/migrate_raw_tables_to_sidecar.py \
        --app-db data/app.db \
        --sidecar-db data/local_edu_tool/local_edu.sqlite3 \
        --dry-run

Add `--apply` to actually move the tables. The script always backs up both
databases to `data/backups/` before writing unless `--no-backup` is passed.

Design:
- Take a full file-copy of both databases into `data/backups/` first.
- Open app-db connection, ATTACH sidecar as `side`.
- For each raw table (22 of them):
    * Drop any leftover copy in sidecar.
    * Recreate schema (including indexes) inside sidecar.
    * `INSERT INTO side.<t> SELECT * FROM main.<t>`.
    * Verify row counts and column names match.
- After all tables succeed and counts match, DROP them from app-db.
- VACUUM app-db to reclaim space.
"""
from __future__ import annotations

import argparse
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent

RAW_TABLES: tuple[str, ...] = (
    # dependency order: parents first, children last
    "gaokao_source_registry",
    "gaokao_batch_dict",
    "gaokao_pathway_dict",
    "gaokao_career_direction",
    "gaokao_province_rule_version",
    "gaokao_province_rule",
    "gaokao_subject_requirement_dict",
    "gaokao_policy_reference",
    "gaokao_score_line",
    "gaokao_score_transform_rule",
    "gaokao_college",
    "gaokao_college_tag",
    "gaokao_college_chapter_rule",
    "gaokao_major",
    "gaokao_major_career_mapping",
    "gaokao_subject_requirement",
    "gaokao_admission_plan",
    "gaokao_admission_result",
    "score_rank_segment",
    "data_import_batch",
    "data_import_error_log",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--app-db",
        type=Path,
        default=REPO_ROOT / "data" / "app.db",
    )
    parser.add_argument(
        "--sidecar-db",
        type=Path,
        default=REPO_ROOT / "data" / "local_edu_tool" / "local_edu.sqlite3",
    )
    parser.add_argument(
        "--backup-dir",
        type=Path,
        default=REPO_ROOT / "data" / "backups",
    )
    parser.add_argument("--dry-run", action="store_true", help="报告不改动")
    parser.add_argument("--apply", action="store_true", help="实际执行迁移")
    parser.add_argument("--no-backup", action="store_true", help="跳过自动备份（不推荐）")
    return parser.parse_args()


def resolve_symlink(path: Path) -> Path:
    if path.is_symlink():
        return path.resolve()
    return path


def backup_file(source: Path, backup_dir: Path, tag: str) -> Path:
    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = backup_dir / f"{source.stem}_before_raw_migration_{tag}_{timestamp}{source.suffix}"
    shutil.copy2(source, dest)
    return dest


def list_tables(conn: sqlite3.Connection, schema: str = "main") -> set[str]:
    rows = conn.execute(
        f"SELECT name FROM {schema}.sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    ).fetchall()
    return {row[0] for row in rows}


def table_row_count(conn: sqlite3.Connection, schema: str, table: str) -> int:
    return int(conn.execute(f'SELECT count(*) FROM {schema}."{table}"').fetchone()[0])


def table_columns(conn: sqlite3.Connection, schema: str, table: str) -> list[str]:
    rows = conn.execute(f'PRAGMA {schema}.table_info("{table}")').fetchall()
    return [row[1] for row in rows]


def fetch_schema_objects(
    conn: sqlite3.Connection, schema: str, table: str
) -> tuple[str | None, list[str]]:
    create_row = conn.execute(
        f"SELECT sql FROM {schema}.sqlite_master WHERE type='table' AND name=?",
        (table,),
    ).fetchone()
    create_sql = create_row[0] if create_row else None
    index_rows = conn.execute(
        f"SELECT sql FROM {schema}.sqlite_master WHERE type='index' AND tbl_name=? AND sql IS NOT NULL ORDER BY name",
        (table,),
    ).fetchall()
    index_sqls = [row[0] for row in index_rows if row[0]]
    return create_sql, index_sqls


def copy_table_to_sidecar(conn: sqlite3.Connection, table: str) -> int:
    create_sql, index_sqls = fetch_schema_objects(conn, "main", table)
    if not create_sql:
        raise RuntimeError(f"app.db 中找不到 raw 表 {table} 的 CREATE 语句")
    src_columns = table_columns(conn, "main", table)
    conn.execute(f'DROP TABLE IF EXISTS side."{table}"')
    # Rewrite CREATE TABLE ... into side."..."; CREATE statement may use either
    # quoted or unquoted table name.
    rewritten_create = _rewrite_create_to_sidecar(create_sql, table)
    conn.execute(rewritten_create)
    for index_sql in index_sqls:
        rewritten_index = _rewrite_index_to_sidecar(index_sql, table)
        conn.execute(rewritten_index)
    col_list = ", ".join(f'"{col}"' for col in src_columns)
    conn.execute(
        f'INSERT INTO side."{table}" ({col_list}) SELECT {col_list} FROM main."{table}"'
    )
    side_count = table_row_count(conn, "side", table)
    main_count = table_row_count(conn, "main", table)
    if side_count != main_count:
        raise RuntimeError(f"表 {table} 行数对不上: main={main_count}, side={side_count}")
    side_columns = table_columns(conn, "side", table)
    if side_columns != src_columns:
        raise RuntimeError(
            f"表 {table} 字段不一致: main={src_columns}, side={side_columns}"
        )
    return side_count


def _rewrite_create_to_sidecar(sql: str, table: str) -> str:
    # Accept: CREATE TABLE <name>, CREATE TABLE "<name>"
    prefixes = (
        f'CREATE TABLE "{table}"',
        f"CREATE TABLE {table}",
    )
    for prefix in prefixes:
        if sql.startswith(prefix):
            return f'CREATE TABLE side."{table}"' + sql[len(prefix):]
    raise RuntimeError(f"无法识别 CREATE TABLE 语句: {sql[:80]!r}")


def _rewrite_index_to_sidecar(sql: str, table: str) -> str:
    # SQLite emits: CREATE [UNIQUE] INDEX <idx> ON <table> (...)
    marker = f" ON {table} "
    quoted_marker = f' ON "{table}" '
    if marker in sql:
        head, tail = sql.split(marker, 1)
        # Put index into side schema by qualifying the index name.
        return _qualify_index_name(head) + f' ON "{table}" ' + tail
    if quoted_marker in sql:
        head, tail = sql.split(quoted_marker, 1)
        return _qualify_index_name(head) + f' ON "{table}" ' + tail
    raise RuntimeError(f"无法识别索引语句: {sql[:80]!r}")


def _qualify_index_name(head: str) -> str:
    # head looks like: CREATE [UNIQUE] INDEX <name>
    tokens = head.strip().split()
    if len(tokens) < 3:
        raise RuntimeError(f"无法解析索引语句头部: {head!r}")
    name = tokens[-1]
    if name.startswith('"') and name.endswith('"'):
        name_inner = name[1:-1]
    else:
        name_inner = name
    tokens[-1] = f'side."{name_inner}"'
    return " ".join(tokens)


def drop_tables_from_main(conn: sqlite3.Connection, tables: list[str]) -> None:
    # Drop in reverse order to respect FKs (children first).
    conn.execute("PRAGMA foreign_keys = OFF")
    try:
        for table in reversed(tables):
            conn.execute(f'DROP TABLE IF EXISTS main."{table}"')
    finally:
        conn.execute("PRAGMA foreign_keys = ON")


def report(args: argparse.Namespace) -> dict[str, object]:
    app_db = resolve_symlink(args.app_db)
    sidecar_db = resolve_symlink(args.sidecar_db)

    with sqlite3.connect(str(app_db)) as app_conn:
        main_tables = list_tables(app_conn)
        main_rows = {t: table_row_count(app_conn, "main", t) for t in RAW_TABLES if t in main_tables}

    with sqlite3.connect(str(sidecar_db)) as side_conn:
        side_tables = list_tables(side_conn)
        side_rows = {t: table_row_count(side_conn, "main", t) for t in RAW_TABLES if t in side_tables}

    return {
        "app_db": str(app_db),
        "sidecar_db": str(sidecar_db),
        "main_tables_in_app": sorted(set(RAW_TABLES) & main_tables),
        "side_tables_in_sidecar": sorted(side_tables & set(RAW_TABLES)),
        "main_rows": main_rows,
        "side_rows": side_rows,
    }


def apply_migration(args: argparse.Namespace) -> dict[str, object]:
    app_db = resolve_symlink(args.app_db)
    sidecar_symlink = args.sidecar_db
    sidecar_db = resolve_symlink(args.sidecar_db)

    if not app_db.exists():
        raise FileNotFoundError(f"app.db 不存在: {app_db}")

    backups: dict[str, str] = {}
    if not args.no_backup:
        backups["app_db"] = str(backup_file(app_db, args.backup_dir, "app"))
        if sidecar_db.exists():
            backups["sidecar"] = str(backup_file(sidecar_db, args.backup_dir, "sidecar"))

    # Always rebuild sidecar next to data/local_edu_tool/local_edu.sqlite3 as a
    # fresh file; if it's currently a symlink (pointing at the read-only
    # handoff), replace it with a real database.
    real_sidecar_path = sidecar_symlink
    if sidecar_symlink.is_symlink():
        sidecar_symlink.unlink()
    if real_sidecar_path.exists():
        # Clear any previous sidecar content so we always start clean.
        real_sidecar_path.unlink()
    real_sidecar_path.parent.mkdir(parents=True, exist_ok=True)
    # Touch an empty sqlite file.
    with sqlite3.connect(str(real_sidecar_path)) as side_init:
        side_init.execute("PRAGMA journal_mode=WAL")

    moved: dict[str, int] = {}
    with sqlite3.connect(str(app_db)) as conn:
        conn.execute("PRAGMA foreign_keys = OFF")
        conn.execute(f"ATTACH DATABASE '{real_sidecar_path}' AS side")
        try:
            main_tables = list_tables(conn, "main")
            for table in RAW_TABLES:
                if table not in main_tables:
                    continue
                moved[table] = copy_table_to_sidecar(conn, table)
            drop_tables_from_main(conn, [t for t in RAW_TABLES if t in main_tables])
            conn.commit()
        finally:
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("DETACH DATABASE side")

    # VACUUM after the write transaction completes.
    with sqlite3.connect(str(app_db)) as conn:
        conn.execute("VACUUM")

    return {
        "app_db": str(app_db),
        "sidecar_db": str(real_sidecar_path),
        "moved_tables": moved,
        "backups": backups,
    }


def main() -> int:
    args = parse_args()
    if args.dry_run or not args.apply:
        status = report(args)
        print("dry-run, 当前状态:")
        for key, value in status.items():
            print(f"- {key}: {value}")
        print("")
        print("如需实际迁移, 追加 --apply")
        return 0

    result = apply_migration(args)
    print("迁移完成:")
    for key, value in result.items():
        print(f"- {key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
