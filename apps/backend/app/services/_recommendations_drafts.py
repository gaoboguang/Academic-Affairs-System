from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import VolunteerDraft
from app.repositories.recommendations import (
    get_employment_direction,
    get_volunteer_draft,
    list_volunteer_drafts as repo_list_volunteer_drafts,
    replace_volunteer_draft_items,
)
from app.repositories.system import write_audit_log
from app.schemas.recommendation import (
    ProvinceVolunteerRuleRead,
    VolunteerDraftPayload,
    VolunteerDraftRead,
    VolunteerDraftSummaryRead,
)
from ._recommendations_shared import _serialize_province_volunteer_rule
from ._recommendations_workbench import _load_applicable_rules


def list_volunteer_drafts(
    session: Session,
    *,
    student_id: int | None = None,
    exam_id: int | None = None,
) -> list[VolunteerDraftSummaryRead]:
    return [_serialize_volunteer_draft_summary(item) for item in repo_list_volunteer_drafts(session, student_id=student_id, exam_id=exam_id)]


def get_volunteer_draft_detail(session: Session, draft_id: int) -> VolunteerDraftRead:
    draft = get_volunteer_draft(session, draft_id)
    if not draft or not draft.is_active:
        raise HTTPException(status_code=404, detail="志愿草稿不存在")
    return _serialize_volunteer_draft(session, draft)


def create_volunteer_draft(session: Session, payload: VolunteerDraftPayload) -> VolunteerDraftRead:
    _validate_volunteer_draft_payload(session, payload)
    draft = VolunteerDraft(
        name=payload.name.strip(),
        student_id=payload.student_id,
        exam_id=payload.exam_id,
        province=payload.province.strip(),
        target_year=payload.target_year,
        batch=_normalize_optional_string(payload.batch),
        exam_mode=_normalize_optional_string(payload.exam_mode),
        candidate_type=payload.candidate_type.strip(),
        score_input_mode=payload.score_input_mode.strip() or "actual_rank",
        score_range_min=payload.score_range_min,
        score_range_max=payload.score_range_max,
        rank_range_min=payload.rank_range_min,
        rank_range_max=payload.rank_range_max,
        reference_exam_name=_normalize_optional_string(payload.reference_exam_name),
        use_historical_mapping=payload.use_historical_mapping,
        risk_preference=payload.risk_preference.strip() or "balanced",
        target_regions_json=_dedupe_strings(payload.target_regions_json),
        school_level_tags_json=_dedupe_strings(payload.school_level_tags_json),
        major_keyword=_normalize_optional_string(payload.major_keyword),
        subject_combination=_normalize_optional_string(payload.subject_combination),
        primary_direction_id=payload.primary_direction_id,
        secondary_direction_id=payload.secondary_direction_id,
        alternative_direction_id=payload.alternative_direction_id,
        priority_focuses_json=_dedupe_strings(payload.priority_focuses_json),
        preferred_industries_json=_dedupe_strings(payload.preferred_industries_json),
        preferred_job_types_json=_dedupe_strings(payload.preferred_job_types_json),
        target_employment_cities_json=_dedupe_strings(payload.target_employment_cities_json),
        accepts_postgraduate=payload.accepts_postgraduate,
        accepts_public_service=payload.accepts_public_service,
        accepts_certificate=payload.accepts_certificate,
        accepts_long_training=payload.accepts_long_training,
        student_rank_override=payload.student_rank_override,
        comprehensive_score=payload.comprehensive_score,
        professional_score=payload.professional_score,
        culture_score=payload.culture_score,
        note=_normalize_optional_string(payload.note),
        rule_snapshot_json=payload.selected_rule.model_dump() if payload.selected_rule else None,
    )
    session.add(draft)
    session.flush()
    replace_volunteer_draft_items(
        session,
        draft,
        items=[(item.order, item.plan_id, item.candidate.model_dump()) for item in payload.items],
    )
    write_audit_log(
        session,
        module="recommendations",
        action="create_volunteer_draft",
        target_type="volunteer_draft",
        target_id=str(draft.id),
        detail_json={"student_id": draft.student_id, "exam_id": draft.exam_id, "item_count": len(payload.items)},
    )
    return _serialize_volunteer_draft(session, draft)


