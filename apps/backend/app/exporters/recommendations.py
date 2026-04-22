from __future__ import annotations

from datetime import datetime

from openpyxl import Workbook

from app.core.config import Settings
from app.utils.parsers import make_timestamped_filename, relative_to_project


def export_recommendation_summary(settings: Settings, meta: dict[str, object], rows: list[dict[str, object]]) -> str:
    workbook = Workbook()
    summary = workbook.active
    summary.title = "推荐概况"
    summary.append(["推荐方案", meta.get("scheme_name")])
    summary.append(["学生", meta.get("student_name")])
    summary.append(["考试", meta.get("exam_name")])
    summary.append(["省份", meta.get("province")])
    summary.append(["目标年份", meta.get("target_year")])
    summary.append(["分数模式", meta.get("score_input_label")])
    summary.append(["模拟说明", meta.get("simulation_note")])
    summary.append(["目标方向", meta.get("target_direction_summary") or "未维护"])
    summary.append(["可接受路径", meta.get("accepted_path_summary") or "未维护"])
    summary.append(["结果数量", len(rows)])

    risk_rows = _build_recommendation_risk_rows(meta, rows)

    risk_overview = workbook.create_sheet("风险概览")
    risk_overview.append(["分组", "类型", "摘要", "说明"])
    for item in risk_rows:
        risk_overview.append([
            _build_recommendation_risk_group_label(item["title"]),
            item["title"],
            item["summary"],
            item["detail"],
        ])

    overview_sheet = workbook.create_sheet("导出前摘要")
    overview_sheet.append(["分组", "标题", "摘要", "说明"])
    for item in risk_rows:
        overview_sheet.append([
            _build_recommendation_risk_group_label(item["title"]),
            item["title"],
            item["summary"],
            item["detail"],
        ])

    detail = workbook.create_sheet("推荐结果")
    detail.append(
        [
            "分组",
            "院校",
            "专业",
            "参考位次",
            "学生位次",
            "比值",
            "依据",
            "职业匹配",
            "对应目标方向",
            "路径提示",
            "职业说明",
            "理由",
            "风险提示",
        ]
    )
    for row in rows:
        detail.append(
            [
                row.get("result_type"),
                row.get("college_name"),
                row.get("major_name"),
                row.get("reference_rank"),
                row.get("student_rank"),
                row.get("ratio"),
                row.get("score_basis"),
                row.get("career_match_strength"),
                " / ".join(row.get("matched_direction_names_json") or []),
                _build_path_hint(row),
                row.get("career_match_summary"),
                row.get("reason_text"),
                ",".join(row.get("risk_flags_json") or []),
            ]
        )

    filename = make_timestamped_filename("recommendation_summary_report", ".xlsx")
    path = settings.exports_dir / filename
    workbook.save(path)
    return relative_to_project(path, settings.project_root)


def export_volunteer_draft_summary(settings: Settings, meta: dict[str, object], rows: list[dict[str, object]]) -> str:
    workbook = Workbook()
    summary = workbook.active
    summary.title = "志愿草稿概况"
    summary.append(["草稿名称", meta.get("draft_name")])
    summary.append(["学生", meta.get("student_name")])
    summary.append(["考试", meta.get("exam_name")])
    summary.append(["省份", meta.get("province")])
    summary.append(["目标年份", meta.get("target_year")])
    summary.append(["批次", meta.get("batch")])
    summary.append(["科类/模式", meta.get("exam_mode")])
    summary.append(["分数模式", meta.get("score_input_label")])
    summary.append(["模拟说明", meta.get("simulation_note")])
    summary.append(["目标方向", meta.get("target_direction_summary") or "未维护"])
    summary.append(["可接受路径", meta.get("accepted_path_summary") or "未维护"])
    summary.append(["规则", meta.get("rule_label")])
    summary.append(["志愿数量", len(rows)])
    summary.append(["备注", meta.get("note")])

    boundary = workbook.create_sheet("边界概览")
    boundary.append(["类型", "摘要", "说明"])
    for item in _build_volunteer_draft_boundary_rows(rows, meta.get("rule_alerts") or []):
        boundary.append([item["title"], item["summary"], item["detail"]])

    rule_sheet = workbook.create_sheet("规则差异摘要")
    rule_sheet.append(["规则", "定位", "总分口径", "志愿上限", "志愿单位", "平行方式", "选科口径", "每单位专业数", "征集志愿", "调剂", "说明"])
    for item in _build_volunteer_draft_rule_rows(meta):
        rule_sheet.append(
            [
                item["title"],
                item["position"],
                item["total_score"],
                item["volunteer_limit"],
                item["volunteer_unit_type"],
                item["parallel_rule_mode"],
                item["subject_requirement_mode"],
                item["max_major_per_unit"],
                item["support_collect_round"],
                item["allow_adjustment"],
                item["notes"],
            ]
        )

    overview_sheet = workbook.create_sheet("导出前摘要")
    overview_sheet.append(["分组", "标题", "摘要", "说明"])
    for item in _build_volunteer_draft_overview_rows(meta, rows):
        overview_sheet.append([
            item["group"],
            item["title"],
            item["summary"],
            item["detail"],
        ])

    detail = workbook.create_sheet("志愿草稿")
    detail.append(
        [
            "顺序",
            "分层",
            "院校",
            "院校代码",
            "专业",
            "专业代码",
            "专业组",
            "计划数",
            "批次",
            "科类/模式",
            "参考位次",
            "最近最低位次",
            "最近最低分",
            "依据",
            "命中规则",
            "录取口径",
            "边界说明",
            "职业匹配",
            "对应目标方向",
            "路径提示",
            "职业说明",
            "理由",
            "风险提示",
        ]
    )
    for row in rows:
        detail.append(
            [
                row.get("order"),
                row.get("result_type"),
                row.get("college_name"),
                row.get("college_code_snapshot"),
                row.get("major_name"),
                row.get("major_code_snapshot"),
                row.get("major_group_code"),
                row.get("plan_count"),
                row.get("batch"),
                row.get("exam_mode"),
                row.get("reference_rank"),
                row.get("latest_min_rank"),
                row.get("latest_min_score"),
                row.get("score_basis"),
                _build_candidate_rule_copy(row),
                _build_candidate_reference_copy(row),
                "；".join(_build_candidate_boundary_notes(row, meta.get("rule_alerts") or [])),
                row.get("career_match_strength"),
                " / ".join(row.get("matched_direction_names_json") or []),
                _build_path_hint(row),
                row.get("career_match_summary"),
                row.get("reason_text"),
                ",".join(row.get("risk_flags_json") or []),
            ]
        )

    filename = make_timestamped_filename("volunteer_draft_summary_report", ".xlsx")
    path = settings.exports_dir / filename
    workbook.save(path)
    return relative_to_project(path, settings.project_root)


