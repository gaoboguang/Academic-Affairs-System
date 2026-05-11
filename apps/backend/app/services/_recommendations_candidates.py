from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import AdmissionRecord, EnrollmentPlan, Student
from app.repositories.exams import get_total_snapshots_for_exam
from app.repositories.recommendations import list_admission_candidates, list_enrollment_plan_candidates

from ._recommendations_shared import RecommendationSettingsState
from ._recommendations_volunteer_options import art_track_matches_text, infer_art_track_from_text, normalize_art_track

ART_LIKE_STUDENT_TYPES = {"art", "sports", "fine_art", "music", "dance", "media"}
GENERAL_REFERENCE_FALLBACK_TYPES = {"spring_exam", "independent_recruitment", "comprehensive_evaluation"}


def detect_student_type(student: Student) -> str:
    normalized_student_type = (student.student_type or "").strip()
    normalized_art_track = normalize_art_track(student.art_track) or ""
    if normalized_student_type and normalized_student_type not in {"general", "repeat", "art", "sports"}:
        return normalized_student_type
    if normalized_art_track == "sports" or normalized_student_type == "sports":
        return "sports"
    if normalized_art_track or normalized_student_type == "art":
        return "art"
    if normalized_student_type == "repeat":
        return "repeat"
    return "general"


def is_art_like_student_type(student_type: str) -> bool:
    return (student_type or "").strip() in ART_LIKE_STUDENT_TYPES


def uses_general_reference_pool(student_type: str) -> bool:
    return (student_type or "").strip() in {"", "general", "repeat"}


def supports_general_reference_fallback(student_type: str) -> bool:
    return (student_type or "").strip() in GENERAL_REFERENCE_FALLBACK_TYPES


def get_student_exam_metrics(session: Session, student_id: int, exam_id: int) -> tuple[float, int | None]:
    snapshot = next(
        (item for item in get_total_snapshots_for_exam(session, exam_id) if item.student_id == student_id),
        None,
    )
    if not snapshot:
        raise HTTPException(status_code=404, detail="该学生在本次考试中暂无总分数据")
    return snapshot.total_score, snapshot.grade_rank


def filter_candidates(
    session: Session,
    *,
    province: str,
    student: Student,
    student_type: str,
    art_track: str | None = None,
    target_regions: list[str],
    school_levels: list[str],
    major_keyword: str | None,
    subject_combination: str | None,
    settings: RecommendationSettingsState,
) -> list[AdmissionRecord]:
    items, _ = get_admission_reference_candidates(
        session,
        province=province,
        student=student,
        student_type=student_type,
        art_track=art_track,
        target_regions=target_regions,
        school_levels=school_levels,
        major_keyword=major_keyword,
        subject_combination=subject_combination,
        settings=settings,
    )
    return items


def get_admission_reference_candidates(
    session: Session,
    *,
    province: str,
    student: Student,
    student_type: str,
    art_track: str | None = None,
    target_regions: list[str],
    school_levels: list[str],
    major_keyword: str | None,
    subject_combination: str | None,
    settings: RecommendationSettingsState,
    batches: tuple[str, ...] = (),
) -> tuple[list[AdmissionRecord], bool]:
    query_student_type = "general" if uses_general_reference_pool(student_type) else student_type
    items = list_admission_candidates(
        session,
        province=province,
        student_type=query_student_type,
        batches=batches or None,
        subject_requirement=subject_combination,
    )
    used_general_reference_fallback = False
    if not items and supports_general_reference_fallback(student_type):
        items = list_admission_candidates(
            session,
            province=province,
            student_type="general",
            batches=batches or None,
            subject_requirement=subject_combination,
        )
        used_general_reference_fallback = bool(items)

    filtered = [
        item
        for item in items
        if _matches_common_candidate_filters(
            student=student,
            student_type=student_type,
            college=item.college,
            major=item.major,
            college_id=item.college.id if item.college else item.college_id,
            major_name=item.major.name if item.major else None,
            candidate_art_track=art_track,
            record_art_track=item.art_track,
            record_text=item.source_note,
            target_regions=target_regions,
            school_levels=school_levels,
            major_keyword=major_keyword,
            settings=settings,
        )
    ]
    return filtered, used_general_reference_fallback


