from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse

from fastapi import HTTPException
from sqlalchemy import func, inspect, or_, select, text
from sqlalchemy.orm import Session

from app.models import (
    AdmissionRecord,
    College,
    EnrollmentPlan,
    ImportJob,
    ProvinceScoreTransformRule,
    ProvinceVolunteerRule,
    SubjectRequirementDict,
)
from app.repositories.system import list_recent_import_jobs
from app.schemas.gaokao import (
    GaokaoCollegeEvidenceRead,
    GaokaoCollegeOptionRead,
    GaokaoDataOverviewRead,
    GaokaoImportBatchRead,
    GaokaoReviewBucketRead,
    GaokaoReviewGroupComparisonFieldRead,
    GaokaoReviewGroupRead,
    GaokaoReviewGroupMemberRead,
    GaokaoReviewItemRead,
    GaokaoReviewQuickFilterRead,
    GaokaoReviewSummaryRead,
    GaokaoShandongMonitorRead,
    GaokaoTableStatRead,
)


SYNC_BOARD_PATH = Path("docs/dev/02_SYNC_BOARD_2026-04-16.md")
SYNC_BOARD_FALLBACK = {
    "data_version": "DB RC1",
    "generated_at": "2026-04-16 10:57",
    "gaokao_college_total": 3344,
    "gaokao_college_with_recruit_site": 1813,
    "gaokao_college_with_chapter_url": 172,
    "chapter_rule_fallback_url_filled": 1805,
    "duplicate_group_total": 4,
    "same_name_cross_site_group_total": 2,
}
RELEVANT_IMPORT_KEYWORDS = (
    "admission",
    "enrollment",
    "gaokao",
    "score_rank",
    "subject_requirement",
    "province_rule",
)
REVIEW_PRIORITY_LABELS = {
    "high": "高优先",
    "medium": "中优先",
    "low": "低优先",
}
REVIEW_FOCUS_TITLES = {
    "all": "全部队列",
    "high_priority": "高优先",
    "missing_chapter": "缺章程",
    "missing_recruit_site": "缺招生网",
    "duplicate_or_same_name": "重复 / 同名组",
    "unresolved": "仍未解决",
}
REVIEW_FOCUS_DESCRIPTIONS = {
    "all": "当前状态与关键字下的全部学校。",
    "high_priority": "证据缺口大或仍未解决的学校，适合先处理。",
    "missing_chapter": "当前缺章程入口或 fallback_url 的学校。",
    "missing_recruit_site": "当前缺招生网入口的学校。",
    "duplicate_or_same_name": "处于重复组或同名跨站组的学校。",
    "unresolved": "review_status 仍为 unresolved 的学校。",
}
REVIEW_SORT_TITLES = {
    "priority_desc": "优先级优先",
    "updated_desc": "最近更新时间",
}
PROVINCE_DISPLAY_NAMES = {
    "sd": "山东",
    "shandong": "山东",
    "山东省": "山东",
}
PROVINCE_FILTER_ALIASES = {
    "山东": ("山东", "山东省", "sd", "shandong"),
}


@dataclass(slots=True)
class _SchemaSnapshot:
    session: Session
    _table_names: set[str] = field(default_factory=set)
    _columns: dict[str, set[str]] = field(default_factory=dict)
    _inspector: object = field(init=False, repr=False)

    def __post_init__(self) -> None:
        inspector = inspect(self.session.get_bind())
        self._table_names = set(inspector.get_table_names())
        self._inspector = inspector

    def has_table(self, table_name: str) -> bool:
        return table_name in self._table_names

    def columns(self, table_name: str) -> set[str]:
        if table_name not in self._columns:
            if not self.has_table(table_name):
                self._columns[table_name] = set()
            else:
                self._columns[table_name] = {
                    item["name"]
                    for item in self._inspector.get_columns(table_name)
                }
        return self._columns[table_name]

    def pick_column(self, table_name: str, *candidates: str) -> str | None:
        available = self.columns(table_name)
        for candidate in candidates:
            if candidate in available:
                return candidate
        return None


@dataclass(slots=True)
class _RawTableSummary:
    table_name: str
    record_total: int
    latest_updated_at: str | None = None


def _pick_raw_session(app_session: Session, gaokao_session: Session | None) -> Session:
    return gaokao_session or app_session


def get_data_overview(
    app_session: Session,
    gaokao_session: Session | None,
    settings,
) -> GaokaoDataOverviewRead:
    doc_baseline = _load_sync_board_baseline(settings.project_root)
    raw_session = _pick_raw_session(app_session, gaokao_session)
    snapshot = _SchemaSnapshot(raw_session)
    notes: list[str] = []
    source_mode = "doc_baseline"

    school_total = int(doc_baseline["gaokao_college_total"])
    recruit_site_covered = int(doc_baseline["gaokao_college_with_recruit_site"])
    chapter_url_covered = int(doc_baseline["gaokao_college_with_chapter_url"])
    fallback_url_covered = int(doc_baseline["chapter_rule_fallback_url_filled"])
    duplicate_group_total = int(doc_baseline["duplicate_group_total"])
    same_name_group_total = int(doc_baseline["same_name_cross_site_group_total"])
    last_updated_at = _stringify_timestamp(doc_baseline["generated_at"])

    if snapshot.has_table("gaokao_college"):
        school_total = _count_rows(raw_session, "gaokao_college")
        recruit_site_covered = _count_nonempty(
            raw_session,
            "gaokao_college",
            snapshot.pick_column("gaokao_college", "recruit_site"),
        )
        chapter_url_covered = _count_nonempty(
            raw_session,
            "gaokao_college",
            snapshot.pick_column("gaokao_college", "chapter_url"),
        )
        fallback_url_covered = _count_nonempty(
            raw_session,
            "gaokao_college",
            snapshot.pick_column("gaokao_college", "chapter_fallback_url"),
        )
        duplicate_group_total = _count_distinct_nonempty(
            raw_session,
            "gaokao_college",
            snapshot.pick_column("gaokao_college", "duplicate_group_key", "duplicate_group_id"),
        ) or duplicate_group_total
        same_name_group_total = _count_distinct_nonempty(
            raw_session,
            "gaokao_college",
            snapshot.pick_column("gaokao_college", "same_name_group_key", "same_name_group_id"),
        ) or same_name_group_total
        last_updated_at = _max_timestamp(
            raw_session,
            "gaokao_college",
            snapshot.pick_column("gaokao_college", "updated_at", "modified_at", "created_at"),
        ) or last_updated_at
        source_mode = "db_rc1_live"
        notes.append("当前概览已直连本地 gaokao 主线库的 gaokao_college 只读表。")
    else:
        notes.append("当前仓库未接入 DB RC1 原始高校主档表，概览指标先回退到同步板基线。")

    chapter_table_key = "gaokao_policy_reference"
    chapter_table_label = "章程证据链"
    chapter_table_record_total = 0
    chapter_table_updated_at = last_updated_at
    chapter_table_notes = ["当前显示章程链接覆盖数；fallback_url 用于没有正式章程入口时的只读兜底。"]

    if snapshot.has_table("gaokao_college_chapter_rule"):
        chapter_url_covered = _count_nonempty(
            raw_session,
            "gaokao_college_chapter_rule",
            snapshot.pick_column("gaokao_college_chapter_rule", "chapter_url"),
        )
        fallback_url_covered = _count_nonempty(
            raw_session,
            "gaokao_college_chapter_rule",
            snapshot.pick_column("gaokao_college_chapter_rule", "chapter_fallback_url"),
        )
        chapter_table_key = "gaokao_college_chapter_rule"
        chapter_table_label = "招生章程证据链"
        chapter_table_record_total = _count_rows(raw_session, "gaokao_college_chapter_rule")
        chapter_table_updated_at = _max_timestamp(
            raw_session,
            "gaokao_college_chapter_rule",
            snapshot.pick_column("gaokao_college_chapter_rule", "updated_at", "modified_at", "created_at"),
        ) or chapter_table_updated_at
        last_updated_at = chapter_table_updated_at or last_updated_at
        chapter_table_notes = ["当前优先读取 gaokao_college_chapter_rule 的正式章程与 fallback 字段。"]
        source_mode = "db_rc1_live"
    elif snapshot.has_table("gaokao_policy_reference"):
        chapter_url_covered = _count_nonempty(
            raw_session,
            "gaokao_policy_reference",
            snapshot.pick_column("gaokao_policy_reference", "chapter_url", "url"),
        )
        fallback_url_covered = _count_nonempty(
            raw_session,
            "gaokao_policy_reference",
            snapshot.pick_column("gaokao_policy_reference", "fallback_url", "local_path"),
        )
        chapter_table_record_total = _count_rows(raw_session, "gaokao_policy_reference")
        chapter_table_updated_at = _max_timestamp(
            raw_session,
            "gaokao_policy_reference",
            snapshot.pick_column("gaokao_policy_reference", "updated_at", "modified_at", "created_at"),
        ) or chapter_table_updated_at
        last_updated_at = chapter_table_updated_at or last_updated_at
        source_mode = "db_rc1_live"
    elif not snapshot.has_table("gaokao_college"):
        notes.append("章程证据链明细表未在当前应用库中暴露，chapter_url / fallback_url 默认回退到同步板基线。")

    enrollment_plan_total = app_session.scalar(select(func.count()).select_from(EnrollmentPlan)) or 0
    enrollment_plan_notes, enrollment_plan_status = _build_app_model_gap_notes(
        raw_session,
        snapshot,
        raw_table="gaokao_admission_plan",
        raw_updated_candidates=("updated_at", "modified_at", "created_at"),
        model_total=enrollment_plan_total,
        base_notes=["该表属于当前应用模型，不等同 Windows DB RC1 原始事实表。"],
    )
    admission_record_total = app_session.scalar(select(func.count()).select_from(AdmissionRecord)) or 0
    admission_record_notes, admission_record_status = _build_app_model_gap_notes(
        raw_session,
        snapshot,
        raw_table="gaokao_admission_result",
        raw_updated_candidates=("updated_at", "modified_at", "created_at"),
        model_total=admission_record_total,
        base_notes=["该表用于当前推荐链路的录取参考。"],
    )

    core_tables = [
        _build_table_stat(
            key="gaokao_college",
            label="高校主档",
            record_total=school_total,
            covered_total=recruit_site_covered,
            coverage_rate=_safe_rate(recruit_site_covered, school_total),
            latest_updated_at=last_updated_at,
            latest_batch_label=str(doc_baseline["data_version"]),
            notes=["覆盖率口径为 recruit_site 已覆盖学校数。"],
        ),
        _build_table_stat(
            key=chapter_table_key,
            label=chapter_table_label,
            record_total=chapter_table_record_total or chapter_url_covered or fallback_url_covered,
            covered_total=chapter_url_covered,
            coverage_rate=_safe_rate(chapter_url_covered, school_total),
            latest_updated_at=chapter_table_updated_at,
            latest_batch_label="chapter_url / fallback_url",
            notes=chapter_table_notes,
        ),
        _build_table_stat(
            key="enrollment_plan",
            label="应用侧招生计划",
            record_total=enrollment_plan_total,
            latest_updated_at=_stringify_timestamp(
                app_session.scalar(select(func.max(EnrollmentPlan.updated_at)))
            ),
            latest_batch_label=_latest_enrollment_plan_batch(app_session),
            status=enrollment_plan_status,
            notes=enrollment_plan_notes,
        ),
        _build_table_stat(
            key="admission_record",
            label="应用侧录取结果",
            record_total=admission_record_total,
            latest_updated_at=_stringify_timestamp(
                app_session.scalar(select(func.max(AdmissionRecord.updated_at)))
            ),
            status=admission_record_status,
            notes=admission_record_notes,
        ),
        _build_table_stat(
            key="province_volunteer_rule",
            label="应用侧省份规则",
            record_total=app_session.scalar(select(func.count()).select_from(ProvinceVolunteerRule)) or 0,
            latest_updated_at=_stringify_timestamp(
                app_session.scalar(select(func.max(ProvinceVolunteerRule.updated_at)))
            ),
            notes=["该表为 Stage B 当前应用规则层；正式 RC1 监控仍以 handoff 为准。"],
        ),
    ]

    return GaokaoDataOverviewRead(
        source_mode=source_mode,
        data_version=str(doc_baseline["data_version"]),
        generated_at=_stringify_timestamp(doc_baseline["generated_at"]),
        school_total=school_total,
        recruit_site_covered=recruit_site_covered,
        recruit_site_coverage_rate=_safe_rate(recruit_site_covered, school_total),
        chapter_url_covered=chapter_url_covered,
        chapter_url_coverage_rate=_safe_rate(chapter_url_covered, school_total),
        fallback_url_covered=fallback_url_covered,
        duplicate_group_total=duplicate_group_total,
        same_name_cross_site_group_total=same_name_group_total,
        recent_batch_label=_build_recent_batch_label(app_session, doc_baseline),
        last_updated_at=last_updated_at,
        notes=notes,
        core_tables=core_tables,
    )


