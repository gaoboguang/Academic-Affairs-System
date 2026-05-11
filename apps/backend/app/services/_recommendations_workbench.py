from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from fastapi import HTTPException
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.models import AdmissionRecord, EnrollmentPlan, Student, StudentPathwayProfile
from app.repositories.exams import get_exam
from app.repositories.recommendations import (
    build_compatible_exam_modes,
    get_employment_direction,
    list_recent_admission_history_for_college,
    list_recent_admission_history,
    list_recent_enrollment_plan_history,
    list_major_employment_mappings_for_majors,
    list_province_volunteer_rules as repo_list_province_volunteer_rules,
)
from app.schemas.recommendation import (
    ProvinceVolunteerRuleRead,
    VolunteerWorkbenchCandidateRead,
    VolunteerWorkbenchPreviewPayload,
    VolunteerWorkbenchPreviewResponse,
    VolunteerWorkbenchRuleAlertRead,
)

from ._recommendations_candidates import (
    detect_student_type,
    filter_enrollment_plans,
    get_admission_reference_candidates,
    get_student_exam_metrics,
    select_enrollment_plan_year,
)
from ._recommendations_fallback_priority import build_fallback_priority
from ._recommendations_result_builder import (
    build_career_preference_state,
    build_recommendation_sort_key,
    evaluate_career_alignment,
    evaluate_recommendation_candidate,
)
from ._recommendations_policy_context import load_batch_dict_context, load_province_policy_context
from ._recommendations_score_lines import (
    ScoreLineReference,
    build_plan_only_reference_evaluation,
    build_score_line_reference_evaluation,
)
from ._recommendations_score_input import apply_input_context_to_evaluation, resolve_score_input_context
from ._recommendations_score_rank import try_lookup_rank_for_score
from ._recommendations_shared import _load_recommendation_settings_state, _serialize_province_volunteer_rule
from ._recommendations_special_type_rules import resolve_special_type_context
from ._recommendations_volunteer_options import (
    ART_MANUAL_REVIEW_TRACKS,
    art_track_matches_text,
    calculate_art_comprehensive_score,
    compatible_batches,
    infer_art_track_from_text,
    normalize_art_track,
    normalize_volunteer_fields,
)

GENERIC_CHAPTER_PENDING_NOTE = "待通过阳光高考章程查询逐校补链，当前仅完成山东 2025 工作集名单。"
VOLUNTEER_WORKBENCH_CANDIDATE_RETURN_LIMIT = 300


@dataclass
class ChapterRuleContext:
    chapter_url: str | None = None
    review_status: str | None = None
    retrieval_status: str | None = None
    campus_note: str | None = None
    other_risk_note: str | None = None
    language_requirement: str | None = None
    single_subject_requirement: str | None = None
    gender_requirement: str | None = None
    height_requirement: str | None = None
    vision_requirement: str | None = None
    color_vision_requirement: str | None = None
    physical_exam_requirement: str | None = None


