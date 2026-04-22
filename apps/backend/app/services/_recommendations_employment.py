from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import EmploymentDirection, MajorEmploymentMapping
from app.repositories.recommendations import (
    get_employment_direction,
    get_employment_direction_by_name,
    get_major,
    get_major_employment_mapping,
    get_major_employment_mapping_by_key,
    list_employment_directions as repo_list_employment_directions,
    list_major_employment_mappings as repo_list_major_employment_mappings,
)
from app.repositories.system import write_audit_log
from app.schemas.recommendation import (
    EmploymentDirectionPayload,
    EmploymentDirectionRead,
    MajorEmploymentMappingPayload,
    MajorEmploymentMappingRead,
)

from ._recommendations_shared import _serialize_employment_direction, _serialize_major_employment_mapping


employment_mapping_strength_options = {"core", "high", "medium", "transferable"}


def list_employment_directions(
    session: Session,
    *,
    keyword: str | None = None,
    category: str | None = None,
) -> list[EmploymentDirectionRead]:
    return [
        _serialize_employment_direction(item)
        for item in repo_list_employment_directions(session, keyword=keyword, category=category)
    ]


def create_employment_direction(session: Session, payload: EmploymentDirectionPayload) -> EmploymentDirectionRead:
    existing = get_employment_direction_by_name(session, payload.name)
    if existing:
        raise HTTPException(status_code=400, detail="就业方向名称已存在")
    item = EmploymentDirection(name=payload.name.strip())
    session.add(item)
    session.flush()
    _apply_employment_direction_payload(item, payload)
    write_audit_log(
        session,
        module="recommendations",
        action="create_employment_direction",
        target_type="employment_direction",
        target_id=str(item.id),
    )
    session.refresh(item)
    return _serialize_employment_direction(item)


def update_employment_direction(
    session: Session,
    direction_id: int,
    payload: EmploymentDirectionPayload,
) -> EmploymentDirectionRead:
    item = get_employment_direction(session, direction_id)
    if not item:
        raise HTTPException(status_code=404, detail="就业方向不存在")
    existing = get_employment_direction_by_name(session, payload.name)
    if existing and existing.id != direction_id:
        raise HTTPException(status_code=400, detail="就业方向名称已存在")
    _apply_employment_direction_payload(item, payload)
    write_audit_log(
        session,
        module="recommendations",
        action="update_employment_direction",
        target_type="employment_direction",
        target_id=str(item.id),
    )
    session.refresh(item)
    return _serialize_employment_direction(item)


def list_major_employment_mappings(
    session: Session,
    *,
    major_id: int | None = None,
    direction_id: int | None = None,
    strength: str | None = None,
    keyword: str | None = None,
) -> list[MajorEmploymentMappingRead]:
    return [
        _serialize_major_employment_mapping(item)
        for item in repo_list_major_employment_mappings(
            session,
            major_id=major_id,
            direction_id=direction_id,
            strength=strength,
            keyword=keyword,
        )
    ]


def create_major_employment_mapping(
    session: Session,
    payload: MajorEmploymentMappingPayload,
) -> MajorEmploymentMappingRead:
    _validate_mapping_payload(session, payload)
    existing = get_major_employment_mapping_by_key(
        session,
        major_id=payload.major_id,
        direction_id=payload.direction_id,
    )
    if existing:
        raise HTTPException(status_code=400, detail="该专业与就业方向的映射已存在")
    item = MajorEmploymentMapping(major_id=payload.major_id, direction_id=payload.direction_id)
    session.add(item)
    session.flush()
    _apply_major_employment_mapping_payload(item, payload)
    write_audit_log(
        session,
        module="recommendations",
        action="create_major_employment_mapping",
        target_type="major_employment_mapping",
        target_id=str(item.id),
    )
    session.refresh(item)
    return _serialize_major_employment_mapping(get_major_employment_mapping(session, item.id) or item)


def update_major_employment_mapping(
    session: Session,
    mapping_id: int,
    payload: MajorEmploymentMappingPayload,
) -> MajorEmploymentMappingRead:
    item = get_major_employment_mapping(session, mapping_id)
    if not item:
        raise HTTPException(status_code=404, detail="专业就业映射不存在")
    _validate_mapping_payload(session, payload)
    existing = get_major_employment_mapping_by_key(
        session,
        major_id=payload.major_id,
        direction_id=payload.direction_id,
    )
    if existing and existing.id != mapping_id:
        raise HTTPException(status_code=400, detail="该专业与就业方向的映射已存在")
    _apply_major_employment_mapping_payload(item, payload)
    write_audit_log(
        session,
        module="recommendations",
        action="update_major_employment_mapping",
        target_type="major_employment_mapping",
        target_id=str(item.id),
    )
    session.refresh(item)
    return _serialize_major_employment_mapping(get_major_employment_mapping(session, item.id) or item)


def _apply_employment_direction_payload(item: EmploymentDirection, payload: EmploymentDirectionPayload) -> None:
    item.name = payload.name.strip()
    item.category = payload.category
    item.alias_names_json = payload.alias_names_json or None
    item.description = payload.description
    item.common_job_types_json = payload.common_job_types_json or None
    item.common_industries_json = payload.common_industries_json or None
    item.prefers_postgraduate = payload.prefers_postgraduate
    item.requires_certificate = payload.requires_certificate
    item.requires_long_cycle = payload.requires_long_cycle
    item.supports_art = payload.supports_art
    item.risk_note = payload.risk_note
    item.source_note = payload.source_note
    item.is_active = payload.is_active


def _validate_mapping_payload(session: Session, payload: MajorEmploymentMappingPayload) -> None:
    if payload.strength not in employment_mapping_strength_options:
        raise HTTPException(status_code=400, detail="映射强度不合法")
    if not get_major(session, payload.major_id):
        raise HTTPException(status_code=404, detail="专业不存在")
    if not get_employment_direction(session, payload.direction_id):
        raise HTTPException(status_code=404, detail="就业方向不存在")


def _apply_major_employment_mapping_payload(item: MajorEmploymentMapping, payload: MajorEmploymentMappingPayload) -> None:
    item.major_id = payload.major_id
    item.direction_id = payload.direction_id
    item.strength = payload.strength
    item.recommendation_note = payload.recommendation_note
    item.requires_postgraduate = payload.requires_postgraduate
    item.requires_certificate = payload.requires_certificate
    item.supported_student_types_json = payload.supported_student_types_json or None
    item.supports_art = payload.supports_art
    item.note = payload.note
    item.is_active = payload.is_active
