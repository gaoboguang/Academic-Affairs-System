from __future__ import annotations

import argparse
import sqlite3
import sys
from datetime import date
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / "apps" / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.core.config import Settings  # noqa: E402
from app.db.session import DatabaseManager  # noqa: E402
from app.services._recommendations_rules import bootstrap_special_type_rules  # noqa: E402
from app.utils.data_health import build_data_health_report, format_data_health_report  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Bootstrap 山东特殊类型规则字典。")
    parser.add_argument(
        "--year",
        type=int,
        action="append",
        help="目标年份，可重复传入；默认使用当前年份。",
    )
    parser.add_argument(
        "--backup-dir",
        type=Path,
        default=ROOT_DIR / "data" / "backups",
        help="规则初始化前的自动备份目录。",
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="跳过规则初始化前的主库备份。",
    )
    return parser.parse_args()


def backup_sqlite_database(source_path: Path, backup_dir: Path) -> Path | None:
    if not source_path.exists():
        return None
    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = date.today().strftime("%Y%m%d")
    suffix = 1
    while True:
        backup_path = backup_dir / f"{source_path.stem}_before_special_type_bootstrap_{timestamp}_{suffix:02d}.db"
        if not backup_path.exists():
            break
        suffix += 1
    with sqlite3.connect(str(source_path)) as source_conn, sqlite3.connect(str(backup_path)) as backup_conn:
        source_conn.backup(backup_conn)
    return backup_path


def main() -> None:
    args = parse_args()
    years = args.year or [date.today().year]
    settings = Settings()
    print("pre_health:")
    print(format_data_health_report(build_data_health_report(settings.db_path)))
    print("")
    backup_path = None if args.no_backup else backup_sqlite_database(settings.db_path, args.backup_dir)
    if backup_path:
        print(f"backup: {backup_path}")
    elif args.no_backup:
        print("backup: skipped by --no-backup")
    else:
        print(f"backup: skipped because database does not exist: {settings.db_path}")
    db = DatabaseManager(settings.database_url, settings.debug)
    try:
        with db.session_scope() as session:
            for year in years:
                result = bootstrap_special_type_rules(session, year=year, record_audit=False)
                print(
                    f"{year}: created={result.created_count}, "
                    f"skipped={result.skipped_count}, total={result.total_count}"
                )
    finally:
        db.dispose()
    print("")
    print("post_health:")
    print(format_data_health_report(build_data_health_report(settings.db_path)))


if __name__ == "__main__":
    main()