def preview_volunteer_workbench(
    session: Session,
    payload: VolunteerWorkbenchPreviewPayload,
) -> VolunteerWorkbenchPreviewResponse:
    student = session.get(Student, payload.student_id)
    exam = get_exam(session, payload.exam_id)
    if not student:
        raise HTTPException(status_code=404, detail="学生不存在")
    if not exam:
        raise HTTPException(status_code=404, detail="考试不存在")

    target_year = payload.target_year or exam.exam_date.year
    pathway_profile = _load_student_pathway_profile(session, student.id, payload.province)
    detected_candidate_type = detect_student_type(student)
    profile_candidate_type = (pathway_profile.candidate_type or "").strip() if pathway_profile else ""
    normalized_fields = normalize_volunteer_fields(
        province=payload.province,
        candidate_type=payload.candidate_type or profile_candidate_type,
        art_track=payload.art_track or (pathway_profile.art_track if pathway_profile else None) or student.art_track,
        batch=payload.batch,
        detected_candidate_type=detected_candidate_type,
    )
    student_type = normalized_fields.candidate_type
    candidate_art_track = normalized_fields.art_track
    normalized_batch = normalized_fields.batch
    query_batches = compatible_batches(payload.province, normalized_batch, student_type)
    total_score, snapshot_rank = get_student_exam_metrics(session, payload.student_id, payload.exam_id)
    resolved_score_mode = payload.score_input_mode
    resolved_student_rank_override = payload.student_rank_override
    resolved_comprehensive_score = payload.comprehensive_score
    resolved_culture_score = payload.culture_score
    resolved_professional_score = payload.professional_score
    input_notes = list(normalized_fields.notes)

    if student_type == "art":
        art_context = _resolve_art_score_context(
            payload=payload,
            profile=pathway_profile,
            total_score=total_score,
            art_track=normalized_fields.art_track,
        )
        if art_context["blocking_detail"]:
            raise HTTPException(status_code=400, detail=art_context["blocking_detail"])
        if art_context["manual_review_detail"]:
            input_notes.append(str(art_context["manual_review_detail"]))
        resolved_score_mode = "estimated_score"
        resolved_student_rank_override = None
        resolved_culture_score = art_context["culture_score"]
        resolved_professional_score = art_context["professional_score"]
        resolved_comprehensive_score = art_context["comprehensive_score"]
        input_notes.append(str(art_context["note"]))
    elif (payload.score_input_mode or "").strip() == "estimated_score":
        lookup_score = payload.comprehensive_score if payload.comprehensive_score is not None else payload.culture_score
        if lookup_score is not None:
            lookup = try_lookup_rank_for_score(
                session,
                province=payload.province,
                target_year=target_year,
                score=float(lookup_score),
            )
            input_notes.append("校内名次不用于志愿推荐；当前仅使用分数通过官方一分一段估算省位次。")
            if lookup:
                resolved_student_rank_override = lookup.rank
                input_notes.append(f"当前按 {lookup.year} 年一分一段把 {float(lookup_score):g} 分换算为约 {lookup.rank} 位。")
                if lookup.basis == "previous_year_score_rank_segment":
                    input_notes.append(f"{target_year} 年一分一段暂缺，当前按最近可用年份做历史估算。")
            else:
                resolved_student_rank_override = None
                input_notes.append("当前缺少可用一分一段表，无法把校内分数换算为省位次；结果只按分数和计划做模拟参考。")
    input_context = resolve_score_input_context(
        score_input_mode=resolved_score_mode,
        student_rank_override=resolved_student_rank_override,
        comprehensive_score=resolved_comprehensive_score,
        culture_score=resolved_culture_score,
        score_range_min=payload.score_range_min,
        score_range_max=payload.score_range_max,
        rank_range_min=payload.rank_range_min,
        rank_range_max=payload.rank_range_max,
        reference_exam_name=payload.reference_exam_name,
        use_historical_mapping=payload.use_historical_mapping,
        risk_preference=payload.risk_preference,
        total_score=resolved_comprehensive_score if student_type == "art" and resolved_comprehensive_score is not None else total_score,
        snapshot_rank=None if resolved_score_mode == "estimated_score" else snapshot_rank,
    )
    effective_rank = input_context["effective_rank"]
    score_value = input_context["score_value"]
    score_source = str(input_context.get("score_source") or "")

    applicable_rules, rule_notes, rule_alerts = _load_applicable_rules(
        session,
        province=payload.province,
        target_year=target_year,
        exam_mode=payload.exam_mode,
        batch=normalized_batch,
        candidate_type=student_type,
    )
    settings = _load_recommendation_settings_state(session)
    plan_year, using_historical_plan_year, target_plan_count = select_enrollment_plan_year(
        session,
        target_year=target_year,
        province=payload.province,
        student_type=student_type,
        batch=normalized_batch,
        exam_mode=payload.exam_mode,
        subject_combination=payload.subject_combination,
        batches=query_batches,
        use_historical_mapping=payload.use_historical_mapping,
    )
    if target_plan_count <= 0:
        detail = _missing_target_year_plan_detail(
            province=payload.province,
            target_year=target_year,
            batch=normalized_batch,
            student_type=student_type,
        )
        if using_historical_plan_year:
            historical_detail = (
                f"{detail} 当前已按“历年映射估算”使用 {plan_year} 年历史招生计划做模拟候选，"
                f"不是 {target_year} 年正式招生计划；正式出分和计划发布后必须重新计算。"
            )
            input_notes.append(historical_detail)
            rule_alerts.append(
                VolunteerWorkbenchRuleAlertRead(
                    code="historical_enrollment_plan_simulation",
                    level="info",
                    title="按历史计划模拟",
                    detail=historical_detail,
                )
            )
        else:
            input_notes.append(detail)
            rule_alerts.append(
                VolunteerWorkbenchRuleAlertRead(
                    code="missing_target_year_enrollment_plan",
                    level="warning",
                    title="缺少目标年份招生计划",
                    detail=detail,
                )
            )
    enrollment_plans = filter_enrollment_plans(
        session,
        year=plan_year,
        province=payload.province,
        student=student,
        student_type=student_type,
        art_track=candidate_art_track,
        batch=normalized_batch,
        exam_mode=payload.exam_mode,
        target_regions=payload.target_regions_json,
        school_levels=payload.school_level_tags_json,
        major_keyword=payload.major_keyword,
        subject_combination=payload.subject_combination,
        settings=settings,
        batches=query_batches,
    )
    admissions, used_general_reference_fallback = get_admission_reference_candidates(
        session,
        province=payload.province,
        student=student,
        student_type=student_type,
        art_track=candidate_art_track,
        target_regions=payload.target_regions_json,
        school_levels=payload.school_level_tags_json,
        major_keyword=payload.major_keyword,
        subject_combination=payload.subject_combination,
        settings=settings,
        batches=query_batches,
    )
    exact_records, college_records = _group_admission_records(admissions)

    thresholds = {
        "safe": settings.safe_ratio_max,
        "steady": settings.steady_ratio_max,
        "rush": settings.rush_ratio_max,
    }
    whitelist_ids = set(settings.whitelist_college_ids)
    career_preference = _build_payload_career_preference_state(session, payload)
    employment_mappings_by_major = _group_major_employment_mappings(
        session,
        [plan.major_id for plan in enrollment_plans if plan.major_id],
    )
    chapter_contexts = _load_chapter_rule_contexts(
        session,
        province=payload.province,
        target_year=target_year,
        college_ids=[plan.college_id for plan in enrollment_plans],
    )
    province_policy_context = load_province_policy_context(
        session,
        province=payload.province,
        target_year=target_year,
    )
    candidates: list[VolunteerWorkbenchCandidateRead] = []
    for plan in enrollment_plans:
        batch_dict_context = load_batch_dict_context(
            session,
            province=plan.province,
            batch=plan.batch,
            student_type=student_type,
        )
        records, used_college_fallback = _match_reference_records(plan, exact_records, college_records)
        career_alignment = evaluate_career_alignment(
            major=plan.major,
            mappings=employment_mappings_by_major.get(plan.major_id or 0, []),
            preference=career_preference,
            training_location=plan.training_location,
            college_location=_build_college_location(plan.college.city if plan.college else None, plan.college.province if plan.college else None),
        )
        score_line_reference: ScoreLineReference | None = None
        used_plan_only_reference = False
        if records:
            evaluation = evaluate_recommendation_candidate(
                student=student,
                student_type=student_type,
                student_rank=effective_rank,
                score_value=score_value,
                records=records,
                thresholds=thresholds,
                is_whitelisted=plan.college_id in whitelist_ids,
                career_alignment=career_alignment,
            )
        else:
            score_line_fallback = build_score_line_reference_evaluation(
                session,
                province=payload.province,
                target_year=target_year,
                student_type=student_type,
                plan=plan,
                score_value=score_value,
                score_source=score_source,
                culture_score=resolved_culture_score,
                comprehensive_score=resolved_comprehensive_score,
            )
            if score_line_fallback:
                evaluation, score_line_reference = score_line_fallback
                if career_alignment:
                    evaluation["career_match_score"] = career_alignment.get("career_match_score")
                    evaluation["career_match_strength"] = career_alignment.get("career_match_strength")
                    evaluation["career_match_summary"] = career_alignment.get("career_match_summary")
                    evaluation["career_match_reasons_json"] = career_alignment.get("career_match_reasons_json") or []
                    evaluation["matched_direction_names_json"] = career_alignment.get("matched_direction_names_json") or []
                    evaluation["requires_postgraduate_path"] = career_alignment.get("requires_postgraduate_path")
                    evaluation["requires_certificate_path"] = career_alignment.get("requires_certificate_path")
                    evaluation["requires_long_training_path"] = career_alignment.get("requires_long_training_path")
                    if career_alignment.get("risk_flags_json"):
                        evaluation["risk_flags_json"] = sorted(
                            set([*(evaluation.get("risk_flags_json") or []), *list(career_alignment.get("risk_flags_json") or [])])
                        )
                    career_summary = str(career_alignment.get("career_match_summary") or "").strip()
                    if career_summary:
                        evaluation["reason_text"] = f"{evaluation['reason_text']} {career_summary}"
                    snapshot_json = dict(evaluation.get("snapshot_json") or {})
                    snapshot_json.update(
                        {
                            "career_match_score": career_alignment.get("career_match_score"),
                            "career_match_strength": career_alignment.get("career_match_strength"),
                            "career_match_summary": career_alignment.get("career_match_summary"),
                            "career_match_reasons_json": career_alignment.get("career_match_reasons_json"),
                            "matched_direction_names_json": career_alignment.get("matched_direction_names_json"),
                            "requires_postgraduate_path": career_alignment.get("requires_postgraduate_path"),
                            "requires_certificate_path": career_alignment.get("requires_certificate_path"),
                            "requires_long_training_path": career_alignment.get("requires_long_training_path"),
                        }
                    )
                    evaluation["snapshot_json"] = snapshot_json
            else:
                plan_only_fallback = build_plan_only_reference_evaluation(
                    province=payload.province,
                    target_year=target_year,
                    student_type=student_type,
                    plan=plan,
                )
                if not plan_only_fallback:
                    continue
                evaluation = plan_only_fallback
                used_plan_only_reference = True
                if career_alignment:
                    evaluation["career_match_score"] = career_alignment.get("career_match_score")
                    evaluation["career_match_strength"] = career_alignment.get("career_match_strength")
                    evaluation["career_match_summary"] = career_alignment.get("career_match_summary")
                    evaluation["career_match_reasons_json"] = career_alignment.get("career_match_reasons_json") or []
                    evaluation["matched_direction_names_json"] = career_alignment.get("matched_direction_names_json") or []
                    evaluation["requires_postgraduate_path"] = career_alignment.get("requires_postgraduate_path")
                    evaluation["requires_certificate_path"] = career_alignment.get("requires_certificate_path")
                    evaluation["requires_long_training_path"] = career_alignment.get("requires_long_training_path")
                    if career_alignment.get("risk_flags_json"):
                        evaluation["risk_flags_json"] = sorted(
                            set([*(evaluation.get("risk_flags_json") or []), *list(career_alignment.get("risk_flags_json") or [])])
                        )
                    career_summary = str(career_alignment.get("career_match_summary") or "").strip()
                    if career_summary:
                        evaluation["reason_text"] = f"{evaluation['reason_text']} {career_summary}"
                    snapshot_json = dict(evaluation.get("snapshot_json") or {})
                    snapshot_json.update(
                        {
                            "career_match_score": career_alignment.get("career_match_score"),
                            "career_match_strength": career_alignment.get("career_match_strength"),
                            "career_match_summary": career_alignment.get("career_match_summary"),
                            "career_match_reasons_json": career_alignment.get("career_match_reasons_json"),
                            "matched_direction_names_json": career_alignment.get("matched_direction_names_json"),
                            "requires_postgraduate_path": career_alignment.get("requires_postgraduate_path"),
                            "requires_certificate_path": career_alignment.get("requires_certificate_path"),
                            "requires_long_training_path": career_alignment.get("requires_long_training_path"),
                        }
                    )
                    evaluation["snapshot_json"] = snapshot_json
        if not evaluation:
            continue
        apply_input_context_to_evaluation(evaluation, input_context)
        candidates.append(
            _build_workbench_candidate(
                session=session,
                plan=plan,
                payload=payload,
                target_year=target_year,
                using_historical_plan_year=using_historical_plan_year,
                evaluation=evaluation,
                used_college_fallback=used_college_fallback,
                used_general_reference_fallback=used_general_reference_fallback,
                records=records,
                applicable_rules=applicable_rules,
                chapter_context=chapter_contexts.get(plan.college_id),
                score_line_reference=score_line_reference,
                used_plan_only_reference=used_plan_only_reference,
                batch_dict_context=batch_dict_context,
                province_policy_context=province_policy_context,
                candidate_art_track=candidate_art_track,
            )
        )

    rule_order_by_batch = {
        rule.batch: (rule.batch_order if rule.batch_order is not None else 999)
        for rule in applicable_rules
    }
    candidates.sort(key=lambda item: _candidate_sort_key(item, rule_order_by_batch))
    candidate_count = len(candidates)
    returned_candidates = candidates[:VOLUNTEER_WORKBENCH_CANDIDATE_RETURN_LIMIT]
    is_candidate_truncated = candidate_count > len(returned_candidates)
    serialized_rules: list[ProvinceVolunteerRuleRead] = [
        _serialize_province_volunteer_rule(item) for item in applicable_rules
    ]
    if used_general_reference_fallback:
        detail = f"当前缺少“{student_type}”专门录取结果，已先回退参考普通类录取结果；正式填报前建议结合学校公告和类别专门批次再复核。"
        rule_notes.append(detail)
        rule_alerts.append(
            VolunteerWorkbenchRuleAlertRead(
                code="fallback_general_reference_data",
                level="info",
                title="已回退到普通类录取参考",
                detail=detail,
            )
        )
    if is_candidate_truncated:
        detail = (
            f"当前智能筛选命中 {candidate_count} 条候选计划，页面仅展示前 "
            f"{VOLUNTEER_WORKBENCH_CANDIDATE_RETURN_LIMIT} 条；建议增加批次、地区、院校层级或专业关键词筛选。"
        )
        rule_notes.append(detail)
        rule_alerts.append(
            VolunteerWorkbenchRuleAlertRead(
                code="candidate_result_truncated",
                level="warning",
                title="智能筛选结果已截断",
                detail=detail,
            )
        )

    return VolunteerWorkbenchPreviewResponse(
        student_id=student.id,
        student_name=student.name,
        exam_id=exam.id,
        exam_name=exam.name,
        province=payload.province,
        target_year=target_year,
        student_type=student_type,
        candidate_type=student_type,
        art_track=candidate_art_track,
        normalized_batch=normalized_batch,
        total_score=resolved_comprehensive_score if student_type == "art" and resolved_comprehensive_score is not None else total_score,
        culture_score=resolved_culture_score,
        professional_score=resolved_professional_score,
        art_comprehensive_score=resolved_comprehensive_score if student_type == "art" else None,
        snapshot_rank=snapshot_rank,
        effective_rank=effective_rank,
        score_input_mode=resolved_score_mode,
        score_input_label=str(input_context["mode_label"]),
        score_confidence=str(input_context["confidence"]),
        input_notes=[*input_notes, *list(input_context["notes"]), *rule_notes],
        rule_alerts=rule_alerts,
        applicable_rule_count=len(serialized_rules),
        applicable_rules=serialized_rules,
        candidate_count=candidate_count,
        returned_candidate_count=len(returned_candidates),
        is_candidate_truncated=is_candidate_truncated,
        candidates=returned_candidates,
    )


