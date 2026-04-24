from __future__ import annotations

from datetime import date

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import ProvinceScoreTransformRule, ProvinceVolunteerRule, SpecialTypeRule, SubjectRequirementDict
from app.repositories.recommendations import (
    get_province_score_transform_rule,
    get_province_score_transform_rule_by_key,
    get_province_volunteer_rule,
    get_province_volunteer_rule_by_key,
    get_special_type_rule,
    get_special_type_rule_by_key,
    get_subject_requirement_dict,
    get_subject_requirement_dict_by_key,
    list_province_score_transform_rules as repo_list_province_score_transform_rules,
    list_province_volunteer_rules as repo_list_province_volunteer_rules,
    list_special_type_rules as repo_list_special_type_rules,
    list_subject_requirement_dicts as repo_list_subject_requirement_dicts,
)
from app.repositories.system import write_audit_log
from app.schemas.recommendation import (
    ProvinceScoreTransformRuleBootstrapResponse,
    ProvinceScoreTransformRulePayload,
    ProvinceScoreTransformRuleRead,
    ProvinceVolunteerRuleBootstrapResponse,
    ProvinceVolunteerRulePayload,
    ProvinceVolunteerRuleRead,
    SpecialTypeRuleBootstrapResponse,
    SpecialTypeRulePayload,
    SpecialTypeRuleRead,
    SubjectRequirementDictBootstrapResponse,
    SubjectRequirementDictPayload,
    SubjectRequirementDictRead,
)

from ._recommendations_rule_baseline import (
    build_province_score_transform_rule_baselines,
    build_province_volunteer_rule_baselines,
    build_subject_requirement_dict_baselines,
)
from ._recommendations_special_type_rules import build_special_type_rule_baselines
from ._recommendations_shared import (
    _serialize_province_score_transform_rule,
    _serialize_province_volunteer_rule,
    _serialize_special_type_rule,
    _serialize_subject_requirement_dict,
)


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


def list_province_score_transform_rules(
    session: Session,
    *,
    province: str | None = None,
    year: int | None = None,
    exam_mode: str | None = None,
    subject_name: str | None = None,
) -> list[ProvinceScoreTransformRuleRead]:
    return [
        _serialize_province_score_transform_rule(item)
        for item in repo_list_province_score_transform_rules(
            session,
            province=province,
            year=year,
            exam_mode=exam_mode,
            subject_name=subject_name,
        )
    ]


def create_province_score_transform_rule(
    session: Session,
    payload: ProvinceScoreTransformRulePayload,
) -> ProvinceScoreTransformRuleRead:
    _validate_province_score_transform_rule_payload(payload)
    existing = get_province_score_transform_rule_by_key(
        session,
        province=payload.province.strip(),
        year=payload.year,
        exam_mode=payload.exam_mode.strip(),
        subject_name=payload.subject_name.strip(),
    )
    if existing:
        raise HTTPException(status_code=400, detail="该省份赋分规则已存在")

    item = ProvinceScoreTransformRule(
        province=payload.province.strip(),
        year=payload.year,
        exam_mode=payload.exam_mode.strip(),
        subject_name=payload.subject_name.strip(),
    )
    session.add(item)
    _apply_province_score_transform_rule_payload(item, payload)
    session.flush()
    write_audit_log(
        session,
        module="recommendations",
        action="create_province_score_transform_rule",
        target_type="province_score_transform_rule",
        target_id=str(item.id),
    )
    session.refresh(item)
    return _serialize_province_score_transform_rule(item)


def update_province_score_transform_rule(
    session: Session,
    rule_id: int,
    payload: ProvinceScoreTransformRulePayload,
) -> ProvinceScoreTransformRuleRead:
    _validate_province_score_transform_rule_payload(payload)
    item = get_province_score_transform_rule(session, rule_id)
    if not item:
        raise HTTPException(status_code=404, detail="赋分规则不存在")
    existing = get_province_score_transform_rule_by_key(
        session,
        province=payload.province.strip(),
        year=payload.year,
        exam_mode=payload.exam_mode.strip(),
        subject_name=payload.subject_name.strip(),
    )
    if existing and existing.id != rule_id:
        raise HTTPException(status_code=400, detail="该省份赋分规则已存在")

    _apply_province_score_transform_rule_payload(item, payload)
    session.flush()
    write_audit_log(
        session,
        module="recommendations",
        action="update_province_score_transform_rule",
        target_type="province_score_transform_rule",
        target_id=str(item.id),
    )
    session.refresh(item)
    return _serialize_province_score_transform_rule(item)


