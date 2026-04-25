from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from datetime import date
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / "apps" / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.core.config import Settings  # noqa: E402
from app.db.session import DatabaseManager  # noqa: E402
from app.services.gaokao_pathways import bootstrap_shandong_pathways  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Bootstrap 山东升学路径和 D2 官方规则字典。")
    parser.add_argument("--target-year", type=int, default=2026, help="目标年份，默认 2026。")
    parser.add_argument(
        "--backup-dir",
        type=Path,
        default=ROOT_DIR / "data" / "backups",
        help="初始化前的自动备份目录。",
    )
    parser.add_argument("--no-backup", action="store_true", help="跳过主库备份。")
    parser.add_argument("--json", action="store_true", help="输出 JSON 结果。")
    return parser.parse_args()


def backup_sqlite_database(source_path: Path, backup_dir: Path, target_year: int) -> Path | None:
    if not source_path.exists():
        return None
    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = date.today().strftime("%Y%m%d")
    suffix = 1
    while True:
        backup_path = backup_dir / (
            f"{source_path.stem}_before_pathway_bootstrap_{target_year}_{timestamp}_{suffix:02d}.db"
        )
        if not backup_path.exists():
            break
        suffix += 1
    with sqlite3.connect(str(source_path)) as source_conn, sqlite3.connect(str(backup_path)) as backup_conn:
        source_conn.backup(backup_conn)
    return backup_path


def main() -> None:
    args = parse_args()
    settings = Settings()
    backup_path = None
    if not args.no_backup:
        backup_path = backup_sqlite_database(settings.db_path, args.backup_dir, args.target_year)

    db = DatabaseManager(settings.database_url, settings.debug)
    try:
        with db.session_scope() as session:
            result = bootstrap_shandong_pathways(session, target_year=args.target_year)
    finally:
        db.dispose()

    payload = result.model_dump()
    payload["backup_path"] = str(backup_path) if backup_path else None
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return

    if backup_path:
        print(f"backup: {backup_path}")
    elif args.no_backup:
        print("backup: skipped by --no-backup")
    else:
        print(f"backup: skipped because database does not exist: {settings.db_path}")
    print(
        "bootstrap: "
        f"province={result.province}, target_year={result.target_year}, "
        f"pathways created={result.created_count}, skipped={result.skipped_count}, "
        f"rules created={result.rule_created_count}, skipped={result.rule_skipped_count}"
    )


if __name__ == "__main__":
    main()