def _build_path_hint(row: dict[str, object]) -> str:
    hints: list[str] = []
    if row.get("requires_postgraduate_path") is True:
        hints.append("读研")
    if row.get("requires_certificate_path") is True:
        hints.append("资格证")
    if row.get("requires_long_training_path") is True:
        hints.append("长培养周期")
    return " / ".join(hints)


def _build_candidate_rule_copy(row: dict[str, object]) -> str | None:
    if not _has_matched_rule(row):
        return None
    parts = [
        row.get("province"),
        str(row.get("year")) if row.get("year") is not None else None,
        row.get("matched_rule_exam_mode"),
        row.get("matched_rule_batch"),
    ]
    suffix = (
        "系统基线"
        if row.get("matched_rule_is_baseline")
        else "专用规则"
        if row.get("matched_rule_candidate_type")
        else "通用规则"
    )
    return f"命中规则：{' / '.join(str(item) for item in parts if item)} · {suffix}"


def _build_candidate_reference_copy(row: dict[str, object]) -> str | None:
    if not row.get("reference_scope") and not row.get("reference_record_count"):
        return None
    scope_label = "院校线参考" if row.get("reference_scope") == "college" else "专业线参考"
    reference_years = row.get("reference_years_json") or []
    year_label = f"{' / '.join(str(item) for item in reference_years)} 年" if reference_years else "年份待补"
    sample_label = f"{row.get('reference_record_count') or 0} 条样本"
    source_notes = row.get("reference_source_notes_json") or []
    source_label = f"来源：{'；'.join(str(item) for item in source_notes if item)}" if source_notes else None
    return " · ".join(str(item) for item in [scope_label, year_label, sample_label, source_label] if item)


def _build_candidate_boundary_notes(row: dict[str, object], rule_alerts: list[dict[str, object]] | list[object]) -> list[str]:
    notes: list[str] = []
    match_tags = {str(item) for item in row.get("match_tags_json") or [] if item}
    risk_flags = {str(item) for item in row.get("risk_flags_json") or [] if item}

    if not _has_matched_rule(row):
        missing_alert = _pick_rule_alert(rule_alerts, [
            "missing_rule_province",
            "missing_rule_year",
            "missing_rule_batch",
            "missing_rule_candidate_type",
            "missing_rule_exam_mode",
        ])
        notes.append(
            str(missing_alert.get("detail"))
            if missing_alert and missing_alert.get("detail")
            else "当前保存草稿时未命中明确省份规则，可能缺少省份、年份、批次或模式规则；填报前建议回到工作台核对规则差异摘要。"
        )
    elif row.get("matched_rule_is_baseline"):
        notes.append("当前只命中系统基线，志愿上限、单位结构和征集志愿仍需按当年公告复核。")
    elif row.get("matched_rule_candidate_type"):
        notes.append(f"当前命中{row.get('matched_rule_candidate_type')}专用规则，同省同年其他类别可能适用不同志愿结构。")
    elif row.get("matched_rule_exam_mode") or row.get("matched_rule_batch"):
        fallback_alert = _pick_rule_alert(rule_alerts, ["fallback_general_candidate_rule"])
        notes.append(
            str(fallback_alert.get("detail"))
            if fallback_alert and fallback_alert.get("detail")
            else "当前按通用规则解释，后续若补齐更细类别规则，候选顺序和说明可能变化。"
        )

    if "兼容模式命中" in match_tags:
        notes.append(f"当前请求模式与计划模式不完全一致，系统按“{row.get('exam_mode')}”兼容口径预览。")

    if row.get("reference_scope") == "college" and row.get("major_id") is not None:
        notes.append("当前专业缺少专业线，先回退到院校线参考；同校不同专业结果仍可能变化。")

    if (row.get("reference_record_count") or 0) > 0 and row.get("province"):
        reference_years = row.get("reference_years_json") or []
        year_label = f"{' / '.join(str(item) for item in reference_years)} 年" if reference_years else "现有年份"
        notes.append(f"录取参考只取 {row.get('province')} {year_label} 样本，同校跨省结果不同属于正常口径差异。")

    stale_reference_gap = _get_reference_year_gap(row.get("year"), row.get("reference_years_json") or [])
    if stale_reference_gap is not None and stale_reference_gap >= 2:
        latest_reference_year = max(int(item) for item in row.get("reference_years_json") or [] if isinstance(item, int))
        notes.append(
            f"当前录取参考最近只到 {latest_reference_year} 年，与 {row.get('year')} 目标年相差 {stale_reference_gap} 年；若近一年数据尚未补齐，排序和解释会偏保守。"
        )

    subject_requirement = row.get("subject_requirement")
    if ("待核对选科" in match_tags or "subject_requirement_check" in risk_flags) and subject_requirement:
        notes.append(f"该计划要求“{subject_requirement}”，最终填报前仍需核对选科限制。")

    deduped: list[str] = []
    for item in notes:
        if item not in deduped:
            deduped.append(item)
    return deduped


