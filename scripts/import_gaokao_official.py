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
from app.services.gaokao_imports import (  # noqa: E402
    ensure_gaokao_import_directories,
    register_gaokao_local_file,
    serialize_gaokao_import_run,
    serialize_gaokao_source_document,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Register a manually downloaded official gaokao file for a source document."
    )
    parser.add_argument("--db", type=Path, default=None, help="SQLite app database path.")
    parser.add_argument("--source-document-id", type=int, required=True, help="gaokao_source_document.id.")
    parser.add_argument("--file", type=Path, required=True, help="Downloaded file under data/imports/gaokao/official or manual.")
    parser.add_argument(
        "--importer-name",
        default="pending_b1_parser",
        help="Importer name reserved for the later parser implementation.",
    )
    parser.add_argument("--json", action="store_true", help="Output JSON.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    settings = _build_settings(args.db)
    ensure_gaokao_import_directories(settings)
    manager = DatabaseManager(settings.database_url, settings.debug)

    try:
        with manager.session_scope() as session:
            document, run = register_gaokao_local_file(
                session,
                settings,
                source_document_id=args.source_document_id,
                file_path=args.file,
                importer_name=args.importer_name,
            )
            payload = {
                "source_document": serialize_gaokao_source_document(document),
                "import_run": serialize_gaokao_import_run(run),
            }
    except OperationalError as exc:
        if "gaokao_source_document" in str(exc):
            print("高考来源登记表尚未创建，请先运行 `npm run backend:migrate`。", file=sys.stderr)
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
        document = payload["source_document"]
        run = payload["import_run"]
        print("本地高考官方文件已登记")
        print(f"- source_document_id: {document['id']}")
        print(f"- title: {document['title']}")
        print(f"- local_file_path: {document['local_file_path']}")
        print(f"- file_sha256: {document['file_sha256']}")
        print(f"- import_run_id: {run['id']}")
        print(f"- status: {run['status']}")
        print("- note: 已登记文件和导入批次，具体解析写库由 B1 接入同一 import_run。")
    return 0


def _build_settings(db_path: Path | None) -> Settings:
    if db_path is None:
        return Settings()
    return Settings(data_dir=db_path.parent, db_path=db_path)


if __name__ == "__main__":
    raise SystemExit(main())
