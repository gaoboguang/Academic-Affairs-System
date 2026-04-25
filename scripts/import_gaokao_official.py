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
from app.services.gaokao_official_importers import (  # noqa: E402
    B1_COVERAGE_DOC,
    download_gaokao_source_document_file,
    import_b1_shandong_core,
    import_registered_gaokao_file,
    stats_item_to_dict,
    write_b1_coverage_doc,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Register or import official Shandong gaokao files for source documents."
    )
    parser.add_argument("--db", type=Path, default=None, help="SQLite app database path.")
    parser.add_argument("--source-document-id", type=int, default=None, help="gaokao_source_document.id.")
    parser.add_argument("--file", type=Path, default=None, help="Downloaded file under data/imports/gaokao/official or manual.")
    parser.add_argument(
        "--importer-name",
        default="pending_b1_parser",
        help="Importer name reserved for the later parser implementation.",
    )
    parser.add_argument("--download-from-source", action="store_true", help="Download the official attachment from the source page first.")
    parser.add_argument("--parse", action="store_true", help="Parse the registered file and write B1 data into target tables.")
    parser.add_argument("--no-download", action="store_true", help="For --b1-shandong-core, only use local official/manual files.")
    parser.add_argument(
        "--b1-shandong-core",
        action="store_true",
        help="Download and import all 2023-2025 Shandong admission, score-rank and score-line sources.",
    )
    parser.add_argument(
        "--coverage-doc",
        type=Path,
        default=Path(B1_COVERAGE_DOC),
        help="Coverage report path for B1 imports.",
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
            if args.b1_shandong_core:
                payload = import_b1_shandong_core(
                    session,
                    settings,
                    download_missing=not args.no_download,
                    coverage_doc=_resolve_coverage_doc(settings, args.coverage_doc),
                )
            else:
                if args.source_document_id is None:
                    raise ValueError("--source-document-id is required unless --b1-shandong-core is used.")
                file_path = args.file
                if args.download_from_source:
                    file_path = download_gaokao_source_document_file(
                        session,
                        settings,
                        source_document_id=args.source_document_id,
                    )
                if file_path is None:
                    raise ValueError("--file is required unless --download-from-source is used.")
                document, run = register_gaokao_local_file(
                    session,
                    settings,
                    source_document_id=args.source_document_id,
                    file_path=file_path,
                    importer_name=args.importer_name,
                )
                payload = {
                    "source_document": serialize_gaokao_source_document(document),
                    "import_run": serialize_gaokao_import_run(run),
                }
                if args.parse:
                    stats = import_registered_gaokao_file(session, settings, import_run_id=run.id)
                    write_b1_coverage_doc(session, settings, _resolve_coverage_doc(settings, args.coverage_doc))
                    payload["import_stats"] = stats_item_to_dict(stats)
                    payload["import_run"] = serialize_gaokao_import_run(run)
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
    elif args.b1_shandong_core:
        print("山东 2023-2025 高考核心官方数据已导入")
        print(f"- coverage_doc: {payload['coverage_doc']}")
        for item in payload["imports"]:
            print(
                f"- {item['year']} {item['source_type']}: "
                f"成功 {item['success_rows']}/{item['total_rows']}，"
                f"created={item['created_rows']}，updated={item['updated_rows']}"
            )
    else:
        document = payload["source_document"]
        run = payload["import_run"]
        print("本地高考官方文件已处理")
        print(f"- source_document_id: {document['id']}")
        print(f"- title: {document['title']}")
        print(f"- local_file_path: {document['local_file_path']}")
        print(f"- file_sha256: {document['file_sha256']}")
        print(f"- import_run_id: {run['id']}")
        print(f"- status: {run['status']}")
        if args.parse:
            stats = payload["import_stats"]
            print(f"- rows: {stats['success_rows']}/{stats['total_rows']} success")
            print("- note: 已登记文件、导入批次，并执行 B1 官方数据解析。")
        else:
            print("- note: 已登记文件和导入批次，可加 `--parse` 执行 B1 解析写库。")
    return 0


def _build_settings(db_path: Path | None) -> Settings:
    if db_path is None:
        return Settings()
    return Settings(data_dir=db_path.parent, db_path=db_path)


def _resolve_coverage_doc(settings: Settings, path: Path) -> Path:
    return path if path.is_absolute() else settings.project_root / path


if __name__ == "__main__":
    raise SystemExit(main())
