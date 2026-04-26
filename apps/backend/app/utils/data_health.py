from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any


CORE_TABLES: tuple[tuple[str, str], ...] = (
    ("college", "应用侧院校"),
    ("major", "应用侧专业"),
    ("college_major", "院校专业关联"),
    ("enrollment_plan", "应用侧招生计划"),
    ("admission_record", "应用侧录取结果"),
    ("province_volunteer_rule", "省份志愿规则"),
    ("province_score_transform_rule", "赋分/成绩转换规则"),
    ("subject_requirement_dict", "选科要求字典"),
    ("special_type_rule", "特殊类型规则"),
    ("employment_direction", "职业方向"),
    ("major_employment_mapping", "专业就业映射"),
    ("score_rank_segment", "一分一段"),
    ("gaokao_admission_plan", "raw 招生计划"),
    ("gaokao_admission_result", "raw 录取结果"),
    ("gaokao_score_line", "raw 省控线/批次线"),
    ("gaokao_batch_dict", "raw 批次词典"),
    ("gaokao_policy_reference", "raw 政策参考"),
    ("gaokao_college_chapter_rule", "raw 招生章程限制链"),
)

SHANDONG_ALIASES = ("山东", "山东省", "sd", "shandong")
SPECIAL_STUDENT_TYPES = ("art", "sports", "spring_exam", "independent_recruitment", "comprehensive_evaluation")
STUDENT_TYPE_ORDER = (
    "general",
    "spring_exam",
    "art",
    "sports",
    "independent_recruitment",
    "comprehensive_evaluation",
)
PENDING_PUBLICATION_YEAR = 2026
DEFAULT_EXPECTED_YEARS = (2020, 2021, 2022, 2023, 2024, 2025, PENDING_PUBLICATION_YEAR)
STUDENT_TYPE_LABELS = {
    "general": "普通类",
    "spring_exam": "春季高考",
    "art": "艺术类",
    "sports": "体育类",
    "independent_recruitment": "单独招生",
    "comprehensive_evaluation": "综合评价招生",
    "summer_total": "夏季高考一分一段",
    "province_rule": "省级政策规则",
    "pending_manual_review": "待人工复核",
    "pending_manual_review_with_official_candidate": "待人工复核（已有官方候选）",
    "confirmed_manual_dispatch_check": "已人工核对（派发检查）",
    "confirmed_manual_review": "已人工核对",
    "partially_filled": "部分补齐",
    "confirmed_manual_live_check": "已人工核对（实时检查）",
    "confirmed_manual_web_search": "已人工核对（网页检索）",
    "普通类": "普通类",
    "春季高考": "春季高考",
    "艺术类": "艺术类",
    "体育类": "体育类",
    "单独招生": "单独招生",
    "综合评价招生": "综合评价招生",
}
RAW_STUDENT_TYPE_ALIASES = {
    "普通类": "general",
    "春季高考": "spring_exam",
    "艺术类": "art",
    "体育类": "sports",
    "单独招生": "independent_recruitment",
    "综合评价招生": "comprehensive_evaluation",
}


def build_data_health_report(
    db_path: Path,
    *,
    province: str = "山东",
    expected_years: tuple[int, ...] = DEFAULT_EXPECTED_YEARS,
) -> dict[str, Any]:
    db_path = db_path.resolve()
    if not db_path.exists():
        return {
            "db_path": str(db_path),
            "exists": False,
            "generated_at": _now_text(),
            "schema_version": None,
            "province": province,
            "expected_years": list(expected_years),
            "field_explanations": _field_explanations(),
            "delivery_assessment": _build_delivery_assessment(
                [f"数据库文件不存在：{db_path}"],
                [],
                [],
                [],
            ),
            "tables": [],
            "coverage": [],
            "publication_status": [],
            "special_type_risks": [],
            "audit_summary": [],
            "gaps": [f"数据库文件不存在：{db_path}"],
            "summary": "数据库文件不存在",
        }

    with sqlite3.connect(str(db_path)) as conn:
        conn.row_factory = sqlite3.Row
        schema = _Schema(conn)
        table_stats = _build_table_stats(conn, schema)
        coverage = _build_coverage(conn, schema, province=province, expected_years=expected_years)
        gaps = _build_gap_summary(conn, schema, coverage, expected_years=expected_years)
        audit_summary = _build_audit_summary(conn, schema, coverage, expected_years=expected_years)
        special_type_risks = _build_special_type_risks(conn, schema, province=province)
        publication_status = _build_2026_publication_status(conn, schema, province=province)
        schema_version = _read_schema_version(conn, schema)

    return {
        "db_path": str(db_path),
        "exists": True,
        "generated_at": _now_text(),
        "schema_version": schema_version,
        "province": province,
        "expected_years": list(expected_years),
        "field_explanations": _field_explanations(),
        "delivery_assessment": _build_delivery_assessment(
            gaps,
            table_stats,
            audit_summary,
            special_type_risks,
        ),
        "tables": table_stats,
        "coverage": coverage,
        "publication_status": publication_status,
        "special_type_risks": special_type_risks,
        "audit_summary": audit_summary,
        "gaps": gaps,
        "summary": _build_summary_line(table_stats, gaps),
    }


