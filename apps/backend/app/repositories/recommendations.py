from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import Select, and_, desc, func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.models import (
    AdmissionRecord,
    College,
    CollegeAlias,
    CollegeMajor,
    EmploymentDirection,
    EnrollmentPlan,
    Major,
    MajorEmploymentMapping,
    ProvinceScoreTransformRule,
    ProvinceVolunteerRule,
    RecommendationResult,
    RecommendationScheme,
    SpecialTypeRule,
    SubjectRequirementDict,
    VolunteerDraft,
    VolunteerDraftItem,
)


def build_compatible_exam_modes(exam_mode: str) -> tuple[str, ...]:
    compatible_modes = {exam_mode}
    if exam_mode in {"物理类", "历史类"}:
        compatible_modes.add("3+1+2")
    elif exam_mode == "3+1+2":
        compatible_modes.update({"物理类", "历史类"})
    return tuple(sorted(compatible_modes))


def build_college_query(
    *,
    keyword: str | None = None,
    province: str | None = None,
    supports_art: bool | None = None,
) -> Select[tuple[College]]:
    stmt = select(College).options(joinedload(College.aliases)).where(College.is_active.is_(True))
    if keyword:
        stmt = stmt.where(College.name.contains(keyword))
    if province:
        stmt = stmt.where(College.province == province)
    if supports_art is not None:
        stmt = stmt.where(College.supports_art == supports_art)
    return stmt.order_by(College.name, College.id)


def list_colleges(
    session: Session,
    *,
    keyword: str | None = None,
    province: str | None = None,
    supports_art: bool | None = None,
) -> Sequence[College]:
    return session.scalars(
        build_college_query(keyword=keyword, province=province, supports_art=supports_art)
    ).unique().all()


def get_college(session: Session, college_id: int) -> College | None:
    stmt = (
        select(College)
        .options(joinedload(College.aliases))
        .where(College.id == college_id)
    )
    return session.scalar(stmt)


def get_college_by_name(session: Session, name: str) -> College | None:
    stmt = (
        select(College)
        .options(joinedload(College.aliases))
        .where(College.name == name)
    )
    return session.scalar(stmt)


def list_majors(
    session: Session,
    *,
    keyword: str | None = None,
    is_art_related: bool | None = None,
) -> Sequence[Major]:
    stmt = select(Major).where(Major.is_active.is_(True))
    if keyword:
        stmt = stmt.where(Major.name.contains(keyword))
    if is_art_related is not None:
        stmt = stmt.where(Major.is_art_related == is_art_related)
    stmt = stmt.order_by(Major.name, Major.id)
    return session.scalars(stmt).all()


def get_major(session: Session, major_id: int) -> Major | None:
    return session.get(Major, major_id)


def get_major_by_name(session: Session, name: str) -> Major | None:
    return session.scalar(select(Major).where(Major.name == name))


def list_employment_directions(
    session: Session,
    *,
    keyword: str | None = None,
    category: str | None = None,
) -> Sequence[EmploymentDirection]:
    stmt = select(EmploymentDirection).where(EmploymentDirection.is_active.is_(True))
    if keyword:
        stmt = stmt.where(EmploymentDirection.name.contains(keyword))
    if category:
        stmt = stmt.where(EmploymentDirection.category == category)
    stmt = stmt.order_by(EmploymentDirection.name, EmploymentDirection.id)
    return session.scalars(stmt).all()


def get_employment_direction(session: Session, direction_id: int) -> EmploymentDirection | None:
    return session.get(EmploymentDirection, direction_id)


def get_employment_direction_by_name(session: Session, name: str) -> EmploymentDirection | None:
    return session.scalar(select(EmploymentDirection).where(EmploymentDirection.name == name))