def list_import_batches(
    app_session: Session,
    gaokao_session: Session | None,
    settings,
) -> list[GaokaoImportBatchRead]:
    raw_session = _pick_raw_session(app_session, gaokao_session)
    snapshot = _SchemaSnapshot(raw_session)

    if snapshot.has_table("data_import_batch"):
        raw_rows = raw_session.execute(
            text(
                """
                SELECT
                    id,
                    batch_code,
                    domain,
                    data_type,
                    province,
                    target_year,
                    source_name,
                    source_title,
                    version_label,
                    status,
                    total_records,
                    started_at,
                    finished_at
                FROM data_import_batch
                WHERE domain = 'gaokao'
                ORDER BY COALESCE(finished_at, started_at) DESC, id DESC
                LIMIT 20
                """
            )
        ).mappings().all()
        if raw_rows:
            return [
                GaokaoImportBatchRead(
                    id=f"data_import_batch_{row['id']}",
                    batch_name=_clean_text(row["source_title"]) or _clean_text(row["batch_code"]) or "高考导入批次",
                    source_type=_clean_text(row["data_type"]) or "gaokao",
                    source_filename=_clean_text(row["source_name"]),
                    status=_normalize_import_batch_status(_clean_text(row["status"])),
                    started_at=_stringify_timestamp(row["started_at"]),
                    finished_at=_stringify_timestamp(row["finished_at"]),
                    record_total=int(row["total_records"] or 0),
                    notes=[_build_raw_import_batch_note(row)],
                )
                for row in raw_rows
            ]

    rows = [
        item for item in list_recent_import_jobs(app_session, limit=20)
        if any(keyword in item.job_type for keyword in RELEVANT_IMPORT_KEYWORDS)
    ]
    if rows:
        return [
            GaokaoImportBatchRead(
                id=f"import_job_{item.id}",
                batch_name=_build_import_job_label(item),
                source_type="import_job",
                source_filename=item.source_filename,
                status=item.status,
                started_at=_stringify_timestamp(item.started_at),
                finished_at=_stringify_timestamp(item.finished_at),
                record_total=_read_import_job_record_total(item),
                notes=["当前批次来自应用侧 import_job 记录。"],
            )
            for item in rows
        ]

    doc_baseline = _load_sync_board_baseline(settings.project_root)
    return [
        GaokaoImportBatchRead(
            id="doc_rc1",
            batch_name="DB RC1 冻结基线",
            source_type="doc_baseline",
            status="frozen",
            finished_at=_stringify_timestamp(doc_baseline["generated_at"]),
            record_total=int(doc_baseline["gaokao_college_total"]),
            notes=["当前应用库没有独立高考导入批次记录，先展示同步板冻结基线。"],
        )
    ]


def list_college_options(
    app_session: Session,
    gaokao_session: Session | None,
    settings,
    *,
    query: str | None,
    limit: int = 10,
) -> list[GaokaoCollegeOptionRead]:
    del settings
    normalized_query = (query or "").strip()
    safe_limit = max(1, min(limit, 50))
    raw_session = _pick_raw_session(app_session, gaokao_session)
    snapshot = _SchemaSnapshot(raw_session)

    if snapshot.has_table("gaokao_college"):
        return _list_college_options_from_raw(raw_session, snapshot, query=normalized_query, limit=safe_limit)

    return _list_college_options_from_model(app_session, query=normalized_query, limit=safe_limit)


