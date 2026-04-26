#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from sqlalchemy.exc import OperationalError


REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "apps" / "backend"))

from app.core.config import Settings  # noqa: E402
from app.db.session import DatabaseManager  # noqa: E402
from app.services.gaokao_official_importers import (  # noqa: E402
    import_b1_shandong_core,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Import Shandong official gaokao admission, score-rank and score-line data."
    )
    parser.add_argument("--db", type=Path, default=None, help="SQLite app database path.")
    parser.add_argument("--year", type=int, action="append", choices=[2020, 2021, 2022, 2023, 2024, 2025], help="Limit import year.")
    parser.add_argument(
        "--source-type",
        action="append",
        choices=["admission_result", "score_rank_segment", "score_line"],
        help="Limit source type.",
    )
    parser.add_argument("--no-download", action="store_true", help="Only use files already placed under data/imports/gaokao.")
    parser.add_argument(
        "--coverage-doc",
        type=Path,
        default=REPO_ROOT / "docs" / "gaokao-shandong-2023-2025-coverage.md",
        help="Coverage markdown output path.",
    )
    parser.add_argument("--json", action="store_true", help="Output JSON.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    settings = _build_settings(args.db)
    manager = DatabaseManager(settings.database_url, settings.debug)
    years = tuple(args.year or [2023, 2024, 2025])
    source_types = tuple(args.source_type or ["admission_result", "score_rank_segment", "score_line"])

    try:
        with manager.session_scope() as session:
            doc_path = args.coverage_doc
            if not doc_path.is_absolute():
                doc_path = REPO_ROOT / doc_path
            payload = import_b1_shandong_core(
                session,
                settings,
                years=years,
                source_types=source_types,
                download_missing=not args.no_download,
                coverage_doc=doc_path,
            )
    except OperationalError as exc:
        if "gaokao_source_document" in str(exc) or "gaokao_import_run" in str(exc):
            print("高考来源导入表尚未创建，请先运行 `npm run backend:migrate`。", file=sys.stderr)
            return 2
        raise
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    finally:
        manager.dispose()

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print("山东官方核心数据导入完成")
        for item in payload["imports"]:
            print(
                f"- {item['year']} {item['source_type']}: "
                f"成功 {item['success_rows']}，失败 {item['failed_rows']}，"
                f"新增 {item['created_rows']}，更新 {item['updated_rows']}"
            )
        print(f"- 覆盖文档：{payload.get('coverage_doc')}")
    return 0


def _build_settings(db_path: Path | None) -> Settings:
    if db_path is None:
        return Settings()
    return Settings(data_dir=db_path.parent, db_path=db_path)


if __name__ == "__main__":
    raise SystemExit(main())
