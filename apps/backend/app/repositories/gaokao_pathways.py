from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import GaokaoPathway, GaokaoPathwayRule, StudentPathwayEvaluation, StudentPathwayProfile


def list_pathways(
    session: Session,
    *,
    province: str | None = None,
    include_inactive: bool = False,
) -> Sequence[GaokaoPathway]:
    stmt = select(GaokaoPathway).options(selectinload(GaokaoPathway.rules))
    if province:
        stmt = stmt.where(GaokaoPathway.province == province)
    if not include_inactive:
        stmt = stmt.where(GaokaoPathway.is_active.is_(True))
    stmt = stmt.order_by(GaokaoPathway.pathway_group, GaokaoPathway.id)
    return session.scalars(stmt).unique().all()


def get_pathway(session: Session, pathway_id: int) -> GaokaoPathway | None:
    stmt = (
        select(GaokaoPathway)
        .options(selectinload(GaokaoPathway.rules))
        .where(GaokaoPathway.id == pathway_id)
    )
    return session.scalar(stmt)


def get_pathway_by_code(
    session: Session,
    *,
    province: str,
    pathway_code: str,
) -> GaokaoPathway | None:
    stmt = (
        select(GaokaoPathway)
        .options(selectinload(GaokaoPathway.rules))
        .where(
            GaokaoPathway.province == province,
            GaokaoPathway.pathway_code == pathway_code,
        )
    )
    return session.scalar(stmt)


def list_pathway_rules(
    session: Session,
    *,
    pathway_id: int,
    include_inactive: bool = False,
) -> Sequence[GaokaoPathwayRule]:
    stmt = select(GaokaoPathwayRule).where(GaokaoPathwayRule.pathway_id == pathway_id)
    if not include_inactive:
        stmt = stmt.where(GaokaoPathwayRule.is_active.is_(True))
    stmt = stmt.order_by(GaokaoPathwayRule.rule_type, GaokaoPathwayRule.id)
    return session.scalars(stmt).all()


def get_pathway_rule_by_code(
    session: Session,
    *,
    pathway_id: int,
    rule_code: str,
) -> GaokaoPathwayRule | None:
    return session.scalar(
        select(GaokaoPathwayRule).where(
            GaokaoPathwayRule.pathway_id == pathway_id,
            GaokaoPathwayRule.rule_code == rule_code,
        )
    )


def get_student_pathway_profile(
    session: Session,
    *,
    student_id: int,
    province: str = "山东",
) -> StudentPathwayProfile | None:
    return session.scalar(
        select(StudentPathwayProfile).where(
            StudentPathwayProfile.student_id == student_id,
            StudentPathwayProfile.province == province,
            StudentPathwayProfile.is_active.is_(True),
        )
    )


def get_student_pathway_evaluation(
    session: Session,
    *,
    student_id: int,
    pathway_id: int,
    target_year: int,
) -> StudentPathwayEvaluation | None:
    return session.scalar(
        select(StudentPathwayEvaluation).where(
            StudentPathwayEvaluation.student_id == student_id,
            StudentPathwayEvaluation.pathway_id == pathway_id,
            StudentPathwayEvaluation.target_year == target_year,
        )
    )