def list_major_employment_mappings(
    session: Session,
    *,
    major_id: int | None = None,
    direction_id: int | None = None,
    strength: str | None = None,
    keyword: str | None = None,
) -> Sequence[MajorEmploymentMapping]:
    stmt = (
        select(MajorEmploymentMapping)
        .options(
            joinedload(MajorEmploymentMapping.major),
            joinedload(MajorEmploymentMapping.direction),
        )
        .where(MajorEmploymentMapping.is_active.is_(True))
    )
    conditions = []
    if major_id:
        conditions.append(MajorEmploymentMapping.major_id == major_id)
    if direction_id:
        conditions.append(MajorEmploymentMapping.direction_id == direction_id)
    if strength:
        conditions.append(MajorEmploymentMapping.strength == strength)
    if keyword:
        conditions.append(
            or_(
                MajorEmploymentMapping.major.has(Major.name.contains(keyword)),
                MajorEmploymentMapping.direction.has(EmploymentDirection.name.contains(keyword)),
            )
        )
    if conditions:
        stmt = stmt.where(and_(*conditions))
    stmt = stmt.order_by(MajorEmploymentMapping.strength, MajorEmploymentMapping.id.desc())
    return session.scalars(stmt).unique().all()


def list_major_employment_mappings_for_majors(
    session: Session,
    *,
    major_ids: list[int],
    direction_ids: list[int] | None = None,
) -> Sequence[MajorEmploymentMapping]:
    if not major_ids:
        return []
    stmt = (
        select(MajorEmploymentMapping)
        .options(
            joinedload(MajorEmploymentMapping.major),
            joinedload(MajorEmploymentMapping.direction),
        )
        .where(
            MajorEmploymentMapping.is_active.is_(True),
            MajorEmploymentMapping.major_id.in_(sorted(set(major_ids))),
        )
    )
    if direction_ids:
        stmt = stmt.where(MajorEmploymentMapping.direction_id.in_(sorted(set(direction_ids))))
    stmt = stmt.order_by(MajorEmploymentMapping.major_id, MajorEmploymentMapping.id.desc())
    return session.scalars(stmt).unique().all()


def get_major_employment_mapping(session: Session, mapping_id: int) -> MajorEmploymentMapping | None:
    stmt = (
        select(MajorEmploymentMapping)
        .options(
            joinedload(MajorEmploymentMapping.major),
            joinedload(MajorEmploymentMapping.direction),
        )
        .where(MajorEmploymentMapping.id == mapping_id)
    )
    return session.scalar(stmt)


def get_major_employment_mapping_by_key(
    session: Session,
    *,
    major_id: int,
    direction_id: int,
) -> MajorEmploymentMapping | None:
    stmt = select(MajorEmploymentMapping).where(
        MajorEmploymentMapping.major_id == major_id,
        MajorEmploymentMapping.direction_id == direction_id,
    )
    return session.scalar(stmt)


def ensure_college_major(session: Session, college_id: int, major_id: int) -> CollegeMajor:
    stmt = select(CollegeMajor).where(
        CollegeMajor.college_id == college_id,
        CollegeMajor.major_id == major_id,
    )
    existing = session.scalar(stmt)
    if existing:
        return existing
    mapping = CollegeMajor(college_id=college_id, major_id=major_id)
    session.add(mapping)
    session.flush()
    return mapping


def list_admission_records(
    session: Session,
    *,
    year: int | None = None,
    province: str | None = None,
    college_id: int | None = None,
    student_type: str | None = None,
) -> Sequence[AdmissionRecord]:
    stmt = (
        select(AdmissionRecord)
        .options(
            joinedload(AdmissionRecord.college),
            joinedload(AdmissionRecord.major),
        )
        .where(AdmissionRecord.is_active.is_(True))
    )
    conditions = []
    if year:
        conditions.append(AdmissionRecord.year == year)
    if province:
        conditions.append(AdmissionRecord.province == province)
    if college_id:
        conditions.append(AdmissionRecord.college_id == college_id)
    if student_type:
        conditions.append(AdmissionRecord.student_type == student_type)
    if conditions:
        stmt = stmt.where(and_(*conditions))
    stmt = stmt.order_by(desc(AdmissionRecord.year), AdmissionRecord.college_id, AdmissionRecord.id)
    return session.scalars(stmt).all()