def _load_applicable_rules(
    session: Session,
    *,
    province: str,
    target_year: int,
    exam_mode: str | None,
    batch: str | None,
    candidate_type: str,
) -> tuple[list, list[str], list[VolunteerWorkbenchRuleAlertRead]]:
    notes: list[str] = []
    alerts: list[VolunteerWorkbenchRuleAlertRead] = []
    province_rules = list(repo_list_province_volunteer_rules(session, province=province, year=None, exam_mode=None))
    target_year_rules = [item for item in province_rules if item.year == target_year]
    if not target_year_rules:
        available_years = sorted({item.year for item in province_rules}, reverse=True)
        if available_years:
            display_years = " / ".join(str(item) for item in available_years[:3])
            detail = f"当前未找到 {province} {target_year} 年省份规则；该省现有 {display_years} 年规则，志愿上限与单位类型需按当年公告人工复核。"
            notes.append(detail)
            alerts.append(
                VolunteerWorkbenchRuleAlertRead(
                    code="missing_rule_year",
                    level="warning",
                    title="缺少目标年份规则",
                    detail=detail,
                )
            )
        else:
            detail = f"当前未找到 {province} 的省份规则；志愿上限与单位类型需先人工确认。"
            notes.append(detail)
            alerts.append(
                VolunteerWorkbenchRuleAlertRead(
                    code="missing_rule_province",
                    level="warning",
                    title="缺少省份规则",
                    detail=detail,
                )
            )
        return [], notes, alerts

    rules = target_year_rules
    if batch:
        batch_rules = [item for item in rules if item.batch == batch]
        if not batch_rules:
            available_batches = " / ".join(sorted({item.batch for item in rules}))
            detail = f"当前未找到 {province} {target_year} 年“{batch}”批次规则；已维护批次：{available_batches}。"
            notes.append(detail)
            alerts.append(
                VolunteerWorkbenchRuleAlertRead(
                    code="missing_rule_batch",
                    level="warning",
                    title="缺少目标批次规则",
                    detail=detail,
                )
            )
            return [], notes, alerts
        rules = batch_rules

    candidate_rules = [item for item in rules if item.candidate_type in {"", candidate_type}]
    if not candidate_rules:
        available_types = " / ".join(sorted({item.candidate_type or "通用" for item in rules}))
        detail = f"当前未找到 {province} {target_year} 年适用于“{candidate_type or '通用'}”的规则；已维护类别：{available_types}。"
        notes.append(detail)
        alerts.append(
            VolunteerWorkbenchRuleAlertRead(
                code="missing_rule_candidate_type",
                level="warning",
                title="缺少考生类别规则",
                detail=detail,
            )
        )
        return [], notes, alerts
    if candidate_type and not any(item.candidate_type == candidate_type for item in candidate_rules):
        detail = f"当前未配置“{candidate_type}”专用规则，先按通用考生规则预览。"
        notes.append(detail)
        alerts.append(
            VolunteerWorkbenchRuleAlertRead(
                code="fallback_general_candidate_rule",
                level="info",
                title="已回退到通用考生规则",
                detail=detail,
            )
        )
    rules = candidate_rules
    best_candidate_rank = min(0 if item.candidate_type == candidate_type else 1 for item in rules)
    rules = [item for item in rules if (0 if item.candidate_type == candidate_type else 1) == best_candidate_rank]
    if exam_mode:
        compatible_modes = build_compatible_exam_modes(exam_mode)
        mode_rules = [item for item in rules if item.exam_mode in compatible_modes]
        if not mode_rules:
            available_modes = " / ".join(sorted({item.exam_mode for item in rules}))
            detail = f"当前未找到 {province} {target_year} 年“{exam_mode}”模式规则；已维护模式：{available_modes}。"
            notes.append(detail)
            alerts.append(
                VolunteerWorkbenchRuleAlertRead(
                    code="missing_rule_exam_mode",
                    level="warning",
                    title="缺少目标模式规则",
                    detail=detail,
                )
            )
            return [], notes, alerts
        if not any(item.exam_mode == exam_mode for item in mode_rules):
            used_modes = " / ".join(sorted({item.exam_mode for item in mode_rules}))
            detail = f"当前未配置“{exam_mode}”精确规则，先按兼容模式 {used_modes} 预览。"
            notes.append(detail)
            alerts.append(
                VolunteerWorkbenchRuleAlertRead(
                    code="compatible_exam_mode_fallback",
                    level="info",
                    title="已回退到兼容模式规则",
                    detail=detail,
                )
            )
        rules = mode_rules
        best_mode_rank = min(0 if item.exam_mode == exam_mode else 1 for item in rules)
        rules = [item for item in rules if (0 if item.exam_mode == exam_mode else 1) == best_mode_rank]
    if any(item.note and "系统基线初始化生成" in item.note for item in rules):
        detail = "当前命中的省份规则为系统基线，志愿上限、单位类型和征集志愿规则仍需按当年公告复核。"
        notes.append(detail)
        alerts.append(
            VolunteerWorkbenchRuleAlertRead(
                code="baseline_rule_matched",
                level="info",
                title="当前命中系统基线规则",
                detail=detail,
            )
        )
    rules.sort(key=lambda item: (item.batch_order or 999, item.id))
    deduped_notes = _dedupe_notes(notes)
    deduped_alerts: list[VolunteerWorkbenchRuleAlertRead] = []
    seen_alerts: set[tuple[str, str]] = set()
    for item in alerts:
        key = (item.code, item.detail)
        if key in seen_alerts:
            continue
        seen_alerts.add(key)
        deduped_alerts.append(item)
    return rules, deduped_notes, deduped_alerts


