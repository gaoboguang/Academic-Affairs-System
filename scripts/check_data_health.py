#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / "apps" / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.utils.data_health import build_data_health_report, format_data_health_report, report_as_json  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="检查 data/app.db 的 P0 数据健康状态。")
    parser.add_argument(
        "--db",
        type=Path,
        default=ROOT_DIR / "data" / "app.db",
        help="要检查的 SQLite 主库路径。",
    )
    parser.add_argument(
        "--province",
        default="山东",
        help="覆盖率摘要的生源省份，默认山东。",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="输出 JSON，便于后续接入页面或脚本。",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_data_health_report(args.db, province=args.province)
    print(report_as_json(report) if args.json else format_data_health_report(report))
    return 0 if report["exists"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