def get_admission_record_by_key(
    session: Session,
    *,
    year: int,
    province: str,
    batch: str,
    college_id: int,
    major_id: int | None,
    student_type: str,
    art_track: str | None,
) -> AdmissionRecord | None:
    stmt = select(AdmissionRecord).where(
        AdmissionRecord.year == year,
        AdmissionRecord.province == province,
        AdmissionRecord.batch == batch,
        AdmissionRecord.college_id == college_id,
        AdmissionRecord.major_id == major_id,
        AdmissionRecord.student_type == student_type,
        AdmissionRecord.art_track == art_track,
    )
    return session.scalar(stmt)


def list_enrollment_plans(
    session: Session,
    *,
    year: int | None = None,
    province: str | None = None,
    batch: str | None = None,
    college_id: int | None = None,
    student_type: str | None = None,
    keyword: str | None = None,
) -> Sequence[EnrollmentPlan]:
    stmt = (
        select(EnrollmentPlan)
        .options(
            joinedload(EnrollmentPlan.college),
            joinedload(EnrollmentPlan.major),
        )
        .where(EnrollmentPlan.is_active.is_(True))
    )
    conditions = []
    if year:
        conditions.append(EnrollmentPlan.year == year)
    if province:
        conditions.append(EnrollmentPlan.province == province)
    if batch:
        conditions.append(EnrollmentPlan.batch == batch)
    if college_id:
        conditions.append(EnrollmentPlan.college_id == college_id)
    if student_type:
        conditions.append(EnrollmentPlan.student_type == student_type)
    if keyword:
        conditions.append(
            or_(
                EnrollmentPlan.college.has(College.name.contains(keyword)),
                EnrollmentPlan.major.has(Major.name.contains(keyword)),
                EnrollmentPlan.major_name_snapshot.contains(keyword),
                EnrollmentPlan.major_group_code.contains(keyword),
            )
        )
    if conditions:
        stmt = stmt.where(and_(*conditions))
    stmt = stmt.order_by(
        desc(EnrollmentPlan.year),
        EnrollmentPlan.province,
        EnrollmentPlan.batch,
        EnrollmentPlan.college_id,
        EnrollmentPlan.major_group_code,
        EnrollmentPlan.id,
    )
    return session.scalars(stmt).unique().all()


def get_enrollment_plan_by_key(
    session: Session,
    *,
    year: int,
    province: str,
    batch: str,
    exam_mode: str,
    college_id: int,
    major_group_code: str,
    major_name_snapshot: str,
    student_type: str,
) -> EnrollmentPlan | None:
    stmt = select(EnrollmentPlan).where(
        EnrollmentPlan.year == year,
        EnrollmentPlan.province == province,
        EnrollmentPlan.batch == batch,
        EnrollmentPlan.exam_mode == exam_mode,
        EnrollmentPlan.college_id == college_id,
        EnrollmentPlan.major_group_code == major_group_code,
        EnrollmentPlan.major_name_snapshot == major_name_snapshot,
        EnrollmentPlan.student_type == student_type,
    )
    return session.scalar(stmt)


def list_admission_candidates(
    session: Session,
    *,
    province: str,
    student_type: str,
    batch: str | None = None,
    subject_requirement: str | None = None,
) -> Sequence[AdmissionRecord]:
    stmt = (
        select(AdmissionRecord)
        .options(
            joinedload(AdmissionRecord.college).joinedload(College.aliases),
            joinedload(AdmissionRecord.major),
        )
        .where(
            AdmissionRecord.province == province,
            AdmissionRecord.is_active.is_(True),
        )
    )
    if batch:
        stmt = stmt.where(AdmissionRecord.batch == batch)
    stmt = stmt.where(AdmissionRecord.student_type.in_(_resolve_candidate_student_type_values(student_type)))
    if subject_requirement:
        stmt = stmt.where(
            (AdmissionRecord.subject_requirement.is_(None))
            | (AdmissionRecord.subject_requirement.contains(subject_requirement))
        )
    stmt = stmt.order_by(desc(AdmissionRecord.year), AdmissionRecord.college_id, AdmissionRecord.major_id)
    return session.scalars(stmt).unique().all()