def _build_volunteer_draft_boundary_rows(
    rows: list[dict[str, object]],
    rule_alerts: list[dict[str, object]] | list[object],
) -> list[dict[str, str]]:
    results: list[dict[str, str]] = []

    baseline_count = sum(1 for row in rows if row.get("matched_rule_is_baseline"))
    if baseline_count:
        results.append(
            {
                "key": "baseline",
                "title": "系统基线口径",
                "summary": f"{baseline_count} 条已选志愿仍按系统基线解释",
                "detail": "打印或定稿前，建议继续核对当年省份公告中的志愿上限、单位结构和征集志愿要求。",
            }
        )

    compatible_count = sum(
        1 for row in rows if "兼容模式命中" in {str(item) for item in row.get("match_tags_json") or [] if item}
    )
    if compatible_count:
        results.append(
            {
                "key": "compatible_mode",
                "title": "兼容模式预览",
                "summary": f"{compatible_count} 条已选志愿按兼容模式预览命中",
                "detail": "这类结果适合做方向性参考，正式填报前仍需核对该省该年的精确模式规则。",
            }
        )

    specific_rule_summary = _build_volunteer_specific_rule_summary(rows)
    if specific_rule_summary:
        results.append(
            {
                "key": "candidate_specific_rule",
                "title": "类别专用规则口径",
                "summary": f"{specific_rule_summary['count']} 条已选志愿当前按{specific_rule_summary['label_text']}专用规则解释",
                "detail": f"当前命中的省份规则已细分到{specific_rule_summary['label_text']}；同省同年其他类别可能适用不同的志愿上限、单位结构和选科口径。",
            }
        )

    missing_rule_count = sum(1 for row in rows if not _has_matched_rule(row))
    missing_rule_alert_summaries = {
        "missing_rule_province": "当前省份规则尚未入库",
        "missing_rule_year": "当前缺少目标年份规则支撑",
        "missing_rule_batch": "当前缺少目标批次规则支撑",
        "missing_rule_candidate_type": "当前缺少类别专用规则支撑",
        "missing_rule_exam_mode": "当前缺少目标模式规则支撑",
    }
    appended_missing_rule = False
    if missing_rule_count:
        for code in [
            "missing_rule_province",
            "missing_rule_year",
            "missing_rule_batch",
            "missing_rule_candidate_type",
            "missing_rule_exam_mode",
        ]:
            alert = _pick_rule_alert(rule_alerts, [code])
            if not alert:
                continue
            appended_missing_rule = True
            results.append(
                {
                    "key": code,
                    "title": str(alert.get("title") or "缺少明确规则"),
                    "summary": f"{missing_rule_count} 条已选志愿{missing_rule_alert_summaries[code]}",
                    "detail": str(alert.get("detail") or ""),
                }
            )
        if not appended_missing_rule:
            results.append(
                {
                    "key": "missing_rule",
                    "title": "缺少明确规则",
                    "summary": f"{missing_rule_count} 条已选志愿当前缺少明确省份规则支撑",
                    "detail": "这些志愿在保存时未命中明确的省份规则，可能缺少省份、年份、批次或模式规则；打印或导出前建议回到工作台核对规则差异摘要。",
                }
            )

    general_rule_count = sum(
        1
        for row in rows
        if _has_matched_rule(row) and not row.get("matched_rule_is_baseline") and not row.get("matched_rule_candidate_type")
    )
    if general_rule_count:
        fallback_alert = _pick_rule_alert(rule_alerts, ["fallback_general_candidate_rule"])
        results.append(
            {
                "key": "general_candidate_rule",
                "title": str(fallback_alert.get("title") if fallback_alert else "通用类别规则口径"),
                "summary": f"{general_rule_count} 条已选志愿当前按通用考生规则解释",
                "detail": str(
                    fallback_alert.get("detail")
                    if fallback_alert
                    else "这通常表示该省该年尚未配置更细的类别专用规则；若后续补齐普通类、艺术类等专用规则，候选解释和排序可能变化。"
                ),
            }
        )

    province_scope_summary = _build_volunteer_province_scope_summary(rows)
    if province_scope_summary:
        scope_text = " / ".join(province_scope_summary["scope_text"])
        results.append(
            {
                "key": "cross_province",
                "title": "跨省口径差异",
                "summary": f"{province_scope_summary['count']} 个省份口径混合",
                "detail": f"这些志愿当前涉及 {scope_text} 等多个口径，跨省比较时，录取位次、最低分和冲稳保分组变化属于正常现象。",
            }
        )

    college_fallback_count = sum(
        1 for row in rows if row.get("reference_scope") == "college" and row.get("major_id") is not None
    )
    if college_fallback_count:
        results.append(
            {
                "key": "college_fallback",
                "title": "院校线回退",
                "summary": f"{college_fallback_count} 条已选志愿缺少专业线，只能先按院校线参考",
                "detail": "同校不同专业的真实录取难度仍可能继续分化，最终定稿前应结合专业线或章程再核对一次。",
            }
        )

    subject_check_count = sum(
        1
        for row in rows
        if (
            "待核对选科" in {str(item) for item in row.get("match_tags_json") or [] if item}
            or "subject_requirement_check" in {str(item) for item in row.get("risk_flags_json") or [] if item}
        )
    )
    if subject_check_count:
        results.append(
            {
                "key": "subject_check",
                "title": "选科待核对",
                "summary": f"{subject_check_count} 条已选志愿仍需逐条核对选科限制",
                "detail": "导出稿可用于讨论和汇报，但最终填报前仍应回到招生章程确认专业或专业组要求。",
            }
        )

    reference_year_mix_summary = _build_volunteer_reference_year_mix_summary(rows)
    if reference_year_mix_summary:
        scope_text = " / ".join(reference_year_mix_summary["scope_text"])
        if len(reference_year_mix_summary["scope_text"]) == 1:
            detail = f"这些志愿当前都按 {scope_text} 口径，但最近录取样本并非同一年；同省跨年份比较时，录取位次、最低分和冲稳保分组变化属于正常现象。"
        else:
            detail = f"这些志愿当前涉及 {scope_text} 等多个口径，最近录取样本也并非同一年；跨省或跨年份比较时，录取位次、最低分和冲稳保分组变化属于正常现象。"
        results.append(
            {
                "key": "mixed_reference_years",
                "title": "跨年份参考样本",
                "summary": f"{reference_year_mix_summary['count']} 条已选志愿最近录取样本分布在 {reference_year_mix_summary['year_text']}",
                "detail": detail,
            }
        )

    stale_reference_count = sum(
        1 for row in rows if _has_stale_reference_years(row.get("year"), row.get("reference_years_json") or [])
    )
    if stale_reference_count:
        results.append(
            {
                "key": "stale_reference_years",
                "title": "参考年份偏旧",
                "summary": f"{stale_reference_count} 条已选志愿最近录取样本与目标年份相差 2 年及以上",
                "detail": "这类志愿当前更适合作为方向性参考；若后续补齐近一年录取数据，排序、边界说明和最终取舍都可能变化。",
            }
        )

    if not results:
        results.append(
            {
                "key": "stable",
                "title": "当前草稿边界较清晰",
                "summary": f"{len(rows)} 条已选志愿主要按精确规则和现有专业线解释",
                "detail": "当前草稿已主要落在精确规则和现有专业线范围内，未发现明显的系统基线回退、兼容模式回退或大面积专业线缺失，可继续做排序和汇报材料整理。",
            }
        )

    return results