def _dedupe_notes(notes: list[str]) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for item in notes:
        if item in seen:
            continue
        seen.add(item)
        deduped.append(item)
    return deduped


def _missing_target_year_plan_detail(
    *,
    province: str,
    target_year: int,
    batch: str | None,
    student_type: str,
) -> str:
    type_label = {
        "general": "普通类",
        "art": "艺术类",
        "sports": "体育类",
        "spring_exam": "春季高考",
        "independent_recruitment": "高职单招",
        "comprehensive_evaluation": "高职综评",
        "repeat": "复读生",
    }.get(student_type or "", student_type or "当前类别")
    batch_text = f"“{batch}”" if batch else "当前批次"
    return (
        f"{province} {target_year} 年正式招生计划尚未导入（{type_label}{batch_text}）；"
        "当前不能按目标年份生成可加入志愿表的正式候选。"
    )


def _group_admission_records(
    records: list[AdmissionRecord],
) -> tuple[dict[tuple[int, int | None], list[AdmissionRecord]], dict[int, list[AdmissionRecord]]]:
    exact_records: dict[tuple[int, int | None], list[AdmissionRecord]] = defaultdict(list)
    college_records: dict[int, list[AdmissionRecord]] = defaultdict(list)
    for item in records:
        exact_records[(item.college_id, item.major_id)].append(item)
        college_records[item.college_id].append(item)
    return exact_records, college_records


def _match_reference_records(
    plan: EnrollmentPlan,
    exact_records: dict[tuple[int, int | None], list[AdmissionRecord]],
    college_records: dict[int, list[AdmissionRecord]],
) -> tuple[list[AdmissionRecord], bool]:
    records = exact_records.get((plan.college_id, plan.major_id))
    if records:
        return records, False
    fallback = college_records.get(plan.college_id, [])
    return fallback, bool(fallback)


