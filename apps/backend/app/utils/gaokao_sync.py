from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path


GAOKAO_EXTRA_TABLES = {
    "data_import_batch",
    "data_import_error_log",
    "score_rank_segment",
}
GAOKAO_SYNC_ORDER = [
    "data_import_batch",
    "data_import_error_log",
    "gaokao_source_registry",
    "gaokao_batch_dict",
    "gaokao_career_direction",
    "gaokao_pathway_dict",
    "gaokao_province_rule_version",
    "gaokao_province_rule",
    "gaokao_score_line",
    "gaokao_score_transform_rule",
    "gaokao_subject_requirement_dict",
    "gaokao_college",
    "gaokao_college_tag",
    "gaokao_major",
    "gaokao_major_career_mapping",
    "gaokao_policy_reference",
    "gaokao_subject_requirement",
    "gaokao_college_chapter_rule",
    "gaokao_admission_plan",
    "gaokao_admission_result",
    "score_rank_segment",
]
EMBEDDED_GAOKAO_HINT_TABLES = (
    "gaokao_college",
    "gaokao_admission_plan",
    "gaokao_subject_requirement_dict",
)


def app_db_has_embedded_gaokao_tables(db_path: Path) -> bool:
    """Historically returned True when raw tables lived inside app.db.

    The 22 raw tables are now isolated to the sidecar database; keeping the
    function around as a no-op avoids touching all legacy import sites.
    """
    return False


def sync_gaokao_handoff_tables(
    source_path: Path,
    target_path: Path,
    *,
    backup_dir: Path | None = None,
) -> dict[str, object]:
    if not source_path.exists():
        raise FileNotFoundError(f"source database not found: {source_path}")
    if not target_path.exists():
        raise FileNotFoundError(f"target database not found: {target_path}")

    backup_path = None
    if backup_dir is not None:
        backup_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"{target_path.stem}_before_gaokao_handoff_merge_{timestamp}.db"
        backup_sqlite_database(target_path, backup_path)

    with sqlite3.connect(f"file:{source_path}?mode=ro", uri=True) as source_conn:
        source_conn.row_factory = sqlite3.Row
        tables = list_sync_tables(source_conn)
        table_sql = {}
        index_sql = {}
        row_counts = {}
        for table in tables:
            create_row = source_conn.execute(
                "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = ?",
                (table,),
            ).fetchone()
            if not create_row or not create_row["sql"]:
                continue
            table_sql[table] = create_row["sql"]
            index_sql[table] = [
                row["sql"]
                for row in source_conn.execute(
                    """
                    SELECT sql
                    FROM sqlite_master
                    WHERE type = 'index' AND tbl_name = ? AND sql IS NOT NULL
                    ORDER BY name
                    """,
                    (table,),
                ).fetchall()
                if row["sql"]
            ]
            row_counts[table] = source_conn.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]

    with sqlite3.connect(str(target_path)) as target_conn:
        target_conn.execute("PRAGMA foreign_keys = OFF")
        target_conn.execute("PRAGMA journal_mode = WAL")
        try:
            for table in tables:
                if table not in table_sql:
                    continue
                target_conn.execute(f'DROP TABLE IF EXISTS "{table}"')
                target_conn.execute(table_sql[table])
                _copy_table_rows(source_conn, target_conn, table)
                for sql in index_sql[table]:
                    target_conn.execute(sql)
            target_conn.commit()
        finally:
            target_conn.execute("PRAGMA foreign_keys = ON")

    return {
        "source_path": str(source_path),
        "target_path": str(target_path),
        "backup_path": str(backup_path) if backup_path else None,
        "tables": tables,
        "row_counts": row_counts,
    }


def backup_sqlite_database(source_path: Path, backup_path: Path) -> None:
    with sqlite3.connect(str(source_path)) as source_conn, sqlite3.connect(str(backup_path)) as backup_conn:
        source_conn.backup(backup_conn)


def list_sync_tables(source_conn: sqlite3.Connection) -> list[str]:
    rows = source_conn.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table' AND name NOT LIKE 'sqlite_%'
        ORDER BY name
        """
    ).fetchall()
    available = {row[0] for row in rows}
    ordered = [table for table in GAOKAO_SYNC_ORDER if table in available]
    ordered_set = set(ordered)
    ordered.extend(
        sorted(
            table
            for table in available
            if (table.startswith("gaokao_") or table in GAOKAO_EXTRA_TABLES) and table not in ordered_set
        )
    )
    return ordered


def _copy_table_rows(
    source_conn: sqlite3.Connection,
    target_conn: sqlite3.Connection,
    table: str,
    *,
    batch_size: int = 2000,
) -> None:
    source_cursor = source_conn.execute(f'SELECT * FROM "{table}"')
    columns = [item[0] for item in source_cursor.description or []]
    if not columns:
        return
    quoted_columns = ", ".join(f'"{column}"' for column in columns)
    placeholders = ", ".join(["?"] * len(columns))
    insert_sql = f'INSERT INTO "{table}" ({quoted_columns}) VALUES ({placeholders})'
    while True:
        rows = source_cursor.fetchmany(batch_size)
        if not rows:
            break
        target_conn.executemany(insert_sql, rows)