def get_review_summary(
    app_session: Session,
    gaokao_session: Session | None,
    settings,
    *,
    status: str | None = None,
    focus: str | None = None,
    sort: str | None = None,
    keyword: str | None = None,
) -> GaokaoReviewSummaryRead:
    doc_baseline = _load_sync_board_baseline(settings.project_root)
    raw_session = _pick_raw_session(app_session, gaokao_session)
    snapshot = _SchemaSnapshot(raw_session)
    requested_status = (status or "all").strip() or "all"
    requested_focus = _normalize_review_focus(focus)
    requested_sort = _normalize_review_sort(sort)
    requested_keyword = (keyword or "").strip()
    notes: list[str] = []

    if not snapshot.has_table("gaokao_college"):
        notes.append("当前应用库未暴露 review_status / retrieval_status 明细表，审阅页先保留同步板基线和空态。")
        if requested_keyword:
            notes.append("当前关键字检索需要 DB RC1 只读表支撑；本地仅同步板基线时暂不提供命中列表。")
        return GaokaoReviewSummaryRead(
            source_available=False,
            source_mode="doc_baseline",
            active_filter=requested_status,
            active_focus=requested_focus,
            active_sort=requested_sort,
            active_keyword=requested_keyword or None,
            queue_total=0,
            chapter_url_covered=int(doc_baseline["gaokao_college_with_chapter_url"]),
            chapter_url_coverage_rate=_safe_rate(
                int(doc_baseline["gaokao_college_with_chapter_url"]),
                int(doc_baseline["gaokao_college_total"]),
            ),
            duplicate_group_total=int(doc_baseline["duplicate_group_total"]),
            same_name_cross_site_group_total=int(doc_baseline["same_name_cross_site_group_total"]),
            counts=[
                GaokaoReviewBucketRead(code="pending_manual_review", title="待人工复核", count=None, description="等待 DB RC1 正式 handoff 后展示。"),
                GaokaoReviewBucketRead(code="pending_manual_review_with_official_candidate", title="待人工复核（已有官方候选）", count=None, description="等待 DB RC1 正式 handoff 后展示。"),
                GaokaoReviewBucketRead(code="unresolved", title="仍未解决", count=None, description="等待 DB RC1 正式 handoff 后展示。"),
            ],
            quick_filters=_build_review_quick_filters([]),
            notes=notes,
        )

    review_status_column = snapshot.pick_column("gaokao_college", "review_status")
    retrieval_status_column = snapshot.pick_column("gaokao_college", "retrieval_status")
    chapter_rule_review_status_column = snapshot.pick_column("gaokao_college_chapter_rule", "review_status")
    id_column = snapshot.pick_column("gaokao_college", "id", "college_id")
    name_column = snapshot.pick_column("gaokao_college", "name", "college_name")
    code_column = snapshot.pick_column("gaokao_college", "college_code", "school_code", "code")
    province_column = snapshot.pick_column("gaokao_college", "province")
    official_site_column = snapshot.pick_column("gaokao_college", "official_site", "website")
    recruit_site_column = snapshot.pick_column("gaokao_college", "recruit_site")
    review_status_column = snapshot.pick_column("gaokao_college", "review_status")
    retrieval_status_column = snapshot.pick_column("gaokao_college", "retrieval_status")
    source_url_column = snapshot.pick_column("gaokao_college", "source_url")
    source_title_column = snapshot.pick_column("gaokao_college", "source_title")
    updated_at_column = snapshot.pick_column("gaokao_college", "updated_at", "modified_at", "created_at")
    duplicate_group_column = snapshot.pick_column("gaokao_college", "duplicate_group_key", "duplicate_group_id")
    same_name_group_column = snapshot.pick_column("gaokao_college", "same_name_group_key", "same_name_group_id")
    keyword_clauses, keyword_params = _build_review_keyword_clauses(
        requested_keyword,
        id_column=id_column,
        name_column=name_column,
        code_column=code_column,
        province_column=province_column,
        recruit_site_column=recruit_site_column,
        source_title_column=source_title_column,
    )

    counts = [
        GaokaoReviewBucketRead(
            code="pending_manual_review",
            title="待人工复核",
            count=_count_equals(
                raw_session,
                "gaokao_college_chapter_rule" if chapter_rule_review_status_column else "gaokao_college",
                chapter_rule_review_status_column or review_status_column,
                "pending_manual_review",
            ),
            description="已有候选但仍需要人工确认正式入口。",
        ),
        GaokaoReviewBucketRead(
            code="pending_manual_review_with_official_candidate",
            title="待人工复核（已有官方候选）",
            count=_count_equals(
                raw_session,
                "gaokao_college_chapter_rule" if chapter_rule_review_status_column else "gaokao_college",
                chapter_rule_review_status_column or review_status_column,
                "pending_manual_review_with_official_candidate",
            ),
            description="当前已找到更像官方入口的候选，但尚未冻结回写。",
        ),
        GaokaoReviewBucketRead(
            code="unresolved",
            title="仍未解决",
            count=_count_equals(
                raw_session,
                "gaokao_college_chapter_rule" if chapter_rule_review_status_column else "gaokao_college",
                chapter_rule_review_status_column or review_status_column,
                "unresolved",
            ),
            description="当前还需要继续补证据或等待人工裁决。",
        ),
    ]

    items = (
        _list_review_items_from_chapter_rule(
            raw_session,
            snapshot,
            status=requested_status,
            keyword=requested_keyword,
        )
        if chapter_rule_review_status_column
        else _list_review_items(
            raw_session,
            snapshot,
            status=requested_status,
            id_column=id_column,
            name_column=name_column,
            code_column=code_column,
            province_column=province_column,
            duplicate_group_column=duplicate_group_column,
            same_name_group_column=same_name_group_column,
            review_status_column=review_status_column,
            retrieval_status_column=retrieval_status_column,
            official_site_column=official_site_column,
            recruit_site_column=recruit_site_column,
            source_url_column=source_url_column,
            source_title_column=source_title_column,
            updated_at_column=updated_at_column,
            keyword_clauses=keyword_clauses,
            keyword_params=keyword_params,
        )
    )
    prioritized_items = _decorate_review_items(items)
    group_source_items = prioritized_items
    if requested_status != "all":
        group_source_items = _decorate_review_items(
            _list_review_items_from_chapter_rule(
                raw_session,
                snapshot,
                status="all",
                keyword=requested_keyword,
            )
            if chapter_rule_review_status_column
            else _list_review_items(
                raw_session,
                snapshot,
                status="all",
                id_column=id_column,
                name_column=name_column,
                code_column=code_column,
                province_column=province_column,
                duplicate_group_column=duplicate_group_column,
                same_name_group_column=same_name_group_column,
                review_status_column=review_status_column,
                retrieval_status_column=retrieval_status_column,
                official_site_column=official_site_column,
                recruit_site_column=recruit_site_column,
                source_url_column=source_url_column,
                source_title_column=source_title_column,
                updated_at_column=updated_at_column,
                keyword_clauses=keyword_clauses,
                keyword_params=keyword_params,
            )
        )
    quick_filters = _build_review_quick_filters(prioritized_items)
    filtered_items = _apply_review_focus(prioritized_items, requested_focus)
    sorted_items = _sort_review_items(filtered_items, requested_sort)
    duplicate_groups = _build_review_group_summaries(
        group_source_items,
        group_type="duplicate",
        group_key_attr="duplicate_group_key",
        prefix="重复组",
    )
    same_name_groups = _build_review_group_summaries(
        group_source_items,
        group_type="same_name",
        group_key_attr="same_name_group_key",
        prefix="同名组",
    )
    priority_groups = _sort_review_groups([*duplicate_groups, *same_name_groups])[:6]
    queue_total = len(sorted_items)
    matched_total = len(prioritized_items) if requested_keyword else None
    if queue_total > 50:
        notes.append(f"当前按“{REVIEW_SORT_TITLES[requested_sort]}”只展示前 50 条学校明细，其余记录请继续用关键字或快速筛选缩小范围。")
    if (requested_status != "all" or requested_focus != "all") and (duplicate_groups or same_name_groups):
        notes.append("组级视图默认保留当前关键字下的全量组成员，不随学校状态筛选或快速筛选收缩，便于直接做组内裁决。")
    highlights = _build_review_highlights(
        sorted_items,
        requested_status,
        requested_keyword,
        requested_focus,
        quick_filters,
        matched_total,
        priority_groups,
    )

    return GaokaoReviewSummaryRead(
        source_available=True,
        source_mode="db_rc1_live",
        active_filter=requested_status,
        active_focus=requested_focus,
        active_sort=requested_sort,
        active_keyword=requested_keyword or None,
        matched_total=matched_total,
        queue_total=queue_total,
        chapter_url_covered=(
            _count_nonempty(
                raw_session,
                "gaokao_college_chapter_rule",
                snapshot.pick_column("gaokao_college_chapter_rule", "chapter_url"),
            )
            if snapshot.has_table("gaokao_college_chapter_rule")
            else _count_nonempty(
                raw_session,
                "gaokao_policy_reference",
                snapshot.pick_column("gaokao_policy_reference", "chapter_url"),
            )
            if snapshot.has_table("gaokao_policy_reference")
            else int(doc_baseline["gaokao_college_with_chapter_url"])
        ),
        chapter_url_coverage_rate=_safe_rate(
            _count_nonempty(
                raw_session,
                "gaokao_college_chapter_rule",
                snapshot.pick_column("gaokao_college_chapter_rule", "chapter_url"),
            )
            if snapshot.has_table("gaokao_college_chapter_rule")
            else _count_nonempty(
                raw_session,
                "gaokao_policy_reference",
                snapshot.pick_column("gaokao_policy_reference", "chapter_url"),
            )
            if snapshot.has_table("gaokao_policy_reference")
            else int(doc_baseline["gaokao_college_with_chapter_url"]),
            _count_rows(raw_session, "gaokao_college"),
        ),
        duplicate_group_total=_count_distinct_nonempty(raw_session, "gaokao_college", duplicate_group_column)
        or int(doc_baseline["duplicate_group_total"]),
        same_name_cross_site_group_total=_count_distinct_nonempty(
            raw_session,
            "gaokao_college",
            same_name_group_column,
        )
        or int(doc_baseline["same_name_cross_site_group_total"]),
        counts=counts,
        quick_filters=quick_filters,
        items=sorted_items[:50],
        priority_groups=priority_groups,
        duplicate_groups=duplicate_groups,
        same_name_groups=same_name_groups,
        highlights=highlights,
        notes=[
            chapter_rule_review_status_column
            and "当前审阅页明细优先来自 gaokao_college_chapter_rule，并补充 gaokao_college 的基础字段。"
            or "当前审阅页明细来自 gaokao_college / gaokao_policy_reference 只读表。",
            *notes,
        ],
    )


def get_college_evidence(
    app_session: Session,
    gaokao_session: Session | None,
    settings,
    college_id: int,
) -> GaokaoCollegeEvidenceRead:
    raw_session = _pick_raw_session(app_session, gaokao_session)
    snapshot = _SchemaSnapshot(raw_session)

    if snapshot.has_table("gaokao_college"):
        evidence = _fetch_college_evidence_from_raw(raw_session, snapshot, college_id)
        if evidence:
            return evidence
        raise HTTPException(status_code=404, detail="学校证据不存在")

    college = app_session.get(College, college_id)
    if college:
        return GaokaoCollegeEvidenceRead(
            source_available=False,
            source_mode="app_model_fallback",
            college_id=college_id,
            college_name=college.name,
            college_code=college.college_code,
            province=college.province,
            message="当前只接入了应用侧院校主档，DB RC1 的章程证据字段尚未在本地应用层暴露。",
            notes=["可先用当前院校主档占位，待 DB RC1 handoff 后再展示 official_site / chapter_url / review_status 等字段。"],
        )

    return GaokaoCollegeEvidenceRead(
        source_available=False,
        source_mode="doc_baseline",
        college_id=college_id,
        message="当前应用侧没有对应学校主档，也没有 DB RC1 证据链表；证据页先保持空态。",
        notes=["如需正式证据页明细，需要 DB RC1 handoff 或单独 DB contract。"],
    )