def format_data_health_report(report: dict[str, Any]) -> str:
    lines = [
        "数据健康检查",
        f"- db: {report['db_path']}",
        f"- generated_at: {report['generated_at']}",
        f"- schema_version: {report.get('schema_version') or 'unknown'}",
        f"- summary: {report.get('summary') or ''}",
        "",
        "核心表数量:",
    ]
    for item in report.get("tables", []):
        notes = f"；{'；'.join(item['notes'])}" if item.get("notes") else ""
        lines.append(f"- {item['label']} ({item['key']}): {item['count']} [{item['status']}]{notes}")

    delivery = report.get("delivery_assessment") or {}
    if delivery:
        lines.append("")
        lines.append("P0 交付判断:")
        lines.append(f"- {delivery.get('label') or delivery.get('status')}: {delivery.get('summary') or ''}")
        for item in delivery.get("blocking_items") or []:
            lines.append(f"- 阻断: {item}")
        for item in delivery.get("warning_items") or []:
            lines.append(f"- 警告: {item}")

    special_type_risks = report.get("special_type_risks") or []
    if special_type_risks:
        lines.append("")
        lines.append("考生类型可用性:")
        for item in special_type_risks:
            fallback_text = f"；fallback: {' / '.join(item.get('fallback_labels') or [])}" if item.get("fallback_labels") else ""
            lines.append(
                f"- {item['label']}: {item.get('readiness_label') or item.get('readiness')}；"
                f"计划 {item.get('plan_count', 0)}；录取 {item.get('admission_count', 0)}；"
                f"省控线 {item.get('score_line_count', 0)}；规则 {item.get('volunteer_rule_count', 0)}"
                f"/{item.get('special_rule_count', 0)}{fallback_text}"
            )
            for note in item.get("notes") or []:
                lines.append(f"  - {note}")

    publication_status = report.get("publication_status") or []
    if publication_status:
        lines.append("")
        lines.append("2026 数据发布状态:")
        for item in publication_status:
            lines.append(
                f"- {item['label']}: {item.get('status_label') or item.get('status')}；"
                f"记录 {item.get('record_count', 0)}；{item.get('action_label') or ''}"
            )
            for note in item.get("notes") or []:
                lines.append(f"  - {note}")

    lines.append("")
    lines.append("山东覆盖摘要:")
    for item in report.get("coverage", []):
        years = ", ".join(str(year) for year in item.get("years", [])) or "无"
        type_parts = [
            f"{entry.get('label') or entry['key']}={entry['count']}"
            for entry in item.get("student_types", [])
        ]
        type_text = "；".join(type_parts) if type_parts else "无分类"
        missing_years = ", ".join(str(year) for year in item.get("missing_years", [])) or "无"
        batch_parts = [
            f"{entry['key']}={entry['count']}"
            for entry in item.get("batch_distribution", [])
        ]
        batch_text = "；".join(batch_parts) if batch_parts else "无批次"
        lines.append(f"- {item['label']}: 年份 {years}；缺少年份 {missing_years}；{type_text}；批次 {batch_text}")

    audit_items = report.get("audit_summary") or []
    if audit_items:
        lines.append("")
        lines.append("导入审计摘要:")
        for item in audit_items:
            notes = f"；{'；'.join(item['notes'])}" if item.get("notes") else ""
            lines.append(
                f"- {item['label']} ({item['key']}): {item['status']}；"
                f"新增 {item.get('created', 0)}；更新 {item.get('updated', 0)}；"
                f"重复 {item.get('duplicates', 0)}；冲突 {item.get('conflicts', 0)}；"
                f"待复核 {item.get('pending_review', 0)}{notes}"
            )

    lines.append("")
    lines.append("缺口摘要:")
    gaps = report.get("gaps") or []
    if gaps:
        lines.extend(f"- {gap}" for gap in gaps)
    else:
        lines.append("- 未发现 P0 规则内的明显缺口。")
    return "\n".join(lines)


def report_as_json(report: dict[str, Any]) -> str:
    return json.dumps(report, ensure_ascii=False, indent=2)


def _field_explanations() -> list[dict[str, str]]:
    return [
        {
            "field": "tables",
            "label": "核心表数量",
            "explanation": "检查交付前必须存在的业务表、raw 高考表和规则表是否有记录。",
        },
        {
            "field": "coverage",
            "label": "山东覆盖矩阵",
            "explanation": "按数据域查看山东当前覆盖了哪些年份、考生类型和批次。",
        },
        {
            "field": "special_type_risks",
            "label": "考生类型可用性",
            "explanation": "把普通类、春考、艺术、体育、单招、综评分开判断，避免把初筛当成完整录取把握。",
        },
        {
            "field": "publication_status",
            "label": "2026 数据发布状态",
            "explanation": "把已公开、已导入、待官方发布和需人工复核的数据分开，避免把未公开的 2026 普通类计划当成完整数据。",
        },
        {
            "field": "audit_summary",
            "label": "导入审计摘要",
            "explanation": "用于补数据前后对照当前记录数、疑似重复、冲突和待人工复核数量。",
        },
        {
            "field": "delivery_assessment",
            "label": "P0 交付判断",
            "explanation": "把健康检查结果分成通过、警告和阻断，方便非程序员判断下一步。",
        },
    ]


def _build_table_stats(conn: sqlite3.Connection, schema: "_Schema") -> list[dict[str, Any]]:
    stats = []
    for table, label in CORE_TABLES:
        exists = schema.has_table(table)
        count = _count_rows(conn, table) if exists else 0
        notes: list[str] = []
        status = "ok" if count > 0 else "empty"
        if not exists:
            status = "missing"
            notes.append("表不存在")
        elif table == "gaokao_policy_reference" and count < 10:
            status = "gap"
            notes.append("政策参考数量偏少，交付版不足以支撑完整边界说明")
        elif table == "gaokao_college_chapter_rule":
            pending = _count_review_pending(conn, schema, table)
            if pending:
                status = "gap"
                notes.append(f"待人工复核 {pending} 条")
        stats.append(
            {
                "key": table,
                "label": label,
                "count": count,
                "status": status,
                "explanation": _table_explanation(table),
                "notes": notes,
            }
        )
    return stats


