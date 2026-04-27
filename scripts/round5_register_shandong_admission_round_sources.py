#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import select, text
from sqlalchemy.exc import OperationalError


REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "apps" / "backend"))

from app.core.config import Settings  # noqa: E402
from app.db.session import DatabaseManager  # noqa: E402
from app.models.gaokao_import import GaokaoImportRun  # noqa: E402
from app.services.gaokao_imports import (  # noqa: E402
    GaokaoSourceDocumentSeed,
    ensure_gaokao_import_directories,
    register_gaokao_local_file,
    seed_gaokao_source_registry,
    upsert_gaokao_source_document,
)


USER_AGENT = "local-edu-tool-round5-source-link/2026-04-26"
DATA_VERSION = "round5_source_link_20260426"
IMPORTER_NAME = "round5_link_existing_admission_result_sources"


@dataclass(frozen=True)
class AdmissionRoundSource:
    year: int
    round_no: str
    title: str
    page_url: str
    file_url: str
    published_at: date


ROUND_SOURCES = (
    AdmissionRoundSource(
        year=2023,
        round_no="2",
        title="山东省2023年普通类常规批第2次志愿投档情况表",
        page_url="https://www.sdzk.cn/NewsInfo.aspx?NewsID=6313",
        file_url="https://www.sdzk.cn/Floadup/file/20230728/6382615177078488259928282.xls",
        published_at=date(2023, 7, 28),
    ),
    AdmissionRoundSource(
        year=2023,
        round_no="3",
        title="山东省2023年普通类常规批第3次志愿投档情况表",
        page_url="https://www.sdzk.cn/NewsInfo.aspx?NewsID=6321",
        file_url="https://www.sdzk.cn/Floadup/file/20230801/6382650008108174904038099.xls",
        published_at=date(2023, 8, 1),
    ),
    AdmissionRoundSource(
        year=2024,
        round_no="2",
        title="山东省2024年普通类常规批第2次志愿投档情况表",
        page_url="https://www.sdzk.cn/NewsInfo.aspx?NewsID=6670",
        file_url="https://www.sdzk.cn/Floadup/file/20240728/6385777552810852585469169.xls",
        published_at=date(2024, 7, 28),
    ),
    AdmissionRoundSource(
        year=2024,
        round_no="3",
        title="山东省2024年普通类常规批第3次志愿投档情况表",
        page_url="https://www.sdzk.cn/NewsInfo.aspx?NewsID=6682",
        file_url="https://www.sdzk.cn/Floadup/file/20240801/6385812396894127885071174.xls",
        published_at=date(2024, 8, 1),
    ),
    AdmissionRoundSource(
        year=2025,
        round_no="2",
        title="山东省2025年普通类常规批第2次志愿投档情况表",
        page_url="https://www.sdzk.cn/NewsInfo.aspx?NewsID=7010",
        file_url="https://www.sdzk.cn/Floadup/file/20250728/6388931521217170972235326.xls",
        published_at=date(2025, 7, 28),
    ),
    AdmissionRoundSource(
        year=2025,
        round_no="3",
        title="山东省2025年普通类常规批第3次志愿投档情况表",
        page_url="https://www.sdzk.cn/NewsInfo.aspx?NewsID=7019",
        file_url="https://www.sdzk.cn/Floadup/file/20250801/6388966818220240355336033.xls",
        published_at=date(2025, 8, 1),
    ),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Register Round 5 Shandong official admission result sources for existing round 2/3 raw rows."
    )
    parser.add_argument("--db", type=Path, default=None, help="SQLite app database path.")
    parser.add_argument("--no-download", action="store_true", help="Use existing files only.")
    parser.add_argument("--json", action="store_true", help="Output JSON.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    settings = _build_settings(args.db)
    manager = DatabaseManager(settings.database_url, settings.debug)
    try:
        with manager.session_scope() as session:
            payload = register_round_sources(session, settings, download_missing=not args.no_download)
    except OperationalError as exc:
        if "gaokao_source_document" in str(exc) or "gaokao_import_run" in str(exc):
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
        return 0
    print("第五轮普通类第2/3次投档来源追溯已登记")
    for item in payload["items"]:
        print(
            f"- {item['year']} 第{item['round_no']}次：source_document_id={item['source_document_id']}，"
            f"import_run_id={item['import_run_id']}，挂接 raw 行 {item['linked_rows']} 条"
        )
    return 0


def register_round_sources(session, settings: Settings, *, download_missing: bool) -> dict[str, Any]:
    ensure_gaokao_import_directories(settings)
    seed_gaokao_source_registry(session)
    items: list[dict[str, Any]] = []
    for source in ROUND_SOURCES:
        document, _created = upsert_gaokao_source_document(
            session,
            GaokaoSourceDocumentSeed(
                province="山东",
                year=source.year,
                source_type="admission_result",
                title=source.title,
                url=source.page_url,
                official_org="山东省教育招生考试院",
                source_registry_code="sdzk",
                published_at=source.published_at,
                parser_name=IMPORTER_NAME,
                note=f"第五轮登记普通类常规批第{source.round_no}次志愿投档情况表；用于挂接既有 raw 投档行来源追溯。",
            ),
        )
        file_path = _resolve_round_source_file(settings, source)
        if file_path is None:
            if not download_missing:
                raise ValueError(f"{source.title} 缺少本地官方文件，请先下载到 data/imports/gaokao/official/{source.year}/")
            file_path = _download_round_file(settings, source)
        document, run, run_created = _register_or_reuse_round_file(
            session,
            settings,
            source_document_id=document.id,
            file_path=file_path,
            importer_name=IMPORTER_NAME,
        )
        linked_rows = _link_existing_raw_rows(session, source, document, run.id)
        run.status = "success"
        run.total_rows = linked_rows
        run.success_rows = linked_rows
        run.failed_rows = 0
        run.skipped_rows = 0
        run.created_rows = 0
        run.updated_rows = linked_rows
        run.raw_snapshot_path = document.local_file_path
        run.finished_at = datetime.now()
        run.note = "第五轮来源追溯挂接：官方文件已登记，既有 raw 投档行已关联 source_document_id / import_run_id。"
        document.status = "imported" if linked_rows else "file_ready"
        items.append(
            {
                "year": source.year,
                "round_no": source.round_no,
                "source_document_id": document.id,
                "import_run_id": run.id,
                "title": source.title,
                "page_url": source.page_url,
                "file_url": source.file_url,
                "local_file_path": document.local_file_path,
                "file_sha256": document.file_sha256,
                "linked_rows": linked_rows,
                "import_run_created": run_created,
            }
        )
    return {"items": items}


def _register_or_reuse_round_file(
    session,
    settings: Settings,
    *,
    source_document_id: int,
    file_path: Path,
    importer_name: str,
) -> tuple[Any, GaokaoImportRun, bool]:
    existing_run = session.scalar(
        select(GaokaoImportRun)
        .where(
            GaokaoImportRun.source_document_id == source_document_id,
            GaokaoImportRun.importer_name == importer_name,
            GaokaoImportRun.status == "success",
        )
        .order_by(GaokaoImportRun.id)
    )
    if existing_run is not None and existing_run.source_document is not None:
        return existing_run.source_document, existing_run, False
    document, run = register_gaokao_local_file(
        session,
        settings,
        source_document_id=source_document_id,
        file_path=file_path,
        importer_name=importer_name,
    )
    return document, run, True


def _link_existing_raw_rows(session, source: AdmissionRoundSource, document, import_run_id: int) -> int:
    result = session.execute(
        text(
            """
            UPDATE gaokao_admission_result
            SET
                source_level = 'official',
                source_title = :source_title,
                source_url = :source_url,
                local_source_path = :local_source_path,
                parser_script_name = :parser_script_name,
                published_at = :published_at,
                review_status = 'confirmed_official_public',
                data_version_label = :data_version_label,
                source_document_id = :source_document_id,
                import_run_id = :import_run_id,
                updated_at = CURRENT_TIMESTAMP
            WHERE province IN ('sd', '山东')
              AND year = :year
              AND candidate_type = '普通类'
              AND batch_name = '常规批'
              AND round_no = :round_no
            """
        ),
        {
            "source_title": source.title,
            "source_url": source.page_url,
            "local_source_path": document.local_file_path,
            "parser_script_name": IMPORTER_NAME,
            "published_at": source.published_at.isoformat(),
            "data_version_label": DATA_VERSION,
            "source_document_id": document.id,
            "import_run_id": import_run_id,
            "year": source.year,
            "round_no": source.round_no,
        },
    )
    return int(result.rowcount or 0)


def _download_round_file(settings: Settings, source: AdmissionRoundSource) -> Path:
    target_dir = settings.data_dir / "imports" / "gaokao" / "official" / str(source.year)
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / f"{source.year}_admission_result_round{source.round_no}_{_safe_filename(source.title)}.xls"
    if target_path.exists():
        return target_path
    request = urllib.request.Request(source.file_url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=60) as response:
        target_path.write_bytes(response.read())
    return target_path


def _resolve_round_source_file(settings: Settings, source: AdmissionRoundSource) -> Path | None:
    search_dirs = [
        settings.data_dir / "imports" / "gaokao" / "official" / str(source.year),
        settings.data_dir / "imports" / "gaokao" / "manual" / str(source.year),
    ]
    needles = [
        f"round{source.round_no}",
        f"第{source.round_no}次",
        f"{source.year}_普通类常规批第{source.round_no}次",
    ]
    for directory in search_dirs:
        if not directory.exists():
            continue
        for path in sorted(directory.iterdir()):
            if not path.is_file() or path.suffix.lower() not in {".xls", ".xlsx"}:
                continue
            if str(source.year) not in path.name:
                continue
            if any(needle in path.name for needle in needles):
                return path
    return None


def _safe_filename(value: str) -> str:
    text_value = re.sub(r"[^\w\u4e00-\u9fff.-]+", "_", value.strip(), flags=re.U)
    return text_value.strip("._")[:150] or "gaokao_source"


def _build_settings(db_path: Path | None) -> Settings:
    if db_path is None:
        return Settings()
    return Settings(data_dir=db_path.parent, db_path=db_path)


if __name__ == "__main__":
    raise SystemExit(main())
