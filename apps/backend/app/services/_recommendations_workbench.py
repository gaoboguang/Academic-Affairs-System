from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models import AdmissionRecord, EnrollmentPlan, Student
from app.repositories.exams import get_exam
from app.repositories.recommendations import (
    build_compatible_exam_modes,
    get_employment_direction,
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
from ._recommendations_shared import _load_recommendation_settings_state, _serialize_province_volunteer_rule
from ._recommendations_special_type_rules import resolve_special_type_context

GENERIC_CHAPTER_PENDING_NOTE = "待通过阳光高考章程查询逐校补链，当前仅完成山东 2025 工作集名单。"


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
    student_type = _resolve_candidate_type(student, payload.candidate_type)
    total_score, snapshot_rank = get_student_exam_metrics(session, payload.student_id, payload.exam_id)
    input_context = resolve_score_input_context(
        score_input_mode=payload.score_input_mode,
        student_rank_override=payload.student_rank_override,
        comprehensive_score=payload.comprehensive_score,
        culture_score=payload.culture_score,
        score_range_min=payload.score_range_min,
        score_range_max=payload.score_range_max,
        rank_range_min=payload.rank_range_min,
        rank_range_max=payload.rank_range_max,
        reference_exam_name=payload.reference_exam_name,
        use_historical_mapping=payload.use_historical_mapping,
        risk_preference=payload.risk_preference,
        total_score=total_score,
        snapshot_rank=snapshot_rank,
    )
    effective_rank = input_context["effective_rank"]
    score_value = input_context["score_value"]
    score_source = str(input_context.get("score_source") or "")

    applicable_rules, rule_notes, rule_alerts = _load_applicable_rules(
        session,
        province=payload.province,
        target_year=target_year,
        exam_mode=payload.exam_mode,
        batch=payload.batch,
        candidate_type=student_type,
    )
    settings = _load_recommendation_settings_state(session)
    enrollment_plans = filter_enrollment_plans(
        session,
        year=target_year,
        province=payload.province,
        student=student,
        student_type=student_type,
        batch=payload.batch,
        exam_mode=payload.exam_mode,
        target_regions=payload.target_regions_json,
        school_levels=payload.school_level_tags_json,
        major_keyword=payload.major_keyword,
        subject_combination=payload.subject_combination,
        settings=settings,
    )
    admissions, used_general_reference_fallback = get_admission_reference_candidates(
        session,
        province=payload.province,
        student=student,
        student_type=student_type,
        target_regions=payload.target_regions_json,
        school_levels=payload.school_level_tags_json,
        major_keyword=payload.major_keyword,
        subject_combination=payload.subject_combination,
        settings=settings,
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
            )
        )

    rule_order_by_batch = {
        rule.batch: (rule.batch_order if rule.batch_order is not None else 999)
        for rule in applicable_rules
    }
    candidates.sort(key=lambda item: _candidate_sort_key(item, rule_order_by_batch))
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

    return VolunteerWorkbenchPreviewResponse(
        student_id=student.id,
        student_name=student.name,
        exam_id=exam.id,
        exam_name=exam.name,
        province=payload.province,
        target_year=target_year,
        student_type=student_type,
        candidate_type=student_type,
        total_score=total_score,
        snapshot_rank=snapshot_rank,
        effective_rank=effective_rank,
        score_input_mode=payload.score_input_mode,
        score_input_label=str(input_context["mode_label"]),
        score_confidence=str(input_context["confidence"]),
        input_notes=[*list(input_context["notes"]), *rule_notes],
        rule_alerts=rule_alerts,
        applicable_rule_count=len(serialized_rules),
        applicable_rules=serialized_rules,
        candidate_count=len(candidates),
        candidates=candidates,
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
) -> VolunteerWorkbenchCandidateRead:
    major_name = plan.major.name if plan.major else plan.major_name_snapshot or None
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
        score_value=_read_optional_float((evaluation.get("snapshot_json") or {}).get("student_score"))
        if isinstance(evaluation.get("snapshot_json"), dict)
        else None,
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
        import_batch_name=plan.import_batch_name,
    )


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


def _resolve_candidate_type(student: Student, candidate_type: str | None) -> str:
    normalized = (candidate_type or "").strip()
    return normalized or detect_student_type(student)


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