def _build_volunteer_draft_rule_rows(meta: dict[str, object]) -> list[dict[str, str]]:
    rules = [item for item in meta.get("applicable_rules") or [] if isinstance(item, dict)]
    if not rules:
        return []

    selected_rule = meta.get("selected_rule") if isinstance(meta.get("selected_rule"), dict) else None
    selected_rule_id = selected_rule.get("id") if selected_rule else None
    has_multiple_rules = len(rules) > 1
    rows: list[dict[str, str]] = []

    for rule in rules:
        is_selected = selected_rule_id is not None and rule.get("id") == selected_rule_id
        notes: list[str] = []
        subject_segments: list[str] = []
        if rule.get("required_subjects_json"):
            subject_segments.append(f"必选 {' / '.join(str(item) for item in rule['required_subjects_json'])}")
        if rule.get("first_choice_subjects_json"):
            subject_segments.append(f"首选 {' / '.join(str(item) for item in rule['first_choice_subjects_json'])}")
        if rule.get("reselect_subjects_json"):
            subject_segments.append(f"再选 {' / '.join(str(item) for item in rule['reselect_subjects_json'])}")
        if subject_segments:
            notes.append(f"选科细则：{'；'.join(subject_segments)}")
        if rule.get("score_rule_summary"):
            notes.append(f"赋分摘要：{rule['score_rule_summary']}")
        special_rules = rule.get("special_rules_json") or []
        if special_rules:
            notes.append(f"附加要求：{'；'.join(str(item) for item in special_rules)}")
        if rule.get("note"):
            notes.append(f"备注：{rule['note']}")

        position = "当前控制规则"
        if has_multiple_rules and not is_selected:
            position = "兼容预览规则"

        rows.append(
            {
                "title": f"{rule.get('province')} {rule.get('year')} {rule.get('exam_mode')} · {rule.get('batch')}",
                "position": position,
                "total_score": f"{rule.get('total_score')} 分",
                "volunteer_limit": f"{rule.get('volunteer_limit')} 个",
                "volunteer_unit_type": str(rule.get("volunteer_unit_type") or ""),
                "parallel_rule_mode": _format_parallel_rule_mode(rule.get("parallel_rule_mode"), rule.get("is_parallel")),
                "subject_requirement_mode": _format_subject_requirement_mode(rule.get("subject_requirement_mode")),
                "max_major_per_unit": f"{rule.get('max_major_per_unit')} 个" if rule.get("max_major_per_unit") else "未设",
                "support_collect_round": "支持" if rule.get("support_collect_round") else "未设",
                "allow_adjustment": "允许" if rule.get("allow_adjustment") else "不允许",
                "notes": "；".join(notes) or ("当前草稿按这条规则解释。" if is_selected else "这条规则用于解释兼容命中差异。"),
            }
        )
    return rows


def _build_volunteer_draft_overview_rows(
    meta: dict[str, object],
    rows: list[dict[str, object]],
) -> list[dict[str, str]]:
    overview_rows: list[dict[str, str]] = []
    for item in _build_volunteer_draft_rule_rows(meta):
        overview_rows.append(
            {
                "group": "规则差异摘要",
                "title": item["title"],
                "summary": item["position"],
                "detail": item["notes"],
            }
        )
    for item in _build_volunteer_draft_boundary_rows(rows, meta.get("rule_alerts") or []):
        overview_rows.append(
            {
                "group": _build_volunteer_draft_overview_group_label(item.get("key")),
                "title": item["title"],
                "summary": item["summary"],
                "detail": item["detail"],
            }
        )
    return overview_rows