def list_enrollment_plan_candidates(
    session: Session,
    *,
    year: int,
    province: str,
    student_type: str,
    batch: str | None = None,
    exam_mode: str | None = None,
    subject_requirement: str | None = None,
) -> Sequence[EnrollmentPlan]:
    stmt = (
        select(EnrollmentPlan)
        .options(
            joinedload(EnrollmentPlan.college).joinedload(College.aliases),
            joinedload(EnrollmentPlan.major),
        )
        .where(
            EnrollmentPlan.year == year,
            EnrollmentPlan.province == province,
            EnrollmentPlan.is_active.is_(True),
        )
    )
    if batch:
        stmt = stmt.where(EnrollmentPlan.batch == batch)
    if exam_mode:
        stmt = stmt.where(EnrollmentPlan.exam_mode.in_(build_compatible_exam_modes(exam_mode)))
    stmt = stmt.where(EnrollmentPlan.student_type.in_(_resolve_candidate_student_type_values(student_type)))
    if subject_requirement:
        stmt = stmt.where(
            (EnrollmentPlan.subject_requirement.is_(None))
            | (EnrollmentPlan.subject_requirement.contains(subject_requirement))
        )
    stmt = stmt.order_by(
        EnrollmentPlan.batch,
        EnrollmentPlan.exam_mode,
        EnrollmentPlan.college_id,
        EnrollmentPlan.major_group_code,
        EnrollmentPlan.id,
    )
    return session.scalars(stmt).unique().all()


def _resolve_candidate_student_type_values(student_type: str) -> tuple[str, ...]:
    normalized = (student_type or "").strip()
    if normalized in {"", "general", "repeat"}:
        return ("general", "common", "")
    return (normalized,)


def list_province_volunteer_rules(
    session: Session,
    *,
    province: str | None = None,
    year: int | None = None,
    exam_mode: str | None = None,
    candidate_type: str | None = None,
) -> Sequence[ProvinceVolunteerRule]:
    stmt = select(ProvinceVolunteerRule).where(ProvinceVolunteerRule.is_active.is_(True))
    conditions = []
    if province:
        conditions.append(ProvinceVolunteerRule.province == province)
    if year:
        conditions.append(ProvinceVolunteerRule.year == year)
    if exam_mode:
        conditions.append(ProvinceVolunteerRule.exam_mode == exam_mode)
    if candidate_type is not None:
        conditions.append(ProvinceVolunteerRule.candidate_type == candidate_type)
    if conditions:
        stmt = stmt.where(and_(*conditions))
    stmt = stmt.order_by(
        desc(ProvinceVolunteerRule.year),
        ProvinceVolunteerRule.province,
        ProvinceVolunteerRule.exam_mode,
        ProvinceVolunteerRule.candidate_type,
        ProvinceVolunteerRule.batch_order.is_(None),
        ProvinceVolunteerRule.batch_order,
        ProvinceVolunteerRule.batch,
        ProvinceVolunteerRule.id,
    )
    return session.scalars(stmt).all()


def get_province_volunteer_rule(session: Session, rule_id: int) -> ProvinceVolunteerRule | None:
    return session.get(ProvinceVolunteerRule, rule_id)


def get_province_volunteer_rule_by_key(
    session: Session,
    *,
    province: str,
    year: int,
    exam_mode: str,
    batch: str,
    candidate_type: str,
) -> ProvinceVolunteerRule | None:
    stmt = select(ProvinceVolunteerRule).where(
        ProvinceVolunteerRule.province == province,
        ProvinceVolunteerRule.year == year,
        ProvinceVolunteerRule.exam_mode == exam_mode,
        ProvinceVolunteerRule.batch == batch,
        ProvinceVolunteerRule.candidate_type == candidate_type,
    )
    return session.scalar(stmt)


def list_province_score_transform_rules(
    session: Session,
    *,
    province: str | None = None,
    year: int | None = None,
    exam_mode: str | None = None,
    subject_name: str | None = None,
) -> Sequence[ProvinceScoreTransformRule]:
    stmt = select(ProvinceScoreTransformRule).where(ProvinceScoreTransformRule.is_active.is_(True))
    conditions = []
    if province:
        conditions.append(ProvinceScoreTransformRule.province == province)
    if year:
        conditions.append(ProvinceScoreTransformRule.year == year)
    if exam_mode is not None:
        conditions.append(ProvinceScoreTransformRule.exam_mode == exam_mode)
    if subject_name:
        conditions.append(ProvinceScoreTransformRule.subject_name == subject_name)
    if conditions:
        stmt = stmt.where(and_(*conditions))
    stmt = stmt.order_by(
        desc(ProvinceScoreTransformRule.year),
        ProvinceScoreTransformRule.province,
        ProvinceScoreTransformRule.exam_mode,
        ProvinceScoreTransformRule.sort_order.is_(None),
        ProvinceScoreTransformRule.sort_order,
        ProvinceScoreTransformRule.subject_name,
        ProvinceScoreTransformRule.id,
    )
    return session.scalars(stmt).all()


