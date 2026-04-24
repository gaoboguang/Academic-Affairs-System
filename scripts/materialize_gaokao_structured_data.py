#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "apps" / "backend"))

from app.utils.gaokao_materialize import materialize_gaokao_structured_tables  # noqa: E402
from app.utils.data_health import build_data_health_report, format_data_health_report  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Materialize embedded gaokao raw tables into project structured tables."
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=REPO_ROOT / "data" / "app.db",
        help="Target application database path.",
    )
    parser.add_argument(
        "--backup-dir",
        type=Path,
        default=REPO_ROOT / "data" / "backups",
        help="Directory for the automatic pre-materialize backup.",
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Skip creating a backup before materializing structured tables.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    print("pre_health:")
    print(format_data_health_report(build_data_health_report(args.db)))
    print("")
    result = materialize_gaokao_structured_tables(
        args.db,
        backup_dir=None if args.no_backup else args.backup_dir,
    )
    print(f"db: {result['db_path']}")
    if result["backup_path"]:
        print(f"backup: {result['backup_path']}")
    print("stats:")
    for key, value in result["stats"].items():
        print(f"- {key}: {value}")
    print("final_counts:")
    for key, value in result["final_counts"].items():
        print(f"- {key}: {value}")
    print("")
    print("post_health:")
    print(format_data_health_report(build_data_health_report(args.db)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