def _build_volunteer_draft_overview_group_label(key: object) -> str:
    if key in {
        "baseline",
        "compatible_mode",
        "candidate_specific_rule",
        "missing_rule",
        "missing_rule_province",
        "missing_rule_year",
        "missing_rule_batch",
        "missing_rule_candidate_type",
        "missing_rule_exam_mode",
        "general_candidate_rule",
    }:
        return "规则差异摘要"
    if key in {
        "college_fallback",
        "mixed_reference_years",
        "stale_reference_years",
        "cross_province",
        "stable",
    }:
        return "边界概览"
    return "风险概览"


def _build_volunteer_specific_rule_summary(rows: list[dict[str, object]]) -> dict[str, object] | None:
    labels: list[str] = []
    for row in rows:
        if not _has_matched_rule(row) or row.get("matched_rule_is_baseline"):
            continue
        label = _format_candidate_type_label(row.get("matched_rule_candidate_type"))
        if label and label not in labels:
            labels.append(label)
    if not labels:
        return None
    count = sum(
        1
        for row in rows
        if _has_matched_rule(row)
        and not row.get("matched_rule_is_baseline")
        and bool(_format_candidate_type_label(row.get("matched_rule_candidate_type")))
    )
    return {
        "count": count,
        "label_text": " / ".join(labels),
    }


def _build_volunteer_reference_year_mix_summary(rows: list[dict[str, object]]) -> dict[str, object] | None:
    latest_years = [
        latest_year
        for row in rows
        for latest_year in [_get_latest_reference_year(row.get("reference_years_json") or [])]
        if latest_year is not None
    ]
    unique_years = sorted(set(latest_years), reverse=True)
    if len(unique_years) <= 1:
        return None
    scope_text = []
    for row in rows:
        province = str(row.get("province") or "").strip()
        if province and province not in scope_text:
            scope_text.append(province)
    return {
        "count": len(latest_years),
        "year_text": f"{' / '.join(str(year) for year in unique_years)} 年",
        "scope_text": scope_text or ["当前省份"],
    }


def _build_volunteer_province_scope_summary(rows: list[dict[str, object]]) -> dict[str, object] | None:
    provinces: list[str] = []
    for row in rows:
        province = str(row.get("province") or "").strip()
        if province and province not in provinces:
            provinces.append(province)
    if len(provinces) <= 1:
        return None
    return {
        "count": len(provinces),
        "scope_text": provinces,
    }


def _has_matched_rule(row: dict[str, object]) -> bool:
    return bool(
        row.get("matched_rule_is_baseline")
        or row.get("matched_rule_exam_mode")
        or row.get("matched_rule_batch")
        or row.get("matched_rule_candidate_type")
    )


def _has_stale_reference_years(target_year: object, reference_years: list[object]) -> bool:
    gap = _get_reference_year_gap(target_year, reference_years)
    return gap is not None and gap >= 2


def _get_reference_year_gap(target_year: object, reference_years: list[object]) -> int | None:
    if not isinstance(target_year, int):
        return None
    latest_year = _get_latest_reference_year(reference_years)
    if latest_year is None:
        return None
    return target_year - latest_year


def _get_latest_reference_year(reference_years: list[object]) -> int | None:
    numeric_years = [item for item in reference_years if isinstance(item, int)]
    if not numeric_years:
        return None
    return max(numeric_years)


def _format_candidate_type_label(value: object) -> str:
    normalized = str(value or "").strip()
    labels = {
        "general": "普通类",
        "art": "艺体类",
        "sports": "体育类",
        "fine_art": "美术类",
        "music": "音乐类",
        "dance": "舞蹈类",
        "media": "传媒类",
    }
    return labels.get(normalized, normalized)


def _pick_rule_alert(rule_alerts: list[dict[str, object]] | list[object], codes: list[str]) -> dict[str, object] | None:
    for item in rule_alerts:
        if isinstance(item, dict) and item.get("code") in codes:
            return item
    return None


def _format_parallel_rule_mode(mode: object, is_parallel: object) -> str:
    mapping = {
        "college_major_parallel": "院校 + 专业平行",
        "group_parallel": "院校专业组平行",
        "major_parallel": "专业平行",
        "ordered_sequential": "顺序志愿",
    }
    if isinstance(mode, str) and mode.strip():
        return mapping.get(mode, mode)
    return "平行志愿" if bool(is_parallel) else "未设"


def _format_subject_requirement_mode(mode: object) -> str:
    mapping = {
        "unified_subject_requirement": "统一选科要求",
        "first_choice_reselect": "首选 + 再选",
        "major_level_requirement": "专业级选科要求",
    }
    if isinstance(mode, str) and mode.strip():
        return mapping.get(mode, mode)
    return "未设"