def _build_workbench_candidate(
    *,
    session: Session,
    plan: EnrollmentPlan,
    payload: VolunteerWorkbenchPreviewPayload,
    target_year: int,
    using_historical_plan_year: bool,
    evaluation: dict[str, object],
    used_college_fallback: bool,
    used_general_reference_fallback: bool,
    records: list[AdmissionRecord],
    applicable_rules: list,
    chapter_context: ChapterRuleContext | None,
    score_line_reference: ScoreLineReference | None = None,
    used_plan_only_reference: bool = False,
    batch_dict_context=None,
    province_policy_context=None,
    candidate_art_track: str | None = None,
) -> VolunteerWorkbenchCandidateRead:
    major_name = _display_plan_major_name(plan)
    risk_flags = list(evaluation.get("risk_flags_json") or [])
    match_tags: list[str] = []
    match_notes: list[str] = []
    matched_rule = _select_candidate_rule(applicable_rules, plan)
    reference_scope = (
        "plan_only"
        if used_plan_only_reference
        else
        "score_line"
        if score_line_reference
        else "college"
        if used_college_fallback and plan.major_id is not None
        else "major"
    )
    chapter_restriction_notes = _build_chapter_restriction_notes(chapter_context)
    special_type_context = resolve_special_type_context(session, plan=plan, student_type=plan.student_type)
    fallback_priority = build_fallback_priority(
        plan=plan,
        reference_scope=reference_scope,
        student_type=plan.student_type,
        score_value=_score_value_for_fallback_priority(evaluation),
        reference_score=score_line_reference.score if score_line_reference else None,
        career_match_score=_read_optional_float(evaluation.get("career_match_score")),
        batch_order=matched_rule.batch_order if matched_rule else None,
        batch_dict_sort_order=batch_dict_context.sort_order if batch_dict_context else None,
        has_chapter_url=bool(chapter_context and chapter_context.chapter_url),
        chapter_review_status=chapter_context.review_status if chapter_context else None,
        has_chapter_restrictions=bool(chapter_restriction_notes),
        special_type_context=special_type_context,
    )
    requested_exam_mode = (payload.exam_mode or "").strip()
    if requested_exam_mode:
        if plan.exam_mode == requested_exam_mode:
            match_tags.append("模式精确命中")
        elif plan.exam_mode in build_compatible_exam_modes(requested_exam_mode):
            match_tags.append("兼容模式命中")
            match_notes.append(f"当前请求模式为“{requested_exam_mode}”，该计划按兼容模式“{plan.exam_mode}”命中。")
    if matched_rule:
        match_notes.append(
            f"当前按 {matched_rule.province} {matched_rule.year} {matched_rule.exam_mode} {matched_rule.batch} 规则解释。"
        )
        if matched_rule.candidate_type:
            match_notes.append(f"本条候选命中“{matched_rule.candidate_type}”专用规则。")
        else:
            match_notes.append("本条候选当前命中通用考生规则。")
        if matched_rule.note and "系统基线初始化生成" in matched_rule.note:
            match_tags.append("基线规则命中")
    if used_plan_only_reference:
        match_tags.append("计划清单初筛")
        if using_historical_plan_year:
            match_notes.append(
                f"当前按 {plan.year} 年历史招生计划模拟（{plan.province}），"
                f"不是 {target_year} 年正式招生计划，正式填报前必须重新计算。"
            )
        else:
            match_notes.append(f"当前按 {plan.province} {plan.year} 年当年招生计划清单做方向性初筛。")
    elif score_line_reference:
        match_tags.append("省控线参考")
        match_notes.append(
            f"当前按 {plan.province} {score_line_reference.year} 年{score_line_reference.candidate_type}{score_line_reference.batch_name}{score_line_reference.line_label} {score_line_reference.score:g} 分初筛。"
        )
        if score_line_reference.year != plan.year:
            match_notes.append(
                f"当前目标年为 {plan.year}，省控线暂按最近可用的 {score_line_reference.year} 年口径参考。"
            )
    elif used_college_fallback and plan.major_id is not None:
        risk_flags.append("major_baseline_missing")
        match_tags.append("院校线参考")
        match_notes.append("当前专业缺少历史专业线，先按院校近年录取基线参考。")
    elif plan.major_id is not None:
        match_tags.append("专业线参考")
    else:
        match_tags.append("院校级计划")
    if plan.subject_requirement and not payload.subject_combination:
        risk_flags.append("subject_requirement_check")
        match_tags.append("待核对选科")
    elif plan.subject_requirement and payload.subject_combination:
        match_tags.append("已带选科条件")
        match_notes.append(f"当前按“{payload.subject_combination}”筛选，计划要求为“{plan.subject_requirement}”。")
    if str(evaluation.get("score_basis")) == "rank":
        match_tags.append("按位次分层")
    elif str(evaluation.get("score_basis")) == "score":
        match_tags.append("按分数参考")
    if chapter_context and chapter_context.chapter_url:
        match_tags.append("章程链路已接入")
    elif chapter_context and not chapter_context.chapter_url and chapter_context.review_status:
        risk_flags.append("chapter_pending_review")
        match_tags.append("章程待补链")
        match_notes.append("当前学校章程链路仍待人工补链，正式填报前建议核对招生章程。")
    if used_general_reference_fallback:
        risk_flags.append("general_reference_fallback")
        match_tags.append("普通类录取参考")
        match_notes.append("当前缺少该类别专门录取结果，先按普通类录取结果参考。")
    if using_historical_plan_year:
        risk_flags.append("historical_plan_simulation")
        match_tags.append("历史计划模拟")
        match_notes.append(
            f"{target_year} 年正式招生计划尚未导入；本条仅按 {plan.year} 年计划和历史参考生成，不能直接当作正式志愿。"
        )
    if chapter_context and chapter_context.campus_note:
        match_notes.append(f"校区备注：{chapter_context.campus_note}")
    if chapter_context and chapter_context.other_risk_note and chapter_context.other_risk_note != GENERIC_CHAPTER_PENDING_NOTE:
        match_notes.append(f"章程备注：{chapter_context.other_risk_note}")
    if batch_dict_context and batch_dict_context.note:
        match_notes.append(f"批次词典：{batch_dict_context.note}")
    if province_policy_context and province_policy_context.title:
        policy_text = f"省级政策：{province_policy_context.title}"
        if province_policy_context.year is not None:
            policy_text = f"{policy_text}（{province_policy_context.year}）"
        match_notes.append(policy_text)
        if province_policy_context.summary:
            match_notes.append(f"政策摘要：{province_policy_context.summary}")
    if chapter_restriction_notes:
        risk_flags.append("chapter_special_requirement")
        match_tags.append("章程限制已提取")
        match_notes.extend(chapter_restriction_notes)
    if fallback_priority:
        match_tags.append(fallback_priority.label)
        match_notes.extend([f"初筛优先级：{fallback_priority.label}（{fallback_priority.score:g}）", *fallback_priority.notes])
        if fallback_priority.category_label:
            match_notes.append(f"细分类别：{fallback_priority.category_label}")
        match_notes.extend(fallback_priority.review_notes or [])
    reference_years = (
        [plan.year]
        if used_plan_only_reference
        else
        [score_line_reference.year]
        if score_line_reference
        else sorted({item.year for item in records}, reverse=True)
    )
    reference_source_notes = (
        ["当年招生计划清单"]
        if used_plan_only_reference
        else
        _dedupe_notes(
            [
                f"{score_line_reference.candidate_type}{score_line_reference.batch_name}{score_line_reference.line_label}",
                score_line_reference.remark,
            ]
        )
        if score_line_reference
        else _dedupe_notes([item.source_note for item in records if item.source_note])
    )
    reason_segments = []
    if used_college_fallback and plan.major_id is not None:
        reason_segments.append("当前专业缺少历史专业线，先按院校近年录取基线参考。")
    reason_segments.append(str(evaluation["reason_text"]))
    if plan.subject_requirement and not payload.subject_combination:
        reason_segments.append(f"选科要求为“{plan.subject_requirement}”，填报前需人工核对。")
    if used_general_reference_fallback:
        reason_segments.append("当前缺少该类别专门录取结果，先按普通类录取结果参考。")
    return VolunteerWorkbenchCandidateRead(
        plan_id=plan.id,
        year=plan.year,
        province=plan.province,
        batch=plan.batch,
        exam_mode=plan.exam_mode,
        college_id=plan.college_id,
        college_name=plan.college.name if plan.college else "",
        college_code_snapshot=plan.college_code_snapshot,
        major_id=plan.major_id,
        major_name=major_name,
        major_group_code=plan.major_group_code or None,
        major_code_snapshot=plan.major_code_snapshot,
        major_direction=plan.major.direction if plan.major else None,
        career_path=plan.major.career_path if plan.major else None,
        major_note=plan.major.note if plan.major else None,
        plan_count=plan.plan_count,
        subject_requirement=plan.subject_requirement,
        tuition_fee=plan.tuition_fee,
        schooling_years=plan.schooling_years,
        training_location=plan.training_location,
        student_type=plan.student_type,
        result_type=str(evaluation["result_type"]),
        reference_rank=evaluation.get("reference_rank"),
        latest_admission_year=evaluation.get("latest_year"),
        latest_min_rank=evaluation.get("latest_min_rank"),
        latest_min_score=evaluation.get("latest_min_score"),
        score_basis=str(evaluation["score_basis"]),
        reference_scope=reference_scope,
        reference_years_json=reference_years,
        reference_record_count=0 if (score_line_reference or used_plan_only_reference) else len(records),
        reference_source_notes_json=reference_source_notes,
        fallback_priority_score=fallback_priority.score if fallback_priority else None,
        fallback_priority_label=fallback_priority.label if fallback_priority else None,
        fallback_priority_notes_json=fallback_priority.notes if fallback_priority else [],
        fallback_category_label=fallback_priority.category_label if fallback_priority else None,
        fallback_review_notes_json=fallback_priority.review_notes if fallback_priority else [],
        ratio=evaluation.get("ratio"),
        career_match_score=evaluation.get("career_match_score"),
        career_match_strength=evaluation.get("career_match_strength"),
        career_match_summary=evaluation.get("career_match_summary"),
        career_match_reasons_json=list(evaluation.get("career_match_reasons_json") or []),
        matched_direction_names_json=list(evaluation.get("matched_direction_names_json") or []),
        requires_postgraduate_path=evaluation.get("requires_postgraduate_path"),
        requires_certificate_path=evaluation.get("requires_certificate_path"),
        requires_long_training_path=evaluation.get("requires_long_training_path"),
        matched_rule_exam_mode=matched_rule.exam_mode if matched_rule else None,
        matched_rule_batch=matched_rule.batch if matched_rule else None,
        matched_rule_candidate_type=matched_rule.candidate_type if matched_rule else None,
        matched_rule_is_baseline=bool(matched_rule and matched_rule.note and "系统基线初始化生成" in matched_rule.note),
        chapter_url=chapter_context.chapter_url if chapter_context else None,
        chapter_review_status=chapter_context.review_status if chapter_context else None,
        chapter_retrieval_status=chapter_context.retrieval_status if chapter_context else None,
        chapter_campus_note=chapter_context.campus_note if chapter_context else None,
        chapter_other_risk_note=chapter_context.other_risk_note if chapter_context else None,
        chapter_language_requirement=chapter_context.language_requirement if chapter_context else None,
        chapter_single_subject_requirement=chapter_context.single_subject_requirement if chapter_context else None,
        chapter_gender_requirement=chapter_context.gender_requirement if chapter_context else None,
        chapter_height_requirement=chapter_context.height_requirement if chapter_context else None,
        chapter_vision_requirement=chapter_context.vision_requirement if chapter_context else None,
        chapter_color_vision_requirement=chapter_context.color_vision_requirement if chapter_context else None,
        chapter_physical_exam_requirement=chapter_context.physical_exam_requirement if chapter_context else None,
        match_tags_json=_dedupe_notes(match_tags),
        match_notes_json=_dedupe_notes(match_notes),
        reason_text=" ".join(reason_segments),
        risk_flags_json=sorted(set(risk_flags)),
        source_note=plan.source_note,
        import_batch_name=(
            f"{plan.import_batch_name or ''}（按 {plan.year} 年历史计划模拟）".strip()
            if using_historical_plan_year
            else plan.import_batch_name
        ),
        recent_history_json=_build_recent_candidate_history(
            session=session,
            plan=plan,
            target_year=target_year,
            student_type=plan.student_type,
            candidate_art_track=candidate_art_track,
            batches=compatible_batches(payload.province, payload.batch, plan.student_type),
            exam_mode=payload.exam_mode,
        ),
    )


