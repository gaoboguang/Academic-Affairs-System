from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models import AdmissionRecord, RecommendationResult, RecommendationScheme, Student
from app.repositories.exams import get_exam
from app.repositories.recommendations import list_major_employment_mappings_for_majors, list_recommendation_results
from app.repositories.students import get_student_career_preference as repo_get_student_career_preference
from app.repositories.system import write_audit_log
from app.schemas.recommendation import (
    RecommendationBatchGenerateItem,
    RecommendationBatchGeneratePayload,
    RecommendationBatchGenerateResponse,
    RecommendationGeneratePayload,
    RecommendationGenerateResponse,
)

from ._recommendations_candidates import detect_student_type, get_admission_reference_candidates, get_student_exam_metrics
from ._recommendations_candidates import filter_enrollment_plans
from ._recommendations_fallback_priority import build_fallback_priority
from ._recommendations_policy_context import load_batch_dict_context, load_province_policy_context
from ._recommendations_result_builder import (
    build_career_preference_state,
    build_recommendation_result,
    build_recommendation_sort_key,
    evaluate_career_alignment,
)
from ._recommendations_score_lines import (
    build_score_line_reference_evaluation,
    supports_plan_only_reference,
    supports_score_line_reference,
)
from ._recommendations_score_lines import build_plan_only_reference_evaluation
from ._recommendations_score_input import apply_input_context_to_evaluation, resolve_score_input_context
from ._recommendations_shared import _load_recommendation_settings_state, _serialize_result
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


def generate_recommendations(
    session: Session,
    payload: RecommendationGeneratePayload,
) -> RecommendationGenerateResponse:
    return _generate_for_student(session, payload)


def batch_generate_recommendations(
    session: Session,
    payload: RecommendationBatchGeneratePayload,
) -> RecommendationBatchGenerateResponse:
    if not payload.student_ids:
        raise HTTPException(status_code=400, detail="学生列表不能为空")
    scheme_ids: list[int] = []
    total_result_count = 0
    items: list[RecommendationBatchGenerateItem] = []
    for student_id in payload.student_ids:
        result = _generate_for_student(
            session,
            RecommendationGeneratePayload(
                student_id=student_id,
                exam_id=payload.exam_id,
                name=payload.name,
                target_year=payload.target_year,
                province=payload.province,
                target_regions_json=payload.target_regions_json,
                school_level_tags_json=payload.school_level_tags_json,
                major_keyword=payload.major_keyword,
                subject_combination=payload.subject_combination,
                obey_adjustment=payload.obey_adjustment,
                note=payload.note,
            ),
        )
        scheme_ids.append(result.scheme_id)
        total_result_count += result.result_count
        student = session.get(Student, student_id)
        scheme = session.get(RecommendationScheme, result.scheme_id)
        items.append(
            RecommendationBatchGenerateItem(
                student_id=student_id,
                student_name=student.name if student else str(student_id),
                province=scheme.province if scheme else "",
                scheme_id=result.scheme_id,
                result_count=result.result_count,
            )
        )

    province_count = len({item.province for item in items if item.province})
    message = "批量推荐完成"
    if province_count > 1:
        message = f"批量推荐完成，已按 {province_count} 个生源地分别生成"

    return RecommendationBatchGenerateResponse(
        message=message,
        scheme_ids=scheme_ids,
        result_count=total_result_count,
        items=items,
    )