def _build_recommendation_risk_rows(meta: dict[str, object], rows: list[dict[str, object]]) -> list[dict[str, str]]:
    results: list[dict[str, str]] = []

    simulation_note = str(meta.get("simulation_note") or "").strip()
    if simulation_note and simulation_note != "默认推荐链路":
        results.append(
            {
                "title": "模拟结果",
                "summary": f"当前推荐结果基于“{meta.get('score_input_label') or '模拟链路'}”生成",
                "detail": simulation_note,
            }
        )

    results.extend(_build_recommendation_history_comparison_rows(meta, rows))

    sample_insufficient_count = sum(
        1 for row in rows if "sample_insufficient" in {str(item) for item in row.get("risk_flags_json") or [] if item}
    )
    if sample_insufficient_count:
        results.append(
            {
                "title": "样本不足",
                "summary": f"{sample_insufficient_count} 条结果存在样本不足提示",
                "detail": "这类推荐更适合作为方向性参考，建议结合近年数据和学校经验做二次判断。",
            }
        )

    rank_missing_count = sum(
        1 for row in rows if "rank_missing" in {str(item) for item in row.get("risk_flags_json") or [] if item}
    )
    if rank_missing_count:
        results.append(
            {
                "title": "缺少位次口径",
                "summary": f"{rank_missing_count} 条结果已改按分数参考",
                "detail": "位次口径不完整时，结果稳定性会低于标准位次链路，建议后续用正式位次复核。",
            }
        )

    manual_check_count = sum(
        1 for row in rows if "manual_formula_check" in {str(item) for item in row.get("risk_flags_json") or [] if item}
    )
    if manual_check_count:
        results.append(
            {
                "title": "需人工复核",
                "summary": f"{manual_check_count} 条结果仍需人工核对招生章程",
                "detail": "这类推荐通常涉及规则边界、专业限制或特殊口径，不能直接作为最终填报结论。",
            }
        )

    path_mismatch_count = sum(
        1
        for row in rows
        if {
            "postgraduate_path_mismatch",
            "certificate_path_mismatch",
            "long_training_path_mismatch",
            "public_service_path_mismatch",
        }
        & {str(item) for item in row.get("risk_flags_json") or [] if item}
    )
    if path_mismatch_count:
        results.append(
            {
                "title": "职业路径不完全匹配",
                "summary": f"{path_mismatch_count} 条结果与当前可接受路径存在偏差",
                "detail": "建议结合学生对读研、资格证、长培养周期和考公考编路径的接受度再做筛选。",
            }
        )

    stale_reference_count = sum(
        1
        for row in rows
        if _has_stale_reference_years(
            meta.get("target_year"),
            _extract_recommendation_reference_years(row),
        )
    )
    if stale_reference_count:
        results.append(
            {
                "title": "参考年份偏旧",
                "summary": f"{stale_reference_count} 条结果最近录取样本与目标年份相差 2 年及以上",
                "detail": "这类推荐更适合作为方向性参考；若近一年录取数据尚未补齐，分层、排序和汇报口径都可能继续变化。",
            }
        )

    if not results:
        results.append(
            {
                "title": "当前结果边界较清晰",
                "summary": f"{len(rows)} 条推荐结果当前未发现明显的全局风险提示",
                "detail": "当前结果主要可按已有位次/分数链路和职业匹配说明做进一步筛选与汇报。",
            }
        )

    return results