def _build_recent_candidate_history(
    *,
    session: Session,
    plan: EnrollmentPlan,
    target_year: int,
    student_type: str,
    candidate_art_track: str | None,
    batches: tuple[str, ...],
    exam_mode: str | None,
) -> list[dict]:
    plan_rows = [
        item
        for item in list_recent_enrollment_plan_history(
            session,
            before_year=target_year,
            province=plan.province,
            college_id=plan.college_id,
            major_id=plan.major_id,
            student_type=student_type,
            batches=batches,
            exam_mode=exam_mode,
            limit=3,
        )
        if _history_item_matches_art_track(
            candidate_art_track,
            item.major.name if item.major else None,
            item.major_name_snapshot,
            item.source_note,
            None,
        )
    ]
    admission_rows = [
        item
        for item in list_recent_admission_history(
            session,
            before_year=target_year,
            province=plan.province,
            college_id=plan.college_id,
            major_id=plan.major_id,
            student_type=student_type,
            batches=batches,
            limit=3,
        )
        if _history_item_matches_art_track(
            candidate_art_track,
            item.major.name if item.major else None,
            None,
            item.source_note,
            item.art_track,
        )
    ]
    if not admission_rows:
        plan_major_key = _canonical_history_major_name(_display_plan_major_name(plan))
        admission_rows = [
            item
            for item in list_recent_admission_history_for_college(
                session,
                before_year=target_year,
                province=plan.province,
                college_id=plan.college_id,
                student_type=student_type,
                batches=batches,
                limit=3,
            )
            if _history_item_matches_art_track(
                candidate_art_track,
                item.major.name if item.major else None,
                None,
                item.source_note,
                item.art_track,
            )
            and _canonical_history_major_name(item.major.name if item.major else None) == plan_major_key
        ]
    years = sorted({item.year for item in [*plan_rows, *admission_rows]}, reverse=True)[:3]
    history: list[dict] = []
    for year in years:
        plan_row = next((item for item in plan_rows if item.year == year), None)
        admission_row = next((item for item in admission_rows if item.year == year), None)
        history.append(
            {
                "year": year,
                "batch": (plan_row.batch if plan_row else admission_row.batch if admission_row else None),
                "plan_count": plan_row.plan_count if plan_row else None,
                "admission_count": admission_row.plan_count if admission_row else None,
                "min_score": admission_row.min_score if admission_row else None,
                "min_rank": admission_row.min_rank if admission_row else None,
                "tuition_fee": plan_row.tuition_fee if plan_row else None,
            }
        )
    return history


