from __future__ import annotations

from collections import defaultdict

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import AdmissionRecord, EnrollmentPlan, Student
from app.repositories.exams import get_exam
from app.repositories.recommendations import (
    build_compatible_exam_modes,
    get_employment_direction,
    list_admission_candidates,
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

from ._recommendations_candidates import detect_student_type, filter_enrollment_plans, get_student_exam_metrics
from ._recommendations_result_builder import (
    build_career_preference_state,
    build_recommendation_sort_key,
    evaluate_career_alignment,
    evaluate_recommendation_candidate,
)
from ._recommendations_score_input import apply_input_context_to_evaluation, resolve_score_input_context
from ._recommendations_shared import _load_recommendation_settings_state, _serialize_province_volunteer_rule


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
    admissions = list_admission_candidates(
        session,
        province=payload.province,
        student_type="general" if student_type == "general" else student_type,
        batch=payload.batch,
        subject_requirement=payload.subject_combination,
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
    candidates: list[VolunteerWorkbenchCandidateRead] = []
    for plan in enrollment_plans:
        records, used_college_fallback = _match_reference_records(plan, exact_records, college_records)
        if not records:
            continue
        career_alignment = evaluate_career_alignment(
            major=plan.major,
            mappings=employment_mappings_by_major.get(plan.major_id or 0, []),
            preference=career_preference,
            training_location=plan.training_location,
            college_location=_build_college_location(plan.college.city if plan.college else None, plan.college.province if plan.college else None),
        )
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
        if not evaluation:
            continue
        apply_input_context_to_evaluation(evaluation, input_context)
        candidates.append(
            _build_workbench_candidate(
                plan=plan,
                payload=payload,
                evaluation=evaluation,
                used_college_fallback=used_college_fallback,
                records=records,
                applicable_rules=applicable_rules,
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
    plan: EnrollmentPlan,
    payload: VolunteerWorkbenchPreviewPayload,
    evaluation: dict[str, object],
    used_college_fallback: bool,
    records: list[AdmissionRecord],
    applicable_rules: list,
) -> VolunteerWorkbenchCandidateRead:
    major_name = plan.major.name if plan.major else plan.major_name_snapshot or None
    risk_flags = list(evaluation.get("risk_flags_json") or [])
    match_tags: list[str] = []
    match_notes: list[str] = []
    matched_rule = _select_candidate_rule(applicable_rules, plan)
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
    if used_college_fallback and plan.major_id is not None:
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
    reference_years = sorted({item.year for item in records}, reverse=True)
    reference_source_notes = _dedupe_notes([item.source_note for item in records if item.source_note])
    reason_segments = []
    if used_college_fallback and plan.major_id is not None:
        reason_segments.append("当前专业缺少历史专业线，先按院校近年录取基线参考。")
    reason_segments.append(str(evaluation["reason_text"]))
    if plan.subject_requirement and not payload.subject_combination:
        reason_segments.append(f"选科要求为“{plan.subject_requirement}”，填报前需人工核对。")
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
        reference_scope="college" if used_college_fallback and plan.major_id is not None else "major",
        reference_years_json=reference_years,
        reference_record_count=len(records),
        reference_source_notes_json=reference_source_notes,
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
        match_tags_json=_dedupe_notes(match_tags),
        match_notes_json=_dedupe_notes(match_notes),
        reason_text=" ".join(reason_segments),
        risk_flags_json=sorted(set(risk_flags)),
        source_note=plan.source_note,
        import_batch_name=plan.import_batch_name,
    )


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
) -> tuple[int, int, float, int, float, int, str, str]:
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
        ),
    )
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