def get_shandong_monitor(
    app_session: Session,
    gaokao_session: Session | None,
    settings,
) -> GaokaoShandongMonitorRead:
    doc_baseline = _load_sync_board_baseline(settings.project_root)
    raw_session = _pick_raw_session(app_session, gaokao_session)
    snapshot = _SchemaSnapshot(raw_session)
    notes = ["山东监控页优先复用现有应用模型；缺失的原始事实表会明确标成待 handoff。"]
    shandong_where_clause, shandong_where_params = _build_province_alias_where_clause("province", "山东")

    sections = [
        _build_shandong_section_from_raw_or_model(
            app_session,
            raw_session,
            snapshot,
            key="province_rules",
            label="山东规则包",
            raw_table="gaokao_province_rule",
            raw_province_column_candidates=("province",),
            raw_updated_candidates=("updated_at", "modified_at", "created_at"),
            raw_where_clause=shandong_where_clause,
            raw_where_params=shandong_where_params,
            model=ProvinceVolunteerRule,
            model_filter=ProvinceVolunteerRule.province == "山东",
            model_batch_label="Stage B 应用规则",
        ),
        _build_shandong_section_from_raw_or_model(
            app_session,
            raw_session,
            snapshot,
            key="score_transform_rules",
            label="山东分数线 / 赋分规则",
            raw_table="gaokao_score_transform_rule",
            raw_province_column_candidates=("province",),
            raw_updated_candidates=("updated_at", "modified_at", "created_at"),
            raw_where_clause=shandong_where_clause,
            raw_where_params=shandong_where_params,
            model=ProvinceScoreTransformRule,
            model_filter=ProvinceScoreTransformRule.province == "山东",
            model_batch_label="Stage B 赋分规则",
            notes=["当前仓库若未接入 gaokao_score_transform_rule，只显示空态。"],
        ),
        _build_shandong_section_from_raw_or_model(
            app_session,
            raw_session,
            snapshot,
            key="score_rank_segments",
            label="山东一分一段",
            raw_table="score_rank_segment",
            raw_province_column_candidates=("province",),
            raw_updated_candidates=("updated_at", "modified_at", "created_at"),
            raw_where_clause=shandong_where_clause,
            raw_where_params=shandong_where_params,
        ),
        _build_shandong_section_from_raw_or_model(
            app_session,
            raw_session,
            snapshot,
            key="subject_requirements",
            label="山东选科要求",
            raw_table="gaokao_subject_requirement_dict",
            raw_province_column_candidates=("province",),
            raw_updated_candidates=("updated_at", "modified_at", "created_at"),
            raw_fallback_table="gaokao_subject_requirement",
            raw_where_clause=shandong_where_clause,
            raw_where_params=shandong_where_params,
            model=SubjectRequirementDict,
            model_filter=SubjectRequirementDict.province == "山东",
            model_batch_label="Stage B 选科字典",
            notes=["若原始 gaokao_subject_requirement_dict 未接入，当前优先回退到应用侧选科要求字典。"],
        ),
        _build_shandong_section_from_raw_or_model(
            app_session,
            raw_session,
            snapshot,
            key="admission_results",
            label="山东投档录取",
            raw_table="gaokao_admission_result",
            raw_province_column_candidates=("province",),
            raw_updated_candidates=("updated_at", "modified_at", "created_at"),
            raw_where_clause=shandong_where_clause,
            raw_where_params=shandong_where_params,
            model=AdmissionRecord,
            model_filter=AdmissionRecord.province == "山东",
        ),
        _build_shandong_section_from_raw_or_model(
            app_session,
            raw_session,
            snapshot,
            key="enrollment_plans",
            label="山东招生计划",
            raw_table="gaokao_admission_plan",
            raw_province_column_candidates=("province",),
            raw_updated_candidates=("updated_at", "modified_at", "created_at"),
            raw_where_clause=shandong_where_clause,
            raw_where_params=shandong_where_params,
            model=EnrollmentPlan,
            model_filter=EnrollmentPlan.province == "山东",
            model_batch_label=_latest_enrollment_plan_batch(app_session),
        ),
    ]
    ready_section_total = sum(1 for item in sections if item.status == "ready")
    gap_section_total = sum(1 for item in sections if item.status != "ready")
    priority_notes = _build_shandong_priority_notes(sections)

    return GaokaoShandongMonitorRead(
        province="山东",
        source_mode="mixed_read_only",
        data_version=str(doc_baseline["data_version"]),
        generated_at=_stringify_timestamp(doc_baseline["generated_at"]),
        ready_section_total=ready_section_total,
        gap_section_total=gap_section_total,
        priority_notes=priority_notes,
        sections=sections,
        notes=notes,
    )


def _build_shandong_section_from_raw_or_model(
    app_session: Session,
    raw_session: Session,
    snapshot: _SchemaSnapshot,
    *,
    key: str,
    label: str,
    raw_table: str,
    raw_province_column_candidates: tuple[str, ...],
    raw_updated_candidates: tuple[str, ...],
    raw_fallback_table: str | None = None,
    raw_where_clause: str | None = None,
    raw_where_params: dict[str, object] | None = None,
    model=None,
    model_filter=None,
    model_batch_label: str | None = None,
    notes: list[str] | None = None,
) -> GaokaoTableStatRead:
    section_notes = list(notes or [])

    table_name = None
    if snapshot.has_table(raw_table):
        table_name = raw_table
    elif raw_fallback_table and snapshot.has_table(raw_fallback_table):
        table_name = raw_fallback_table

    if table_name:
        province_column = snapshot.pick_column(table_name, *raw_province_column_candidates)
        if table_name == raw_table and not province_column and raw_fallback_table and snapshot.has_table(raw_fallback_table):
            table_name = raw_fallback_table
            province_column = snapshot.pick_column(table_name, *raw_province_column_candidates)
        where_clause = raw_where_clause
        where_params = raw_where_params
        if not where_clause and province_column:
            where_clause = f"{province_column} = :province"
            where_params = {"province": "山东"}
        if table_name == raw_table and raw_fallback_table and snapshot.has_table(raw_fallback_table):
            current_total = _count_rows(
                raw_session,
                raw_table,
                where_clause=where_clause,
                params=where_params,
            )
            if current_total == 0:
                table_name = raw_fallback_table
                fallback_province_column = snapshot.pick_column(raw_fallback_table, *raw_province_column_candidates)
                if fallback_province_column and raw_where_clause:
                    where_clause, where_params = _build_province_alias_where_clause(fallback_province_column, "山东")
                elif fallback_province_column:
                    where_clause = f"{fallback_province_column} = :province"
                    where_params = {"province": "山东"}
        record_total = _count_rows(
            raw_session,
            table_name,
            where_clause=where_clause,
            params=where_params,
        )
        updated_at = _max_timestamp(
            raw_session,
            table_name,
            snapshot.pick_column(table_name, *raw_updated_candidates),
            where_clause=where_clause,
            params=where_params,
        )
        section_notes.append("当前优先读取本地 gaokao_* 只读表。")
        if raw_fallback_table and table_name == raw_fallback_table:
            section_notes.append(f"{raw_table} 当前无数据，已自动回退到 {raw_fallback_table}。")
        return _build_table_stat(
            key=key,
            label=label,
            record_total=record_total,
            latest_updated_at=updated_at,
            status="ready" if record_total else "empty",
            notes=section_notes,
        )

    if model is not None:
        statement = select(func.count()).select_from(model)
        if model_filter is not None:
            statement = statement.where(model_filter)
        record_total = app_session.scalar(statement) or 0
        updated_statement = select(func.max(model.updated_at))
        if model_filter is not None:
            updated_statement = updated_statement.where(model_filter)
        section_notes.append("当前使用应用侧模型做只读 fallback。")
        return _build_table_stat(
            key=key,
            label=label,
            record_total=record_total,
            latest_updated_at=_stringify_timestamp(app_session.scalar(updated_statement)),
            latest_batch_label=model_batch_label,
            status="ready" if record_total else "partial",
            notes=section_notes,
        )

    section_notes.append("当前缺少可复用表，等待 DB RC1 正式 handoff。")
    return _build_table_stat(
        key=key,
        label=label,
        record_total=0,
        latest_batch_label="待 handoff",
        status="waiting",
        notes=section_notes,
    )


def _fetch_college_evidence_from_raw(
    session: Session,
    snapshot: _SchemaSnapshot,
    college_id: int,
) -> GaokaoCollegeEvidenceRead | None:
    id_column = snapshot.pick_column("gaokao_college", "id", "college_id")
    if not id_column:
        return None

    name_column = snapshot.pick_column("gaokao_college", "name", "college_name")
    code_column = snapshot.pick_column("gaokao_college", "college_code", "school_code", "code")
    province_column = snapshot.pick_column("gaokao_college", "province")
    official_site_column = snapshot.pick_column("gaokao_college", "official_site", "website")
    recruit_site_column = snapshot.pick_column("gaokao_college", "recruit_site")
    review_status_column = snapshot.pick_column("gaokao_college", "review_status")
    retrieval_status_column = snapshot.pick_column("gaokao_college", "retrieval_status")
    source_url_column = snapshot.pick_column("gaokao_college", "source_url")
    source_title_column = snapshot.pick_column("gaokao_college", "source_title")
    updated_at_column = snapshot.pick_column("gaokao_college", "updated_at", "modified_at", "created_at")
    chapter_url_column = snapshot.pick_column("gaokao_college", "chapter_url")
    fallback_url_column = snapshot.pick_column("gaokao_college", "chapter_fallback_url")

    select_columns = [
        f"c.{id_column} AS college_id",
        f"c.{name_column} AS college_name" if name_column else "NULL AS college_name",
        f"c.{code_column} AS college_code" if code_column else "NULL AS college_code",
        f"c.{province_column} AS province" if province_column else "NULL AS province",
        f"c.{official_site_column} AS official_site" if official_site_column else "NULL AS official_site",
        f"c.{recruit_site_column} AS recruit_site" if recruit_site_column else "NULL AS recruit_site",
        f"c.{review_status_column} AS review_status" if review_status_column else "NULL AS review_status",
        f"c.{retrieval_status_column} AS retrieval_status" if retrieval_status_column else "NULL AS retrieval_status",
        f"c.{source_url_column} AS source_url" if source_url_column else "NULL AS source_url",
        f"c.{source_title_column} AS source_title" if source_title_column else "NULL AS source_title",
        f"c.{updated_at_column} AS updated_at" if updated_at_column else "NULL AS updated_at",
        f"c.{chapter_url_column} AS chapter_url" if chapter_url_column else "NULL AS chapter_url",
        f"c.{fallback_url_column} AS fallback_url" if fallback_url_column else "NULL AS fallback_url",
    ]

    row = session.execute(
        text(
            f"""
            SELECT {", ".join(select_columns)}
            FROM gaokao_college c
            WHERE c.{id_column} = :college_id
            LIMIT 1
            """
        ),
        {"college_id": college_id},
    ).mappings().first()

    if not row:
        return None

    chapter_rule_row = None
    if snapshot.has_table("gaokao_college_chapter_rule"):
        chapter_rule_row = session.execute(
            text(
                """
                SELECT
                    chapter_url,
                    chapter_fallback_url,
                    review_status,
                    retrieval_status,
                    source_url,
                    source_title,
                    updated_at
                FROM gaokao_college_chapter_rule
                WHERE college_id = :college_id
                ORDER BY COALESCE(updated_at, created_at) DESC, id DESC
                LIMIT 1
                """
            ),
            {"college_id": college_id},
        ).mappings().first()
    elif snapshot.has_table("gaokao_policy_reference"):
        policy_college_column = snapshot.pick_column("gaokao_policy_reference", "college_id")
        if policy_college_column:
            chapter_rule_row = session.execute(
                text(
                    f"""
                    SELECT
                        {snapshot.pick_column("gaokao_policy_reference", "chapter_url", "url") or 'NULL'} AS chapter_url,
                        {snapshot.pick_column("gaokao_policy_reference", "fallback_url", "local_path") or 'NULL'} AS chapter_fallback_url,
                        NULL AS review_status,
                        NULL AS retrieval_status,
                        NULL AS source_url,
                        NULL AS source_title,
                        {snapshot.pick_column("gaokao_policy_reference", "updated_at", "modified_at", "created_at") or 'NULL'} AS updated_at
                    FROM gaokao_policy_reference
                    WHERE {policy_college_column} = :college_id
                    ORDER BY COALESCE({snapshot.pick_column("gaokao_policy_reference", "updated_at", "modified_at", "created_at") or 'id'}, id) DESC
                    LIMIT 1
                    """
                ),
                {"college_id": college_id},
            ).mappings().first()

    return GaokaoCollegeEvidenceRead(
        source_available=True,
        source_mode="db_rc1_live",
        college_id=int(row["college_id"]),
        college_name=_clean_text(row["college_name"]),
        college_code=_clean_text(row["college_code"]),
        province=_normalize_province_value(_clean_text(row["province"])),
        official_site=_clean_text(row["official_site"]),
        recruit_site=_clean_text(row["recruit_site"]),
        chapter_url=(_clean_text(chapter_rule_row["chapter_url"]) if chapter_rule_row else None) or _clean_text(row["chapter_url"]),
        fallback_url=(_clean_text(chapter_rule_row["chapter_fallback_url"]) if chapter_rule_row else None) or _clean_text(row["fallback_url"]),
        source_url=(_clean_text(chapter_rule_row["source_url"]) if chapter_rule_row else None) or _clean_text(row["source_url"]),
        source_title=(_clean_text(chapter_rule_row["source_title"]) if chapter_rule_row else None) or _clean_text(row["source_title"]),
        review_status=(_clean_text(chapter_rule_row["review_status"]) if chapter_rule_row else None) or _clean_text(row["review_status"]),
        retrieval_status=(_clean_text(chapter_rule_row["retrieval_status"]) if chapter_rule_row else None) or _clean_text(row["retrieval_status"]),
        updated_at=(_stringify_timestamp(chapter_rule_row["updated_at"]) if chapter_rule_row else None) or _stringify_timestamp(row["updated_at"]),
        notes=["当前证据链字段优先来自 gaokao_college_chapter_rule，其余基础字段来自 gaokao_college。"],
    )