def _history_item_matches_art_track(
    candidate_art_track: str | None,
    major_name: str | None,
    major_name_snapshot: str | None,
    source_note: str | None,
    record_art_track: str | None,
) -> bool:
    normalized_candidate = normalize_art_track(candidate_art_track)
    if not normalized_candidate:
        return True
    normalized_record = normalize_art_track(record_art_track) or infer_art_track_from_text(
        major_name,
        major_name_snapshot,
        source_note,
    )
    if normalized_record:
        return normalized_record == normalized_candidate
    return art_track_matches_text(normalized_candidate, major_name, major_name_snapshot, source_note)


def _display_plan_major_name(plan: EnrollmentPlan) -> str | None:
    snapshot_name = (plan.major_name_snapshot or "").strip() or None
    major_name = plan.major.name if plan.major else None
    if snapshot_name and infer_art_track_from_text(snapshot_name) and snapshot_name != major_name:
        return snapshot_name
    return major_name or snapshot_name


def _canonical_history_major_name(value: str | None) -> str:
    text_value = (value or "").strip()
    if not text_value:
        return ""
    for marker in ("（", "(", "<", " "):
        if marker in text_value:
            text_value = text_value.split(marker, 1)[0]
    return text_value.strip()


def _load_chapter_rule_contexts(
    session: Session,
    *,
    province: str,
    target_year: int,
    college_ids: list[int],
) -> dict[int, ChapterRuleContext]:
    if not college_ids:
        return {}
    has_table = session.execute(
        text(
            """
            SELECT COUNT(*)
            FROM sqlite_master
            WHERE type = 'table' AND name = 'gaokao_college_chapter_rule'
            """
        )
    ).scalar()
    if not has_table:
        return {}
    unique_college_ids = sorted(set(college_ids))
    placeholders = ", ".join(f":college_id_{index}" for index in range(len(unique_college_ids)))
    params = {f"college_id_{index}": value for index, value in enumerate(unique_college_ids)}
    province_aliases = _province_aliases(province)
    province_placeholders = ", ".join(f":province_{index}" for index in range(len(province_aliases)))
    params.update({f"province_{index}": value for index, value in enumerate(province_aliases)})
    params["target_year"] = target_year
    available_columns = {
        row[1]
        for row in session.execute(text('PRAGMA table_info("gaokao_college_chapter_rule")')).all()
    }
    rows = session.execute(
        text(
            f"""
            SELECT
                college_id,
                chapter_url,
                review_status,
                retrieval_status,
                campus_note,
                other_risk_note,
                {_chapter_rule_select_expression("language_requirement", available_columns)},
                {_chapter_rule_select_expression("single_subject_requirement", available_columns)},
                {_chapter_rule_select_expression("gender_requirement", available_columns)},
                {_chapter_rule_select_expression("height_requirement", available_columns)},
                {_chapter_rule_select_expression("vision_requirement", available_columns)},
                {_chapter_rule_select_expression("color_vision_requirement", available_columns)},
                {_chapter_rule_select_expression("physical_exam_requirement", available_columns)},
                updated_at,
                year
            FROM gaokao_college_chapter_rule
            WHERE college_id IN ({placeholders})
              AND province IN ({province_placeholders})
              AND year = :target_year
            ORDER BY
                CASE WHEN chapter_url IS NOT NULL AND trim(chapter_url) != '' THEN 1 ELSE 0 END DESC,
                updated_at DESC,
                id DESC
            """
        ),
        params,
    ).mappings().all()
    result: dict[int, ChapterRuleContext] = {}
    for row in rows:
        college_id = row["college_id"]
        if college_id in result:
            continue
        result[int(college_id)] = ChapterRuleContext(
            chapter_url=_clean_optional_text(row["chapter_url"]),
            review_status=_clean_optional_text(row["review_status"]),
            retrieval_status=_clean_optional_text(row["retrieval_status"]),
            campus_note=_clean_optional_text(row["campus_note"]),
            other_risk_note=_clean_optional_text(row["other_risk_note"]),
            language_requirement=_clean_optional_text(row["language_requirement"]),
            single_subject_requirement=_clean_optional_text(row["single_subject_requirement"]),
            gender_requirement=_clean_optional_text(row["gender_requirement"]),
            height_requirement=_clean_optional_text(row["height_requirement"]),
            vision_requirement=_clean_optional_text(row["vision_requirement"]),
            color_vision_requirement=_clean_optional_text(row["color_vision_requirement"]),
            physical_exam_requirement=_clean_optional_text(row["physical_exam_requirement"]),
        )
    return result


def _province_aliases(province: str) -> list[str]:
    normalized = (province or "").strip()
    if normalized == "山东":
        return ["山东", "山东省", "sd", "shandong"]
    return [normalized]


def _clean_optional_text(value: object) -> str | None:
    if value is None:
        return None
    current = str(value).strip()
    return current or None


def _chapter_rule_select_expression(column: str, available_columns: set[str]) -> str:
    if column in available_columns:
        return f"{column} AS {column}"
    return f"NULL AS {column}"


def _build_chapter_restriction_notes(chapter_context: ChapterRuleContext | None) -> list[str]:
    if not chapter_context:
        return []
    notes: list[str] = []
    if chapter_context.language_requirement:
        notes.append(f"语言要求：{chapter_context.language_requirement}")
    if chapter_context.single_subject_requirement:
        notes.append(f"单科要求：{chapter_context.single_subject_requirement}")
    if chapter_context.gender_requirement:
        notes.append(f"性别要求：{chapter_context.gender_requirement}")
    if chapter_context.height_requirement:
        notes.append(f"身高要求：{chapter_context.height_requirement}")
    if chapter_context.vision_requirement:
        notes.append(f"视力要求：{chapter_context.vision_requirement}")
    if chapter_context.color_vision_requirement:
        notes.append(f"色觉要求：{chapter_context.color_vision_requirement}")
    if chapter_context.physical_exam_requirement:
        notes.append(f"体检要求：{chapter_context.physical_exam_requirement}")
    return notes