def update_volunteer_draft(session: Session, draft_id: int, payload: VolunteerDraftPayload) -> VolunteerDraftRead:
    _validate_volunteer_draft_payload(session, payload)
    draft = get_volunteer_draft(session, draft_id)
    if not draft or not draft.is_active:
        raise HTTPException(status_code=404, detail="志愿草稿不存在")
    draft.name = payload.name.strip()
    draft.student_id = payload.student_id
    draft.exam_id = payload.exam_id
    draft.province = payload.province.strip()
    draft.target_year = payload.target_year
    draft.batch = _normalize_optional_string(payload.batch)
    draft.exam_mode = _normalize_optional_string(payload.exam_mode)
    draft.candidate_type = payload.candidate_type.strip()
    draft.score_input_mode = payload.score_input_mode.strip() or "actual_rank"
    draft.score_range_min = payload.score_range_min
    draft.score_range_max = payload.score_range_max
    draft.rank_range_min = payload.rank_range_min
    draft.rank_range_max = payload.rank_range_max
    draft.reference_exam_name = _normalize_optional_string(payload.reference_exam_name)
    draft.use_historical_mapping = payload.use_historical_mapping
    draft.risk_preference = payload.risk_preference.strip() or "balanced"
    draft.target_regions_json = _dedupe_strings(payload.target_regions_json)
    draft.school_level_tags_json = _dedupe_strings(payload.school_level_tags_json)
    draft.major_keyword = _normalize_optional_string(payload.major_keyword)
    draft.subject_combination = _normalize_optional_string(payload.subject_combination)
    draft.primary_direction_id = payload.primary_direction_id
    draft.secondary_direction_id = payload.secondary_direction_id
    draft.alternative_direction_id = payload.alternative_direction_id
    draft.priority_focuses_json = _dedupe_strings(payload.priority_focuses_json)
    draft.preferred_industries_json = _dedupe_strings(payload.preferred_industries_json)
    draft.preferred_job_types_json = _dedupe_strings(payload.preferred_job_types_json)
    draft.target_employment_cities_json = _dedupe_strings(payload.target_employment_cities_json)
    draft.accepts_postgraduate = payload.accepts_postgraduate
    draft.accepts_public_service = payload.accepts_public_service
    draft.accepts_certificate = payload.accepts_certificate
    draft.accepts_long_training = payload.accepts_long_training
    draft.student_rank_override = payload.student_rank_override
    draft.comprehensive_score = payload.comprehensive_score
    draft.professional_score = payload.professional_score
    draft.culture_score = payload.culture_score
    draft.note = _normalize_optional_string(payload.note)
    draft.rule_snapshot_json = payload.selected_rule.model_dump() if payload.selected_rule else None
    replace_volunteer_draft_items(
        session,
        draft,
        items=[(item.order, item.plan_id, item.candidate.model_dump()) for item in payload.items],
    )
    session.flush()
    write_audit_log(
        session,
        module="recommendations",
        action="update_volunteer_draft",
        target_type="volunteer_draft",
        target_id=str(draft.id),
        detail_json={"student_id": draft.student_id, "exam_id": draft.exam_id, "item_count": len(payload.items)},
    )
    return _serialize_volunteer_draft(session, draft)


def delete_volunteer_draft(session: Session, draft_id: int) -> None:
    draft = get_volunteer_draft(session, draft_id)
    if not draft or not draft.is_active:
        raise HTTPException(status_code=404, detail="志愿草稿不存在")
    draft.is_active = False
    for item in draft.items:
        item.is_active = False
    session.flush()
    write_audit_log(
        session,
        module="recommendations",
        action="delete_volunteer_draft",
        target_type="volunteer_draft",
        target_id=str(draft.id),
    )


def _validate_volunteer_draft_payload(session: Session, payload: VolunteerDraftPayload) -> None:
    if not payload.name.strip():
        raise HTTPException(status_code=400, detail="草稿名称不能为空")
    if not payload.province.strip():
        raise HTTPException(status_code=400, detail="省份不能为空")
    if payload.score_range_min is not None and payload.score_range_max is not None and payload.score_range_min > payload.score_range_max:
        raise HTTPException(status_code=400, detail="分数区间下限不能大于上限")
    if payload.rank_range_min is not None and payload.rank_range_max is not None and payload.rank_range_min > payload.rank_range_max:
        raise HTTPException(status_code=400, detail="位次区间下限不能大于上限")
    if not payload.items:
        raise HTTPException(status_code=400, detail="志愿草稿至少需要 1 条计划")
    _validate_direction_selection(
        session,
        payload.primary_direction_id,
        payload.secondary_direction_id,
        payload.alternative_direction_id,
    )
    seen_orders: set[int] = set()
    for item in payload.items:
        if item.order <= 0:
            raise HTTPException(status_code=400, detail="志愿顺序必须从 1 开始")
        if item.order in seen_orders:
            raise HTTPException(status_code=400, detail="志愿顺序不能重复")
        seen_orders.add(item.order)