def _list_college_options_from_raw(
    session: Session,
    snapshot: _SchemaSnapshot,
    *,
    query: str,
    limit: int,
) -> list[GaokaoCollegeOptionRead]:
    id_column = snapshot.pick_column("gaokao_college", "id", "college_id")
    if not id_column:
        return []

    name_column = snapshot.pick_column("gaokao_college", "name", "college_name")
    code_column = snapshot.pick_column("gaokao_college", "college_code", "school_code", "code")
    province_column = snapshot.pick_column("gaokao_college", "province")
    review_status_column = snapshot.pick_column("gaokao_college", "review_status")
    updated_at_column = snapshot.pick_column("gaokao_college", "updated_at", "modified_at", "created_at")

    select_columns = [
        f"c.{id_column} AS college_id",
        f"c.{name_column} AS college_name" if name_column else "NULL AS college_name",
        f"c.{code_column} AS college_code" if code_column else "NULL AS college_code",
        f"c.{province_column} AS province" if province_column else "NULL AS province",
        f"c.{review_status_column} AS review_status" if review_status_column else "NULL AS review_status",
    ]

    params: dict[str, object] = {"limit": limit}
    where_clauses: list[str] = []
    rank_clauses: list[str] = []
    if query:
        like_query = f"%{query}%"
        params["query_exact"] = query
        params["like_query"] = like_query
        if query.isdigit():
            params["exact_id"] = int(query)
            where_clauses.append(f"c.{id_column} = :exact_id")
            rank_clauses.append(f"WHEN c.{id_column} = :exact_id THEN 0")
        if code_column:
            where_clauses.append(f"c.{code_column} LIKE :like_query")
            rank_clauses.append(f"WHEN c.{code_column} = :query_exact THEN 1")
        if name_column:
            where_clauses.append(f"c.{name_column} LIKE :like_query")
            rank_clauses.append(f"WHEN c.{name_column} = :query_exact THEN 2")
        if province_column:
            where_clauses.append(f"c.{province_column} LIKE :like_query")
        if not where_clauses:
            return []

    where_sql = f"WHERE {' OR '.join(where_clauses)}" if where_clauses else ""
    updated_order = f"c.{updated_at_column} DESC" if updated_at_column else f"c.{id_column} DESC"
    rank_sql = f"CASE {' '.join(rank_clauses)} ELSE 9 END," if rank_clauses else ""
    rows = session.execute(
        text(
            f"""
            SELECT {", ".join(select_columns)}
            FROM gaokao_college c
            {where_sql}
            ORDER BY {rank_sql} {updated_order}
            LIMIT :limit
            """
        ),
        params,
    ).mappings().all()

    return [
        GaokaoCollegeOptionRead(
            college_id=int(row["college_id"]),
            college_name=_clean_text(row["college_name"]),
            college_code=_clean_text(row["college_code"]),
            province=_normalize_province_value(_clean_text(row["province"])),
            review_status=_clean_text(row["review_status"]) or _latest_chapter_rule_status(session, snapshot, int(row["college_id"])),
            source_mode="db_rc1_live",
        )
        for row in rows
    ]


def _list_review_items_from_chapter_rule(
    session: Session,
    snapshot: _SchemaSnapshot,
    *,
    status: str,
    keyword: str,
) -> list[GaokaoReviewItemRead]:
    if not snapshot.has_table("gaokao_college_chapter_rule"):
        return []

    college_id_column = snapshot.pick_column("gaokao_college", "id", "college_id") or "id"
    college_name_column = snapshot.pick_column("gaokao_college", "name", "college_name")
    college_code_column = snapshot.pick_column("gaokao_college", "college_code", "school_code", "code")
    college_province_column = snapshot.pick_column("gaokao_college", "province") or "province"
    official_site_column = snapshot.pick_column("gaokao_college", "official_site", "website")
    recruit_site_column = snapshot.pick_column("gaokao_college", "recruit_site")
    chapter_url_column = snapshot.pick_column("gaokao_college", "chapter_url")
    fallback_url_column = snapshot.pick_column("gaokao_college", "chapter_fallback_url")
    duplicate_group_column = snapshot.pick_column("gaokao_college", "duplicate_group_key", "duplicate_group_id")
    same_name_group_column = snapshot.pick_column("gaokao_college", "same_name_group_key", "same_name_group_id")
    chapter_rule_name_column = snapshot.pick_column("gaokao_college_chapter_rule", "college_name_snapshot")
    chapter_rule_code_column = snapshot.pick_column("gaokao_college_chapter_rule", "college_code_snapshot")

    college_name_expr = f"c.{college_name_column}" if college_name_column else "NULL"
    chapter_rule_name_expr = f"r.{chapter_rule_name_column}" if chapter_rule_name_column else "NULL"
    college_code_expr = f"c.{college_code_column}" if college_code_column else "NULL"
    chapter_rule_code_expr = f"r.{chapter_rule_code_column}" if chapter_rule_code_column else "NULL"
    official_site_expr = f"c.{official_site_column}" if official_site_column else "NULL"
    recruit_site_expr = f"c.{recruit_site_column}" if recruit_site_column else "NULL"
    chapter_url_expr = f"c.{chapter_url_column}" if chapter_url_column else "NULL"
    fallback_url_expr = f"c.{fallback_url_column}" if fallback_url_column else "NULL"

    where_clauses: list[str] = []
    params: dict[str, object] = {}
    if status != "all":
        where_clauses.append("r.review_status = :status")
        params["status"] = status
    if keyword.strip():
        params["keyword_like"] = f"%{keyword.strip()}%"
        where_clauses.append(
            "("
            "CAST(COALESCE(c.id, r.college_id) AS TEXT) LIKE :keyword_like OR "
            f"COALESCE({college_name_expr}, {chapter_rule_name_expr}) LIKE :keyword_like OR "
            f"COALESCE({college_code_expr}, {chapter_rule_code_expr}) LIKE :keyword_like OR "
            "COALESCE(c.province, r.province) LIKE :keyword_like OR "
            f"COALESCE({recruit_site_expr}, '') LIKE :keyword_like OR "
            "COALESCE(r.source_title, '') LIKE :keyword_like"
            ")"
        )

    rows = session.execute(
        text(
            f"""
            SELECT
                COALESCE(c.{college_id_column}, r.college_id) AS college_id,
                COALESCE({college_name_expr}, {chapter_rule_name_expr}) AS college_name,
                COALESCE({college_code_expr}, {chapter_rule_code_expr}) AS college_code,
                COALESCE(c.{college_province_column}, r.province) AS province,
                {"c." + duplicate_group_column + " AS duplicate_group_key," if duplicate_group_column else "NULL AS duplicate_group_key,"}
                {"c." + same_name_group_column + " AS same_name_group_key," if same_name_group_column else "NULL AS same_name_group_key,"}
                r.review_status AS review_status,
                r.retrieval_status AS retrieval_status,
                {official_site_expr} AS official_site,
                {recruit_site_expr} AS recruit_site,
                COALESCE(r.chapter_url, {chapter_url_expr}) AS chapter_url,
                COALESCE(r.chapter_fallback_url, {fallback_url_expr}) AS fallback_url,
                r.source_url AS source_url,
                r.source_title AS source_title,
                COALESCE(r.updated_at, c.updated_at) AS updated_at
            FROM gaokao_college_chapter_rule r
            LEFT JOIN gaokao_college c ON c.{college_id_column} = r.college_id
            {"WHERE " + " AND ".join(where_clauses) if where_clauses else ""}
            ORDER BY COALESCE(r.updated_at, c.updated_at) DESC, COALESCE(c.{college_id_column}, r.college_id) DESC
            """
        ),
        params,
    ).mappings().all()

    items: list[GaokaoReviewItemRead] = []
    seen_college_ids: set[int] = set()
    for row in rows:
        college_id = int(row["college_id"]) if row["college_id"] is not None else None
        if college_id is not None and college_id in seen_college_ids:
            continue
        if college_id is not None:
            seen_college_ids.add(college_id)
        items.append(
            GaokaoReviewItemRead(
                college_id=college_id,
                college_name=_clean_text(row["college_name"]),
                college_code=_clean_text(row["college_code"]),
                province=_normalize_province_value(_clean_text(row["province"])),
                duplicate_group_key=_clean_text(row["duplicate_group_key"]),
                same_name_group_key=_clean_text(row["same_name_group_key"]),
                review_status=_clean_text(row["review_status"]),
                retrieval_status=_clean_text(row["retrieval_status"]),
                official_site=_clean_text(row["official_site"]),
                recruit_site=_clean_text(row["recruit_site"]),
                chapter_url=_clean_text(row["chapter_url"]),
                fallback_url=_clean_text(row["fallback_url"]),
                source_url=_clean_text(row["source_url"]),
                source_title=_clean_text(row["source_title"]),
                updated_at=_stringify_timestamp(row["updated_at"]),
            )
        )

    return items