def bootstrap_province_score_transform_rules(
    session: Session,
    *,
    year: int | None = None,
    record_audit: bool = True,
) -> ProvinceScoreTransformRuleBootstrapResponse:
    target_year = year or date.today().year
    created_count = 0
    skipped_count = 0
    payloads = build_province_score_transform_rule_baselines(target_year)
    for payload in payloads:
        existing = get_province_score_transform_rule_by_key(
            session,
            province=payload.province.strip(),
            year=payload.year,
            exam_mode=payload.exam_mode.strip(),
            subject_name=payload.subject_name.strip(),
        )
        if existing:
            skipped_count += 1
            continue

        item = ProvinceScoreTransformRule(
            province=payload.province.strip(),
            year=payload.year,
            exam_mode=payload.exam_mode.strip(),
            subject_name=payload.subject_name.strip(),
        )
        session.add(item)
        _apply_province_score_transform_rule_payload(item, payload)
        created_count += 1

    if record_audit and created_count:
        write_audit_log(
            session,
            module="recommendations",
            action="bootstrap_province_score_transform_rules",
            target_type="province_score_transform_rule",
            target_id=str(target_year),
        )

    return ProvinceScoreTransformRuleBootstrapResponse(
        year=target_year,
        total_count=len(payloads),
        created_count=created_count,
        skipped_count=skipped_count,
    )


def list_subject_requirement_dicts(
    session: Session,
    *,
    province: str | None = None,
    year: int | None = None,
    exam_mode: str | None = None,
    requirement_code: str | None = None,
) -> list[SubjectRequirementDictRead]:
    return [
        _serialize_subject_requirement_dict(item)
        for item in repo_list_subject_requirement_dicts(
            session,
            province=province,
            year=year,
            exam_mode=exam_mode,
            requirement_code=requirement_code,
        )
    ]


def create_subject_requirement_dict(
    session: Session,
    payload: SubjectRequirementDictPayload,
) -> SubjectRequirementDictRead:
    _validate_subject_requirement_dict_payload(payload)
    existing = get_subject_requirement_dict_by_key(
        session,
        province=payload.province.strip(),
        year=payload.year,
        exam_mode=payload.exam_mode.strip(),
        requirement_code=payload.requirement_code.strip(),
    )
    if existing:
        raise HTTPException(status_code=400, detail="该选科要求字典项已存在")

    item = SubjectRequirementDict(
        province=payload.province.strip(),
        year=payload.year,
        exam_mode=payload.exam_mode.strip(),
        requirement_code=payload.requirement_code.strip(),
    )
    session.add(item)
    _apply_subject_requirement_dict_payload(item, payload)
    session.flush()
    write_audit_log(
        session,
        module="recommendations",
        action="create_subject_requirement_dict",
        target_type="subject_requirement_dict",
        target_id=str(item.id),
    )
    session.refresh(item)
    return _serialize_subject_requirement_dict(item)


def update_subject_requirement_dict(
    session: Session,
    dict_id: int,
    payload: SubjectRequirementDictPayload,
) -> SubjectRequirementDictRead:
    _validate_subject_requirement_dict_payload(payload)
    item = get_subject_requirement_dict(session, dict_id)
    if not item:
        raise HTTPException(status_code=404, detail="选科要求字典项不存在")
    existing = get_subject_requirement_dict_by_key(
        session,
        province=payload.province.strip(),
        year=payload.year,
        exam_mode=payload.exam_mode.strip(),
        requirement_code=payload.requirement_code.strip(),
    )
    if existing and existing.id != dict_id:
        raise HTTPException(status_code=400, detail="该选科要求字典项已存在")

    _apply_subject_requirement_dict_payload(item, payload)
    session.flush()
    write_audit_log(
        session,
        module="recommendations",
        action="update_subject_requirement_dict",
        target_type="subject_requirement_dict",
        target_id=str(item.id),
    )
    session.refresh(item)
    return _serialize_subject_requirement_dict(item)