def _build_2026_publication_status(
    conn: sqlite3.Connection,
    schema: "_Schema",
    *,
    province: str,
) -> list[dict[str, Any]]:
    target_year = 2026
    general_plan_count = _count_year_type_records(
        conn,
        schema,
        "enrollment_plan",
        target_year,
        province=province,
        type_column="student_type",
        normalized_type="general",
    ) + _count_year_type_records(
        conn,
        schema,
        "gaokao_admission_plan",
        target_year,
        province=province,
        type_column="candidate_type",
        normalized_type="general",
    )
    general_admission_count = _count_year_type_records(
        conn,
        schema,
        "admission_record",
        target_year,
        province=province,
        type_column="student_type",
        normalized_type="general",
    ) + _count_year_type_records(
        conn,
        schema,
        "gaokao_admission_result",
        target_year,
        province=province,
        type_column="candidate_type",
        normalized_type="general",
    )
    rank_segment_count = _count_year_records(conn, schema, "score_rank_segment", target_year, province=province)
    score_line_count = _count_year_records(conn, schema, "gaokao_score_line", target_year, province=province)
    subject_requirement_count = _count_year_records(
        conn,
        schema,
        "subject_requirement_dict",
        target_year,
        province=province,
    )
    policy_reference_count = _count_year_records(conn, schema, "gaokao_policy_reference", target_year, province=province)

    subject_docs = _source_documents(conn, schema, year=target_year, source_type="subject_requirement", province=province)
    policy_docs = _source_documents(conn, schema, year=target_year, source_type="policy", province=province)
    plan_limit_docs = _source_documents(
        conn,
        schema,
        year=target_year,
        source_type="single_comprehensive_plan_limit",
        province=province,
    )

    items = [
        _publication_item(
            key="general_admission_plan",
            label="普通类正式招生计划",
            category="普通类夏季高考",
            status="imported" if general_plan_count else "pending_official_release",
            record_count=general_plan_count,
            source_documents=[],
            action_label="待山东省教育招生考试院发布后再导入" if not general_plan_count else "已看到 2026 普通类计划记录，仍需核验完整性",
            explanation="2026 夏季高考普通类正式招生计划是推荐前必须单独确认的数据，不能用单招/综评计划代替。",
            notes=[
                "当前推荐可先使用 2023-2025 历史投档数据和 2025/2026 适用选科要求。",
                "正式填报前必须以山东省教育招生考试院最终发布的普通类招生计划为准。",
            ],
            blocks_recommendation=False,
        ),
        _publication_item(
            key="general_admission_result",
            label="普通类投档/录取结果",
            category="普通类夏季高考",
            status="imported" if general_admission_count else "not_applicable",
            record_count=general_admission_count,
            source_documents=[],
            action_label="录取投档完成后才会产生，当前不能要求导入",
            explanation="2026 投档结果发生在录取阶段之后，填报前不可用；推荐只能参考历史年份。",
            notes=["不得伪造 2026 投档分、最低位次或录取结果。"],
            blocks_recommendation=False,
        ),
        _publication_item(
            key="score_rank_segment",
            label="一分一段表",
            category="成绩换算",
            status="imported" if rank_segment_count else "pending_official_release",
            record_count=rank_segment_count,
            source_documents=[],
            action_label="待 2026 成绩公布后导入；未发布前用最近一年时必须明示估算",
            explanation="一分一段用于把预估分数换算为全省位次；未发布时只能按上一年临时估算。",
            notes=["如果用 2025 一分一段换算 2026 预估位次，必须显示“按上一年一分一段估算”。"],
            blocks_recommendation=False,
        ),
        _publication_item(
            key="score_line",
            label="各类别分数线 / 省控线",
            category="资格线",
            status="imported" if score_line_count else "pending_official_release",
            record_count=score_line_count,
            source_documents=[],
            action_label="待 2026 分数线发布后导入；未发布前仅能参考历史资格线",
            explanation="省控线用于判断一段线、二段线和特殊类型资格线，不能替代专业录取位次。",
            notes=["艺术、体育等特殊类型在缺专门录取结果时也只能做资格线初筛。"],
            blocks_recommendation=False,
        ),
        _publication_item(
            key="subject_requirement",
            label="2025/2026 适用选科要求",
            category="选科要求",
            status="imported" if subject_requirement_count else _status_from_source_documents(subject_docs, fallback="published"),
            record_count=subject_requirement_count,
            source_documents=subject_docs,
            action_label="推荐时必须校验选科；未满足选科要求的专业不能进入冲稳保",
            explanation="山东 2025/2026 推荐需要使用适用版选科要求，作为专业候选的硬约束。",
            notes=["如果只登记了来源但未完成结构化导入，推荐结果必须提示选科仍需人工核对。"],
            blocks_recommendation=subject_requirement_count == 0,
        ),
        _publication_item(
            key="single_comprehensive_policy",
            label="单招 / 综评政策通知",
            category="2026 已公开政策",
            status="imported" if policy_reference_count else _status_from_source_documents(policy_docs, fallback="published"),
            record_count=policy_reference_count,
            source_documents=policy_docs,
            action_label="已作为政策来源登记；只能解释单招/综评边界",
            explanation="该政策通知可用于登记 2026 单招/综评时间、组织方式和计划原则。",
            notes=["该来源不能当作 2026 夏季高考普通类正式招生计划。"],
            blocks_recommendation=False,
        ),
        _publication_item(
            key="single_comprehensive_plan_limit",
            label="单招 / 综评院校计划限额",
            category="2026 已公开计划边界",
            status=_status_from_source_documents(plan_limit_docs, fallback="manual_review_required"),
            record_count=0,
            source_documents=plan_limit_docs,
            action_label="官方附件需人工下载、登记并核验后再解析",
            explanation="计划限额可作为单招/综评数据入口，但不能扩展成普通类夏季高考计划。",
            notes=["若自动抓取受阻，使用 backend:gaokao-import-official 登记放在 data/imports/gaokao/manual/ 或 official/ 下的官方附件。"],
            blocks_recommendation=False,
        ),
        _publication_item(
            key="college_chapters",
            label="高校单招 / 综评章程和分专业计划",
            category="高校官网材料",
            status="manual_review_required",
            record_count=0,
            source_documents=[],
            action_label="按高校官网逐校人工核验或下载后导入",
            explanation="高校章程、分专业计划和特殊要求分散在各校官网，当前不做不稳定批量抓取。",
            notes=["未核验前只能作为待审阅材料，不能给出完整录取把握。"],
            blocks_recommendation=False,
        ),
    ]
    return items


def _publication_item(
    *,
    key: str,
    label: str,
    category: str,
    status: str,
    record_count: int,
    source_documents: list[dict[str, Any]],
    action_label: str,
    explanation: str,
    notes: list[str],
    blocks_recommendation: bool,
) -> dict[str, Any]:
    return {
        "key": key,
        "label": label,
        "category": category,
        "target_year": 2026,
        "status": status,
        "status_label": _publication_status_label(status),
        "record_count": record_count,
        "source_documents": source_documents,
        "action_label": action_label,
        "explanation": explanation,
        "notes": _dedupe_text(notes),
        "blocks_recommendation": blocks_recommendation,
    }


def _publication_status_label(value: str) -> str:
    mapping = {
        "published": "已公开，待结构化导入",
        "imported": "已导入",
        "pending_official_release": "待官方发布",
        "not_applicable": "当前阶段不适用",
        "manual_review_required": "需人工核验",
    }
    return mapping.get(value, value)


def _status_from_source_documents(docs: list[dict[str, Any]], *, fallback: str) -> str:
    if not docs:
        return fallback
    statuses = {str(item.get("status") or "") for item in docs}
    if "imported" in statuses or "success" in statuses:
        return "imported"
    if "file_ready" in statuses:
        return "manual_review_required"
    return "published"


def _count_year_records(
    conn: sqlite3.Connection,
    schema: "_Schema",
    table: str,
    year: int,
    *,
    province: str,
) -> int:
    if not schema.has_table(table):
        return 0
    year_column = schema.pick_column(table, "year", "gaokao_year", "target_year")
    if not year_column:
        return 0
    province_column = schema.pick_column(table, "province", "student_province")
    where, params = _province_where(schema, table, province_column, province)
    where, params = _append_where_condition(where, params, f'"{year_column}" = ?', year)
    return _count_with_where(conn, table, where, params)


def _count_year_type_records(
    conn: sqlite3.Connection,
    schema: "_Schema",
    table: str,
    year: int,
    *,
    province: str,
    type_column: str,
    normalized_type: str,
) -> int:
    if not schema.has_table(table):
        return 0
    year_column = schema.pick_column(table, "year", "gaokao_year", "target_year")
    if not year_column:
        return 0
    province_column = schema.pick_column(table, "province", "student_province")
    where, params = _province_where(schema, table, province_column, province)
    where, params = _append_where_condition(where, params, f'"{year_column}" = ?', year)
    if type_column in schema.columns(table):
        aliases = _student_type_aliases(normalized_type)
        placeholders = ", ".join(["?"] * len(aliases))
        where, params = _append_where_condition(
            where,
            params,
            f'lower(COALESCE("{type_column}", "")) IN ({placeholders})',
            None,
        )
        params = (*params[:-1], *(alias.lower() for alias in aliases))
    return _count_with_where(conn, table, where, params)


