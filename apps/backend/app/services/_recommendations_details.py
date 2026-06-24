from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy import desc, select
from sqlalchemy.orm import Session, joinedload

from app.models import (
    AdmissionRecord,
    College,
    CollegeMajorProfile,
    CollegeProfileDetail,
    CollegeYearSummary,
    EnrollmentPlan,
    GaokaoSourceDocument,
    Major,
    MajorEmploymentMapping,
    MajorProfileDetail,
)
from app.repositories.recommendations import get_college, get_major
from app.schemas.recommendation import (
    CollegeAdmissionHistoryRead,
    CollegeDetailRead,
    CollegeMajorProfileRead,
    CollegeProfileDetailRead,
    CollegeYearSummaryRead,
    GaokaoProfileSourceRead,
    MajorAdmissionHistoryRead,
    MajorDetailRead,
    MajorProfileDetailRead,
)

from ._recommendations_shared import (
    _serialize_admission_record,
    _serialize_college,
    _serialize_enrollment_plan,
    _serialize_major,
    _serialize_major_employment_mapping,
)


DETAIL_HISTORY_LIMIT = 80
DETAIL_PREVIEW_LIMIT = 20


def get_college_detail(session: Session, college_id: int) -> CollegeDetailRead:
    college = get_college(session, college_id)
    if college is None:
        raise HTTPException(status_code=404, detail="院校不存在")
    profile = session.scalar(
        select(CollegeProfileDetail).where(
            CollegeProfileDetail.college_id == college_id,
            CollegeProfileDetail.is_active.is_(True),
        )
    )
    year_summaries = session.scalars(
        select(CollegeYearSummary)
        .where(
            CollegeYearSummary.college_id == college_id,
            CollegeYearSummary.is_active.is_(True),
        )
        .order_by(desc(CollegeYearSummary.year), CollegeYearSummary.id)
    ).all()
    major_profiles = session.scalars(
        select(CollegeMajorProfile)
        .options(
            joinedload(CollegeMajorProfile.college),
            joinedload(CollegeMajorProfile.major),
        )
        .where(
            CollegeMajorProfile.college_id == college_id,
            CollegeMajorProfile.is_active.is_(True),
        )
        .order_by(CollegeMajorProfile.id)
    ).unique().all()
    admissions = _list_college_admissions(session, college_id=college_id, limit=DETAIL_PREVIEW_LIMIT)
    plans = _list_college_plans(session, college_id=college_id, limit=DETAIL_PREVIEW_LIMIT)
    return CollegeDetailRead(
        college=_serialize_college(college),
        profile=_serialize_college_profile(profile) if profile else None,
        year_summaries=[_serialize_college_year_summary(item) for item in year_summaries],
        major_profiles=[_serialize_college_major_profile(item) for item in major_profiles],
        recent_admissions=[_serialize_admission_record(item) for item in admissions],
        recent_plans=[_serialize_enrollment_plan(item) for item in plans],
        source_documents=_build_sources(
            session,
            profile,
            *year_summaries,
            *major_profiles,
            *admissions,
            *plans,
        ),
    )


def get_college_admission_history(session: Session, college_id: int) -> CollegeAdmissionHistoryRead:
    college = get_college(session, college_id)
    if college is None:
        raise HTTPException(status_code=404, detail="院校不存在")
    admissions = _list_college_admissions(session, college_id=college_id, limit=DETAIL_HISTORY_LIMIT)
    plans = _list_college_plans(session, college_id=college_id, limit=DETAIL_HISTORY_LIMIT)
    return CollegeAdmissionHistoryRead(
        college_id=college.id,
        college_name=college.name,
        admissions=[_serialize_admission_record(item) for item in admissions],
        plans=[_serialize_enrollment_plan(item) for item in plans],
    )


