from __future__ import annotations

from collections.abc import Sequence
from datetime import date

from sqlalchemy import Select, desc, func, select
from sqlalchemy.orm import Session, joinedload

from app.models import StudentGrowthAttachment, StudentGrowthRecord


def build_growth_record_query(
    student_id: int,
    *,
    record_type: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
) -> Select[tuple[StudentGrowthRecord]]:
    stmt = (
        select(StudentGrowthRecord)
        .options(
            joinedload(StudentGrowthRecord.student),
            joinedload(StudentGrowthRecord.attachments)
            .joinedload(StudentGrowthAttachment.stored_file),
        )
        .where(
            StudentGrowthRecord.student_id == student_id,
            StudentGrowthRecord.is_active.is_(True),
        )
    )
    if record_type:
        stmt = stmt.where(StudentGrowthRecord.record_type == record_type)
    if start_date:
        stmt = stmt.where(StudentGrowthRecord.occurred_on >= start_date)
    if end_date:
        stmt = stmt.where(StudentGrowthRecord.occurred_on <= end_date)
    return stmt.order_by(desc(StudentGrowthRecord.occurred_on), desc(StudentGrowthRecord.id))


def list_growth_records(
    session: Session,
    student_id: int,
    *,
    record_type: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
) -> tuple[Sequence[StudentGrowthRecord], int]:
    stmt = build_growth_record_query(student_id, record_type=record_type, start_date=start_date, end_date=end_date)
    total = session.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    return session.scalars(stmt).unique().all(), total


def get_growth_record(session: Session, record_id: int) -> StudentGrowthRecord | None:
    stmt = (
        select(StudentGrowthRecord)
        .options(
            joinedload(StudentGrowthRecord.student),
            joinedload(StudentGrowthRecord.attachments)
            .joinedload(StudentGrowthAttachment.stored_file),
        )
        .where(StudentGrowthRecord.id == record_id)
    )
    return session.scalar(stmt)