def _build_recommendation_history_comparison_rows(
    meta: dict[str, object],
    rows: list[dict[str, object]],
) -> list[dict[str, str]]:
    compare_scheme = meta.get("compare_scheme")
    compare_rows = meta.get("compare_rows")
    if not isinstance(compare_scheme, dict) or not isinstance(compare_rows, list) or not compare_rows or not rows:
        return []

    current_map = {_recommendation_comparison_key(item): item for item in rows}
    compare_map = {
        _recommendation_comparison_key(item): item
        for item in compare_rows
        if isinstance(item, dict)
    }
    if not current_map or not compare_map:
        return []

    added_count = 0
    removed_count = 0
    changed_count = 0
    common_count = 0
    reference_year_changed_count = 0
    stale_shift_count = 0
    affected_count = 0
    stale_only_count = 0
    reference_year_group_shift_count = 0
    reference_rank_shift_count = 0
    latest_min_rank_shift_count = 0
    latest_min_score_shift_count = 0

    for key, current_item in current_map.items():
        compare_item = compare_map.get(key)
        if not isinstance(compare_item, dict):
            added_count += 1
            continue

        if _has_numeric_metric_shift(
            _read_recommendation_metric_number(current_item.get("reference_rank")),
            _read_recommendation_metric_number(compare_item.get("reference_rank")),
        ):
            reference_rank_shift_count += 1
        if _has_numeric_metric_shift(
            _read_recommendation_snapshot_number(current_item, "latest_min_rank"),
            _read_recommendation_snapshot_number(compare_item, "latest_min_rank"),
        ):
            latest_min_rank_shift_count += 1
        if _has_numeric_metric_shift(
            _read_recommendation_snapshot_number(current_item, "latest_min_score"),
            _read_recommendation_snapshot_number(compare_item, "latest_min_score"),
        ):
            latest_min_score_shift_count += 1

        current_latest_reference_year = _get_recommendation_latest_reference_year(current_item)
        compare_latest_reference_year = _get_recommendation_latest_reference_year(compare_item)
        reference_year_changed = False
        if (
            current_latest_reference_year is not None
            and compare_latest_reference_year is not None
            and current_latest_reference_year != compare_latest_reference_year
        ):
            reference_year_changed = True
            reference_year_changed_count += 1
            if current_item.get("result_type") != compare_item.get("result_type"):
                reference_year_group_shift_count += 1

        current_is_stale = _has_stale_recommendation_reference_year(
            current_item,
            meta.get("target_year"),
        )
        compare_is_stale = _has_stale_recommendation_reference_year(
            compare_item,
            compare_scheme.get("target_year"),
        )
        stale_state_changed = current_is_stale != compare_is_stale
        if reference_year_changed or stale_state_changed:
            affected_count += 1
        if stale_state_changed:
            stale_shift_count += 1
            if not reference_year_changed:
                stale_only_count += 1

        if current_item.get("result_type") != compare_item.get("result_type"):
            changed_count += 1
            continue

        common_count += 1

    for key in compare_map:
        if key not in current_map:
            removed_count += 1

    changed_total = added_count + removed_count + changed_count
    compare_label = _build_recommendation_compare_label(compare_scheme)
    is_cross_province = (
        isinstance(current_province := meta.get("province"), str)
        and isinstance(compare_province := compare_scheme.get("province"), str)
        and current_province.strip()
        and compare_province.strip()
        and current_province.strip() != compare_province.strip()
    )
    is_same_province_year = (
        isinstance(current_province := meta.get("province"), str)
        and isinstance(compare_province := compare_scheme.get("province"), str)
        and current_province.strip()
        and compare_province.strip()
        and isinstance(current_target_year := meta.get("target_year"), int)
        and isinstance(compare_target_year := compare_scheme.get("target_year"), int)
        and current_province.strip() == compare_province.strip()
        and current_target_year != compare_target_year
    )
    same_province_year_impact_count = changed_count + stale_shift_count if is_same_province_year else 0
    results = [
        {
            "title": "历史方案差异",
            "summary": (
                f"相对{compare_label}，当前方案新增 {added_count} 条、移除 {removed_count} 条、分组调整 {changed_count} 条"
                if changed_total
                else f"相对{compare_label}，当前方案结构保持稳定"
            ),
            "detail": (
                f"{_build_recommendation_group_delta_detail(rows, list(compare_map.values()))}；保留 {common_count} 条可比结果。"
            ),
        }
    ]

    reference_summary = _build_recommendation_reference_summary(
        changed_count=reference_year_changed_count,
        affected_count=affected_count,
        stale_shift_count=stale_shift_count,
        stale_only_count=stale_only_count,
        group_shift_count=reference_year_group_shift_count,
        current_target_year=meta.get("target_year"),
        compare_target_year=compare_scheme.get("target_year"),
        current_province=meta.get("province"),
        compare_province=compare_scheme.get("province"),
        reference_rank_shift_count=reference_rank_shift_count,
        latest_min_rank_shift_count=latest_min_rank_shift_count,
        latest_min_score_shift_count=latest_min_score_shift_count,
    )
    if reference_summary:
        if is_cross_province and affected_count:
            results.append(
                {
                    "title": "跨省口径差异",
                    "summary": f"{affected_count} 条可比结果受跨省口径影响",
                    "detail": f"当前方案按 {meta.get('province')} 口径，对比方案按 {compare_scheme.get('province')} 口径；同校同专业在跨省比较时，录取位次和分组变化属于正常现象。",
                }
            )
        if is_same_province_year and same_province_year_impact_count:
            results.append(
                {
                    "title": "同省跨年份差异",
                    "summary": f"{same_province_year_impact_count} 条可比结果受同省跨年份口径变化影响",
                    "detail": _build_same_province_year_metric_detail(
                        reference_rank_shift_count=reference_rank_shift_count,
                        latest_min_rank_shift_count=latest_min_rank_shift_count,
                        latest_min_score_shift_count=latest_min_score_shift_count,
                    ),
                }
            )
        results.append(
            {
                "title": "历史方案参考变化",
                "summary": reference_summary["summary"],
                "detail": f"{compare_label}；{reference_summary['detail']}",
            }
        )

    return results


def _build_recommendation_risk_group_label(title: object) -> str:
    if title in {
        "历史方案差异",
        "跨省口径差异",
        "同省跨年份差异",
        "历史方案参考变化",
    }:
        return "历史对照摘要"
    if title in {
        "模拟结果",
        "样本不足",
        "缺少位次口径",
        "需人工复核",
        "参考年份偏旧",
        "当前结果边界较清晰",
    }:
        return "边界概览"
    return "风险概览"


def _extract_recommendation_reference_years(row: dict[str, object]) -> list[object]:
    snapshot = row.get("snapshot_json")
    if not isinstance(snapshot, dict):
        return []
    reference_years = snapshot.get("reference_years")
    return reference_years if isinstance(reference_years, list) else []


def _recommendation_comparison_key(row: dict[str, object]) -> str:
    college_id = row.get("college_id")
    major_id = row.get("major_id")
    return f"{college_id}-{major_id if major_id is not None else 0}"


def _build_recommendation_group_delta_detail(
    rows: list[dict[str, object]],
    compare_rows: list[dict[str, object]],
) -> str:
    current_group_counts = _build_recommendation_group_counts(rows)
    compare_group_counts = _build_recommendation_group_counts(compare_rows)
    parts: list[str] = []
    for key, label in [
        ("challenge", "冲刺"),
        ("steady", "稳妥"),
        ("safe", "保底"),
    ]:
        current = current_group_counts.get(key, 0)
        compare = compare_group_counts.get(key, 0)
        delta = current - compare
        parts.append(f"{label} {current} 对 {compare}（{_format_signed_delta(delta)}）")
    return "；".join(parts)


def _build_recommendation_group_counts(rows: list[dict[str, object]]) -> dict[str, int]:
    counts = {"challenge": 0, "steady": 0, "safe": 0}
    for row in rows:
        result_type = row.get("result_type")
        if result_type in counts:
            counts[str(result_type)] += 1
    return counts


def _format_signed_delta(value: int) -> str:
    if value > 0:
        return f"+{value}"
    if value < 0:
        return str(value)
    return "0"