def get_major_detail(session: Session, major_id: int) -> MajorDetailRead:
    major = get_major(session, major_id)
    if major is None:
        raise HTTPException(status_code=404, detail="专业不存在")
    profile = session.scalar(
        select(MajorProfileDetail).where(
            MajorProfileDetail.major_id == major_id,
            MajorProfileDetail.is_active.is_(True),
        )
    )
    college_profiles = session.scalars(
        select(CollegeMajorProfile)
        .options(
            joinedload(CollegeMajorProfile.college),
            joinedload(CollegeMajorProfile.major),
        )
        .where(
            CollegeMajorProfile.major_id == major_id,
            CollegeMajorProfile.is_active.is_(True),
        )
        .order_by(CollegeMajorProfile.id)
    ).unique().all()
    mappings = session.scalars(
        select(MajorEmploymentMapping)
        .options(
            joinedload(MajorEmploymentMapping.major),
            joinedload(MajorEmploymentMapping.direction),
        )
        .where(
            MajorEmploymentMapping.major_id == major_id,
            MajorEmploymentMapping.is_active.is_(True),
        )
        .order_by(MajorEmploymentMapping.strength, MajorEmploymentMapping.id.desc())
    ).unique().all()
    admissions = _list_major_admissions(session, major_id=major_id, limit=DETAIL_PREVIEW_LIMIT)
    plans = _list_major_plans(session, major_id=major_id, limit=DETAIL_PREVIEW_LIMIT)
    return MajorDetailRead(
        major=_serialize_major(major),
        profile=_serialize_major_profile(profile) if profile else None,
        college_profiles=[_serialize_college_major_profile(item) for item in college_profiles],
        employment_mappings=[_serialize_major_employment_mapping(item) for item in mappings],
        recent_admissions=[_serialize_admission_record(item) for item in admissions],
        recent_plans=[_serialize_enrollment_plan(item) for item in plans],
        subject_requirement_samples=_subject_requirement_samples(plans),
        source_documents=_build_sources(
            session,
            profile,
            *college_profiles,
            *admissions,
            *plans,
        ),
    )


def get_major_admission_history(session: Session, major_id: int) -> MajorAdmissionHistoryRead:
    major = get_major(session, major_id)
    if major is None:
        raise HTTPException(status_code=404, detail="专业不存在")
    admissions = _list_major_admissions(session, major_id=major_id, limit=DETAIL_HISTORY_LIMIT)
    plans = _list_major_plans(session, major_id=major_id, limit=DETAIL_HISTORY_LIMIT)
    return MajorAdmissionHistoryRead(
        major_id=major.id,
        major_name=major.name,
        admissions=[_serialize_admission_record(item) for item in admissions],
        plans=[_serialize_enrollment_plan(item) for item in plans],
    )


def _list_college_admissions(session: Session, *, college_id: int, limit: int) -> list[AdmissionRecord]:
    return session.scalars(
        select(AdmissionRecord)
        .options(joinedload(AdmissionRecord.college), joinedload(AdmissionRecord.major))
        .where(AdmissionRecord.college_id == college_id, AdmissionRecord.is_active.is_(True))
        .order_by(desc(AdmissionRecord.year), AdmissionRecord.batch, AdmissionRecord.id)
        .limit(limit)
    ).unique().all()


def _list_college_plans(session: Session, *, college_id: int, limit: int) -> list[EnrollmentPlan]:
    return session.scalars(
        select(EnrollmentPlan)
        .options(joinedload(EnrollmentPlan.college), joinedload(EnrollmentPlan.major))
        .where(EnrollmentPlan.college_id == college_id, EnrollmentPlan.is_active.is_(True))
        .order_by(desc(EnrollmentPlan.year), EnrollmentPlan.batch, EnrollmentPlan.id)
        .limit(limit)
    ).unique().all()


def _list_major_admissions(session: Session, *, major_id: int, limit: int) -> list[AdmissionRecord]:
    return session.scalars(
        select(AdmissionRecord)
        .options(joinedload(AdmissionRecord.college), joinedload(AdmissionRecord.major))
        .where(AdmissionRecord.major_id == major_id, AdmissionRecord.is_active.is_(True))
        .order_by(desc(AdmissionRecord.year), AdmissionRecord.batch, AdmissionRecord.id)
        .limit(limit)
    ).unique().all()


def _list_major_plans(session: Session, *, major_id: int, limit: int) -> list[EnrollmentPlan]:
    return session.scalars(
        select(EnrollmentPlan)
        .options(joinedload(EnrollmentPlan.college), joinedload(EnrollmentPlan.major))
        .where(EnrollmentPlan.major_id == major_id, EnrollmentPlan.is_active.is_(True))
        .order_by(desc(EnrollmentPlan.year), EnrollmentPlan.batch, EnrollmentPlan.id)
        .limit(limit)
    ).unique().all()


