from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models import GaokaoImportRun, GaokaoSourceDocument
from app.utils.parsers import relative_to_project


GAOKAO_SOURCE_STATUS_REGISTERED = "registered"
GAOKAO_SOURCE_STATUS_FILE_READY = "file_ready"
GAOKAO_IMPORT_STATUS_PENDING = "pending"
DEFAULT_PARSER_VERSION = "a1-framework"


@dataclass(frozen=True)
class GaokaoSourceRegistrySeed:
    source_code: str
    source_name: str
    province_scope: str | None
    topic: str
    source_level: str
    source_type: str
    platform: str
    trust_level: str
    priority: int
    entry_url: str
    allow_domains: list[str]
    tags: list[str]
    note: str


@dataclass(frozen=True)
class GaokaoSourceDocumentSeed:
    province: str
    year: int
    source_type: str
    title: str
    url: str
    official_org: str
    source_registry_code: str
    published_at: date | None = None
    parser_name: str | None = None
    note: str | None = None


DEFAULT_SOURCE_REGISTRY_SEEDS = (
    GaokaoSourceRegistrySeed(
        source_code="sdzk",
        source_name="山东省教育招生考试院",
        province_scope="山东",
        topic="gaokao",
        source_level="official",
        source_type="education_exam_authority",
        platform="website",
        trust_level="primary",
        priority=10,
        entry_url="https://www.sdzk.cn/",
        allow_domains=["sdzk.cn", "www.sdzk.cn"],
        tags=["山东", "高考", "投档", "一分一段", "分数线", "选科要求"],
        note="山东高考投档、分数线、一分一段和选科要求优先来源。",
    ),
    GaokaoSourceRegistrySeed(
        source_code="sdedu",
        source_name="山东省教育厅",
        province_scope="山东",
        topic="gaokao",
        source_level="official",
        source_type="education_department",
        platform="website",
        trust_level="primary",
        priority=20,
        entry_url="https://edu.shandong.gov.cn/",
        allow_domains=["edu.shandong.gov.cn"],
        tags=["山东", "教育厅", "单独招生", "综合评价招生", "政策通知"],
        note="山东省级招生政策和单招综评通知来源。",
    ),
    GaokaoSourceRegistrySeed(
        source_code="college_admission_site",
        source_name="高校官网招生章程",
        province_scope=None,
        topic="gaokao",
        source_level="official",
        source_type="college_admission_chapter",
        platform="website",
        trust_level="primary",
        priority=30,
        entry_url="",
        allow_domains=[],
        tags=["高校", "招生章程", "专业限制", "体检", "语种", "单科要求"],
        note="逐校招生章程和专业特殊要求来源；自动抓取失败时必须人工核验。",
    ),
)


