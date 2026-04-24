from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import EmploymentDirection, Major, MajorEmploymentMapping
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
    EmploymentDirectionBootstrapResponse,
    EmploymentDirectionPayload,
    EmploymentDirectionRead,
    MajorEmploymentMappingBootstrapResponse,
    MajorEmploymentMappingPayload,
    MajorEmploymentMappingRead,
)

from ._recommendations_employment_baseline import EMPLOYMENT_DIRECTION_BASELINES, EMPLOYMENT_MAPPING_RULES
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


def bootstrap_employment_directions(
    session: Session,
    *,
    record_audit: bool = True,
) -> EmploymentDirectionBootstrapResponse:
    created_count = 0
    skipped_count = 0
    for payload in EMPLOYMENT_DIRECTION_BASELINES:
        existing = get_employment_direction_by_name(session, payload.name)
        if existing:
            skipped_count += 1
            continue
        item = EmploymentDirection(name=payload.name.strip())
        session.add(item)
        session.flush()
        _apply_employment_direction_payload(item, payload)
        created_count += 1

    if record_audit and created_count:
        write_audit_log(
            session,
            module="recommendations",
            action="bootstrap_employment_directions",
            target_type="employment_direction",
            target_id=str(created_count),
        )

    return EmploymentDirectionBootstrapResponse(
        total_count=len(EMPLOYMENT_DIRECTION_BASELINES),
        created_count=created_count,
        skipped_count=skipped_count,
    )


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


def bootstrap_major_employment_mappings(
    session: Session,
    *,
    record_audit: bool = True,
) -> MajorEmploymentMappingBootstrapResponse:
    bootstrap_employment_directions(session, record_audit=False)
    directions_by_name = {
        item.name: item
        for item in session.scalars(select(EmploymentDirection).where(EmploymentDirection.is_active.is_(True))).all()
    }
    majors = session.scalars(select(Major).where(Major.is_active.is_(True))).all()

    created_count = 0
    skipped_count = 0
    matched_major_ids: set[int] = set()

    for major in majors:
        for payload in _build_major_mapping_payloads(major, directions_by_name):
            existing = get_major_employment_mapping_by_key(
                session,
                major_id=payload.major_id,
                direction_id=payload.direction_id,
            )
            if existing:
                skipped_count += 1
                matched_major_ids.add(major.id)
                continue

            item = MajorEmploymentMapping(major_id=payload.major_id, direction_id=payload.direction_id)
            session.add(item)
            session.flush()
            _apply_major_employment_mapping_payload(item, payload)
            created_count += 1
            matched_major_ids.add(major.id)

    if record_audit and created_count:
        write_audit_log(
            session,
            module="recommendations",
            action="bootstrap_major_employment_mappings",
            target_type="major_employment_mapping",
            target_id=str(created_count),
        )

    return MajorEmploymentMappingBootstrapResponse(
        major_total_count=len(majors),
        matched_major_count=len(matched_major_ids),
        created_count=created_count,
        skipped_count=skipped_count,
    )


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


def _build_major_mapping_payloads(
    major: Major,
    directions_by_name: dict[str, EmploymentDirection],
) -> list[MajorEmploymentMappingPayload]:
    normalized_name = (major.name or "").strip()
    normalized_category = (major.category or "").strip()
    joined_text = f"{normalized_name} {normalized_category}"
    payloads: list[MajorEmploymentMappingPayload] = []
    seen_direction_ids: set[int] = set()

    for rule in EMPLOYMENT_MAPPING_RULES:
        direction = directions_by_name.get(str(rule["direction"]))
        if not direction:
            continue
        if direction.id in seen_direction_ids:
            continue
        major_keywords = [str(item) for item in rule.get("major_keywords", [])]
        category_keywords = [str(item) for item in rule.get("category_keywords", [])]
        if not any(keyword in joined_text for keyword in major_keywords + category_keywords):
            continue
        payloads.append(
            MajorEmploymentMappingPayload(
                major_id=major.id,
                direction_id=direction.id,
                strength=str(rule.get("strength") or "medium"),
                recommendation_note=f"系统基线初始化生成：{major.name} 当前按专业名称/类别与“{direction.name}”建立第一轮映射。",
                requires_postgraduate=bool(rule.get("requires_postgraduate", False)),
                requires_certificate=bool(rule.get("requires_certificate", False)),
                supported_student_types_json=[str(item) for item in rule.get("supported_student_types_json", [])],
                supports_art=bool(rule.get("supports_art", False)),
                note="系统基线初始化生成",
                is_active=True,
            )
        )
        seen_direction_ids.add(direction.id)

    return payloads