def _source_documents(
    conn: sqlite3.Connection,
    schema: "_Schema",
    *,
    year: int,
    source_type: str,
    province: str,
) -> list[dict[str, Any]]:
    table = "gaokao_source_document"
    if not schema.has_table(table):
        return []
    province_column = schema.pick_column(table, "province")
    where, params = _province_where(schema, table, province_column, province)
    where, params = _append_where_condition(where, params, '"year" = ?', year)
    where, params = _append_where_condition(where, params, '"source_type" = ?', source_type)
    rows = conn.execute(
        f'''
        SELECT id, title, url, official_org, published_at, local_file_path, file_sha256, status, note
        FROM "{table}"
        {where}
        ORDER BY id
        ''',
        params,
    ).fetchall()
    return [
        {
            "id": int(row["id"]),
            "title": str(row["title"] or ""),
            "url": row["url"],
            "official_org": row["official_org"],
            "published_at": row["published_at"],
            "local_file_path": row["local_file_path"],
            "file_sha256": row["file_sha256"],
            "status": row["status"],
            "note": row["note"],
        }
        for row in rows
    ]


def _student_type_aliases(value: str) -> tuple[str, ...]:
    mapping = {
        "general": ("general", "普通类"),
        "spring_exam": ("spring_exam", "春季高考"),
        "art": ("art", "艺术类"),
        "sports": ("sports", "体育类"),
        "independent_recruitment": ("independent_recruitment", "单独招生"),
        "comprehensive_evaluation": ("comprehensive_evaluation", "综合评价招生"),
    }
    return mapping.get(value, (value,))


def _build_coverage(
    conn: sqlite3.Connection,
    schema: "_Schema",
    *,
    province: str,
    expected_years: tuple[int, ...],
) -> list[dict[str, Any]]:
    configs = (
        ("enrollment_plan", "应用侧招生计划", "student_type", ("batch", "batch_name", "batch_type", "admission_batch")),
        ("admission_record", "应用侧录取结果", "student_type", ("batch", "batch_name", "batch_type", "admission_batch")),
        ("score_rank_segment", "一分一段", "score_type", ("batch", "batch_name", "category", "segment_type")),
        ("gaokao_admission_plan", "raw 招生计划", "candidate_type", ("batch", "batch_name", "batch_type", "admission_batch")),
        ("gaokao_admission_result", "raw 录取结果", "candidate_type", ("batch", "batch_name", "batch_type", "admission_batch")),
        ("gaokao_score_line", "raw 省控线/批次线", "candidate_type", ("batch", "batch_name", "line_type", "batch_type")),
        ("gaokao_policy_reference", "raw 政策参考", "policy_type", ("policy_type", "batch", "batch_name")),
        ("gaokao_college_chapter_rule", "raw 招生章程限制链", "review_status", ("review_status", "rule_type", "batch")),
    )
    items = []
    for table, label, type_column, batch_columns in configs:
        if not schema.has_table(table):
            items.append(_empty_coverage(table, label, "missing"))
            continue
        year_column = schema.pick_column(table, "year", "gaokao_year", "target_year")
        province_column = schema.pick_column(table, "province", "student_province")
        if not year_column:
            items.append(_empty_coverage(table, label, "no_year_column"))
            continue
        where, params = _province_where(schema, table, province_column, province)
        years = [
            int(row[0])
            for row in conn.execute(
                f'SELECT DISTINCT "{year_column}" FROM "{table}" {where} ORDER BY "{year_column}"',
                params,
            ).fetchall()
            if row[0] is not None
        ]
        student_types = []
        if type_column in schema.columns(table):
            for row in conn.execute(
                f'''
                SELECT COALESCE("{type_column}", '未分类') AS key, COUNT(*) AS count
                FROM "{table}"
                {where}
                GROUP BY COALESCE("{type_column}", '未分类')
                ORDER BY count DESC, key
                ''',
                params,
            ).fetchall():
                key = str(row["key"])
                student_types.append({"key": key, "label": _label_for_key(key), "count": int(row["count"])})
        total = _count_with_where(conn, table, where, params)
        item = {
            "key": table,
            "label": label,
            "status": "ok" if total else "empty",
            "total": total,
            "years": years,
            "missing_years": sorted(set(expected_years) - set(years)),
            "student_types": student_types,
            "batch_distribution": _distribution(
                conn,
                schema,
                table,
                schema.pick_column(table, *batch_columns),
                where,
                params,
            ),
            "year_breakdown": _year_breakdown(
                conn,
                schema,
                table,
                year_column,
                type_column if type_column in schema.columns(table) else None,
                schema.pick_column(table, *batch_columns),
                where,
                params,
            ),
        }
        items.append(_enrich_coverage_item(item))
    return items


def _enrich_coverage_item(item: dict[str, Any]) -> dict[str, Any]:
    key = str(item["key"])
    missing_years = list(item.get("missing_years") or [])
    actionable_missing_years = _actionable_missing_years(missing_years)
    total = int(item.get("total") or 0)
    notes: list[str] = []
    readiness = "ready"
    risk_level = "normal"
    if item.get("status") == "missing":
        readiness = "missing"
        risk_level = "blocking"
        notes.append("表不存在，不能参与当前数据判断。")
    elif item.get("status") == "no_year_column":
        readiness = "unknown"
        risk_level = "warning"
        notes.append("缺少年份列，无法判断哪些年份可用。")
    elif total == 0:
        readiness = "empty"
        risk_level = "warning"
        notes.append("当前没有山东口径记录。")
    elif actionable_missing_years:
        readiness = "partial"
        risk_level = "warning"
        notes.append(f"缺少年份：{_join_years(actionable_missing_years)}。")
    elif PENDING_PUBLICATION_YEAR in missing_years:
        notes.append(f"{PENDING_PUBLICATION_YEAR} 年数据待官方发布，未发布前不作为历史补齐缺口。")

    type_keys = _coverage_type_keys(item)
    if key == "admission_record" and type_keys and type_keys <= {"general"}:
        readiness = "partial"
        risk_level = "warning"
        notes.append("当前录取结果主要支撑普通类；特殊类型不能按完整录取线理解。")
    elif key == "gaokao_admission_result" and type_keys and type_keys <= {"general"}:
        readiness = "partial"
        risk_level = "warning"
        notes.append("raw 录取结果当前主要是普通类口径。")
    elif key == "gaokao_score_line" and total:
        notes.append("省控线可用于艺术/体育资格线初筛，但不能替代院校或专业录取结果。")
    elif key == "enrollment_plan" and set(SPECIAL_STUDENT_TYPES).intersection(type_keys):
        notes.append("招生计划说明可报方向和容量，不等同于录取把握。")
    elif key == "gaokao_college_chapter_rule" and total:
        notes.append("章程限制链仍需结合待复核状态判断可信度。")
    elif key == "gaokao_policy_reference" and total < 10:
        readiness = "partial"
        risk_level = "warning"
        notes.append("政策参考数量偏少，交付前还需要补官方政策和填报规则。")

    item["readiness"] = readiness
    item["readiness_label"] = _readiness_label(readiness)
    item["risk_level"] = risk_level
    item["explanation"] = _coverage_explanation(key)
    item["notes"] = notes
    return item


