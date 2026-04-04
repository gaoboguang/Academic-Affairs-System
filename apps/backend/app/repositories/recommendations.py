from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import Select, and_, desc, func, select
from sqlalchemy.orm import Session, joinedload

from app.models import (
    AdmissionRecord,
    College,
    CollegeAlias,
    CollegeMajor,
    Major,
    RecommendationResult,
    RecommendationScheme,
)


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


def list_admission_candidates(
    session: Session,
    *,
    province: str,
    student_type: str,
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
    if student_type == "general":
        stmt = stmt.where(AdmissionRecord.student_type.in_(["general", "common", ""]))
    else:
        stmt = stmt.where(AdmissionRecord.student_type != "general")
    if subject_requirement:
        stmt = stmt.where(
            (AdmissionRecord.subject_requirement.is_(None))
            | (AdmissionRecord.subject_requirement.contains(subject_requirement))
        )
    stmt = stmt.order_by(desc(AdmissionRecord.year), AdmissionRecord.college_id, AdmissionRecord.major_id)
    return session.scalars(stmt).unique().all()


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
