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
    list_gaokao_source_documents,
    seed_default_gaokao_sources,
    serialize_gaokao_source_document,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Register official gaokao source documents and prepare local import directories."
    )
    parser.add_argument("--db", type=Path, default=None, help="SQLite app database path.")
    parser.add_argument("--seed-defaults", action="store_true", help="Upsert the default Shandong official sources.")
    parser.add_argument("--ensure-dirs", action="store_true", help="Create data/imports/gaokao directories.")
    parser.add_argument("--list", action="store_true", help="List registered gaokao source documents.")
    parser.add_argument("--json", action="store_true", help="Output JSON.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    settings = _build_settings(args.db)
    manager = DatabaseManager(settings.database_url, settings.debug)
    payload: dict[str, object] = {}
    should_seed = args.seed_defaults or not any([args.ensure_dirs, args.list])

    try:
        with manager.session_scope() as session:
            if args.ensure_dirs and not should_seed:
                payload["directories"] = ensure_gaokao_import_directories(settings)
            if should_seed:
                payload["seed"] = seed_default_gaokao_sources(session, settings)
            if args.list or should_seed:
                payload["source_documents"] = [
                    serialize_gaokao_source_document(item) for item in list_gaokao_source_documents(session)
                ]
    except OperationalError as exc:
        if "gaokao_source_document" in str(exc):
            print("高考来源登记表尚未创建，请先运行 `npm run backend:migrate`。", file=sys.stderr)
            return 2
        raise
    finally:
        manager.dispose()
    _print_payload(payload, as_json=args.json)
    return 0


def _build_settings(db_path: Path | None) -> Settings:
    if db_path is None:
        return Settings()
    return Settings(data_dir=db_path.parent, db_path=db_path)


def _print_payload(payload: dict[str, object], *, as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return

    seed = payload.get("seed")
    if isinstance(seed, dict):
        print("高考官方来源登记已更新")
        print(f"- source registry upserted: {seed.get('source_registry_upserted')}")
        print(f"- source documents upserted: {seed.get('source_documents_upserted')}")
        print(f"- source documents created: {seed.get('source_documents_created')}")
        directories = seed.get("directories")
        if isinstance(directories, dict):
            for label, path in directories.items():
                print(f"- {label}: {path}")

    source_documents = payload.get("source_documents")
    if isinstance(source_documents, list):
        print("")
        print("已登记来源文档:")
        for item in source_documents:
            if not isinstance(item, dict):
                continue
            print(
                f"- #{item.get('id')} {item.get('year')} {item.get('source_type')} "
                f"{item.get('title')} [{item.get('status')}]"
            )

    directories = payload.get("directories")
    if isinstance(directories, dict):
        print("高考导入目录已准备:")
        for label, path in directories.items():
            print(f"- {label}: {path}")


if __name__ == "__main__":
    raise SystemExit(main())