def _build_audit_summary(
    conn: sqlite3.Connection,
    schema: "_Schema",
    coverage: list[dict[str, Any]],
    *,
    expected_years: tuple[int, ...],
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    coverage_by_key = {item["key"]: item for item in coverage}
    labels = {table: label for table, label in CORE_TABLES}

    for key in (
        "enrollment_plan",
        "admission_record",
        "score_rank_segment",
        "gaokao_score_line",
        "gaokao_policy_reference",
        "gaokao_college_chapter_rule",
    ):
        coverage_item = coverage_by_key.get(key)
        label = labels.get(key, coverage_item.get("label", key) if coverage_item else key)
        status = "missing"
        notes: list[str] = []
        total = 0
        conflicts = 0
        pending_review = 0
        duplicates = 0

        if coverage_item:
            total = int(coverage_item.get("total") or 0)
            missing_years = _actionable_missing_years(list(coverage_item.get("missing_years") or []))
            if coverage_item.get("status") in {"missing", "no_year_column"}:
                status = str(coverage_item.get("status"))
                notes.append(_format_monitor_status_for_audit(status))
            elif total == 0:
                status = "empty"
                notes.append("当前没有山东口径记录")
            elif missing_years:
                status = "gap"
                notes.append(f"缺少年份：{_join_years(missing_years)}")
            else:
                status = "ok"

        if key == "enrollment_plan":
            year_counts = _year_counts(conn, schema, key)
            low_years = [f"{year}={year_counts.get(year, 0)}" for year in (2024, 2025) if year_counts.get(year, 0) < 1000]
            if low_years:
                status = "gap"
                notes.append(f"近年招生计划数量偏少：{'；'.join(low_years)}")
        elif key == "admission_record":
            plan_types = _coverage_type_keys(coverage_by_key.get("enrollment_plan"))
            admission_types = _coverage_type_keys(coverage_item)
            missing_special = _sort_student_types(set(SPECIAL_STUDENT_TYPES).intersection(plan_types) - admission_types)
            if missing_special:
                status = "gap"
                notes.append(f"特殊类型缺专门录取结果，仅可做初筛：{_format_student_type_list(missing_special)}")
        elif key == "gaokao_policy_reference" and total < 10:
            status = "gap"
            notes.append(f"政策参考数量偏少：{total}")
        elif key == "gaokao_college_chapter_rule" and schema.has_table(key):
            pending_review = _count_review_pending(conn, schema, key)
            if pending_review:
                status = "gap"
                notes.append(f"待人工复核 {pending_review} 条")
        if schema.has_table(key):
            duplicates = _estimate_duplicates(conn, schema, key)
            conflicts = _estimate_conflicts(conn, schema, key)
            if duplicates:
                notes.append(f"疑似重复 {duplicates} 组")
            if conflicts:
                status = "gap"
                notes.append(f"疑似冲突 {conflicts} 组")

        items.append(
            {
                "key": key,
                "label": label,
                "status": status,
                "created": 0,
                "updated": total,
                "duplicates": duplicates,
                "conflicts": conflicts,
                "pending_review": pending_review,
                "notes": notes,
            }
        )
    return items


def _build_gap_summary(
    conn: sqlite3.Connection,
    schema: "_Schema",
    coverage: list[dict[str, Any]],
    *,
    expected_years: tuple[int, ...],
) -> list[str]:
    gaps: list[str] = []
    by_key = {item["key"]: item for item in coverage}
    completed_years = tuple(year for year in expected_years if year < PENDING_PUBLICATION_YEAR)

    admission_years = set(by_key.get("admission_record", {}).get("years", []))
    missing_admission_years = sorted(set(completed_years) - admission_years)
    if missing_admission_years:
        gaps.append(f"应用侧录取结果缺少年份：{_join_years(missing_admission_years)}")

    admission_types = _coverage_type_keys(by_key.get("admission_record"))
    plan_types = _coverage_type_keys(by_key.get("enrollment_plan"))
    missing_special_results = _sort_student_types(set(SPECIAL_STUDENT_TYPES).intersection(plan_types) - admission_types)
    if missing_special_results:
        gaps.append(f"特殊类型已有招生计划但缺专门录取结果：{_format_student_type_list(missing_special_results)}")

    enrollment_year_counts = _year_counts(conn, schema, "enrollment_plan")
    for year in (2024, 2025):
        count = enrollment_year_counts.get(year, 0)
        if count < 1000:
            gaps.append(f"山东招生计划 {year} 年数量偏少：{count} 条，需继续核验完整性")

    score_rank_years = set(by_key.get("score_rank_segment", {}).get("years", []))
    missing_rank_years = sorted(set(completed_years) - score_rank_years)
    if missing_rank_years:
        gaps.append(f"一分一段缺少年份：{_join_years(missing_rank_years)}")

    score_line_years = set(by_key.get("gaokao_score_line", {}).get("years", []))
    missing_line_years = sorted(set(completed_years) - score_line_years)
    if missing_line_years:
        gaps.append(f"省控线/批次线缺少年份：{_join_years(missing_line_years)}")

    policy_total = _count_rows(conn, "gaokao_policy_reference") if schema.has_table("gaokao_policy_reference") else 0
    if policy_total < 10:
        gaps.append(f"政策参考数量偏少：{policy_total} 条，交付前需补山东官方政策和填报规则")

    if schema.has_table("gaokao_college_chapter_rule"):
        pending = _count_review_pending(conn, schema, "gaokao_college_chapter_rule")
        if pending:
            gaps.append(f"招生章程限制链仍有 {pending} 条待人工复核")

    return gaps


def _actionable_missing_years(years: list[int]) -> list[int]:
    return sorted(year for year in years if year < PENDING_PUBLICATION_YEAR)


def _build_special_type_risks(
    conn: sqlite3.Connection,
    schema: "_Schema",
    *,
    province: str,
) -> list[dict[str, Any]]:
    plan_counts = _normalized_type_counts(conn, schema, "enrollment_plan", "student_type", province=province)
    raw_plan_counts = _normalized_type_counts(conn, schema, "gaokao_admission_plan", "candidate_type", province=province)
    admission_counts = _normalized_type_counts(conn, schema, "admission_record", "student_type", province=province)
    raw_admission_counts = _normalized_type_counts(conn, schema, "gaokao_admission_result", "candidate_type", province=province)
    score_line_counts = _normalized_type_counts(conn, schema, "gaokao_score_line", "candidate_type", province=province)
    volunteer_rule_counts = _normalized_type_counts(conn, schema, "province_volunteer_rule", "candidate_type", province=province)
    special_rule_counts = _normalized_type_counts(conn, schema, "special_type_rule", "student_type", province=province)

    items: list[dict[str, Any]] = []
    for student_type in STUDENT_TYPE_ORDER:
        plan_count = plan_counts.get(student_type, 0)
        raw_plan_count = raw_plan_counts.get(student_type, 0)
        admission_count = admission_counts.get(student_type, 0)
        raw_admission_count = raw_admission_counts.get(student_type, 0)
        score_line_count = score_line_counts.get(student_type, 0)
        volunteer_rule_count = volunteer_rule_counts.get(student_type, 0)
        special_rule_count = special_rule_counts.get(student_type, 0)
        effective_plan_count = plan_count or raw_plan_count
        effective_admission_count = admission_count or raw_admission_count
        fallback_modes: list[str] = []
        notes: list[str] = []

        if student_type == "general":
            if effective_admission_count:
                readiness = "ready"
                risk_level = "normal"
                explanation = "普通类已有 2020-2025 录取结果，可作为当前推荐主链路的主要参考。"
                if plan_count and plan_count < 1000:
                    notes.append("招生计划仍需继续核验年度完整性。")
            else:
                readiness = "missing"
                risk_level = "blocking"
                explanation = "普通类缺少录取结果，不能支撑主推荐链路。"
        elif effective_plan_count == 0:
            readiness = "missing"
            risk_level = "blocking"
            explanation = "当前没有看到该类型招生计划，不能做候选池或初筛。"
        elif effective_admission_count:
            readiness = "partial"
            risk_level = "warning"
            explanation = "已有少量专门录取结果，但仍需按年份、批次和来源继续核验完整性。"
        elif student_type in {"art", "sports"} and score_line_count:
            readiness = "screening_only"
            risk_level = "warning"
            fallback_modes.append("score_line_reference")
            explanation = "当前有招生计划和省控线，可做资格线初筛；缺少专门录取结果，不能判断院校录取把握。"
        elif student_type in {"art", "sports"}:
            readiness = "screening_only"
            risk_level = "warning"
            fallback_modes.append("plan_only_reference")
            explanation = "当前有招生计划但缺少专门录取结果和完整省控线；只能做方向性初筛，必须人工复核资格线。"
        else:
            readiness = "screening_only"
            risk_level = "warning"
            fallback_modes.extend(["plan_only_reference", "general_reference_fallback"])
            explanation = "当前有招生计划和规则字典，但缺少专门录取结果；只能做方向性初筛，部分场景会参考普通类结果并显式标风险。"

        if student_type != "general" and not effective_admission_count:
            notes.append("缺少该类型专门录取结果，页面、打印和导出都必须显示初筛或 fallback 风险。")
        if not volunteer_rule_count:
            risk_level = "warning" if risk_level == "normal" else risk_level
            notes.append("缺少省份志愿规则，规则上限和批次解释需要人工复核。")
        if student_type != "general" and not special_rule_count:
            risk_level = "warning" if risk_level == "normal" else risk_level
            notes.append("缺少特殊类型细分类别规则，无法给出细分核对清单。")
        if student_type in {"art", "sports"} and not score_line_count:
            notes.append("缺少该类型省控线，资格线初筛也不完整。")

        items.append(
            {
                "key": student_type,
                "label": STUDENT_TYPE_LABELS[student_type],
                "readiness": readiness,
                "readiness_label": _readiness_label(readiness),
                "risk_level": risk_level,
                "plan_count": plan_count,
                "raw_plan_count": raw_plan_count,
                "admission_count": admission_count,
                "raw_admission_count": raw_admission_count,
                "score_line_count": score_line_count,
                "volunteer_rule_count": volunteer_rule_count,
                "special_rule_count": special_rule_count,
                "fallback_modes": fallback_modes,
                "fallback_labels": [_fallback_label(mode) for mode in fallback_modes],
                "explanation": explanation,
                "notes": notes,
            }
        )
    return items


def _normalized_type_counts(
    conn: sqlite3.Connection,
    schema: "_Schema",
    table: str,
    type_column: str,
    *,
    province: str,
) -> dict[str, int]:
    if not schema.has_table(table) or type_column not in schema.columns(table):
        return {}
    province_column = schema.pick_column(table, "province", "student_province")
    where, params = _province_where(schema, table, province_column, province)
    rows = conn.execute(
        f'''
        SELECT COALESCE("{type_column}", '未分类') AS key, COUNT(*) AS count
        FROM "{table}"
        {where}
        GROUP BY COALESCE("{type_column}", '未分类')
        ''',
        params,
    ).fetchall()
    counts: dict[str, int] = {}
    for row in rows:
        normalized = _normalize_student_type(str(row["key"]))
        counts[normalized] = counts.get(normalized, 0) + int(row["count"])
    return counts


def _build_delivery_assessment(
    gaps: list[str],
    table_stats: list[dict[str, Any]],
    audit_summary: list[dict[str, Any]],
    special_type_risks: list[dict[str, Any]],
) -> dict[str, Any]:
    blocking_items: list[str] = []
    warning_items: list[str] = []
    pass_items: list[str] = []

    missing_tables = [item["label"] for item in table_stats if item.get("status") == "missing"]
    empty_tables = [item["label"] for item in table_stats if item.get("status") == "empty"]
    if missing_tables:
        blocking_items.append(f"核心表缺失：{'、'.join(missing_tables)}")
    if empty_tables:
        blocking_items.append(f"核心表为空：{'、'.join(empty_tables)}")
    for item in audit_summary:
        if int(item.get("conflicts") or 0) > 0:
            blocking_items.append(f"{item['label']} 仍有 {item['conflicts']} 条疑似冲突")

    for gap in gaps:
        warning_items.append(gap)
    for item in special_type_risks:
        if item.get("readiness") == "screening_only":
            warning_items.append(f"{item['label']} 当前只能初筛，不能当作完整录取把握")
        elif item.get("readiness") == "missing":
            blocking_items.append(f"{item['label']} 缺少招生计划或关键规则，暂不能使用")

    if not blocking_items:
        pass_items.append("主库可读取，核心表未缺失，P0 备份恢复检查可继续执行。")
    if not gaps:
        pass_items.append("当前 P0 规则内未发现数据缺口。")

    if blocking_items:
        status = "blocked"
        label = "阻断交付"
        summary = "存在核心表缺失、空表或冲突，先不要交付给日常使用。"
    elif warning_items:
        status = "warning"
        label = "可验收但有数据警告"
        summary = "P0 安全底座可继续验收，但数据可用性仍需补齐和人工复核。"
    else:
        status = "pass"
        label = "P0 可通过"
        summary = "当前健康检查未发现阻断项或 P0 数据缺口。"

    return {
        "status": status,
        "label": label,
        "summary": summary,
        "pass_items": _dedupe_text(pass_items),
        "warning_items": _dedupe_text(warning_items),
        "blocking_items": _dedupe_text(blocking_items),
    }


def _year_counts(conn: sqlite3.Connection, schema: "_Schema", table: str) -> dict[int, int]:
    if not schema.has_table(table) or "year" not in schema.columns(table):
        return {}
    province_column = schema.pick_column(table, "province", "student_province")
    where, params = _province_where(schema, table, province_column, "山东")
    return {
        int(row["year"]): int(row["count"])
        for row in conn.execute(
            f'SELECT "year" AS year, COUNT(*) AS count FROM "{table}" {where} GROUP BY "year"',
            params,
        ).fetchall()
        if row["year"] is not None
    }


def _distribution(
    conn: sqlite3.Connection,
    schema: "_Schema",
    table: str,
    column: str | None,
    where: str,
    params: tuple[object, ...],
    *,
    limit: int = 12,
) -> list[dict[str, Any]]:
    if not column or column not in schema.columns(table):
        return []
    return [
        {"key": str(row["key"]), "label": _label_for_key(str(row["key"])), "count": int(row["count"])}
        for row in conn.execute(
            f'''
            SELECT COALESCE("{column}", '未分类') AS key, COUNT(*) AS count
            FROM "{table}"
            {where}
            GROUP BY COALESCE("{column}", '未分类')
            ORDER BY count DESC, key
            LIMIT ?
            ''',
            (*params, limit),
        ).fetchall()
    ]


def _year_breakdown(
    conn: sqlite3.Connection,
    schema: "_Schema",
    table: str,
    year_column: str,
    type_column: str | None,
    batch_column: str | None,
    where: str,
    params: tuple[object, ...],
) -> list[dict[str, Any]]:
    totals = conn.execute(
        f'''
        SELECT "{year_column}" AS year, COUNT(*) AS count
        FROM "{table}"
        {where}
        GROUP BY "{year_column}"
        ORDER BY "{year_column}"
        ''',
        params,
    ).fetchall()
    items: list[dict[str, Any]] = []
    for row in totals:
        if row["year"] is None:
            continue
        year = int(row["year"])
        year_where, year_params = _append_where_condition(where, params, f'"{year_column}" = ?', year)
        items.append(
            {
                "year": year,
                "total": int(row["count"]),
                "student_types": _distribution(conn, schema, table, type_column, year_where, year_params, limit=8),
                "batches": _distribution(conn, schema, table, batch_column, year_where, year_params, limit=8),
                "status": "ok" if int(row["count"]) else "empty",
            }
        )
    return items


def _append_where_condition(
    where: str,
    params: tuple[object, ...],
    condition: str,
    value: object,
) -> tuple[str, tuple[object, ...]]:
    if where:
        return f"{where} AND {condition}", (*params, value)
    return f"WHERE {condition}", (value,)


def _estimate_duplicates(conn: sqlite3.Connection, schema: "_Schema", table: str) -> int:
    columns = _unique_columns(
        [
            schema.pick_column(table, "year", "gaokao_year", "target_year"),
            schema.pick_column(table, "college_id", "college_code", "school_code", "college_name"),
            schema.pick_column(table, "major_id", "major_code", "major_name", "spname"),
            schema.pick_column(table, "student_type", "candidate_type", "score_type", "policy_type", "review_status"),
            schema.pick_column(table, "art_track", "subject_group", "line_type", "title"),
            schema.pick_column(table, "batch", "batch_name", "batch_type", "admission_batch"),
            schema.pick_column(table, "score", "min_score", "control_score"),
            schema.pick_column(table, "url", "source_url", "local_path"),
        ]
    )
    if len(columns) < 2:
        return 0
    province_column = schema.pick_column(table, "province", "student_province")
    where, params = _province_where(schema, table, province_column, "山东")
    group_by = ", ".join(f'COALESCE("{column}", "")' for column in columns)
    row = conn.execute(
        f'''
        SELECT COUNT(*) AS duplicate_groups
        FROM (
            SELECT 1
            FROM "{table}"
            {where}
            GROUP BY {group_by}
            HAVING COUNT(*) > 1
        ) AS duplicate_groups
        ''',
        params,
    ).fetchone()
    return int(row["duplicate_groups"] or 0)


def _unique_columns(columns: list[str | None]) -> list[str]:
    unique: list[str] = []
    for column in columns:
        if column and column not in unique:
            unique.append(column)
    return unique


def _estimate_conflicts(conn: sqlite3.Connection, schema: "_Schema", table: str) -> int:
    status_column = schema.pick_column(table, "review_status", "conflict_status", "status")
    if not status_column:
        return 0
    province_column = schema.pick_column(table, "province", "student_province")
    where, params = _province_where(schema, table, province_column, "山东")
    status_condition = f'''
        lower(COALESCE("{status_column}", "")) IN (
            'conflict',
            'conflicted',
            'unresolved',
            'pending_conflict_review'
        )
    '''
    full_where, full_params = _append_where_condition(where, params, status_condition, None)
    if full_params and full_params[-1] is None:
        full_params = full_params[:-1]
    row = conn.execute(
        f'SELECT COUNT(*) AS count FROM "{table}" {full_where}',
        full_params,
    ).fetchone()
    return int(row["count"] or 0)


def _count_rows(conn: sqlite3.Connection, table: str) -> int:
    return int(conn.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0])


