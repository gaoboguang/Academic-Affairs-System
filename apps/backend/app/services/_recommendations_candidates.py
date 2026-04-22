from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import AdmissionRecord, EnrollmentPlan, Student
from app.repositories.exams import get_total_snapshots_for_exam
from app.repositories.recommendations import list_admission_candidates, list_enrollment_plan_candidates

from ._recommendations_shared import RecommendationSettingsState


def detect_student_type(student: Student) -> str:
    if student.art_track:
        return "art"
    if student.student_type and student.student_type not in {"general", "repeat"}:
        return student.student_type
    return "general"


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
    target_regions: list[str],
    school_levels: list[str],
    major_keyword: str | None,
    subject_combination: str | None,
    settings: RecommendationSettingsState,
) -> list[AdmissionRecord]:
    items = list_admission_candidates(
        session,
        province=province,
        student_type="general" if student_type == "general" else student_type,
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
            major_name=item.major.name if item.major else None,
            record_art_track=item.art_track,
            target_regions=target_regions,
            school_levels=school_levels,
            major_keyword=major_keyword,
            settings=settings,
        )
    ]


def filter_enrollment_plans(
    session: Session,
    *,
    year: int,
    province: str,
    student: Student,
    student_type: str,
    batch: str | None,
    exam_mode: str | None,
    target_regions: list[str],
    school_levels: list[str],
    major_keyword: str | None,
    subject_combination: str | None,
    settings: RecommendationSettingsState,
) -> list[EnrollmentPlan]:
    items = list_enrollment_plan_candidates(
        session,
        year=year,
        province=province,
        student_type="general" if student_type == "general" else student_type,
        batch=batch,
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
            record_art_track=None,
            target_regions=target_regions,
            school_levels=school_levels,
            major_keyword=major_keyword,
            settings=settings,
        )
    ]


def _matches_common_candidate_filters(
    *,
    student: Student,
    student_type: str,
    college,
    major,
    college_id: int,
    major_name: str | None,
    record_art_track: str | None,
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
    if major_keyword and (not major_name or major_keyword not in major_name):
        return False
    if student_type != "general" and college and not college.supports_art:
        return False
    if student_type != "general" and student.art_track and record_art_track and record_art_track != student.art_track:
        return False
    return True
