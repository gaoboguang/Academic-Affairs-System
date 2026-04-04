from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import and_, desc, func, select
from sqlalchemy.orm import Session, joinedload

from app.models import (
    Semester,
    TeacherWorkloadExtra,
    TeacherWorkloadResult,
    TimetableBatch,
    TimetableEntry,
    WorkloadRuleItem,
    WorkloadRuleVersion,
)


def list_timetable_batches(session: Session, semester_id: int | None = None) -> Sequence[TimetableBatch]:
    stmt = select(TimetableBatch).options(joinedload(TimetableBatch.semester).joinedload(Semester.academic_year))
    if semester_id:
        stmt = stmt.where(TimetableBatch.semester_id == semester_id)
    stmt = stmt.order_by(desc(TimetableBatch.import_time), desc(TimetableBatch.id))
    return session.scalars(stmt).all()


def get_timetable_batch(session: Session, batch_id: int) -> TimetableBatch | None:
    stmt = (
        select(TimetableBatch)
        .options(joinedload(TimetableBatch.semester).joinedload(Semester.academic_year))
        .where(TimetableBatch.id == batch_id)
    )
    return session.scalar(stmt)


def list_timetable_entries(
    session: Session,
    *,
    batch_id: int,
    unresolved_only: bool = False,
) -> Sequence[TimetableEntry]:
    stmt = (
        select(TimetableEntry)
        .options(
            joinedload(TimetableEntry.teacher),
            joinedload(TimetableEntry.school_class),
            joinedload(TimetableEntry.subject),
        )
        .where(TimetableEntry.batch_id == batch_id)
        .order_by(TimetableEntry.weekday, TimetableEntry.period_no, TimetableEntry.id)
    )
    if unresolved_only:
        stmt = stmt.where(TimetableEntry.mapping_status != "matched")
    return session.scalars(stmt).all()


def get_latest_effective_batch(session: Session, semester_id: int) -> TimetableBatch | None:
    stmt = (
        select(TimetableBatch)
        .where(
            TimetableBatch.semester_id == semester_id,
            TimetableBatch.is_active.is_(True),
            TimetableBatch.status.in_(["completed", "completed_with_unresolved"]),
        )
        .order_by(desc(TimetableBatch.import_time), desc(TimetableBatch.id))
    )
    return session.scalar(stmt)


def list_rule_versions(session: Session) -> Sequence[WorkloadRuleVersion]:
    stmt = (
        select(WorkloadRuleVersion)
        .options(joinedload(WorkloadRuleVersion.semester).joinedload(Semester.academic_year))
        .order_by(desc(WorkloadRuleVersion.is_default), desc(WorkloadRuleVersion.id))
    )
    return session.scalars(stmt).all()


def get_rule_version(session: Session, rule_version_id: int) -> WorkloadRuleVersion | None:
    stmt = (
        select(WorkloadRuleVersion)
        .options(joinedload(WorkloadRuleVersion.semester).joinedload(Semester.academic_year))
        .where(WorkloadRuleVersion.id == rule_version_id)
    )
    return session.scalar(stmt)


def list_rule_items(session: Session, rule_version_id: int) -> Sequence[WorkloadRuleItem]:
    stmt = (
        select(WorkloadRuleItem)
        .where(
            WorkloadRuleItem.rule_version_id == rule_version_id,
            WorkloadRuleItem.is_active.is_(True),
        )
        .order_by(WorkloadRuleItem.dimension_type, WorkloadRuleItem.match_key, WorkloadRuleItem.id)
    )
    return session.scalars(stmt).all()


def list_workload_extras(session: Session, semester_id: int | None = None) -> Sequence[TeacherWorkloadExtra]:
    stmt = select(TeacherWorkloadExtra).options(joinedload(TeacherWorkloadExtra.teacher))
    if semester_id:
        stmt = stmt.where(TeacherWorkloadExtra.semester_id == semester_id)
    stmt = stmt.order_by(desc(TeacherWorkloadExtra.id))
    return session.scalars(stmt).all()


def list_workload_results(
    session: Session,
    *,
    semester_id: int | None = None,
    rule_version_id: int | None = None,
) -> Sequence[TeacherWorkloadResult]:
    stmt = select(TeacherWorkloadResult).options(
        joinedload(TeacherWorkloadResult.teacher),
        joinedload(TeacherWorkloadResult.semester).joinedload(Semester.academic_year),
        joinedload(TeacherWorkloadResult.rule_version),
    )
    conditions = []
    if semester_id:
        conditions.append(TeacherWorkloadResult.semester_id == semester_id)
    if rule_version_id:
        conditions.append(TeacherWorkloadResult.rule_version_id == rule_version_id)
    if conditions:
        stmt = stmt.where(and_(*conditions))
    stmt = stmt.order_by(desc(TeacherWorkloadResult.semester_workload), TeacherWorkloadResult.id)
    return session.scalars(stmt).all()


def get_workload_result(
    session: Session,
    *,
    teacher_id: int,
    semester_id: int,
    rule_version_id: int,
) -> TeacherWorkloadResult | None:
    stmt = select(TeacherWorkloadResult).where(
        TeacherWorkloadResult.teacher_id == teacher_id,
        TeacherWorkloadResult.semester_id == semester_id,
        TeacherWorkloadResult.rule_version_id == rule_version_id,
    )
    return session.scalar(stmt)


def count_batch_entries(session: Session, batch_id: int) -> tuple[int, int]:
    total = session.scalar(
        select(func.count()).select_from(TimetableEntry).where(TimetableEntry.batch_id == batch_id)
    ) or 0
    unresolved = session.scalar(
        select(func.count()).select_from(TimetableEntry).where(
            TimetableEntry.batch_id == batch_id,
            TimetableEntry.mapping_status != "matched",
        )
    ) or 0
    return total, unresolved


def count_workload_results_by_rule_version(session: Session, rule_version_id: int) -> int:
    return session.scalar(
        select(func.count()).select_from(TeacherWorkloadResult).where(
            TeacherWorkloadResult.rule_version_id == rule_version_id
        )
    ) or 0