def _build_recommendation_compare_label(compare_scheme: dict[str, object]) -> str:
    scheme_name = str(compare_scheme.get("scheme_name") or "").strip() or "最近历史方案"
    generated_date = _format_compare_scheme_generated_date(compare_scheme.get("generated_at"))
    return f"“{scheme_name}”（{generated_date}）" if generated_date else f"“{scheme_name}”"


def _format_compare_scheme_generated_date(value: object) -> str | None:
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, str):
        current = value.strip()
        if not current:
            return None
        return current[:10]
    return None


def _build_recommendation_reference_summary(
    *,
    changed_count: int,
    affected_count: int,
    stale_shift_count: int,
    stale_only_count: int,
    group_shift_count: int,
    current_target_year: object,
    compare_target_year: object,
    current_province: object,
    compare_province: object,
    reference_rank_shift_count: int,
    latest_min_rank_shift_count: int,
    latest_min_score_shift_count: int,
) -> dict[str, str] | None:
    if not changed_count and not stale_shift_count:
        return None

    if (
        isinstance(current_target_year, int)
        and isinstance(compare_target_year, int)
        and current_target_year != compare_target_year
    ):
        year_summary = f"当前方案目标年份 {current_target_year}，对比方案目标年份 {compare_target_year}"
    else:
        year_summary = "两版方案的可比推荐在近年样本上出现了变化"

    summary_segments: list[str] = []
    if changed_count:
        group_impact_text = (
            f"其中 {group_shift_count} 条同时伴随冲稳保分组变化"
            if group_shift_count > 0
            else "目前还未直接带来冲稳保分组变化"
        )
        summary_segments.append(
            f"{changed_count} 条保留院校/专业的最近录取样本年份发生变化，{group_impact_text}"
        )
    if stale_shift_count:
        summary_segments.append(f"{stale_shift_count} 条结果的“年份偏旧”状态发生变化")

    if changed_count and group_shift_count == 0:
        group_impact_detail = "这些变化当前更多影响解释口径和排序，不一定会直接改动冲稳保分组。"
    elif changed_count:
        group_impact_detail = f"在参考年份发生变化的保留结果里，有 {group_shift_count} 条同时出现了冲稳保分组调整。"
    else:
        group_impact_detail = "当前没有检测到明确的参考年份切换，但“年份偏旧”状态已经发生变化。"

    province_summary = (
        f"当前方案按 {current_province} 口径，对比方案按 {compare_province} 口径；同校同专业在跨省比较时，录取位次和分组变化属于正常现象。"
        if isinstance(current_province, str)
        and isinstance(compare_province, str)
        and current_province.strip()
        and compare_province.strip()
        and current_province.strip() != compare_province.strip()
        else None
    )
    same_province_year_summary = (
        f"两版方案都按 {current_province} 口径，但目标年份不同；{_build_same_province_year_metric_detail(reference_rank_shift_count=reference_rank_shift_count, latest_min_rank_shift_count=latest_min_rank_shift_count, latest_min_score_shift_count=latest_min_score_shift_count)}"
        if isinstance(current_province, str)
        and isinstance(compare_province, str)
        and isinstance(current_target_year, int)
        and isinstance(compare_target_year, int)
        and current_province.strip()
        and current_province.strip() == compare_province.strip()
        and current_target_year != compare_target_year
        else None
    )
    stale_only_summary = (
        f"其中 {stale_only_count} 条只是“年份偏旧”状态切换，最近录取样本年份本身未变化，通常意味着目标年份切换后，旧样本是否仍算“偏旧”的判断发生了变化。"
        if stale_only_count > 0
        else None
    )

    return {
        "summary": "，".join(summary_segments),
        "detail": "；".join(
            item
            for item in [
                year_summary,
                group_impact_detail,
                stale_only_summary,
                province_summary,
                same_province_year_summary,
                "若同校同专业的参考年份被补新或回退，分组、排序和汇报口径出现变化属于正常现象。",
            ]
            if item
        ),
    }


def _build_same_province_year_metric_detail(
    *,
    reference_rank_shift_count: int,
    latest_min_rank_shift_count: int,
    latest_min_score_shift_count: int,
) -> str:
    segments: list[str] = []
    if reference_rank_shift_count:
        segments.append(f"{reference_rank_shift_count} 条参考位次变化")
    if latest_min_rank_shift_count:
        segments.append(f"{latest_min_rank_shift_count} 条最近最低位次变化")
    if latest_min_score_shift_count:
        segments.append(f"{latest_min_score_shift_count} 条最近最低分变化")
    if not segments:
        return "当前至少有参考年份或“年份偏旧”状态切换，即使位次/分数口径暂未明显变化，解释口径也已经按不同年份样本重算。"
    return f"当前可比结果里，{'，'.join(segments)}，说明同省跨年份对照下录取样本和参考口径本身已经更新，分组和排序变化属于正常现象。"


def _has_stale_recommendation_reference_year(item: dict[str, object], target_year: object) -> bool:
    gap = _get_reference_year_gap(target_year, _extract_recommendation_reference_years(item))
    return gap is not None and gap >= 2


def _get_recommendation_latest_reference_year(item: dict[str, object]) -> int | None:
    reference_years = [value for value in _extract_recommendation_reference_years(item) if isinstance(value, int)]
    if not reference_years:
        return None
    return max(reference_years)


def _read_recommendation_snapshot_number(item: dict[str, object], key: str) -> float | None:
    snapshot = item.get("snapshot_json")
    if not isinstance(snapshot, dict):
        return None
    return _read_recommendation_metric_number(snapshot.get(key))


def _read_recommendation_metric_number(value: object) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _has_numeric_metric_shift(current_value: float | None, compare_value: float | None) -> bool:
    return current_value is not None and compare_value is not None and current_value != compare_value