DEFAULT_SOURCE_DOCUMENT_SEEDS = (
    GaokaoSourceDocumentSeed(
        province="山东",
        year=2025,
        source_type="admission_result",
        title="山东省2025年普通类常规批第1次志愿投档情况表",
        url="https://www.sdzk.cn/NewsInfo.aspx?NewsID=6996",
        official_org="山东省教育招生考试院",
        source_registry_code="sdzk",
        published_at=date(2025, 7, 19),
        parser_name="shandong_admission_result",
        note="B1 导入普通类投档数据时应关联此来源文档。",
    ),
    GaokaoSourceDocumentSeed(
        province="山东",
        year=2024,
        source_type="admission_result",
        title="山东省2024年普通类常规批第1次志愿投档情况表",
        url="https://www.sdzk.cn/NewsInfo.aspx?NewsID=6656",
        official_org="山东省教育招生考试院",
        source_registry_code="sdzk",
        published_at=date(2024, 7, 19),
        parser_name="shandong_admission_result",
        note="B1 导入普通类投档数据时应关联此来源文档。",
    ),
    GaokaoSourceDocumentSeed(
        province="山东",
        year=2023,
        source_type="admission_result",
        title="山东省2023年普通类常规批第1次志愿投档情况表",
        url="https://www.sdzk.cn/NewsInfo.aspx?NewsID=6279",
        official_org="山东省教育招生考试院",
        source_registry_code="sdzk",
        published_at=date(2023, 7, 19),
        parser_name="shandong_admission_result",
        note="B1 导入普通类投档数据时应关联此来源文档。",
    ),
    GaokaoSourceDocumentSeed(
        province="山东",
        year=2025,
        source_type="score_rank_segment",
        title="山东省2025年夏季高考文化成绩一分一段表",
        url="https://www.sdzk.cn/NewsInfo.aspx?NewsID=6943",
        official_org="山东省教育招生考试院",
        source_registry_code="sdzk",
        published_at=date(2025, 6, 25),
        parser_name="shandong_score_rank_segment",
        note="用于预估分数到全省位次换算。",
    ),
    GaokaoSourceDocumentSeed(
        province="山东",
        year=2024,
        source_type="score_rank_segment",
        title="山东省2024年夏季高考文化成绩一分一段表",
        url="https://www.sdzk.cn/NewsInfo.aspx?NewsID=6577",
        official_org="山东省教育招生考试院",
        source_registry_code="sdzk",
        published_at=date(2024, 6, 25),
        parser_name="shandong_score_rank_segment",
        note="用于预估分数到全省位次换算。",
    ),
    GaokaoSourceDocumentSeed(
        province="山东",
        year=2023,
        source_type="score_rank_segment",
        title="山东省2023年夏季高考文化成绩一分一段表",
        url="https://www.sdzk.cn/NewsInfo.aspx?NewsID=6212",
        official_org="山东省教育招生考试院",
        source_registry_code="sdzk",
        published_at=date(2023, 6, 25),
        parser_name="shandong_score_rank_segment",
        note="A0 已确认 2023 一分一段缺失，B1 应优先补齐。",
    ),
    GaokaoSourceDocumentSeed(
        province="山东",
        year=2025,
        source_type="score_line",
        title="山东省2025年各类别分数线",
        url="https://www.sdzk.cn/NewsInfo.aspx?NewsID=6941",
        official_org="山东省教育招生考试院",
        source_registry_code="sdzk",
        published_at=date(2025, 6, 25),
        parser_name="shandong_score_line",
        note="用于普通类批次线和特殊类型资格线解释。",
    ),
    GaokaoSourceDocumentSeed(
        province="山东",
        year=2024,
        source_type="score_line",
        title="山东省2024年各类别分数线",
        url="https://www.sdzk.cn/NewsInfo.aspx?NewsID=6579",
        official_org="山东省教育招生考试院",
        source_registry_code="sdzk",
        published_at=date(2024, 6, 25),
        parser_name="shandong_score_line",
        note="用于普通类批次线和特殊类型资格线解释。",
    ),
    GaokaoSourceDocumentSeed(
        province="山东",
        year=2023,
        source_type="score_line",
        title="山东省2023年各类别分数线",
        url="https://www.sdzk.cn/NewsInfo.aspx?NewsID=6210",
        official_org="山东省教育招生考试院",
        source_registry_code="sdzk",
        published_at=date(2023, 6, 25),
        parser_name="shandong_score_line",
        note="A0 已确认 2023 省控线缺失，B1 应优先补齐。",
    ),
    GaokaoSourceDocumentSeed(
        province="山东",
        year=2025,
        source_type="subject_requirement",
        title="2024通用版普通高校拟在山东招生专业（类）选考科目要求",
        url="https://www.sdzk.cn/NewsInfo.aspx?NewsID=6819",
        official_org="山东省教育招生考试院",
        source_registry_code="sdzk",
        published_at=date(2025, 3, 17),
        parser_name="shandong_subject_requirement",
        note="该通用版适用于 2025 与 2026 年山东考生。",
    ),
    GaokaoSourceDocumentSeed(
        province="山东",
        year=2026,
        source_type="subject_requirement",
        title="2024通用版普通高校拟在山东招生专业（类）选考科目要求",
        url="https://www.sdzk.cn/NewsInfo.aspx?NewsID=6819",
        official_org="山东省教育招生考试院",
        source_registry_code="sdzk",
        published_at=date(2025, 3, 17),
        parser_name="shandong_subject_requirement",
        note="该通用版适用于 2025 与 2026 年山东考生。",
    ),
    GaokaoSourceDocumentSeed(
        province="山东",
        year=2026,
        source_type="policy",
        title="关于做好2026年高职（专科）单独考试招生和综合评价招生工作的通知",
        url="https://edu.shandong.gov.cn/art/2025/12/22/art_107093_10344338.html",
        official_org="山东省教育厅",
        source_registry_code="sdedu",
        published_at=date(2025, 12, 22),
        parser_name="shandong_policy_reference",
        note="仅用于 2026 单招/综评政策登记；不得当作普通类正式招生计划。",
    ),
    GaokaoSourceDocumentSeed(
        province="山东",
        year=2026,
        source_type="single_comprehensive_plan_limit",
        title="2026年高职（专科）单独招生和综合评价招生院校计划限额",
        url="https://edu.shandong.gov.cn/art/2025/12/22/art_107093_10344338.html",
        official_org="山东省教育厅",
        source_registry_code="sdedu",
        published_at=date(2025, 12, 22),
        parser_name="shandong_single_comprehensive_plan_limit",
        note="教育厅通知附件口径；用于单招/综评计划限额登记或人工导入，不得当作 2026 夏季高考普通类正式计划。",
    ),
)