def bootstrap_subject_requirement_dicts(
    session: Session,
    *,
    year: int | None = None,
    record_audit: bool = True,
) -> SubjectRequirementDictBootstrapResponse:
    target_year = year or date.today().year
    created_count = 0
    skipped_count = 0
    payloads = build_subject_requirement_dict_baselines(target_year)
    for payload in payloads:
        existing = get_subject_requirement_dict_by_key(
            session,
            province=payload.province.strip(),
            year=payload.year,
            exam_mode=payload.exam_mode.strip(),
            requirement_code=payload.requirement_code.strip(),
        )
        if existing:
            skipped_count += 1
            continue

        item = SubjectRequirementDict(
            province=payload.province.strip(),
            year=payload.year,
            exam_mode=payload.exam_mode.strip(),
            requirement_code=payload.requirement_code.strip(),
        )
        session.add(item)
        _apply_subject_requirement_dict_payload(item, payload)
        created_count += 1

    if record_audit and created_count:
        write_audit_log(
            session,
            module="recommendations",
            action="bootstrap_subject_requirement_dicts",
            target_type="subject_requirement_dict",
            target_id=str(target_year),
        )

    return SubjectRequirementDictBootstrapResponse(
        year=target_year,
        total_count=len(payloads),
        created_count=created_count,
        skipped_count=skipped_count,
    )


def list_special_type_rules(
    session: Session,
    *,
    province: str | None = None,
    year: int | None = None,
    student_type: str | None = None,
) -> list[SpecialTypeRuleRead]:
    return [
        _serialize_special_type_rule(item)
        for item in repo_list_special_type_rules(
            session,
            province=province,
            year=year,
            student_type=student_type,
        )
    ]


def create_special_type_rule(
    session: Session,
    payload: SpecialTypeRulePayload,
) -> SpecialTypeRuleRead:
    _validate_special_type_rule_payload(payload)
    existing = get_special_type_rule_by_key(
        session,
        province=payload.province.strip(),
        year=payload.year,
        student_type=payload.student_type.strip(),
        category_code=payload.category_code.strip(),
    )
    if existing:
        raise HTTPException(status_code=400, detail="该特殊类型规则已存在")

    item = SpecialTypeRule(
        province=payload.province.strip(),
        year=payload.year,
        student_type=payload.student_type.strip(),
        category_code=payload.category_code.strip(),
        category_label=payload.category_label.strip(),
    )
    session.add(item)
    _apply_special_type_rule_payload(item, payload)
    session.flush()
    write_audit_log(
        session,
        module="recommendations",
        action="create_special_type_rule",
        target_type="special_type_rule",
        target_id=str(item.id),
    )
    session.refresh(item)
    return _serialize_special_type_rule(item)


def update_special_type_rule(
    session: Session,
    rule_id: int,
    payload: SpecialTypeRulePayload,
) -> SpecialTypeRuleRead:
    _validate_special_type_rule_payload(payload)
    item = get_special_type_rule(session, rule_id)
    if not item:
        raise HTTPException(status_code=404, detail="特殊类型规则不存在")
    existing = get_special_type_rule_by_key(
        session,
        province=payload.province.strip(),
        year=payload.year,
        student_type=payload.student_type.strip(),
        category_code=payload.category_code.strip(),
    )
    if existing and existing.id != rule_id:
        raise HTTPException(status_code=400, detail="该特殊类型规则已存在")

    _apply_special_type_rule_payload(item, payload)
    session.flush()
    write_audit_log(
        session,
        module="recommendations",
        action="update_special_type_rule",
        target_type="special_type_rule",
        target_id=str(item.id),
    )
    session.refresh(item)
    return _serialize_special_type_rule(item)