def _count_with_where(conn: sqlite3.Connection, table: str, where: str, params: tuple[object, ...]) -> int:
    return int(conn.execute(f'SELECT COUNT(*) FROM "{table}" {where}', params).fetchone()[0])


def _count_review_pending(conn: sqlite3.Connection, schema: "_Schema", table: str) -> int:
    column = schema.pick_column(table, "review_status")
    if not column:
        return 0
    rows = conn.execute(
        f'''
        SELECT COUNT(*)
        FROM "{table}"
        WHERE COALESCE("{column}", '') IN (
            'pending_manual_review',
            'pending_manual_review_with_official_candidate',
            'unresolved',
            'partially_filled'
        )
        '''
    ).fetchone()
    return int(rows[0] or 0)


def _province_where(
    schema: "_Schema",
    table: str,
    province_column: str | None,
    province: str,
) -> tuple[str, tuple[object, ...]]:
    if not province_column or province_column not in schema.columns(table):
        return "", ()
    aliases = SHANDONG_ALIASES if province == "山东" else (province,)
    placeholders = ", ".join(["?"] * len(aliases))
    return f'WHERE lower(COALESCE("{province_column}", "")) IN ({placeholders})', tuple(alias.lower() for alias in aliases)


def _coverage_type_keys(item: dict[str, Any] | None) -> set[str]:
    if not item:
        return set()
    return {_normalize_student_type(str(entry["key"])) for entry in item.get("student_types", [])}