def _serialize_volunteer_draft_summary(item: VolunteerDraft) -> VolunteerDraftSummaryRead:
    return VolunteerDraftSummaryRead(
        id=item.id,
        name=item.name,
        student_id=item.student_id,
        student_name=item.student.name if item.student else None,
        exam_id=item.exam_id,
        exam_name=item.exam.name if item.exam else None,
        province=item.province,
        target_year=item.target_year,
        batch=item.batch,
        exam_mode=item.exam_mode,
        candidate_type=item.candidate_type,
        score_input_mode=item.score_input_mode,
        item_count=len([draft_item for draft_item in item.items if draft_item.is_active]),
        created_at=item.created_at,
        updated_at=item.updated_at,
        is_active=item.is_active,
    )


def _serialize_volunteer_draft(session: Session, item: VolunteerDraft) -> VolunteerDraftRead:
    selected_rule = _deserialize_rule_snapshot(item.rule_snapshot_json)
    applicable_rules, _, rule_alerts = _load_applicable_rules(
        session,
        province=item.province,
        target_year=item.target_year,
        exam_mode=item.exam_mode,
        batch=item.batch,
        candidate_type=item.candidate_type,
    )
    items = sorted((draft_item for draft_item in item.items if draft_item.is_active), key=lambda draft_item: draft_item.sort_order)
    return VolunteerDraftRead(
        **_serialize_volunteer_draft_summary(item).model_dump(),
        score_range_min=item.score_range_min,
        score_range_max=item.score_range_max,
        rank_range_min=item.rank_range_min,
        rank_range_max=item.rank_range_max,
        reference_exam_name=item.reference_exam_name,
        use_historical_mapping=item.use_historical_mapping,
        risk_preference=item.risk_preference,
        target_regions_json=item.target_regions_json or [],
        school_level_tags_json=item.school_level_tags_json or [],
        major_keyword=item.major_keyword,
        subject_combination=item.subject_combination,
        primary_direction_id=item.primary_direction_id,
        secondary_direction_id=item.secondary_direction_id,
        alternative_direction_id=item.alternative_direction_id,
        priority_focuses_json=item.priority_focuses_json or [],
        preferred_industries_json=item.preferred_industries_json or [],
        preferred_job_types_json=item.preferred_job_types_json or [],
        target_employment_cities_json=item.target_employment_cities_json or [],
        accepts_postgraduate=item.accepts_postgraduate,
        accepts_public_service=item.accepts_public_service,
        accepts_certificate=item.accepts_certificate,
        accepts_long_training=item.accepts_long_training,
        student_rank_override=item.student_rank_override,
        comprehensive_score=item.comprehensive_score,
        professional_score=item.professional_score,
        culture_score=item.culture_score,
        note=item.note,
        selected_rule=selected_rule,
        rule_alerts=rule_alerts,
        applicable_rules=[_serialize_province_volunteer_rule(rule) for rule in applicable_rules],
        items=[
            {
                "id": draft_item.id,
                "order": draft_item.sort_order,
                "plan_id": draft_item.plan_id,
                "candidate": draft_item.candidate_snapshot_json,
                "created_at": draft_item.created_at,
                "updated_at": draft_item.updated_at,
                "is_active": draft_item.is_active,
            }
            for draft_item in items
        ],
    )


def _deserialize_rule_snapshot(rule_snapshot_json: dict | None) -> ProvinceVolunteerRuleRead | None:
    if not rule_snapshot_json:
        return None
    try:
        return ProvinceVolunteerRuleRead.model_validate(rule_snapshot_json)
    except Exception:
        return None


def _normalize_optional_string(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


def _dedupe_strings(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        normalized = value.strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        result.append(normalized)
    return result


def _validate_direction_selection(
    session: Session,
    primary_direction_id: int | None,
    secondary_direction_id: int | None,
    alternative_direction_id: int | None,
) -> None:
    selected_ids = [
        direction_id
        for direction_id in [primary_direction_id, secondary_direction_id, alternative_direction_id]
        if direction_id is not None
    ]
    if len(selected_ids) != len(set(selected_ids)):
        raise HTTPException(status_code=400, detail="首选、次选和替代就业方向不能重复")
    for direction_id in selected_ids:
        direction = get_employment_direction(session, direction_id)
        if not direction or not direction.is_active:
            raise HTTPException(status_code=404, detail="就业方向不存在")