def _list_college_options_from_model(
    session: Session,
    *,
    query: str,
    limit: int,
) -> list[GaokaoCollegeOptionRead]:
    statement = select(College).where(College.is_active.is_(True))
    if query:
        filters = [College.name.ilike(f"%{query}%")]
        if query.isdigit():
            filters.append(College.id == int(query))
        if getattr(College, "college_code", None) is not None:
            filters.append(College.college_code.ilike(f"%{query}%"))
        if getattr(College, "province", None) is not None:
            filters.append(College.province.ilike(f"%{query}%"))
        statement = statement.where(or_(*filters))
    statement = statement.order_by(College.updated_at.desc(), College.id.desc()).limit(limit)
    rows = session.scalars(statement).all()
    return [
        GaokaoCollegeOptionRead(
            college_id=item.id,
            college_name=item.name,
            college_code=item.college_code,
            province=item.province,
            source_mode="app_model_fallback",
        )
        for item in rows
    ]


def _list_review_items(
    session: Session,
    snapshot: _SchemaSnapshot,
    *,
    status: str,
    id_column: str | None,
    name_column: str | None,
    code_column: str | None,
    province_column: str | None,
    duplicate_group_column: str | None,
    same_name_group_column: str | None,
    review_status_column: str | None,
    retrieval_status_column: str | None,
    official_site_column: str | None,
    recruit_site_column: str | None,
    source_url_column: str | None,
    source_title_column: str | None,
    updated_at_column: str | None,
    keyword_clauses: list[str],
    keyword_params: dict[str, object],
) -> list[GaokaoReviewItemRead]:
    if not id_column:
        return []

    select_columns = [
        f"c.{id_column} AS college_id",
        f"c.{name_column} AS college_name" if name_column else "NULL AS college_name",
        f"c.{code_column} AS college_code" if code_column else "NULL AS college_code",
        f"c.{province_column} AS province" if province_column else "NULL AS province",
        f"c.{duplicate_group_column} AS duplicate_group_key" if duplicate_group_column else "NULL AS duplicate_group_key",
        f"c.{same_name_group_column} AS same_name_group_key" if same_name_group_column else "NULL AS same_name_group_key",
        f"c.{review_status_column} AS review_status" if review_status_column else "NULL AS review_status",
        f"c.{retrieval_status_column} AS retrieval_status" if retrieval_status_column else "NULL AS retrieval_status",
        f"c.{official_site_column} AS official_site" if official_site_column else "NULL AS official_site",
        f"c.{recruit_site_column} AS recruit_site" if recruit_site_column else "NULL AS recruit_site",
        f"c.{source_url_column} AS source_url" if source_url_column else "NULL AS source_url",
        f"c.{source_title_column} AS source_title" if source_title_column else "NULL AS source_title",
        f"c.{updated_at_column} AS updated_at" if updated_at_column else "NULL AS updated_at",
        "NULL AS chapter_url",
        "NULL AS fallback_url",
    ]
    join_clause = ""
    if snapshot.has_table("gaokao_policy_reference"):
        policy_college_column = snapshot.pick_column("gaokao_policy_reference", "college_id")
        chapter_url_column = snapshot.pick_column("gaokao_policy_reference", "chapter_url")
        fallback_url_column = snapshot.pick_column("gaokao_policy_reference", "fallback_url")
        if policy_college_column:
            select_columns[-2] = f"p.{chapter_url_column} AS chapter_url" if chapter_url_column else "NULL AS chapter_url"
            select_columns[-1] = f"p.{fallback_url_column} AS fallback_url" if fallback_url_column else "NULL AS fallback_url"
            join_clause = f" LEFT JOIN gaokao_policy_reference p ON p.{policy_college_column} = c.{id_column}"

    where_clauses: list[str] = []
    params: dict[str, object] = dict(keyword_params)
    if status != "all" and review_status_column:
        where_clauses.append(f"c.{review_status_column} = :status")
        params["status"] = status
    if keyword_clauses:
        where_clauses.append(f"({' OR '.join(keyword_clauses)})")
    order_column = updated_at_column or id_column
    where_sql = f" WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

    rows = session.execute(
        text(
            f"""
            SELECT {", ".join(select_columns)}
            FROM gaokao_college c
            {join_clause}
            {where_sql}
            ORDER BY c.{order_column} DESC
            """
        ),
        params,
    ).mappings().all()

    return [
        GaokaoReviewItemRead(
            college_id=int(row["college_id"]) if row["college_id"] is not None else None,
            college_name=_clean_text(row["college_name"]),
            college_code=_clean_text(row["college_code"]),
            province=_clean_text(row["province"]),
            duplicate_group_key=_clean_text(row["duplicate_group_key"]),
            same_name_group_key=_clean_text(row["same_name_group_key"]),
            review_status=_clean_text(row["review_status"]),
            retrieval_status=_clean_text(row["retrieval_status"]),
            official_site=_clean_text(row["official_site"]),
            recruit_site=_clean_text(row["recruit_site"]),
            chapter_url=_clean_text(row["chapter_url"]),
            fallback_url=_clean_text(row["fallback_url"]),
            source_url=_clean_text(row["source_url"]),
            source_title=_clean_text(row["source_title"]),
            updated_at=_stringify_timestamp(row["updated_at"]),
        )
        for row in rows
    ]


def _build_review_group_summaries(
    items: list[GaokaoReviewItemRead],
    *,
    group_type: str,
    group_key_attr: str,
    prefix: str,
) -> list[GaokaoReviewGroupRead]:
    grouped_items: dict[str, list[GaokaoReviewItemRead]] = {}
    for item in items:
        group_key = getattr(item, group_key_attr)
        if not group_key:
            continue
        grouped_items.setdefault(group_key, []).append(item)

    groups: list[GaokaoReviewGroupRead] = []
    for group_key, group_members in grouped_items.items():
        sorted_members = _sort_review_items(group_members, "priority_desc")
        high_priority_member_total = sum(1 for item in sorted_members if item.priority_code == "high")
        unresolved_total = sum(1 for item in sorted_members if item.review_status == "unresolved")
        missing_chapter_total = sum(1 for item in sorted_members if not (item.chapter_url or item.fallback_url))
        missing_recruit_site_total = sum(1 for item in sorted_members if not item.recruit_site)
        priority_score = _build_review_group_priority_score(
            sorted_members,
            group_type=group_type,
            high_priority_member_total=high_priority_member_total,
            unresolved_total=unresolved_total,
            missing_chapter_total=missing_chapter_total,
            missing_recruit_site_total=missing_recruit_site_total,
        )
        priority_code = _resolve_review_priority_code(priority_score)
        priority_reasons = _build_review_group_priority_reasons(
            item_count=len(sorted_members),
            high_priority_member_total=high_priority_member_total,
            unresolved_total=unresolved_total,
            missing_chapter_total=missing_chapter_total,
            missing_recruit_site_total=missing_recruit_site_total,
        )

        groups.append(
            GaokaoReviewGroupRead(
                key=group_key,
                title=f"{prefix} {group_key}",
                group_type=group_type,
                item_count=len(sorted_members),
                members=[
                    item.college_name or f"学校 {item.college_id}"
                    for item in sorted_members
                    if item.college_name or item.college_id
                ],
                member_items=[
                    _build_review_group_member(item)
                    for item in sorted_members[:8]
                ],
                comparison_fields=_build_review_group_comparison_fields(sorted_members),
                priority_code=priority_code,
                priority_label=REVIEW_PRIORITY_LABELS[priority_code],
                priority_score=priority_score,
                priority_reasons=priority_reasons,
                suggested_action=_build_review_group_action(
                    group_type=group_type,
                    unresolved_total=unresolved_total,
                    missing_chapter_total=missing_chapter_total,
                    missing_recruit_site_total=missing_recruit_site_total,
                ),
                high_priority_member_total=high_priority_member_total,
                unresolved_total=unresolved_total,
                missing_chapter_total=missing_chapter_total,
                missing_recruit_site_total=missing_recruit_site_total,
            )
        )

    return _sort_review_groups(groups)


def _build_review_keyword_clauses(
    keyword: str,
    *,
    id_column: str | None,
    name_column: str | None,
    code_column: str | None,
    province_column: str | None,
    recruit_site_column: str | None,
    source_title_column: str | None,
) -> tuple[list[str], dict[str, object]]:
    normalized_keyword = keyword.strip()
    if not normalized_keyword:
        return [], {}

    params: dict[str, object] = {
        "keyword_exact": normalized_keyword,
        "keyword_like": f"%{normalized_keyword}%",
    }
    clauses: list[str] = []
    if normalized_keyword.isdigit() and id_column:
        clauses.append(f"c.{id_column} = :keyword_id")
        params["keyword_id"] = int(normalized_keyword)
    if name_column:
        clauses.append(f"c.{name_column} LIKE :keyword_like")
    if code_column:
        clauses.append(f"c.{code_column} LIKE :keyword_like")
    if province_column:
        clauses.append(f"c.{province_column} LIKE :keyword_like")
    if recruit_site_column:
        clauses.append(f"c.{recruit_site_column} LIKE :keyword_like")
    if source_title_column:
        clauses.append(f"c.{source_title_column} LIKE :keyword_like")
    return clauses, params


def _normalize_review_focus(value: str | None) -> str:
    normalized_value = (value or "all").strip() or "all"
    if normalized_value not in REVIEW_FOCUS_TITLES:
        return "all"
    return normalized_value


def _normalize_review_sort(value: str | None) -> str:
    normalized_value = (value or "priority_desc").strip() or "priority_desc"
    if normalized_value not in REVIEW_SORT_TITLES:
        return "priority_desc"
    return normalized_value


def _decorate_review_items(items: list[GaokaoReviewItemRead]) -> list[GaokaoReviewItemRead]:
    return [
        item.model_copy(update=_build_review_priority_payload(item))
        for item in items
    ]


