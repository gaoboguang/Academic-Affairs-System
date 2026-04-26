#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = REPO_ROOT / "data" / "app.db"
DEFAULT_BACKUP_DIR = REPO_ROOT / "data" / "backups"


POLICY_SOURCE_TYPES = {
    "admission_work_opinion",
    "policy_qa",
}

POLICY_SUMMARY_BY_TYPE = {
    "admission_work_opinion": "山东省教育招生考试院发布的当年录取工作意见，用于核对批次设置、志愿填报、投档录取规则和录取边界。",
    "policy_qa": "山东省教育招生考试院发布的招生考试或志愿填报问答，用于解释填报口径、政策边界和人工复核提示。",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Import Round 5 discovered Shandong policy source documents into gaokao_policy_reference."
    )
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH, help="SQLite app database path.")
    parser.add_argument("--backup-dir", type=Path, default=DEFAULT_BACKUP_DIR, help="Directory for DB backups.")
    parser.add_argument("--no-backup", action="store_true", help="Skip database backup.")
    parser.add_argument("--json", action="store_true", help="Output JSON.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    db_path = args.db.resolve()
    if not db_path.exists():
        print(f"database not found: {db_path}", file=sys.stderr)
        return 2

    backup_path = None
    if not args.no_backup:
        backup_path = _backup_database(db_path, args.backup_dir.resolve())

    with sqlite3.connect(str(db_path)) as conn:
        conn.row_factory = sqlite3.Row
        payload = import_policy_references(conn)

    payload["backup_path"] = str(backup_path) if backup_path else None
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    print(f"第五轮政策参考已写入：新增 {payload['created']}，更新 {payload['updated']}，当前总数 {payload['policy_reference_total']}。")
    if backup_path:
        print(f"备份：{backup_path}")
    return 0


def import_policy_references(conn: sqlite3.Connection) -> dict[str, Any]:
    _require_tables(conn)
    source_rows = conn.execute(
        """
        SELECT
            id,
            province,
            year,
            source_type,
            title,
            url,
            published_at,
            local_file_path,
            note
        FROM gaokao_source_document
        WHERE province IN ('山东', 'sd')
          AND source_type IN ('admission_work_opinion', 'policy_qa')
          AND status IN ('registered', 'file_ready', 'imported')
        ORDER BY year, source_type, id
        """
    ).fetchall()

    created = 0
    updated = 0
    items: list[dict[str, Any]] = []
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for row in source_rows:
        existing = conn.execute(
            "SELECT id FROM gaokao_policy_reference WHERE url = ? LIMIT 1",
            (row["url"],),
        ).fetchone()
        payload = {
            "province": "山东",
            "year": row["year"],
            "policy_type": row["source_type"],
            "title": row["title"],
            "url": row["url"],
            "local_path": row["local_file_path"],
            "summary": _summary_for_source(row),
            "source_level": "official",
            "version_id": None,
            "import_batch_id": row["id"],
            "published_at": row["published_at"],
            "updated_at": now,
            "status": "active",
        }
        if existing:
            conn.execute(
                """
                UPDATE gaokao_policy_reference
                SET
                    province = :province,
                    year = :year,
                    policy_type = :policy_type,
                    title = :title,
                    local_path = :local_path,
                    summary = :summary,
                    source_level = :source_level,
                    version_id = :version_id,
                    import_batch_id = :import_batch_id,
                    published_at = :published_at,
                    updated_at = :updated_at,
                    status = :status
                WHERE id = :id
                """,
                {**payload, "id": existing["id"]},
            )
            policy_reference_id = existing["id"]
            updated += 1
            created_flag = False
        else:
            conn.execute(
                """
                INSERT INTO gaokao_policy_reference (
                    province, year, policy_type, title, url, local_path, summary,
                    source_level, version_id, import_batch_id, published_at,
                    created_at, updated_at, status
                ) VALUES (
                    :province, :year, :policy_type, :title, :url, :local_path, :summary,
                    :source_level, :version_id, :import_batch_id, :published_at,
                    :created_at, :updated_at, :status
                )
                """,
                {**payload, "created_at": now},
            )
            policy_reference_id = int(conn.execute("SELECT last_insert_rowid()").fetchone()[0])
            created += 1
            created_flag = True
        items.append(
            {
                "policy_reference_id": policy_reference_id,
                "created": created_flag,
                "source_document_id": row["id"],
                "year": row["year"],
                "policy_type": row["source_type"],
                "title": row["title"],
                "url": row["url"],
            }
        )

    conn.commit()
    return {
        "created": created,
        "updated": updated,
        "total_sources": len(source_rows),
        "policy_reference_total": _count_rows(conn, "gaokao_policy_reference"),
        "items": items,
    }


def _summary_for_source(row: sqlite3.Row) -> str:
    base = POLICY_SUMMARY_BY_TYPE.get(str(row["source_type"]), "山东省教育招生考试院官方政策参考。")
    note = str(row["note"] or "").strip()
    if not note:
        return base
    return f"{base} 来源登记备注：{note}"


def _require_tables(conn: sqlite3.Connection) -> None:
    tables = {
        row["name"]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name IN ('gaokao_source_document', 'gaokao_policy_reference')"
        ).fetchall()
    }
    missing = {"gaokao_source_document", "gaokao_policy_reference"} - tables
    if missing:
        raise RuntimeError(f"missing required tables: {', '.join(sorted(missing))}")


def _count_rows(conn: sqlite3.Connection, table: str) -> int:
    return int(conn.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0])


def _backup_database(source_path: Path, backup_dir: Path) -> Path:
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup_path = backup_dir / f"{source_path.stem}_before_round5_policy_reference_import_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    with sqlite3.connect(str(source_path)) as source_conn, sqlite3.connect(str(backup_path)) as backup_conn:
        source_conn.backup(backup_conn)
    return backup_path


if __name__ == "__main__":
    raise SystemExit(main())