def _generate_for_student(session: Session, payload: RecommendationGeneratePayload) -> RecommendationGenerateResponse:
    student = session.get(Student, payload.student_id)
    exam = get_exam(session, payload.exam_id)
    if not student:
        raise HTTPException(status_code=404, detail="学生不存在")
    if not exam:
        raise HTTPException(status_code=404, detail="考试不存在")

    settings = _load_recommendation_settings_state(session)
    target_year = payload.target_year or exam.exam_date.year
    student_type = detect_student_type(student)
    student_total_score, snapshot_rank = get_student_exam_metrics(session, payload.student_id, payload.exam_id)
    province = _resolve_recommendation_province(payload.province, student.origin_province)
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
        total_score=student_total_score,
        snapshot_rank=snapshot_rank,
    )
    student_rank = input_context["effective_rank"]
    score_source = str(input_context.get("score_source") or "")
    candidate_records, used_general_reference_fallback = get_admission_reference_candidates(
        session,
        province=province,
        student=student,
        student_type=student_type,
        target_regions=payload.target_regions_json,
        school_levels=payload.school_level_tags_json,
        major_keyword=payload.major_keyword,
        subject_combination=payload.subject_combination,
        settings=settings,
    )
    fallback_plans = []
    if not candidate_records and (supports_score_line_reference(student_type) or supports_plan_only_reference(student_type)):
        fallback_plans = filter_enrollment_plans(
            session,
            year=target_year,
            province=province,
            student=student,
            student_type=student_type,
            batch=None,
            exam_mode=None,
            target_regions=payload.target_regions_json,
            school_levels=payload.school_level_tags_json,
            major_keyword=payload.major_keyword,
            subject_combination=payload.subject_combination,
            settings=settings,
        )
    if not candidate_records and not fallback_plans:
        raise HTTPException(status_code=404, detail="当前条件下暂无可推荐的录取数据")

    scheme = RecommendationScheme(
        name=(payload.name or f"{student.name}-{exam.name}-推荐").strip(),
        target_year=target_year,
        province=province,
        student_type=student_type,
        rule_json={
            "origin_province": province,
            "target_year": target_year,
            "target_regions_json": payload.target_regions_json,
            "school_level_tags_json": payload.school_level_tags_json,
            "major_keyword": payload.major_keyword,
            "subject_combination": payload.subject_combination,
            "obey_adjustment": payload.obey_adjustment,
            "score_input_mode": payload.score_input_mode,
            "score_range_min": payload.score_range_min,
            "score_range_max": payload.score_range_max,
            "rank_range_min": payload.rank_range_min,
            "rank_range_max": payload.rank_range_max,
            "reference_exam_name": payload.reference_exam_name,
            "use_historical_mapping": payload.use_historical_mapping,
            "risk_preference": payload.risk_preference,
            "student_rank_override": payload.student_rank_override,
            "comprehensive_score": payload.comprehensive_score,
            "professional_score": payload.professional_score,
            "culture_score": payload.culture_score,
            "note": payload.note,
        },
        is_default=False,
    )
    session.add(scheme)
    session.flush()

    thresholds = {
        "safe": settings.safe_ratio_max,
        "steady": settings.steady_ratio_max,
        "rush": settings.rush_ratio_max,
    }
    whitelist_ids = set(settings.whitelist_college_ids)
    grouped_candidates: dict[tuple[int, int | None], list[AdmissionRecord]] = defaultdict(list)
    for item in candidate_records:
        grouped_candidates[(item.college_id, item.major_id)].append(item)

    results: list[RecommendationResult] = []
    score_value = input_context["score_value"]
    student_career_preference = repo_get_student_career_preference(session, payload.student_id)
    career_preference = _build_student_career_preference_state(student_career_preference)
    employment_mappings_by_major = _group_major_employment_mappings(
        session,
        [major_id for (_, major_id) in grouped_candidates if major_id],
    )
    chapter_contexts = _load_chapter_rule_contexts(
        session,
        province=province,
        target_year=target_year,
        college_ids=[
            *[college_id for (college_id, _) in grouped_candidates],
            *[plan.college_id for plan in fallback_plans],
        ],
    )
    province_policy_context = load_province_policy_context(
        session,
        province=province,
        target_year=target_year,
    )
    for (college_id, major_id), records in grouped_candidates.items():
        first_record = records[0]
        career_alignment = evaluate_career_alignment(
            major=first_record.major,
            mappings=employment_mappings_by_major.get(major_id or 0, []),
            preference=career_preference,
            college_location=_build_college_location(
                first_record.college.city if first_record.college else None,
                first_record.college.province if first_record.college else None,
            ),
        )
        result = build_recommendation_result(
            student=student,
            exam_id=payload.exam_id,
            scheme_id=scheme.id,
            student_type=student_type,
            student_rank=student_rank,
            score_value=score_value,
            records=records,
            thresholds=thresholds,
            is_whitelisted=college_id in whitelist_ids,
            career_alignment=career_alignment,
            input_context=input_context,
        )
        if result:
            if used_general_reference_fallback:
                risk_flags = sorted(set([*(result.risk_flags_json or []), "general_reference_fallback"]))
                result.risk_flags_json = risk_flags
                result.reason_text = f"{result.reason_text} 当前缺少该类别专门录取结果，先按普通类录取结果参考。"
                snapshot = dict(result.snapshot_json or {})
                snapshot["used_general_reference_fallback"] = True
                snapshot["reference_candidate_type"] = "general"
                result.snapshot_json = snapshot
            chapter_context = chapter_contexts.get(college_id)
            batch_dict_context = load_batch_dict_context(
                session,
                province=province,
                batch=first_record.batch,
                student_type=student_type,
            )
            snapshot = dict(result.snapshot_json or {})
            if chapter_context:
                if chapter_context.chapter_url:
                    snapshot["chapter_url"] = chapter_context.chapter_url
                if chapter_context.review_status:
                    snapshot["chapter_review_status"] = chapter_context.review_status
                if chapter_context.retrieval_status:
                    snapshot["chapter_retrieval_status"] = chapter_context.retrieval_status
                if chapter_context.campus_note:
                    snapshot["chapter_campus_note"] = chapter_context.campus_note
                    result.reason_text = f"{result.reason_text} 校区备注：{chapter_context.campus_note}。"
                if chapter_context.other_risk_note and chapter_context.other_risk_note != GENERIC_CHAPTER_PENDING_NOTE:
                    snapshot["chapter_other_risk_note"] = chapter_context.other_risk_note
                    result.reason_text = f"{result.reason_text} 章程备注：{chapter_context.other_risk_note}。"
                chapter_restrictions = _build_chapter_restriction_notes(chapter_context)
                if chapter_restrictions:
                    snapshot["chapter_language_requirement"] = chapter_context.language_requirement
                    snapshot["chapter_single_subject_requirement"] = chapter_context.single_subject_requirement
                    snapshot["chapter_gender_requirement"] = chapter_context.gender_requirement
                    snapshot["chapter_height_requirement"] = chapter_context.height_requirement
                    snapshot["chapter_vision_requirement"] = chapter_context.vision_requirement
                    snapshot["chapter_color_vision_requirement"] = chapter_context.color_vision_requirement
                    snapshot["chapter_physical_exam_requirement"] = chapter_context.physical_exam_requirement
                    result.risk_flags_json = sorted(set([*(result.risk_flags_json or []), "chapter_special_requirement"]))
                    result.reason_text = f"{result.reason_text} {' '.join(f'{item}。' for item in chapter_restrictions)}"
                if not chapter_context.chapter_url and chapter_context.review_status:
                    result.risk_flags_json = sorted(set([*(result.risk_flags_json or []), "chapter_pending_review"]))
                    result.reason_text = f"{result.reason_text} 当前学校招生章程仍待补链，正式填报前建议核对招生章程。"
            if batch_dict_context and batch_dict_context.pathway_code:
                snapshot["batch_pathway_code"] = batch_dict_context.pathway_code
            if batch_dict_context and batch_dict_context.note:
                snapshot["batch_dict_note"] = batch_dict_context.note
                result.reason_text = f"{result.reason_text} 批次词典：{batch_dict_context.note}。"
            if province_policy_context and province_policy_context.title:
                snapshot["province_policy_title"] = province_policy_context.title
                snapshot["province_policy_year"] = province_policy_context.year
                snapshot["province_policy_type"] = province_policy_context.policy_type
                if province_policy_context.url:
                    snapshot["province_policy_url"] = province_policy_context.url
                if province_policy_context.summary:
                    snapshot["province_policy_summary"] = province_policy_context.summary
                    result.reason_text = f"{result.reason_text} 政策摘要：{province_policy_context.summary}。"
            result.snapshot_json = snapshot
            results.append(result)

    if fallback_plans:
        fallback_major_ids = [plan.major_id for plan in fallback_plans if plan.major_id]
        fallback_employment_mappings_by_major = _group_major_employment_mappings(session, fallback_major_ids)
        for plan in fallback_plans:
            batch_dict_context = load_batch_dict_context(
                session,
                province=plan.province,
                batch=plan.batch,
                student_type=student_type,
            )
            score_line_fallback = build_score_line_reference_evaluation(
                session,
                province=province,
                target_year=target_year,
                student_type=student_type,
                plan=plan,
                score_value=score_value,
                score_source=score_source,
            )
            if score_line_fallback:
                evaluation, score_line_reference = score_line_fallback
            else:
                score_line_reference = None
                plan_only_fallback = build_plan_only_reference_evaluation(
                    province=province,
                    target_year=target_year,
                    student_type=student_type,
                    plan=plan,
                )
                if not plan_only_fallback:
                    continue
                evaluation = plan_only_fallback
            career_alignment = evaluate_career_alignment(
                major=plan.major,
                mappings=fallback_employment_mappings_by_major.get(plan.major_id or 0, []),
                preference=career_preference,
                college_location=_build_college_location(
                    plan.college.city if plan.college else None,
                    plan.college.province if plan.college else None,
                ),
                training_location=plan.training_location,
            )
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
            snapshot_json = dict(evaluation.get("snapshot_json") or {})
            snapshot_json["reference_scope"] = str(snapshot_json.get("reference_scope") or "score_line")
            if batch_dict_context and batch_dict_context.pathway_code:
                snapshot_json["batch_pathway_code"] = batch_dict_context.pathway_code
            if batch_dict_context and batch_dict_context.note:
                snapshot_json["batch_dict_note"] = batch_dict_context.note
                evaluation["reason_text"] = f"{evaluation['reason_text']} 批次词典：{batch_dict_context.note}。"
            if province_policy_context and province_policy_context.title:
                snapshot_json["province_policy_title"] = province_policy_context.title
                snapshot_json["province_policy_year"] = province_policy_context.year
                snapshot_json["province_policy_type"] = province_policy_context.policy_type
                if province_policy_context.url:
                    snapshot_json["province_policy_url"] = province_policy_context.url
                if province_policy_context.summary:
                    snapshot_json["province_policy_summary"] = province_policy_context.summary
                    evaluation["reason_text"] = f"{evaluation['reason_text']} 政策摘要：{province_policy_context.summary}。"
            chapter_context = chapter_contexts.get(plan.college_id)
            chapter_restrictions = _build_chapter_restriction_notes(chapter_context)
            special_type_context = resolve_special_type_context(session, plan=plan, student_type=student_type)
            fallback_priority = build_fallback_priority(
                plan=plan,
                reference_scope=str(snapshot_json.get("reference_scope") or ""),
                student_type=student_type,
                score_value=_read_optional_float(snapshot_json.get("student_score")),
                reference_score=score_line_reference.score if score_line_reference else None,
                career_match_score=_read_optional_float(evaluation.get("career_match_score")),
                batch_order=None,
                batch_dict_sort_order=batch_dict_context.sort_order if batch_dict_context else None,
                has_chapter_url=bool(chapter_context and chapter_context.chapter_url),
                chapter_review_status=chapter_context.review_status if chapter_context else None,
                has_chapter_restrictions=bool(chapter_restrictions),
                special_type_context=special_type_context,
            )
            if fallback_priority:
                snapshot_json["fallback_priority_score"] = fallback_priority.score
                snapshot_json["fallback_priority_label"] = fallback_priority.label
                snapshot_json["fallback_priority_notes_json"] = fallback_priority.notes
                snapshot_json["fallback_category_label"] = fallback_priority.category_label
                snapshot_json["fallback_review_notes_json"] = fallback_priority.review_notes or []
                evaluation["reason_text"] = (
                    f"{evaluation['reason_text']} 初筛优先级：{fallback_priority.label}（{fallback_priority.score:g}）。"
                )
                if fallback_priority.category_label:
                    evaluation["reason_text"] = f"{evaluation['reason_text']} 细分类别：{fallback_priority.category_label}。"
                if fallback_priority.review_notes:
                    evaluation["reason_text"] = (
                        f"{evaluation['reason_text']} 核对清单：{'；'.join(fallback_priority.review_notes)}。"
                    )
            if str(snapshot_json.get("reference_scope") or "") == "score_line" and score_line_reference:
                snapshot_json["reference_record_count"] = 0
                snapshot_json["reference_source_notes_json"] = _dedupe_strings(
                    [
                        f"{score_line_reference.candidate_type}{score_line_reference.batch_name}{score_line_reference.line_label}",
                        score_line_reference.remark,
                    ]
                )
            elif str(snapshot_json.get("reference_scope") or "") == "plan_only":
                snapshot_json["reference_record_count"] = 0
                snapshot_json["reference_source_notes_json"] = ["当年招生计划清单"]
            evaluation["snapshot_json"] = snapshot_json
            apply_input_context_to_evaluation(evaluation, input_context)
            result = RecommendationResult(
                student_id=student.id,
                exam_id=payload.exam_id,
                scheme_id=scheme.id,
                result_type=str(evaluation["result_type"]),
                college_id=plan.college_id,
                major_id=plan.major_id,
                reference_rank=evaluation.get("reference_rank"),
                student_rank=evaluation.get("student_rank"),
                score_basis=str(evaluation["score_basis"]),
                ratio=evaluation.get("ratio"),
                reason_text=str(evaluation["reason_text"]),
                risk_flags_json=list(evaluation.get("risk_flags_json") or []),
                snapshot_json=dict(evaluation.get("snapshot_json") or {}),
            )
            if chapter_context:
                snapshot = dict(result.snapshot_json or {})
                if chapter_context.chapter_url:
                    snapshot["chapter_url"] = chapter_context.chapter_url
                if chapter_context.review_status:
                    snapshot["chapter_review_status"] = chapter_context.review_status
                if chapter_context.retrieval_status:
                    snapshot["chapter_retrieval_status"] = chapter_context.retrieval_status
                if chapter_context.campus_note:
                    snapshot["chapter_campus_note"] = chapter_context.campus_note
                    result.reason_text = f"{result.reason_text} 校区备注：{chapter_context.campus_note}。"
                if chapter_context.other_risk_note and chapter_context.other_risk_note != GENERIC_CHAPTER_PENDING_NOTE:
                    snapshot["chapter_other_risk_note"] = chapter_context.other_risk_note
                    result.reason_text = f"{result.reason_text} 章程备注：{chapter_context.other_risk_note}。"
                if chapter_restrictions:
                    snapshot["chapter_language_requirement"] = chapter_context.language_requirement
                    snapshot["chapter_single_subject_requirement"] = chapter_context.single_subject_requirement
                    snapshot["chapter_gender_requirement"] = chapter_context.gender_requirement
                    snapshot["chapter_height_requirement"] = chapter_context.height_requirement
                    snapshot["chapter_vision_requirement"] = chapter_context.vision_requirement
                    snapshot["chapter_color_vision_requirement"] = chapter_context.color_vision_requirement
                    snapshot["chapter_physical_exam_requirement"] = chapter_context.physical_exam_requirement
                    result.risk_flags_json = sorted(set([*(result.risk_flags_json or []), "chapter_special_requirement"]))
                    result.reason_text = f"{result.reason_text} {' '.join(f'{item}。' for item in chapter_restrictions)}"
                    if not chapter_context.chapter_url and chapter_context.review_status:
                        result.risk_flags_json = sorted(set([*(result.risk_flags_json or []), "chapter_pending_review"]))
                        result.reason_text = f"{result.reason_text} 当前学校招生章程仍待补链，正式填报前建议核对招生章程。"
                result.snapshot_json = snapshot
            results.append(result)

    if not results:
        raise HTTPException(status_code=404, detail="当前条件下没有可生成的推荐结果")

    for item in results:
        session.add(item)
    session.flush()
    write_audit_log(
        session,
        module="recommendations",
        action="generate",
        target_type="recommendation_scheme",
        target_id=str(scheme.id),
        detail_json={"student_id": payload.student_id, "result_count": len(results)},
    )
    serialized = [
        _serialize_result(item)
        for item in list_recommendation_results(session, student_id=payload.student_id, scheme_id=scheme.id)
    ]
    serialized.sort(
        key=lambda item: build_recommendation_sort_key(
            result_type=item.result_type,
            career_match_score=item.career_match_score,
            career_match_strength=item.career_match_strength,
            ratio=item.ratio,
            reference_rank=item.reference_rank,
            college_name=item.college_name,
            major_name=item.major_name,
            fallback_priority_score=item.fallback_priority_score,
        )
    )
    return RecommendationGenerateResponse(
        scheme_id=scheme.id,
        scheme_name=scheme.name,
        student_id=payload.student_id,
        result_count=len(serialized),
        challenge=[item for item in serialized if item.result_type == "challenge"],
        steady=[item for item in serialized if item.result_type == "steady"],
        safe=[item for item in serialized if item.result_type == "safe"],
    )


