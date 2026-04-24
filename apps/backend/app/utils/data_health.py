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
DEFAULT_EXPECTED_YEARS = (2020, 2021, 2022, 2023, 2024, 2025)


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
            "tables": [],
            "coverage": [],
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
        schema_version = _read_schema_version(conn, schema)

    return {
        "db_path": str(db_path),
        "exists": True,
        "generated_at": _now_text(),
        "schema_version": schema_version,
        "province": province,
        "expected_years": list(expected_years),
        "tables": table_stats,
        "coverage": coverage,
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

    lines.append("")
    lines.append("山东覆盖摘要:")
    for item in report.get("coverage", []):
        years = ", ".join(str(year) for year in item.get("years", [])) or "无"
        type_parts = [
            f"{entry['key']}={entry['count']}"
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
                "notes": notes,
            }
        )
    return stats


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
                student_types.append({"key": str(row["key"]), "count": int(row["count"])})
        total = _count_with_where(conn, table, where, params)
        items.append(
            {
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
        )
    return items


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
            missing_years = list(coverage_item.get("missing_years") or [])
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
            missing_special = sorted(set(SPECIAL_STUDENT_TYPES).intersection(plan_types) - admission_types)
            if missing_special:
                status = "gap"
                notes.append(f"特殊类型缺专门录取结果，仅可做初筛：{', '.join(missing_special)}")
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

    admission_years = set(by_key.get("admission_record", {}).get("years", []))
    missing_admission_years = sorted(set(expected_years) - admission_years)
    if missing_admission_years:
        gaps.append(f"应用侧录取结果缺少年份：{_join_years(missing_admission_years)}")

    admission_types = _coverage_type_keys(by_key.get("admission_record"))
    plan_types = _coverage_type_keys(by_key.get("enrollment_plan"))
    missing_special_results = sorted(set(SPECIAL_STUDENT_TYPES).intersection(plan_types) - admission_types)
    if missing_special_results:
        gaps.append(f"特殊类型已有招生计划但缺专门录取结果：{', '.join(missing_special_results)}")

    enrollment_year_counts = _year_counts(conn, schema, "enrollment_plan")
    for year in (2024, 2025):
        count = enrollment_year_counts.get(year, 0)
        if count < 1000:
            gaps.append(f"山东招生计划 {year} 年数量偏少：{count} 条，需继续核验完整性")

    score_rank_years = set(by_key.get("score_rank_segment", {}).get("years", []))
    missing_rank_years = sorted(set(expected_years) - score_rank_years)
    if missing_rank_years:
        gaps.append(f"一分一段缺少年份：{_join_years(missing_rank_years)}")

    score_line_years = set(by_key.get("gaokao_score_line", {}).get("years", []))
    missing_line_years = sorted(set(expected_years) - score_line_years)
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
        {"key": str(row["key"]), "count": int(row["count"])}
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
            schema.pick_column(table, "subject_group", "line_type", "title"),
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
    return {str(entry["key"]) for entry in item.get("student_types", [])}


def _empty_coverage(table: str, label: str, status: str) -> dict[str, Any]:
    return {
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


def _format_monitor_status_for_audit(value: str) -> str:
    mapping = {
        "missing": "表不存在",
        "no_year_column": "缺少年份列，无法形成阶段一覆盖矩阵",
        "empty": "当前没有山东口径记录",
    }
    return mapping.get(value, value)


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