def _select_candidate_rule(applicable_rules: list, plan: EnrollmentPlan):
    exact_match = next(
        (item for item in applicable_rules if item.batch == plan.batch and item.exam_mode == plan.exam_mode),
        None,
    )
    if exact_match:
        return exact_match
    compatible_match = next((item for item in applicable_rules if item.batch == plan.batch), None)
    if compatible_match:
        return compatible_match
    return applicable_rules[0] if applicable_rules else None


def _candidate_sort_key(
    item: VolunteerWorkbenchCandidateRead,
    rule_order_by_batch: dict[str, int],
) -> tuple[int, int, float, float, int, float, int, str, str]:
    return (
        rule_order_by_batch.get(item.batch, 999),
        *build_recommendation_sort_key(
            result_type=item.result_type,
            career_match_score=item.career_match_score,
            career_match_strength=item.career_match_strength,
            ratio=item.ratio,
            reference_rank=item.latest_min_rank or item.reference_rank,
            college_name=item.college_name,
            major_name=item.major_name or item.major_group_code,
            fallback_priority_score=item.fallback_priority_score,
        ),
    )


def _read_optional_float(value: object) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _score_value_for_fallback_priority(evaluation: dict[str, object]) -> float | None:
    snapshot = evaluation.get("snapshot_json")
    if not isinstance(snapshot, dict):
        return None
    score_basis = str(snapshot.get("score_line_score_basis") or evaluation.get("score_basis") or "")
    if score_basis == "culture_score":
        return _read_optional_float(snapshot.get("culture_score")) or _read_optional_float(snapshot.get("student_score"))
    if score_basis == "comprehensive_score":
        return _read_optional_float(snapshot.get("comprehensive_score")) or _read_optional_float(snapshot.get("student_score"))
    return _read_optional_float(snapshot.get("student_score"))


def _resolve_candidate_type(student: Student, candidate_type: str | None) -> str:
    normalized = (candidate_type or "").strip()
    return normalized or detect_student_type(student)


def _load_student_pathway_profile(
    session: Session,
    student_id: int,
    province: str,
) -> StudentPathwayProfile | None:
    normalized_province = (province or "").strip()
    profile = session.scalar(
        select(StudentPathwayProfile).where(
            StudentPathwayProfile.student_id == student_id,
            StudentPathwayProfile.province == normalized_province,
            StudentPathwayProfile.is_active.is_(True),
        )
    ) if normalized_province else None
    if profile:
        return profile
    return session.scalar(
        select(StudentPathwayProfile)
        .where(
            StudentPathwayProfile.student_id == student_id,
            StudentPathwayProfile.is_active.is_(True),
        )
        .order_by(
            (StudentPathwayProfile.province == "山东").desc(),
            StudentPathwayProfile.id.desc(),
        )
    )


def _resolve_art_score_context(
    *,
    payload: VolunteerWorkbenchPreviewPayload,
    profile: StudentPathwayProfile | None,
    total_score: float,
    art_track: str | None,
) -> dict[str, object]:
    normalized_art_track = normalize_art_track(art_track)
    if not normalized_art_track:
        return {"blocking_detail": "艺术类推荐需要先选择艺术类别。"}
    if normalized_art_track in ART_MANUAL_REVIEW_TRACKS:
        return {
            "blocking_detail": "戏曲类、校考或省际联考录取原则差异较大，需按当年公告和院校章程人工复核。",
            "manual_review_detail": None,
        }
    culture_score = payload.culture_score if payload.culture_score is not None else payload.comprehensive_score
    if culture_score is None:
        culture_score = total_score
    professional_score = (
        payload.professional_score
        if payload.professional_score is not None
        else profile.art_professional_score
        if profile
        else None
    )
    professional_full_score = profile.art_professional_full_score if profile and profile.art_professional_full_score else 300
    if culture_score is None:
        return {"blocking_detail": "艺术类推荐需要文化成绩。"}
    if professional_score is None:
        return {"blocking_detail": "艺术类推荐需要先维护艺术专业统考分。"}
    comprehensive_score = calculate_art_comprehensive_score(
        art_track=normalized_art_track,
        culture_score=float(culture_score),
        professional_score=float(professional_score),
        professional_full_score=float(professional_full_score or 300),
    )
    if comprehensive_score is None:
        return {"blocking_detail": "当前艺术类别暂未配置可自动计算的省统考综合分公式。"}
    return {
        "blocking_detail": None,
        "manual_review_detail": None,
        "culture_score": float(culture_score),
        "professional_score": float(professional_score),
        "comprehensive_score": comprehensive_score,
        "note": f"艺术类已按山东 2026 省统考公式计算综合分：文化分 {float(culture_score):g}，专业分 {float(professional_score):g}，综合分 {comprehensive_score:g}。",
    }


def _group_major_employment_mappings(
    session: Session,
    major_ids: list[int],
) -> dict[int, list]:
    grouped: dict[int, list] = defaultdict(list)
    for item in list_major_employment_mappings_for_majors(session, major_ids=major_ids):
        grouped[item.major_id].append(item)
    return grouped


def _build_payload_career_preference_state(
    session: Session,
    payload: VolunteerWorkbenchPreviewPayload,
) -> dict[str, object] | None:
    direction_name_map: dict[int, str | None] = {}
    for direction_id in [
        payload.primary_direction_id,
        payload.secondary_direction_id,
        payload.alternative_direction_id,
    ]:
        if direction_id is None or direction_id in direction_name_map:
            continue
        direction = get_employment_direction(session, direction_id)
        direction_name_map[direction_id] = direction.name if direction and direction.is_active else None
    return build_career_preference_state(
        primary_direction_id=payload.primary_direction_id,
        primary_direction_name=direction_name_map.get(payload.primary_direction_id or -1),
        secondary_direction_id=payload.secondary_direction_id,
        secondary_direction_name=direction_name_map.get(payload.secondary_direction_id or -1),
        alternative_direction_id=payload.alternative_direction_id,
        alternative_direction_name=direction_name_map.get(payload.alternative_direction_id or -1),
        priority_focuses_json=payload.priority_focuses_json,
        preferred_industries_json=payload.preferred_industries_json,
        preferred_job_types_json=payload.preferred_job_types_json,
        target_employment_cities_json=payload.target_employment_cities_json,
        accepts_postgraduate=payload.accepts_postgraduate,
        accepts_public_service=payload.accepts_public_service,
        accepts_certificate=payload.accepts_certificate,
        accepts_long_training=payload.accepts_long_training,
    )


def _build_college_location(city: str | None, province: str | None) -> str | None:
    segments = [segment.strip() for segment in [city, province] if segment and segment.strip()]
    return " / ".join(segments) or None