def _empty_coverage(table: str, label: str, status: str) -> dict[str, Any]:
    item = {
        "key": table,
        "label": label,
        "status": status,
        "total": 0,
        "years": [],
        "missing_years": list(DEFAULT_EXPECTED_YEARS),
        "student_types": [],
        "batch_distribution": [],
        "year_breakdown": [],
    }
    return _enrich_coverage_item(item)


def _format_monitor_status_for_audit(value: str) -> str:
    mapping = {
        "missing": "表不存在",
        "no_year_column": "缺少年份列，无法形成阶段一覆盖矩阵",
        "empty": "当前没有山东口径记录",
    }
    return mapping.get(value, value)


def _readiness_label(value: str) -> str:
    mapping = {
        "ready": "可作为主链路参考",
        "partial": "部分可用，需看缺口",
        "screening_only": "只能初筛",
        "missing": "暂不可用",
        "empty": "暂无数据",
        "unknown": "口径待确认",
    }
    return mapping.get(value, value)


def _fallback_label(value: str) -> str:
    mapping = {
        "score_line_reference": "省控线资格参考",
        "plan_only_reference": "计划清单初筛",
        "general_reference_fallback": "普通类录取结果参考",
    }
    return mapping.get(value, value)


def _label_for_key(value: str) -> str:
    return STUDENT_TYPE_LABELS.get(value, value)


