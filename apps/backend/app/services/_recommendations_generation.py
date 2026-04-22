from __future__ import annotations

from collections import defaultdict

from fastapi import HTTPException
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

from ._recommendations_candidates import detect_student_type, filter_candidates, get_student_exam_metrics
from ._recommendations_result_builder import (
    build_career_preference_state,
    build_recommendation_result,
    build_recommendation_sort_key,
    evaluate_career_alignment,
)
from ._recommendations_score_input import resolve_score_input_context
from ._recommendations_shared import _load_recommendation_settings_state, _serialize_result


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
    candidate_records = filter_candidates(
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
    if not candidate_records:
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
