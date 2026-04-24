#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "apps" / "backend"))

from app.utils.gaokao_sync import sync_gaokao_handoff_tables  # noqa: E402
from app.utils.data_health import build_data_health_report, format_data_health_report  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Merge the Windows handoff gaokao raw tables into data/app.db."
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=REPO_ROOT / "data" / "local_edu_tool" / "local_edu.sqlite3",
        help="Source handoff database path.",
    )
    parser.add_argument(
        "--target",
        type=Path,
        default=REPO_ROOT / "data" / "app.db",
        help="Target app database path.",
    )
    parser.add_argument(
        "--backup-dir",
        type=Path,
        default=REPO_ROOT / "data" / "backups",
        help="Directory for the automatic pre-merge backup.",
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Skip creating a backup before syncing tables.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    print("pre_health:")
    print(format_data_health_report(build_data_health_report(args.target)))
    print("")
    result = sync_gaokao_handoff_tables(
        args.source,
        args.target,
        backup_dir=None if args.no_backup else args.backup_dir,
    )
    print(f"source: {result['source_path']}")
    print(f"target: {result['target_path']}")
    if result["backup_path"]:
        print(f"backup: {result['backup_path']}")
    print(f"tables: {len(result['tables'])}")
    for table in result["tables"]:
        count = result["row_counts"].get(table, 0)
        print(f"- {table}: {count}")
    print("")
    print("post_health:")
    print(format_data_health_report(build_data_health_report(args.target)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