def ensure_gaokao_import_directories(settings: Settings) -> dict[str, str]:
    base_dir = settings.data_dir / "imports" / "gaokao"
    directories = {
        "official": base_dir / "official",
        "manual": base_dir / "manual",
        "error_reports": base_dir / "error_reports",
        "raw_snapshots": base_dir / "raw_snapshots",
    }
    for path in directories.values():
        path.mkdir(parents=True, exist_ok=True)
    return {key: relative_to_project(path, settings.project_root) for key, path in directories.items()}


def seed_default_gaokao_sources(session: Session, settings: Settings) -> dict[str, int | dict[str, str]]:
    directories = ensure_gaokao_import_directories(settings)
    registry_count = seed_gaokao_source_registry(session)
    document_count = 0
    for seed in DEFAULT_SOURCE_DOCUMENT_SEEDS:
        document, created = upsert_gaokao_source_document(session, seed)
        document_count += int(created)
    return {
        "source_registry_upserted": registry_count,
        "source_documents_upserted": len(DEFAULT_SOURCE_DOCUMENT_SEEDS),
        "source_documents_created": document_count,
        "directories": directories,
    }


def seed_gaokao_source_registry(session: Session) -> int:
    bind = session.get_bind()
    if bind is None:
        return 0
    table_exists = bool(
        session.execute(
            text(
                """
                SELECT 1
                FROM sqlite_master
                WHERE type = 'table' AND name = 'gaokao_source_registry'
                """
            )
        ).first()
    )
    if not table_exists:
        return 0

    upsert_sql = text(
        """
        INSERT INTO gaokao_source_registry (
            source_code, domain, source_name, province_scope, topic, source_level,
            source_type, platform, trust_level, priority, entry_url, allow_domains,
            must_include, exclude_keywords, tags, note, status, created_at, updated_at
        ) VALUES (
            :source_code, 'gaokao', :source_name, :province_scope, :topic, :source_level,
            :source_type, :platform, :trust_level, :priority, :entry_url, :allow_domains,
            :must_include, :exclude_keywords, :tags, :note, 'active', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
        )
        ON CONFLICT(source_code) DO UPDATE SET
            source_name = excluded.source_name,
            province_scope = excluded.province_scope,
            topic = excluded.topic,
            source_level = excluded.source_level,
            source_type = excluded.source_type,
            platform = excluded.platform,
            trust_level = excluded.trust_level,
            priority = excluded.priority,
            entry_url = excluded.entry_url,
            allow_domains = excluded.allow_domains,
            tags = excluded.tags,
            note = excluded.note,
            status = 'active',
            updated_at = CURRENT_TIMESTAMP
        """
    )
    for seed in DEFAULT_SOURCE_REGISTRY_SEEDS:
        session.execute(
            upsert_sql,
            {
                "source_code": seed.source_code,
                "source_name": seed.source_name,
                "province_scope": seed.province_scope,
                "topic": seed.topic,
                "source_level": seed.source_level,
                "source_type": seed.source_type,
                "platform": seed.platform,
                "trust_level": seed.trust_level,
                "priority": seed.priority,
                "entry_url": seed.entry_url,
                "allow_domains": json.dumps(seed.allow_domains, ensure_ascii=False),
                "must_include": json.dumps([], ensure_ascii=False),
                "exclude_keywords": json.dumps([], ensure_ascii=False),
                "tags": json.dumps(seed.tags, ensure_ascii=False),
                "note": seed.note,
            },
        )
    return len(DEFAULT_SOURCE_REGISTRY_SEEDS)


def upsert_gaokao_source_document(
    session: Session,
    seed: GaokaoSourceDocumentSeed,
) -> tuple[GaokaoSourceDocument, bool]:
    existing = session.scalar(
        select(GaokaoSourceDocument).where(
            GaokaoSourceDocument.province == seed.province,
            GaokaoSourceDocument.year == seed.year,
            GaokaoSourceDocument.source_type == seed.source_type,
            GaokaoSourceDocument.url == seed.url,
        )
    )
    if existing is None:
        document = GaokaoSourceDocument(
            province=seed.province,
            year=seed.year,
            source_type=seed.source_type,
            title=seed.title,
            url=seed.url,
            official_org=seed.official_org,
            source_registry_code=seed.source_registry_code,
            published_at=seed.published_at,
            parser_name=seed.parser_name,
            parser_version=DEFAULT_PARSER_VERSION if seed.parser_name else None,
            status=GAOKAO_SOURCE_STATUS_REGISTERED,
            note=seed.note,
        )
        session.add(document)
        session.flush()
        return document, True

    existing.title = seed.title
    existing.official_org = seed.official_org
    existing.source_registry_code = seed.source_registry_code
    existing.published_at = seed.published_at
    existing.parser_name = seed.parser_name
    existing.parser_version = existing.parser_version or (DEFAULT_PARSER_VERSION if seed.parser_name else None)
    existing.note = seed.note
    session.flush()
    return existing, False