def get_province_score_transform_rule(
    session: Session,
    rule_id: int,
) -> ProvinceScoreTransformRule | None:
    return session.get(ProvinceScoreTransformRule, rule_id)


def get_province_score_transform_rule_by_key(
    session: Session,
    *,
    province: str,
    year: int,
    exam_mode: str,
    subject_name: str,
) -> ProvinceScoreTransformRule | None:
    stmt = select(ProvinceScoreTransformRule).where(
        ProvinceScoreTransformRule.province == province,
        ProvinceScoreTransformRule.year == year,
        ProvinceScoreTransformRule.exam_mode == exam_mode,
        ProvinceScoreTransformRule.subject_name == subject_name,
    )
    return session.scalar(stmt)


def list_subject_requirement_dicts(
    session: Session,
    *,
    province: str | None = None,
    year: int | None = None,
    exam_mode: str | None = None,
    requirement_code: str | None = None,
) -> Sequence[SubjectRequirementDict]:
    stmt = select(SubjectRequirementDict).where(SubjectRequirementDict.is_active.is_(True))
    conditions = []
    if province:
        conditions.append(SubjectRequirementDict.province == province)
    if year:
        conditions.append(SubjectRequirementDict.year == year)
    if exam_mode is not None:
        conditions.append(SubjectRequirementDict.exam_mode == exam_mode)
    if requirement_code:
        conditions.append(SubjectRequirementDict.requirement_code == requirement_code)
    if conditions:
        stmt = stmt.where(and_(*conditions))
    stmt = stmt.order_by(
        desc(SubjectRequirementDict.year),
        SubjectRequirementDict.province,
        SubjectRequirementDict.exam_mode,
        SubjectRequirementDict.sort_order.is_(None),
        SubjectRequirementDict.sort_order,
        SubjectRequirementDict.requirement_text,
        SubjectRequirementDict.id,
    )
    return session.scalars(stmt).all()


def get_subject_requirement_dict(
    session: Session,
    dict_id: int,
) -> SubjectRequirementDict | None:
    return session.get(SubjectRequirementDict, dict_id)


def get_subject_requirement_dict_by_key(
    session: Session,
    *,
    province: str,
    year: int,
    exam_mode: str,
    requirement_code: str,
) -> SubjectRequirementDict | None:
    stmt = select(SubjectRequirementDict).where(
        SubjectRequirementDict.province == province,
        SubjectRequirementDict.year == year,
        SubjectRequirementDict.exam_mode == exam_mode,
        SubjectRequirementDict.requirement_code == requirement_code,
    )
    return session.scalar(stmt)


def list_special_type_rules(
    session: Session,
    *,
    province: str | None = None,
    year: int | None = None,
    student_type: str | None = None,
) -> Sequence[SpecialTypeRule]:
    stmt = select(SpecialTypeRule).where(SpecialTypeRule.is_active.is_(True))
    conditions = []
    if province:
        conditions.append(SpecialTypeRule.province == province)
    if year:
        conditions.append(SpecialTypeRule.year == year)
    if student_type:
        conditions.append(SpecialTypeRule.student_type == student_type)
    if conditions:
        stmt = stmt.where(and_(*conditions))
    stmt = stmt.order_by(
        desc(SpecialTypeRule.year),
        SpecialTypeRule.province,
        SpecialTypeRule.student_type,
        SpecialTypeRule.sort_order.is_(None),
        SpecialTypeRule.sort_order,
        SpecialTypeRule.category_code,
        SpecialTypeRule.id,
    )
    return session.scalars(stmt).all()