def _serialize_college_profile(item: CollegeProfileDetail) -> CollegeProfileDetailRead:
    return CollegeProfileDetailRead(
        id=item.id,
        college_id=item.college_id,
        enrollment_code=item.enrollment_code,
        authority_department=item.authority_department,
        education_level=item.education_level,
        is_985=item.is_985,
        is_211=item.is_211,
        is_dual_class=item.is_dual_class,
        ruanke_rank=item.ruanke_rank,
        eol_rank=item.eol_rank,
        area=item.area,
        master_program_count=item.master_program_count,
        doctor_program_count=item.doctor_program_count,
        official_website=item.official_website,
        admission_website=item.admission_website,
        phone=item.phone,
        email=item.email,
        address=item.address,
        summary=item.summary,
        source_path=item.source_path,
        source_sha256=item.source_sha256,
        is_active=item.is_active,
    )


def _serialize_college_year_summary(item: CollegeYearSummary) -> CollegeYearSummaryRead:
    return CollegeYearSummaryRead(
        id=item.id,
        college_id=item.college_id,
        province=item.province,
        year=item.year,
        total_plan_count=item.total_plan_count,
        specialty_count=item.specialty_count,
        min_rank=item.min_rank,
        estimated_min_score=item.estimated_min_score,
        source_note=item.source_note,
        source_path=item.source_path,
        source_sha256=item.source_sha256,
        is_active=item.is_active,
    )


def _serialize_major_profile(item: MajorProfileDetail) -> MajorProfileDetailRead:
    return MajorProfileDetailRead(
        id=item.id,
        major_id=item.major_id,
        major_code=item.major_code,
        education_level=item.education_level,
        schooling_years=item.schooling_years,
        direction=item.direction,
        tags_json=item.tags_json or [],
        summary=item.summary,
        source_path=item.source_path,
        source_sha256=item.source_sha256,
        is_active=item.is_active,
    )


def _serialize_college_major_profile(item: CollegeMajorProfile) -> CollegeMajorProfileRead:
    return CollegeMajorProfileRead(
        id=item.id,
        college_id=item.college_id,
        college_name=item.college.name if item.college else None,
        major_id=item.major_id,
        major_name=item.major.name if item.major else None,
        school_major_feature=item.school_major_feature,
        is_national_feature=item.is_national_feature,
        is_provincial_feature=item.is_provincial_feature,
        is_key_major=item.is_key_major,
        schooling_years=item.schooling_years,
        education_level=item.education_level,
        source_path=item.source_path,
        source_sha256=item.source_sha256,
        is_active=item.is_active,
    )


def _subject_requirement_samples(plans: list[EnrollmentPlan]) -> list[str]:
    values: list[str] = []
    seen: set[str] = set()
    for plan in plans:
        value = (plan.subject_requirement or "").strip()
        if value and value not in seen:
            values.append(value)
            seen.add(value)
    return values[:8]


def _build_sources(session: Session, *items: object | None) -> list[GaokaoProfileSourceRead]:
    sources: list[GaokaoProfileSourceRead] = []
    seen_paths: set[tuple[str, str | None]] = set()
    source_document_ids: set[int] = set()
    for item in items:
        if item is None:
            continue
        source_document_id = getattr(item, "source_document_id", None)
        if source_document_id:
            source_document_ids.add(int(source_document_id))
        source_path = getattr(item, "source_path", None) or getattr(item, "local_source_path", None)
        source_sha256 = getattr(item, "source_sha256", None) or getattr(item, "file_sha256", None)
        if source_path:
            key = (str(source_path), str(source_sha256) if source_sha256 else None)
            if key not in seen_paths:
                sources.append(
                    GaokaoProfileSourceRead(
                        source_path=str(source_path),
                        source_sha256=str(source_sha256) if source_sha256 else None,
                        source_type=item.__class__.__tablename__ if hasattr(item.__class__, "__tablename__") else "profile",
                        title=None,
                    )
                )
                seen_paths.add(key)
    if source_document_ids:
        docs = session.scalars(
            select(GaokaoSourceDocument).where(GaokaoSourceDocument.id.in_(sorted(source_document_ids)))
        ).all()
        for doc in docs:
            source_path = doc.local_file_path or doc.url
            key = (str(source_path), doc.file_sha256) if source_path else (f"source_document:{doc.id}", doc.file_sha256)
            if key in seen_paths:
                continue
            sources.append(
                GaokaoProfileSourceRead(
                    source_path=source_path,
                    source_sha256=doc.file_sha256,
                    source_type=doc.source_type,
                    title=doc.title,
                )
            )
            seen_paths.add(key)
    return sources
