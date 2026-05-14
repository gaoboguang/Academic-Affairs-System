from __future__ import annotations

from app.exporters._recommendation_export_formatters import (
    RECOMMENDATION_GLOBAL_RISK_NOTICES,
    format_compare_scheme_generated_date as _format_compare_scheme_generated_date,
    format_signed_delta as _format_signed_delta,
    read_recommendation_metric_number as _read_recommendation_metric_number,
    read_recommendation_snapshot_number as _read_recommendation_snapshot_number,
)


def _build_recommendation_risk_rows(meta: dict[str, object], rows: list[dict[str, object]]) -> list[dict[str, str]]:
    results: list[dict[str, str]] = [
        {
            "title": "统一风险口径",
            "summary": "正式输出保留普通类、特殊类型、2024/2026 数据和章程复核边界",
            "detail": notice,
        }
        for notice in RECOMMENDATION_GLOBAL_RISK_NOTICES
    ]

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

    general_reference_fallback_count = sum(
        1 for row in rows if "general_reference_fallback" in {str(item) for item in row.get("risk_flags_json") or [] if item}
    )
    if general_reference_fallback_count:
        results.append(
            {
                "title": "普通类录取参考回退",
                "summary": f"{general_reference_fallback_count} 条结果当前按普通类录取结果参考",
                "detail": "这类结果适合先做方向性筛选，正式填报前仍需结合该类别自己的录取口径、公告和批次规则再复核。",
            }
        )

    score_line_reference_count = sum(1 for row in rows if row.get("reference_scope") == "score_line")
    if score_line_reference_count:
        results.append(
            {
                "title": "省控线资格参考",
                "summary": f"{score_line_reference_count} 条结果当前仅按山东省控线做初筛",
                "detail": "这类结果说明当前缺少该类别专门录取结果，只能先按省级控制线判断是否具备基本资格，不能直接视作院校或专业录取把握。",
            }
        )

    plan_only_reference_count = sum(1 for row in rows if row.get("reference_scope") == "plan_only")
    if plan_only_reference_count:
        results.append(
            {
                "title": "计划清单初筛",
                "summary": f"{plan_only_reference_count} 条结果当前仅按当年招生计划做方向性初筛",
                "detail": "这类结果说明当前缺少该类别专门录取结果，也没有可直接复用的官方控制线；正式填报前必须结合该类别公告、章程和后续结果再复核。",
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
        "统一风险口径",
        "模拟结果",
        "样本不足",
        "缺少位次口径",
        "省控线资格参考",
        "计划清单初筛",
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
        ("watch", "仅关注"),
    ]:
        current = current_group_counts.get(key, 0)
        compare = compare_group_counts.get(key, 0)
        delta = current - compare
        parts.append(f"{label} {current} 对 {compare}（{_format_signed_delta(delta)}）")
    return "；".join(parts)


def _build_recommendation_group_counts(rows: list[dict[str, object]]) -> dict[str, int]:
    counts = {"challenge": 0, "steady": 0, "safe": 0, "watch": 0}
    for row in rows:
        result_type = row.get("result_type")
        if result_type in counts:
            counts[str(result_type)] += 1
    return counts


def _build_recommendation_compare_label(compare_scheme: dict[str, object]) -> str:
    scheme_name = str(compare_scheme.get("scheme_name") or "").strip() or "最近历史方案"
    generated_date = _format_compare_scheme_generated_date(compare_scheme.get("generated_at"))
    return f"“{scheme_name}”（{generated_date}）" if generated_date else f"“{scheme_name}”"


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


def _has_numeric_metric_shift(current_value: float | None, compare_value: float | None) -> bool:
    return current_value is not None and compare_value is not None and current_value != compare_value

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