def _build_review_priority_payload(item: GaokaoReviewItemRead) -> dict[str, object]:
    score = 0
    reasons: list[str] = []

    if item.review_status == "unresolved":
        score += 48
        reasons.append("仍未解决")
    elif item.review_status == "pending_manual_review_with_official_candidate":
        score += 22
        reasons.append("已有官方候选待确认")
    elif item.review_status == "pending_manual_review":
        score += 12
        reasons.append("待人工复核")

    if not (item.chapter_url or item.fallback_url):
        score += 26
        reasons.append("缺章程入口")
    if not item.recruit_site:
        score += 20
        reasons.append("缺招生网入口")
    if item.duplicate_group_key:
        score += 12
        reasons.append("位于重复组")
    if item.same_name_group_key:
        score += 10
        reasons.append("位于同名跨站组")
    if item.retrieval_status and item.retrieval_status not in {"retrieved", "ready", "success", "done"}:
        score += 8
        reasons.append(f"抓取状态 {item.retrieval_status}")
    if not item.official_site:
        score += 4
        reasons.append("官方站待确认")

    priority_code = _resolve_review_priority_code(score)

    return {
        "priority_code": priority_code,
        "priority_label": REVIEW_PRIORITY_LABELS[priority_code],
        "priority_score": score,
        "priority_reasons": reasons[:4],
    }


def _resolve_review_priority_code(score: int) -> str:
    if score >= 60:
        return "high"
    if score >= 35:
        return "medium"
    return "low"


def _build_review_group_member(item: GaokaoReviewItemRead) -> GaokaoReviewGroupMemberRead:
    return GaokaoReviewGroupMemberRead(
        college_id=item.college_id,
        college_name=item.college_name,
        college_code=item.college_code,
        review_status=item.review_status,
        province=item.province,
        official_site=item.official_site,
        recruit_site=item.recruit_site,
        chapter_url=item.chapter_url,
        fallback_url=item.fallback_url,
        effective_chapter_url=item.chapter_url or item.fallback_url,
        source_title=item.source_title,
        source_url=item.source_url,
        updated_at=item.updated_at,
        priority_code=item.priority_code,
        priority_label=item.priority_label,
        priority_score=item.priority_score,
        priority_reasons=item.priority_reasons,
    )


def _build_review_group_comparison_fields(
    items: list[GaokaoReviewItemRead],
) -> list[GaokaoReviewGroupComparisonFieldRead]:
    field_configs = (
        ("province", "省份", "text"),
        ("college_code", "院校代码", "text"),
        ("official_site", "官方站", "site"),
        ("recruit_site", "招生网", "site"),
        ("effective_chapter_url", "章程入口", "url"),
        ("source_title", "来源标题", "text"),
        ("source_url", "来源链接", "url"),
    )
    comparison_fields: list[GaokaoReviewGroupComparisonFieldRead] = []
    for key, title, value_kind in field_configs:
        values = [
            (item.chapter_url or item.fallback_url) if key == "effective_chapter_url" else getattr(item, key)
            for item in items
        ]
        comparison_fields.append(
            _build_review_group_comparison_field(
                key=key,
                title=title,
                values=values,
                value_kind=value_kind,
            )
        )
    return comparison_fields


def _build_review_group_comparison_field(
    *,
    key: str,
    title: str,
    values: list[str | None],
    value_kind: str,
) -> GaokaoReviewGroupComparisonFieldRead:
    normalized_values = [_normalize_review_group_compare_value(value, value_kind=value_kind) for value in values]
    sample_values = list(dict.fromkeys(value for value in normalized_values if value))
    missing_total = sum(1 for value in normalized_values if not value)

    if not sample_values:
        status = "empty"
        summary = "当前全缺"
    elif len(sample_values) == 1 and missing_total == 0:
        status = "same"
        summary = f"已对齐：{sample_values[0]}"
    elif len(sample_values) == 1:
        status = "partial"
        summary = f"1 个值，{missing_total} 条待补齐"
    else:
        status = "mixed"
        summary = f"{len(sample_values)} 个不同值"
        if missing_total:
            summary = f"{summary}，{missing_total} 条待补齐"

    return GaokaoReviewGroupComparisonFieldRead(
        key=key,
        title=title,
        status=status,
        distinct_total=len(sample_values),
        missing_total=missing_total,
        sample_values=sample_values[:3],
        summary=summary,
    )


def _normalize_review_group_compare_value(value: str | None, *, value_kind: str) -> str | None:
    cleaned_value = _clean_text(value)
    if not cleaned_value:
        return None
    if value_kind == "text":
        return cleaned_value

    parsed = urlparse(cleaned_value)
    if not parsed.netloc:
        return cleaned_value

    if value_kind == "site":
        return parsed.netloc

    normalized_path = parsed.path.rstrip("/")
    return f"{parsed.netloc}{normalized_path}" if normalized_path else parsed.netloc


def _build_review_group_priority_score(
    items: list[GaokaoReviewItemRead],
    *,
    group_type: str,
    high_priority_member_total: int,
    unresolved_total: int,
    missing_chapter_total: int,
    missing_recruit_site_total: int,
) -> int:
    top_member_score = max((item.priority_score for item in items), default=0)
    group_size_bonus = max(0, len(items) - 1) * 8
    group_type_bonus = 8 if group_type == "duplicate" else 5
    return (
        top_member_score
        + high_priority_member_total * 22
        + unresolved_total * 16
        + missing_chapter_total * 12
        + missing_recruit_site_total * 8
        + group_size_bonus
        + group_type_bonus
    )


def _build_review_group_priority_reasons(
    *,
    item_count: int,
    high_priority_member_total: int,
    unresolved_total: int,
    missing_chapter_total: int,
    missing_recruit_site_total: int,
) -> list[str]:
    reasons: list[str] = []
    if high_priority_member_total:
        reasons.append(f"{high_priority_member_total} 所学校已落入高优先")
    if unresolved_total:
        reasons.append(f"{unresolved_total} 所仍未解决")
    if missing_chapter_total:
        reasons.append(f"{missing_chapter_total} 所缺章程入口")
    if missing_recruit_site_total:
        reasons.append(f"{missing_recruit_site_total} 所缺招生网")
    if item_count > 1:
        reasons.append(f"{item_count} 条记录需要组内对照")
    return reasons[:4] or [f"{item_count} 条记录需要组内对照"]


def _build_review_group_action(
    *,
    group_type: str,
    unresolved_total: int,
    missing_chapter_total: int,
    missing_recruit_site_total: int,
) -> str:
    if unresolved_total or missing_chapter_total or missing_recruit_site_total:
        return "先逐条打开证据链，核对官方站、招生网和章程入口是否指向同一学校。"
    if group_type == "duplicate":
        return "先核对院校代码、来源站点和更新时间，确认是否为重复采集或旧站残留。"
    return "先比对组内省份、学校代码和来源站点，确认是同名异校还是同校多站。"


def _build_review_quick_filters(items: list[GaokaoReviewItemRead]) -> list[GaokaoReviewQuickFilterRead]:
    counts = {
        "all": len(items),
        "high_priority": sum(1 for item in items if item.priority_code == "high"),
        "missing_chapter": sum(1 for item in items if not (item.chapter_url or item.fallback_url)),
        "missing_recruit_site": sum(1 for item in items if not item.recruit_site),
        "duplicate_or_same_name": sum(1 for item in items if item.duplicate_group_key or item.same_name_group_key),
        "unresolved": sum(1 for item in items if item.review_status == "unresolved"),
    }
    return [
        GaokaoReviewQuickFilterRead(
            code=code,
            title=REVIEW_FOCUS_TITLES[code],
            count=counts.get(code, 0),
            description=REVIEW_FOCUS_DESCRIPTIONS[code],
        )
        for code in (
            "all",
            "high_priority",
            "missing_chapter",
            "missing_recruit_site",
            "duplicate_or_same_name",
            "unresolved",
        )
    ]


def _sort_review_groups(groups: list[GaokaoReviewGroupRead]) -> list[GaokaoReviewGroupRead]:
    return sorted(
        groups,
        key=lambda item: (
            item.priority_score,
            item.item_count,
            item.key,
        ),
        reverse=True,
    )


def _apply_review_focus(items: list[GaokaoReviewItemRead], focus: str) -> list[GaokaoReviewItemRead]:
    if focus == "all":
        return list(items)
    if focus == "high_priority":
        return [item for item in items if item.priority_code == "high"]
    if focus == "missing_chapter":
        return [item for item in items if not (item.chapter_url or item.fallback_url)]
    if focus == "missing_recruit_site":
        return [item for item in items if not item.recruit_site]
    if focus == "duplicate_or_same_name":
        return [item for item in items if item.duplicate_group_key or item.same_name_group_key]
    if focus == "unresolved":
        return [item for item in items if item.review_status == "unresolved"]
    return list(items)


def _sort_review_items(items: list[GaokaoReviewItemRead], sort: str) -> list[GaokaoReviewItemRead]:
    if sort == "updated_desc":
        return sorted(
            items,
            key=lambda item: (
                item.updated_at or "",
                item.priority_score,
                item.college_id or 0,
            ),
            reverse=True,
        )

    return sorted(
        items,
        key=lambda item: (
            item.priority_score,
            item.updated_at or "",
            item.college_id or 0,
        ),
        reverse=True,
    )


def _build_review_highlights(
    items: list[GaokaoReviewItemRead],
    status: str,
    keyword: str,
    focus: str,
    quick_filters: list[GaokaoReviewQuickFilterRead],
    matched_total: int | None,
    priority_groups: list[GaokaoReviewGroupRead],
) -> list[str]:
    highlights: list[str] = []
    quick_filter_map = {item.code: item for item in quick_filters}
    if keyword:
        highlights.append(f"当前关键字“{keyword}”命中 {matched_total if matched_total is not None else len(items)} 所学校。")
    if focus != "all":
        highlights.append(f"当前优先视图“{REVIEW_FOCUS_TITLES[focus]}”筛出 {len(items)} 所学校。")
    if status != "all":
        highlights.append(f"当前仅展示“{status}”状态下的学校。")
    top_group = priority_groups[0] if priority_groups else None
    if top_group and top_group.priority_code == "high":
        highlights.append(f"当前最先建议处理“{top_group.title}”，组内 {top_group.item_count} 条记录。")
    if not items:
        return highlights

    high_priority_total = quick_filter_map.get("high_priority")
    if focus == "all" and high_priority_total and high_priority_total.count:
        highlights.append(f"{high_priority_total.count} 所学校当前属于高优先，建议优先查看证据链。")
        return highlights[:4]

    chapter_missing = sum(1 for item in items if not (item.chapter_url or item.fallback_url))
    recruit_missing = sum(1 for item in items if not item.recruit_site)
    unresolved_total = sum(1 for item in items if item.review_status == "unresolved")

    if chapter_missing:
        highlights.append(f"{chapter_missing} 所学校当前仍缺章程入口或 fallback_url。")
    if recruit_missing:
        highlights.append(f"{recruit_missing} 所学校当前仍缺招生网入口。")
    if unresolved_total:
        highlights.append(f"{unresolved_total} 所学校仍处于 unresolved，适合优先催办证据链补齐。")
    return highlights[:4]