def bootstrap_special_type_rules(
    session: Session,
    *,
    year: int | None = None,
    record_audit: bool = True,
) -> SpecialTypeRuleBootstrapResponse:
    target_year = year or date.today().year
    created_count = 0
    skipped_count = 0
    payloads = build_special_type_rule_baselines(target_year)
    for payload in payloads:
        existing = get_special_type_rule_by_key(
            session,
            province=payload.province.strip(),
            year=payload.year,
            student_type=payload.student_type.strip(),
            category_code=payload.category_code.strip(),
        )
        if existing:
            skipped_count += 1
            continue

        item = SpecialTypeRule(
            province=payload.province.strip(),
            year=payload.year,
            student_type=payload.student_type.strip(),
            category_code=payload.category_code.strip(),
            category_label=payload.category_label.strip(),
        )
        session.add(item)
        _apply_special_type_rule_payload(item, payload)
        created_count += 1

    if record_audit and created_count:
        write_audit_log(
            session,
            module="recommendations",
            action="bootstrap_special_type_rules",
            target_type="special_type_rule",
            target_id=str(target_year),
        )

    return SpecialTypeRuleBootstrapResponse(
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


def _validate_province_score_transform_rule_payload(payload: ProvinceScoreTransformRulePayload) -> None:
    if not payload.province.strip():
        raise HTTPException(status_code=400, detail="省份不能为空")
    if not payload.subject_name.strip():
        raise HTTPException(status_code=400, detail="科目名称不能为空")
    if payload.score_mode.strip() not in {"raw", "grade_assigned"}:
        raise HTTPException(status_code=400, detail="分数模式只支持 raw 或 grade_assigned")
    if payload.sort_order is not None and payload.sort_order <= 0:
        raise HTTPException(status_code=400, detail="排序必须大于 0")


def _apply_province_score_transform_rule_payload(
    item: ProvinceScoreTransformRule,
    payload: ProvinceScoreTransformRulePayload,
) -> None:
    item.province = payload.province.strip()
    item.year = payload.year
    item.exam_mode = payload.exam_mode.strip()
    item.subject_code = payload.subject_code.strip() if payload.subject_code else None
    item.subject_name = payload.subject_name.strip()
    item.score_mode = payload.score_mode.strip()
    item.sort_order = payload.sort_order
    item.grade_table_json = payload.grade_table_json or None
    item.formula_json = payload.formula_json or None
    item.source_note = payload.source_note.strip() if payload.source_note else None
    item.note = payload.note.strip() if payload.note else None
    item.is_active = payload.is_active


def _validate_subject_requirement_dict_payload(payload: SubjectRequirementDictPayload) -> None:
    if not payload.province.strip():
        raise HTTPException(status_code=400, detail="省份不能为空")
    if not payload.requirement_code.strip():
        raise HTTPException(status_code=400, detail="要求编码不能为空")
    if not payload.requirement_text.strip():
        raise HTTPException(status_code=400, detail="要求文本不能为空")
    if not payload.match_mode.strip():
        raise HTTPException(status_code=400, detail="匹配模式不能为空")
    if payload.sort_order is not None and payload.sort_order <= 0:
        raise HTTPException(status_code=400, detail="排序必须大于 0")


def _apply_subject_requirement_dict_payload(
    item: SubjectRequirementDict,
    payload: SubjectRequirementDictPayload,
) -> None:
    normalized_subjects = sorted({value.strip() for value in payload.normalized_subjects_json if value.strip()})
    item.province = payload.province.strip()
    item.year = payload.year
    item.exam_mode = payload.exam_mode.strip()
    item.requirement_code = payload.requirement_code.strip()
    item.requirement_text = payload.requirement_text.strip()
    item.match_mode = payload.match_mode.strip()
    item.sort_order = payload.sort_order
    item.normalized_subjects_json = normalized_subjects or None
    item.source_note = payload.source_note.strip() if payload.source_note else None
    item.note = payload.note.strip() if payload.note else None
    item.is_active = payload.is_active


def _validate_special_type_rule_payload(payload: SpecialTypeRulePayload) -> None:
    if not payload.province.strip():
        raise HTTPException(status_code=400, detail="省份不能为空")
    if payload.year <= 0:
        raise HTTPException(status_code=400, detail="年份必须大于 0")
    if not payload.student_type.strip():
        raise HTTPException(status_code=400, detail="考生类型不能为空")
    if not payload.category_code.strip():
        raise HTTPException(status_code=400, detail="类别编码不能为空")
    if not payload.category_label.strip():
        raise HTTPException(status_code=400, detail="类别名称不能为空")
    if payload.sort_order is not None and payload.sort_order <= 0:
        raise HTTPException(status_code=400, detail="排序必须大于 0")
    if payload.priority_bonus < 0:
        raise HTTPException(status_code=400, detail="优先级加成不能小于 0")


def _apply_special_type_rule_payload(
    item: SpecialTypeRule,
    payload: SpecialTypeRulePayload,
) -> None:
    match_keywords = [value.strip() for value in payload.match_keywords_json if value.strip()]
    review_notes = [value.strip() for value in payload.review_notes_json if value.strip()]
    priority_notes = [value.strip() for value in payload.priority_notes_json if value.strip()]
    item.province = payload.province.strip()
    item.year = payload.year
    item.student_type = payload.student_type.strip()
    item.category_code = payload.category_code.strip()
    item.category_label = payload.category_label.strip()
    item.sort_order = payload.sort_order
    item.match_keywords_json = match_keywords or None
    item.review_notes_json = review_notes or None
    item.priority_bonus = payload.priority_bonus
    item.priority_notes_json = priority_notes or None
    item.source_note = payload.source_note.strip() if payload.source_note else None
    item.note = payload.note.strip() if payload.note else None
    item.is_active = payload.is_active