def list_gaokao_source_documents(session: Session) -> list[GaokaoSourceDocument]:
    return list(
        session.scalars(
            select(GaokaoSourceDocument).order_by(
                GaokaoSourceDocument.year.desc(),
                GaokaoSourceDocument.source_type,
                GaokaoSourceDocument.id,
            )
        ).all()
    )


def get_gaokao_source_document(session: Session, source_document_id: int) -> GaokaoSourceDocument | None:
    return session.get(GaokaoSourceDocument, source_document_id)


def register_gaokao_local_file(
    session: Session,
    settings: Settings,
    *,
    source_document_id: int,
    file_path: Path,
    importer_name: str,
) -> tuple[GaokaoSourceDocument, GaokaoImportRun]:
    document = get_gaokao_source_document(session, source_document_id)
    if document is None:
        raise ValueError(f"source document not found: {source_document_id}")

    resolved_file = file_path.expanduser().resolve(strict=True)
    _ensure_allowed_gaokao_import_file(settings, resolved_file)

    document.local_file_path = relative_to_project(resolved_file, settings.project_root)
    document.file_sha256 = _sha256_file(resolved_file)
    document.fetched_at = datetime.now()
    document.parser_name = document.parser_name or importer_name
    document.parser_version = document.parser_version or DEFAULT_PARSER_VERSION
    document.status = GAOKAO_SOURCE_STATUS_FILE_READY

    run = GaokaoImportRun(
        source_document_id=document.id,
        importer_name=importer_name,
        started_at=datetime.now(),
        finished_at=datetime.now(),
        status=GAOKAO_IMPORT_STATUS_PENDING,
        total_rows=0,
        success_rows=0,
        failed_rows=0,
        skipped_rows=0,
        created_rows=0,
        updated_rows=0,
        raw_snapshot_path=document.local_file_path,
        note="已登记本地官方文件，等待对应解析器写入业务数据。",
    )
    session.add(run)
    session.flush()
    return document, run


def serialize_gaokao_source_document(document: GaokaoSourceDocument) -> dict[str, object]:
    return {
        "id": document.id,
        "province": document.province,
        "year": document.year,
        "source_type": document.source_type,
        "title": document.title,
        "url": document.url,
        "official_org": document.official_org,
        "source_registry_code": document.source_registry_code,
        "published_at": document.published_at.isoformat() if document.published_at else None,
        "fetched_at": document.fetched_at.isoformat(sep=" ") if document.fetched_at else None,
        "local_file_path": document.local_file_path,
        "file_sha256": document.file_sha256,
        "parser_name": document.parser_name,
        "parser_version": document.parser_version,
        "status": document.status,
        "note": document.note,
    }


def serialize_gaokao_import_run(run: GaokaoImportRun) -> dict[str, object]:
    return {
        "id": run.id,
        "source_document_id": run.source_document_id,
        "importer_name": run.importer_name,
        "started_at": run.started_at.isoformat(sep=" ") if run.started_at else None,
        "finished_at": run.finished_at.isoformat(sep=" ") if run.finished_at else None,
        "status": run.status,
        "total_rows": run.total_rows,
        "success_rows": run.success_rows,
        "failed_rows": run.failed_rows,
        "skipped_rows": run.skipped_rows,
        "created_rows": run.created_rows,
        "updated_rows": run.updated_rows,
        "error_report_path": run.error_report_path,
        "raw_snapshot_path": run.raw_snapshot_path,
        "note": run.note,
    }


def _ensure_allowed_gaokao_import_file(settings: Settings, file_path: Path) -> None:
    allowed_roots = [
        (settings.data_dir / "imports" / "gaokao" / "official").resolve(strict=False),
        (settings.data_dir / "imports" / "gaokao" / "manual").resolve(strict=False),
    ]
    if not any(_is_relative_to(file_path, root) for root in allowed_roots):
        allowed_text = " 或 ".join(relative_to_project(root, settings.project_root) for root in allowed_roots)
        raise ValueError(f"file must be under {allowed_text}: {file_path}")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True