def filter_enrollment_plans(
    session: Session,
    *,
    year: int,
    province: str,
    student: Student,
    student_type: str,
    art_track: str | None = None,
    batch: str | None,
    exam_mode: str | None,
    target_regions: list[str],
    school_levels: list[str],
    major_keyword: str | None,
    subject_combination: str | None,
    settings: RecommendationSettingsState,
    batches: tuple[str, ...] = (),
) -> list[EnrollmentPlan]:
    query_student_type = "general" if uses_general_reference_pool(student_type) else student_type
    items = list_enrollment_plan_candidates(
        session,
        year=year,
        province=province,
        student_type=query_student_type,
        batch=batch,
        batches=batches or None,
        exam_mode=exam_mode,
        subject_requirement=subject_combination,
    )
    return [
        item
        for item in items
        if _matches_common_candidate_filters(
            student=student,
            student_type=student_type,
            college=item.college,
            major=item.major,
            college_id=item.college.id if item.college else item.college_id,
            major_name=item.major.name if item.major else item.major_name_snapshot or None,
            candidate_art_track=art_track,
            record_art_track=None,
            record_text=_join_filter_text(item.major_name_snapshot, item.source_note),
            target_regions=target_regions,
            school_levels=school_levels,
            major_keyword=major_keyword,
            settings=settings,
        )
    ]


def select_enrollment_plan_year(
    session: Session,
    *,
    target_year: int,
    province: str,
    student_type: str,
    batch: str | None,
    exam_mode: str | None,
    subject_combination: str | None,
    batches: tuple[str, ...] = (),
    use_historical_mapping: bool = False,
) -> tuple[int, bool, int]:
    from app.repositories.recommendations import (
        count_enrollment_plan_candidates,
        list_enrollment_plan_candidate_years,
    )

    query_student_type = "general" if uses_general_reference_pool(student_type) else student_type
    target_count = count_enrollment_plan_candidates(
        session,
        year=target_year,
        province=province,
        student_type=query_student_type,
        batch=batch,
        batches=batches or None,
        exam_mode=exam_mode,
        subject_requirement=subject_combination,
    )
    if target_count > 0:
        return target_year, False, target_count
    if not use_historical_mapping:
        return target_year, False, 0
    candidate_years = list_enrollment_plan_candidate_years(
        session,
        before_year=target_year,
        province=province,
        student_type=query_student_type,
        batch=batch,
        batches=batches or None,
        exam_mode=exam_mode,
        subject_requirement=subject_combination,
    )
    if not candidate_years:
        return target_year, False, 0
    return candidate_years[0], True, 0


def _matches_common_candidate_filters(
    *,
    student: Student,
    student_type: str,
    college,
    major,
    college_id: int,
    major_name: str | None,
    candidate_art_track: str | None,
    record_art_track: str | None,
    record_text: str | None,
    target_regions: list[str],
    school_levels: list[str],
    major_keyword: str | None,
    settings: RecommendationSettingsState,
) -> bool:
    whitelist_ids = set(settings.whitelist_college_ids)
    blacklist_ids = set(settings.blacklist_college_ids)
    expected_levels = set(school_levels)
    if college_id in blacklist_ids and college_id not in whitelist_ids:
        return False

    is_whitelisted = college_id in whitelist_ids
    if target_regions and college and college.province not in target_regions and college.city not in target_regions and not is_whitelisted:
        return False
    if expected_levels:
        level_tags = set(college.school_level_tags_json or []) if college else set()
        if not level_tags.intersection(expected_levels) and not is_whitelisted:
            return False
    searchable_major_text = _join_filter_text(major_name, record_text)
    if major_keyword and major_keyword not in searchable_major_text:
        return False
    if is_art_like_student_type(student_type) and college and not college.supports_art:
        return False
    normalized_candidate_art_track = normalize_art_track(candidate_art_track) or normalize_art_track(student.art_track)
    normalized_record_art_track = normalize_art_track(record_art_track) or infer_art_track_from_text(major_name, record_text)
    if (
        is_art_like_student_type(student_type)
        and normalized_candidate_art_track
        and normalized_record_art_track
        and normalized_record_art_track != normalized_candidate_art_track
    ):
        return False
    if (
        is_art_like_student_type(student_type)
        and normalized_candidate_art_track
        and not normalized_record_art_track
        and not art_track_matches_text(normalized_candidate_art_track, major_name, record_text)
    ):
        return False
    return True


def _join_filter_text(*values: str | None) -> str:
    return " ".join((value or "").strip() for value in values if (value or "").strip())