def _build_shandong_priority_notes(sections: list[GaokaoTableStatRead]) -> list[str]:
    severity_rank = {"waiting": 0, "partial": 1, "empty": 2, "ready": 3}
    notes: list[str] = []
    for item in sorted(sections, key=lambda row: (severity_rank.get(row.status, 9), row.label)):
        if item.status == "waiting":
            notes.append(f"{item.label} 当前待 handoff，若山东首期要演示，建议优先补这块只读表。")
        elif item.status == "partial":
            notes.append(f"{item.label} 目前只有应用侧 fallback，适合继续补原始事实表或最近批次。")
        elif item.status == "empty":
            notes.append(f"{item.label} 当前暂无数据，建议先确认是否已导入山东相关材料。")
    if not notes:
        notes.append("山东首期关键材料当前都已有只读数据或 fallback 口径，可直接用于演示。")
    return notes[:3]


def _count_rows(
    session: Session,
    table_name: str,
    *,
    where_clause: str | None = None,
    params: dict[str, object] | None = None,
) -> int:
    query = f"SELECT COUNT(*) FROM {table_name}"
    if where_clause:
        query = f"{query} WHERE {where_clause}"
    return int(session.execute(text(query), params or {}).scalar() or 0)


def _count_nonempty(session: Session, table_name: str, column_name: str | None) -> int:
    if not column_name:
        return 0
    return _count_rows(
        session,
        table_name,
        where_clause=f"{column_name} IS NOT NULL AND TRIM({column_name}) != ''",
    )


def _count_distinct_nonempty(session: Session, table_name: str, column_name: str | None) -> int | None:
    if not column_name:
        return None
    value = session.execute(
        text(
            f"""
            SELECT COUNT(DISTINCT {column_name})
            FROM {table_name}
            WHERE {column_name} IS NOT NULL AND TRIM({column_name}) != ''
            """
        )
    ).scalar()
    return int(value or 0)


def _count_equals(session: Session, table_name: str, column_name: str | None, expected: str) -> int | None:
    if not column_name:
        return None
    return _count_rows(
        session,
        table_name,
        where_clause=f"{column_name} = :expected",
        params={"expected": expected},
    )


def _max_timestamp(
    session: Session,
    table_name: str,
    column_name: str | None,
    *,
    where_clause: str | None = None,
    params: dict[str, object] | None = None,
) -> str | None:
    if not column_name:
        return None
    query = f"SELECT MAX({column_name}) FROM {table_name}"
    if where_clause:
        query = f"{query} WHERE {where_clause}"
    return _stringify_timestamp(session.execute(text(query), params or {}).scalar())


def _summarize_raw_table(
    session: Session,
    snapshot: _SchemaSnapshot,
    *,
    table_name: str,
    updated_candidates: tuple[str, ...],
) -> _RawTableSummary | None:
    if not snapshot.has_table(table_name):
        return None
    return _RawTableSummary(
        table_name=table_name,
        record_total=_count_rows(session, table_name),
        latest_updated_at=_max_timestamp(
            session,
            table_name,
            snapshot.pick_column(table_name, *updated_candidates),
        ),
    )


def _build_app_model_gap_notes(
    raw_session: Session,
    snapshot: _SchemaSnapshot,
    *,
    raw_table: str,
    raw_updated_candidates: tuple[str, ...],
    model_total: int,
    base_notes: list[str] | None = None,
) -> tuple[list[str], str]:
    notes = list(base_notes or [])
    raw_summary = _summarize_raw_table(
        raw_session,
        snapshot,
        table_name=raw_table,
        updated_candidates=raw_updated_candidates,
    )

    if model_total > 0:
        return notes, "ready"

    if raw_summary and raw_summary.record_total:
        notes.append(
            f"当前应用模型仍为 0 条，但独立 gaokao 只读表 {raw_summary.table_name} 已有 {raw_summary.record_total} 条原始记录；"
            "这说明空态来自应用侧尚未导入或映射，不代表高考主线库缺数据。"
        )
        return notes, "partial"

    if raw_summary:
        notes.append(
            f"当前应用模型仍为 0 条，且独立 gaokao 只读表 {raw_summary.table_name} 也暂无记录；"
            "请先确认是否已导入对应批次。"
        )
        return notes, "empty"

    notes.append(
        f"当前应用模型仍为 0 条，且本地 gaokao 只读库未暴露 {raw_table}；"
        "如需判断是未导入还是未 handoff，请先检查独立高考库。"
    )
    return notes, "waiting"


def _build_table_stat(
    *,
    key: str,
    label: str,
    record_total: int,
    covered_total: int | None = None,
    coverage_rate: float | None = None,
    latest_updated_at: str | None = None,
    latest_batch_label: str | None = None,
    status: str | None = None,
    notes: list[str] | None = None,
) -> GaokaoTableStatRead:
    derived_status = status or ("ready" if record_total else "empty")
    return GaokaoTableStatRead(
        key=key,
        label=label,
        record_total=record_total,
        covered_total=covered_total,
        coverage_rate=coverage_rate,
        latest_updated_at=latest_updated_at,
        latest_batch_label=latest_batch_label,
        status=derived_status,
        notes=notes or [],
    )


def _build_recent_batch_label(session: Session, doc_baseline: dict[str, object]) -> str:
    batch_name = _latest_enrollment_plan_batch(session)
    if batch_name:
        return batch_name
    return f"{doc_baseline['data_version']} / {doc_baseline['generated_at']}"


def _latest_enrollment_plan_batch(session: Session) -> str | None:
    return session.scalar(
        select(EnrollmentPlan.import_batch_name)
        .where(EnrollmentPlan.import_batch_name.is_not(None))
        .order_by(EnrollmentPlan.updated_at.desc(), EnrollmentPlan.id.desc())
        .limit(1)
    )


def _build_import_job_label(item: ImportJob) -> str:
    mapping = {
        "admission_import": "录取数据导入",
        "admissions": "录取数据导入",
        "enrollment_plan_import": "招生计划导入",
        "enrollment_plans": "招生计划导入",
        "gaokao_import": "高考数据导入",
    }
    return mapping.get(item.job_type, item.job_type.replace("_", " "))


def _build_raw_import_batch_note(row: dict[str, object]) -> str:
    province = _normalize_province_value(_clean_text(row.get("province"))) or "全量"
    target_year = row.get("target_year")
    version_label = _clean_text(row.get("version_label"))
    parts = [province]
    if target_year:
        parts.append(str(target_year))
    if version_label:
        parts.append(version_label)
    return " / ".join(parts)


def _normalize_import_batch_status(value: str | None) -> str:
    mapping = {
        "completed": "success",
        "running": "processing",
        "processing": "processing",
        "partially_failed": "partial",
        "partial_success": "partial",
        "failed": "failed",
        "rolled_back": "rolled_back",
    }
    return mapping.get(value or "", value or "success")


def _read_import_job_record_total(item: ImportJob) -> int | None:
    if not isinstance(item.result_json, dict):
        return None
    for key in ("imported", "record_total", "success_count"):
        value = item.result_json.get(key)
        if isinstance(value, int):
            return value
    return None


def _load_sync_board_baseline(project_root: Path) -> dict[str, object]:
    sync_board = project_root / SYNC_BOARD_PATH
    if not sync_board.exists():
        return dict(SYNC_BOARD_FALLBACK)

    content = sync_board.read_text(encoding="utf-8")
    result = dict(SYNC_BOARD_FALLBACK)

    generated_match = re.search(r"生成口径时间：`([^`]+)`", content)
    if generated_match:
        result["generated_at"] = generated_match.group(1).strip()

    for key in (
        "gaokao_college_total",
        "gaokao_college_with_recruit_site",
        "gaokao_college_with_chapter_url",
        "chapter_rule_fallback_url_filled",
        "duplicate_group_total",
        "same_name_cross_site_group_total",
    ):
        match = re.search(rf"{re.escape(key)} = (\d+)", content)
        if match:
            result[key] = int(match.group(1))
    return result


def _safe_rate(part: int | None, total: int | None) -> float | None:
    if not part or not total:
        return 0.0 if total else None
    return round((part / total) * 100, 2)


def _stringify_timestamp(value: object) -> str | None:
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat(sep=" ", timespec="seconds")
    text_value = str(value).strip()
    return text_value or None


def _clean_text(value: object) -> str | None:
    if value is None:
        return None
    text_value = str(value).strip()
    return text_value or None


def _normalize_province_value(value: str | None) -> str | None:
    if not value:
        return None
    normalized = value.strip()
    return PROVINCE_DISPLAY_NAMES.get(normalized.lower(), normalized)


def _build_province_alias_where_clause(column_name: str, province_name: str) -> tuple[str, dict[str, object]]:
    aliases = PROVINCE_FILTER_ALIASES.get(province_name, (province_name,))
    params = {f"province_alias_{index}": alias.lower() for index, alias in enumerate(aliases)}
    clause = " OR ".join(
        f"LOWER(TRIM({column_name})) = :province_alias_{index}"
        for index in range(len(aliases))
    )
    return f"({clause})", params


def _latest_chapter_rule_status(session: Session, snapshot: _SchemaSnapshot, college_id: int) -> str | None:
    if not snapshot.has_table("gaokao_college_chapter_rule"):
        return None
    value = session.execute(
        text(
            """
            SELECT review_status
            FROM gaokao_college_chapter_rule
            WHERE college_id = :college_id
            ORDER BY COALESCE(updated_at, created_at) DESC, id DESC
            LIMIT 1
            """
        ),
        {"college_id": college_id},
    ).scalar()
    return _clean_text(value)