def _format_student_type_list(values: list[str]) -> str:
    return "、".join(STUDENT_TYPE_LABELS.get(value, value) for value in values)


def _sort_student_types(values: set[str]) -> list[str]:
    order = {value: index for index, value in enumerate(STUDENT_TYPE_ORDER)}
    return sorted(values, key=lambda value: (order.get(value, len(order)), value))


def _normalize_student_type(value: str) -> str:
    cleaned = value.strip()
    if cleaned in RAW_STUDENT_TYPE_ALIASES:
        return RAW_STUDENT_TYPE_ALIASES[cleaned]
    lowered = cleaned.lower()
    return RAW_STUDENT_TYPE_ALIASES.get(lowered, lowered)


def _table_explanation(table: str) -> str:
    mapping = {
        "college": "应用侧院校主档，供页面、推荐和导出使用。",
        "major": "应用侧专业主档，供专业匹配和推荐结果使用。",
        "college_major": "院校与专业的关联表，决定候选能否落到专业层。",
        "enrollment_plan": "应用侧招生计划，表示某年某类考生有哪些可报方向和计划容量。",
        "admission_record": "应用侧录取结果，是普通类推荐主链路最重要的录取参考。",
        "province_volunteer_rule": "省份志愿规则，用于解释批次、志愿数量、志愿单位和调剂规则。",
        "province_score_transform_rule": "赋分/成绩转换规则，用于解释高考模式和赋分口径。",
        "subject_requirement_dict": "选科要求字典，用于把原始选科描述转成可筛选条件。",
        "special_type_rule": "特殊类型规则字典，用于春考、艺体、单招、综评的初筛类别和核对清单。",
        "employment_direction": "职业方向库，用于职业偏好和专业方向解释。",
        "major_employment_mapping": "专业就业映射，用于职业匹配排序和解释。",
        "score_rank_segment": "一分一段，用于把分数转换为位次或进行跨年参考。",
        "gaokao_admission_plan": "raw 招生计划，保留原始高考数据事实。",
        "gaokao_admission_result": "raw 录取结果，保留原始录取事实。",
        "gaokao_score_line": "raw 省控线/批次线，可用于资格线参考。",
        "gaokao_batch_dict": "raw 批次词典，用于解释批次口径。",
        "gaokao_policy_reference": "raw 政策参考，用于填报政策和边界说明。",
        "gaokao_college_chapter_rule": "raw 招生章程限制链，用于语言、体检、校区、单科等人工复核。",
    }
    return mapping.get(table, "项目数据表。")


def _coverage_explanation(key: str) -> str:
    mapping = {
        "enrollment_plan": "判断山东哪些年份、考生类型和批次有招生计划；计划存在不等于录取把握。",
        "admission_record": "判断山东哪些年份和类型有录取结果；推荐的录取把握必须优先看这里。",
        "score_rank_segment": "判断山东一分一段覆盖哪些年份；缺少年份会影响分数到位次映射。",
        "gaokao_admission_plan": "raw 招生计划原始事实，用于和应用侧招生计划互相核对。",
        "gaokao_admission_result": "raw 录取结果原始事实，用于和应用侧录取记录互相核对。",
        "gaokao_score_line": "省控线/批次线覆盖情况，艺术和体育当前主要靠它做资格线初筛。",
        "gaokao_policy_reference": "政策参考覆盖情况，决定填报规则和边界说明是否足够。",
        "gaokao_college_chapter_rule": "招生章程限制链覆盖情况，决定语言、体检、单科等风险是否可复核。",
    }
    return mapping.get(key, "按年份、类别和批次统计当前山东数据覆盖。")


def _dedupe_text(items: list[str]) -> list[str]:
    result: list[str] = []
    for item in items:
        if item and item not in result:
            result.append(item)
    return result


def _read_schema_version(conn: sqlite3.Connection, schema: "_Schema") -> str | None:
    if not schema.has_table("alembic_version"):
        return None
    row = conn.execute("SELECT version_num FROM alembic_version LIMIT 1").fetchone()
    return str(row[0]) if row and row[0] else None


def _build_summary_line(table_stats: list[dict[str, Any]], gaps: list[str]) -> str:
    missing = sum(1 for item in table_stats if item["status"] == "missing")
    empty = sum(1 for item in table_stats if item["status"] == "empty")
    gap = sum(1 for item in table_stats if item["status"] == "gap")
    return f"核心表缺失 {missing} 个，空表 {empty} 个，需关注表 {gap} 个，P0 缺口 {len(gaps)} 条"


def _join_years(years: list[int]) -> str:
    return ", ".join(str(year) for year in years)


def _now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class _Schema:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn
        self._tables: set[str] | None = None
        self._columns: dict[str, set[str]] = {}

    def has_table(self, table: str) -> bool:
        return table in self.tables

    def columns(self, table: str) -> set[str]:
        if table not in self._columns:
            if not self.has_table(table):
                self._columns[table] = set()
            else:
                self._columns[table] = {row["name"] for row in self._conn.execute(f'PRAGMA table_info("{table}")').fetchall()}
        return self._columns[table]

    def pick_column(self, table: str, *candidates: str) -> str | None:
        columns = self.columns(table)
        for candidate in candidates:
            if candidate in columns:
                return candidate
        return None

    @property
    def tables(self) -> set[str]:
        if self._tables is None:
            self._tables = {
                row["name"]
                for row in self._conn.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                ).fetchall()
            }
        return self._tables
