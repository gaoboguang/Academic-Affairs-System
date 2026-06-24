from __future__ import annotations

from app.exporters._recommendation_export_formatters import (
    format_parallel_rule_mode as _format_parallel_rule_mode,
    format_subject_requirement_mode as _format_subject_requirement_mode,
)


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
    if row.get("reference_scope") == "college":
        scope_label = "院校线参考"
    elif row.get("reference_scope") == "score_line":
        scope_label = "省控线参考"
    elif row.get("reference_scope") == "plan_only":
        scope_label = "计划清单参考"
    else:
        scope_label = "专业线参考"
    reference_years = row.get("reference_years_json") or []
    year_label = f"{' / '.join(str(item) for item in reference_years)} 年" if reference_years else "年份待补"
    if row.get("reference_scope") == "score_line":
        sample_label = "省级控制线口径"
    elif row.get("reference_scope") == "plan_only":
        sample_label = "当年计划口径"
    else:
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

    if "general_reference_fallback" in risk_flags:
        notes.append(
            "当前缺少该类别专门录取结果，先按普通类录取结果做方向性参考；"
            "这不是该类别专门录取把握，正式填报前仍需结合类别公告、批次规则和学校章程复核。"
        )

    if row.get("reference_scope") == "score_line":
        notes.append("当前结果只按省级控制线做资格初筛，不能直接视作院校或专业录取把握。")

    if row.get("reference_scope") == "plan_only":
        notes.append("当前结果只按当年招生计划清单做方向性初筛，不能直接作为冲稳保或录取把握判断。")

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
        "fallback_general_reference_data": "当前缺少该类别专门录取结果，已回退参考普通类录取结果",
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

    general_reference_fallback_count = sum(
        1 for row in rows if "general_reference_fallback" in {str(item) for item in row.get("risk_flags_json") or [] if item}
    )
    if general_reference_fallback_count:
        fallback_alert = _pick_rule_alert(rule_alerts, ["fallback_general_reference_data"])
        results.append(
            {
                "key": "general_reference_fallback",
                "title": str(fallback_alert.get("title") if fallback_alert else "普通类录取参考回退"),
                "summary": f"{general_reference_fallback_count} 条已选志愿当前按普通类录取结果参考",
                "detail": str(
                    fallback_alert.get("detail")
                    if fallback_alert
                    else "这类结果适合先做方向性筛选；正式填报前仍需结合该类别自己的录取口径、公告和批次规则再复核。"
                ),
            }
        )

    score_line_reference_count = sum(1 for row in rows if row.get("reference_scope") == "score_line")
    if score_line_reference_count:
        results.append(
            {
                "key": "score_line_reference",
                "title": "省控线初筛",
                "summary": f"{score_line_reference_count} 条已选志愿当前仅按省控线做资格参考",
                "detail": "这类结果说明当前缺少该类别专门录取结果，只能先按山东省控线筛掉明显不满足线的计划；正式填报前仍需逐校核对录取与章程口径。",
            }
        )

    plan_only_reference_count = sum(1 for row in rows if row.get("reference_scope") == "plan_only")
    if plan_only_reference_count:
        results.append(
            {
                "key": "plan_only_reference",
                "title": "计划清单初筛",
                "summary": f"{plan_only_reference_count} 条已选志愿当前仅按当年招生计划做方向性初筛",
                "detail": "这类结果说明当前缺少该类别专门录取结果，也没有可直接复用的官方控制线；正式填报前必须结合该类别公告、章程和后续结果再复核。",
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
        "general_reference_fallback",
        "college_fallback",
        "score_line_reference",
        "plan_only_reference",
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
        "spring_exam": "春季高考",
        "independent_recruitment": "单独招生",
        "comprehensive_evaluation": "综合评价招生",
    }
    return labels.get(normalized, normalized)


def _pick_rule_alert(rule_alerts: list[dict[str, object]] | list[object], codes: list[str]) -> dict[str, object] | None:
    for item in rule_alerts:
        if isinstance(item, dict) and item.get("code") in codes:
            return item
    return None