def get_special_type_rule(
    session: Session,
    rule_id: int,
) -> SpecialTypeRule | None:
    return session.get(SpecialTypeRule, rule_id)


def get_special_type_rule_by_key(
    session: Session,
    *,
    province: str,
    year: int,
    student_type: str,
    category_code: str,
) -> SpecialTypeRule | None:
    stmt = select(SpecialTypeRule).where(
        SpecialTypeRule.province == province,
        SpecialTypeRule.year == year,
        SpecialTypeRule.student_type == student_type,
        SpecialTypeRule.category_code == category_code,
    )
    return session.scalar(stmt)


def list_volunteer_drafts(
    session: Session,
    *,
    student_id: int | None = None,
    exam_id: int | None = None,
) -> Sequence[VolunteerDraft]:
    stmt = (
        select(VolunteerDraft)
        .options(
            joinedload(VolunteerDraft.student),
            joinedload(VolunteerDraft.exam),
            joinedload(VolunteerDraft.items),
        )
        .where(VolunteerDraft.is_active.is_(True))
    )
    if student_id:
        stmt = stmt.where(VolunteerDraft.student_id == student_id)
    if exam_id:
        stmt = stmt.where(VolunteerDraft.exam_id == exam_id)
    stmt = stmt.order_by(desc(VolunteerDraft.updated_at), desc(VolunteerDraft.id))
    return session.scalars(stmt).unique().all()


def get_volunteer_draft(session: Session, draft_id: int) -> VolunteerDraft | None:
    stmt = (
        select(VolunteerDraft)
        .options(
            joinedload(VolunteerDraft.student),
            joinedload(VolunteerDraft.exam),
            joinedload(VolunteerDraft.items),
        )
        .where(VolunteerDraft.id == draft_id)
    )
    return session.scalar(stmt)


def replace_volunteer_draft_items(
    session: Session,
    draft: VolunteerDraft,
    *,
    items: list[tuple[int, int | None, dict]],
) -> None:
    for item in list(draft.items):
        session.delete(item)
    session.flush()

    draft.items = []
    for order, plan_id, candidate_snapshot_json in items:
        draft.items.append(
            VolunteerDraftItem(
                sort_order=order,
                plan_id=plan_id,
                candidate_snapshot_json=candidate_snapshot_json,
            )
        )
    session.flush()


def get_scheme(session: Session, scheme_id: int) -> RecommendationScheme | None:
    stmt = (
        select(RecommendationScheme)
        .options(joinedload(RecommendationScheme.results))
        .where(RecommendationScheme.id == scheme_id)
    )
    return session.scalar(stmt)


def list_recommendation_results(
    session: Session,
    *,
    student_id: int | None = None,
    scheme_id: int | None = None,
) -> Sequence[RecommendationResult]:
    stmt = select(RecommendationResult).options(
        joinedload(RecommendationResult.student),
        joinedload(RecommendationResult.college),
        joinedload(RecommendationResult.major),
        joinedload(RecommendationResult.scheme),
    )
    conditions = []
    if student_id:
        conditions.append(RecommendationResult.student_id == student_id)
    if scheme_id:
        conditions.append(RecommendationResult.scheme_id == scheme_id)
    if conditions:
        stmt = stmt.where(and_(*conditions))
    stmt = stmt.order_by(desc(RecommendationResult.generated_at), RecommendationResult.result_type, RecommendationResult.id)
    return session.scalars(stmt).all()


def list_recommendation_history_rows(session: Session, student_id: int | None = None) -> Sequence[tuple]:
    stmt = (
        select(
            RecommendationResult.scheme_id,
            RecommendationScheme.name,
            RecommendationResult.student_id,
            func.max(RecommendationResult.generated_at),
            func.count(),
        )
        .join(RecommendationScheme, RecommendationResult.scheme_id == RecommendationScheme.id)
        .group_by(
            RecommendationResult.scheme_id,
            RecommendationScheme.name,
            RecommendationResult.student_id,
        )
        .order_by(desc(func.max(RecommendationResult.generated_at)))
    )
    if student_id:
        stmt = stmt.where(RecommendationResult.student_id == student_id)
    return session.execute(stmt).all()
