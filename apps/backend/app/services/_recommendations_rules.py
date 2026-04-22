from __future__ import annotations

from datetime import date

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import ProvinceVolunteerRule
from app.repositories.recommendations import (
    get_province_volunteer_rule,
    get_province_volunteer_rule_by_key,
    list_province_volunteer_rules as repo_list_province_volunteer_rules,
)
from app.repositories.system import write_audit_log
from app.schemas.recommendation import (
    ProvinceVolunteerRuleBootstrapResponse,
    ProvinceVolunteerRulePayload,
    ProvinceVolunteerRuleRead,
)

from ._recommendations_rule_baseline import build_province_volunteer_rule_baselines
from ._recommendations_shared import _serialize_province_volunteer_rule


def list_province_volunteer_rules(
    session: Session,
    *,
    province: str | None = None,
    year: int | None = None,
    exam_mode: str | None = None,
    candidate_type: str | None = None,
) -> list[ProvinceVolunteerRuleRead]:
    return [
        _serialize_province_volunteer_rule(item)
        for item in repo_list_province_volunteer_rules(
            session,
            province=province,
            year=year,
            exam_mode=exam_mode,
            candidate_type=candidate_type,
        )
    ]


def create_province_volunteer_rule(
    session: Session,
    payload: ProvinceVolunteerRulePayload,
) -> ProvinceVolunteerRuleRead:
    _validate_province_volunteer_rule_payload(payload)
    existing = get_province_volunteer_rule_by_key(
        session,
        province=payload.province.strip(),
        year=payload.year,
        exam_mode=payload.exam_mode.strip(),
        batch=payload.batch.strip(),
        candidate_type=payload.candidate_type.strip(),
    )
    if existing:
        raise HTTPException(status_code=400, detail="该省份批次规则已存在")

    item = ProvinceVolunteerRule(
        province=payload.province.strip(),
        year=payload.year,
        exam_mode=payload.exam_mode.strip(),
        batch=payload.batch.strip(),
        candidate_type=payload.candidate_type.strip(),
    )
    session.add(item)
    _apply_province_volunteer_rule_payload(item, payload)
    session.flush()
    write_audit_log(
        session,
        module="recommendations",
        action="create_province_volunteer_rule",
        target_type="province_volunteer_rule",
        target_id=str(item.id),
    )
    session.refresh(item)
    return _serialize_province_volunteer_rule(item)


def update_province_volunteer_rule(
    session: Session,
    rule_id: int,
    payload: ProvinceVolunteerRulePayload,
) -> ProvinceVolunteerRuleRead:
    _validate_province_volunteer_rule_payload(payload)
    item = get_province_volunteer_rule(session, rule_id)
    if not item:
        raise HTTPException(status_code=404, detail="省份规则不存在")
    existing = get_province_volunteer_rule_by_key(
        session,
        province=payload.province.strip(),
        year=payload.year,
        exam_mode=payload.exam_mode.strip(),
        batch=payload.batch.strip(),
        candidate_type=payload.candidate_type.strip(),
    )
    if existing and existing.id != rule_id:
        raise HTTPException(status_code=400, detail="该省份批次规则已存在")

    _apply_province_volunteer_rule_payload(item, payload)
    session.flush()
    write_audit_log(
        session,
        module="recommendations",
        action="update_province_volunteer_rule",
        target_type="province_volunteer_rule",
        target_id=str(item.id),
    )
    session.refresh(item)
    return _serialize_province_volunteer_rule(item)


def bootstrap_province_volunteer_rules(
    session: Session,
    *,
    year: int | None = None,
    record_audit: bool = True,
) -> ProvinceVolunteerRuleBootstrapResponse:
    target_year = year or date.today().year
    created_count = 0
    skipped_count = 0
    payloads = build_province_volunteer_rule_baselines(target_year)
    for payload in payloads:
        existing = get_province_volunteer_rule_by_key(
            session,
            province=payload.province.strip(),
            year=payload.year,
            exam_mode=payload.exam_mode.strip(),
            batch=payload.batch.strip(),
            candidate_type=payload.candidate_type.strip(),
        )
        if existing:
            skipped_count += 1
            continue

        item = ProvinceVolunteerRule(
            province=payload.province.strip(),
            year=payload.year,
            exam_mode=payload.exam_mode.strip(),
            batch=payload.batch.strip(),
            candidate_type=payload.candidate_type.strip(),
        )
        session.add(item)
        _apply_province_volunteer_rule_payload(item, payload)
        created_count += 1

    if record_audit and created_count:
        write_audit_log(
            session,
            module="recommendations",
            action="bootstrap_province_volunteer_rules",
            target_type="province_volunteer_rule",
            target_id=str(target_year),
        )

    return ProvinceVolunteerRuleBootstrapResponse(
        year=target_year,
        total_count=len(payloads),
        created_count=created_count,
        skipped_count=skipped_count,
    )


def _validate_province_volunteer_rule_payload(payload: ProvinceVolunteerRulePayload) -> None:
    if not payload.province.strip():
        raise HTTPException(status_code=400, detail="省份不能为空")
    if not payload.exam_mode.strip():
        raise HTTPException(status_code=400, detail="高考模式不能为空")
    if not payload.batch.strip():
        raise HTTPException(status_code=400, detail="批次不能为空")
    if payload.total_score <= 0:
        raise HTTPException(status_code=400, detail="总分口径必须大于 0")
    if payload.volunteer_limit <= 0:
        raise HTTPException(status_code=400, detail="志愿数上限必须大于 0")
    if not payload.volunteer_unit_type.strip():
        raise HTTPException(status_code=400, detail="志愿单位类型不能为空")
    if payload.max_major_per_unit is not None and payload.max_major_per_unit <= 0:
        raise HTTPException(status_code=400, detail="同单位专业上限必须大于 0")


def _apply_province_volunteer_rule_payload(item: ProvinceVolunteerRule, payload: ProvinceVolunteerRulePayload) -> None:
    special_rules = sorted({value.strip() for value in payload.special_rules_json if value.strip()})
    required_subjects = sorted({value.strip() for value in payload.required_subjects_json if value.strip()})
    first_choice_subjects = sorted({value.strip() for value in payload.first_choice_subjects_json if value.strip()})
    reselect_subjects = sorted({value.strip() for value in payload.reselect_subjects_json if value.strip()})
    item.province = payload.province.strip()
    item.year = payload.year
    item.exam_mode = payload.exam_mode.strip()
    item.batch = payload.batch.strip()
    item.candidate_type = payload.candidate_type.strip()
    item.batch_order = payload.batch_order
    item.total_score = payload.total_score
    item.volunteer_limit = payload.volunteer_limit
    item.volunteer_unit_type = payload.volunteer_unit_type.strip()
    item.subject_requirement_mode = payload.subject_requirement_mode.strip() if payload.subject_requirement_mode else None
    item.required_subjects_json = required_subjects or None
    item.first_choice_subjects_json = first_choice_subjects or None
    item.reselect_subjects_json = reselect_subjects or None
    item.score_rule_summary = payload.score_rule_summary.strip() if payload.score_rule_summary else None
    item.parallel_rule_mode = payload.parallel_rule_mode.strip() if payload.parallel_rule_mode else None
    item.max_major_per_unit = payload.max_major_per_unit
    item.is_parallel = payload.is_parallel
    item.allow_adjustment = payload.allow_adjustment
    item.support_collect_round = payload.support_collect_round
    item.special_rules_json = special_rules or None
    item.note = payload.note.strip() if payload.note else None
    item.is_active = payload.is_active