def _group_major_employment_mappings(
    session: Session,
    major_ids: list[int],
) -> dict[int, list]:
    grouped: dict[int, list] = defaultdict(list)
    for item in list_major_employment_mappings_for_majors(session, major_ids=major_ids):
        grouped[item.major_id].append(item)
    return grouped


def _build_student_career_preference_state(preference) -> dict[str, object] | None:
    if not preference or not preference.is_active:
        return None
    return build_career_preference_state(
        primary_direction_id=preference.primary_direction_id,
        primary_direction_name=preference.primary_direction.name if preference.primary_direction else None,
        secondary_direction_id=preference.secondary_direction_id,
        secondary_direction_name=preference.secondary_direction.name if preference.secondary_direction else None,
        alternative_direction_id=preference.alternative_direction_id,
        alternative_direction_name=preference.alternative_direction.name if preference.alternative_direction else None,
        priority_focuses_json=preference.priority_focuses_json,
        preferred_industries_json=preference.preferred_industries_json,
        preferred_job_types_json=preference.preferred_job_types_json,
        target_employment_cities_json=preference.target_employment_cities_json,
        accepts_postgraduate=preference.accepts_postgraduate,
        accepts_public_service=preference.accepts_public_service,
        accepts_certificate=preference.accepts_certificate,
        accepts_long_training=preference.accepts_long_training,
    )


def _build_college_location(city: str | None, province: str | None) -> str | None:
    segments = [segment.strip() for segment in [city, province] if segment and segment.strip()]
    return " / ".join(segments) or None


def _resolve_recommendation_province(request_province: str | None, student_origin_province: str | None) -> str:
    province = (request_province or "").strip() or (student_origin_province or "").strip()
    if not province:
        raise HTTPException(status_code=400, detail="未选择生源地，且学生档案未维护生源地省份")
    return province


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
                updated_at
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
        college_id = int(row["college_id"])
        if college_id in result:
            continue
        result[college_id] = ChapterRuleContext(
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


def _read_optional_float(value: object) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _dedupe_strings(values: list[str | None]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        current = (value or "").strip()
        if not current or current in seen:
            continue
        seen.add(current)
        result.append(current)
    return result
