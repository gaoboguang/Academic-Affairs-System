from __future__ import annotations

from datetime import datetime
import json
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    AdmissionRecord,
    College,
    ConfigItem,
    EmploymentDirection,
    EnrollmentPlan,
    Major,
    MajorEmploymentMapping,
    ProvinceScoreTransformRule,
    ProvinceVolunteerRule,
    RecommendationResult,
    SpecialTypeRule,
    SubjectRequirementDict,
)
from app.schemas.recommendation import (
    AdmissionRecordRead,
    CollegeRead,
    EmploymentDirectionRead,
    EnrollmentPlanRead,
    MajorRead,
    MajorEmploymentMappingRead,
    ProvinceScoreTransformRuleRead,
    ProvinceVolunteerRuleRead,
    RecommendationCollegeOption,
    RecommendationResultRead,
    RecommendationSettingsRead,
    RecommendationStrategyPresetRead,
    SpecialTypeRuleRead,
    SubjectRequirementDictRead,
)


RECOMMENDATION_CONFIG_DEFAULTS = {
    "safe_ratio_max": ("0.85", "float", "保底区间上限"),
    "steady_ratio_max": ("1.00", "float", "稳妥区间上限"),
    "rush_ratio_max": ("1.15", "float", "冲刺区间上限"),
    "whitelist_college_ids_json": ("[]", "json", "推荐白名单院校"),
    "blacklist_college_ids_json": ("[]", "json", "推荐黑名单院校"),
    "strategy_presets_json": ("[]", "json", "推荐策略模板"),
}


class RecommendationSettingsState:
    def __init__(
        self,
        *,
        safe_ratio_max: float,
        steady_ratio_max: float,
        rush_ratio_max: float,
        whitelist_college_ids: list[int],
        blacklist_college_ids: list[int],
    ) -> None:
        self.safe_ratio_max = safe_ratio_max
        self.steady_ratio_max = steady_ratio_max
        self.rush_ratio_max = rush_ratio_max
        self.whitelist_college_ids = whitelist_college_ids
        self.blacklist_college_ids = blacklist_college_ids


def _serialize_college(item: College) -> CollegeRead:
    return CollegeRead(
        id=item.id,
        name=item.name,
        college_code=item.college_code,
        province=item.province,
        city=item.city,
        school_type=item.school_type,
        school_level_tags_json=item.school_level_tags_json,
        intro=item.intro,
        website=item.website,
        supports_art=item.supports_art,
        note=item.note,
        alias_names=[alias.alias_name for alias in item.aliases if alias.is_active],
        is_active=item.is_active,
    )


def _serialize_major(item: Major) -> MajorRead:
    return MajorRead.model_validate(item)


def _serialize_employment_direction(item: EmploymentDirection) -> EmploymentDirectionRead:
    return EmploymentDirectionRead(
        id=item.id,
        name=item.name,
        category=item.category,
        alias_names_json=item.alias_names_json or [],
        description=item.description,
        common_job_types_json=item.common_job_types_json or [],
        common_industries_json=item.common_industries_json or [],
        prefers_postgraduate=item.prefers_postgraduate,
        requires_certificate=item.requires_certificate,
        requires_long_cycle=item.requires_long_cycle,
        supports_art=item.supports_art,
        risk_note=item.risk_note,
        source_note=item.source_note,
        is_active=item.is_active,
    )


def _serialize_major_employment_mapping(item: MajorEmploymentMapping) -> MajorEmploymentMappingRead:
    return MajorEmploymentMappingRead(
        id=item.id,
        major_id=item.major_id,
        major_name=item.major.name if item.major else "",
        direction_id=item.direction_id,
        direction_name=item.direction.name if item.direction else "",
        direction_category=item.direction.category if item.direction else None,
        strength=item.strength,
        recommendation_note=item.recommendation_note,
        requires_postgraduate=item.requires_postgraduate,
        requires_certificate=item.requires_certificate,
        supported_student_types_json=item.supported_student_types_json or [],
        supports_art=item.supports_art,
        note=item.note,
        is_active=item.is_active,
    )


def _serialize_admission_record(item: AdmissionRecord) -> AdmissionRecordRead:
    return AdmissionRecordRead(
        id=item.id,
        year=item.year,
        province=item.province,
        batch=item.batch,
        college_id=item.college_id,
        college_name=item.college.name if item.college else None,
        major_id=item.major_id,
        major_name=item.major.name if item.major else None,
        student_type=item.student_type,
        art_track=item.art_track,
        subject_requirement=item.subject_requirement,
        min_score=item.min_score,
        min_rank=item.min_rank,
        avg_score=item.avg_score,
        max_score=item.max_score,
        plan_count=item.plan_count,
        source_note=item.source_note,
        is_active=item.is_active,
    )


def _serialize_enrollment_plan(item: EnrollmentPlan) -> EnrollmentPlanRead:
    major_name = item.major.name if item.major else item.major_name_snapshot or None
    return EnrollmentPlanRead(
        id=item.id,
        year=item.year,
        province=item.province,
        batch=item.batch,
        exam_mode=item.exam_mode,
        college_id=item.college_id,
        college_name=item.college.name if item.college else None,
        college_code_snapshot=item.college_code_snapshot,
        major_id=item.major_id,
        major_name=major_name,
        major_group_code=item.major_group_code,
        major_code_snapshot=item.major_code_snapshot,
        plan_count=item.plan_count,
        subject_requirement=item.subject_requirement,
        tuition_fee=item.tuition_fee,
        schooling_years=item.schooling_years,
        training_location=item.training_location,
        student_type=item.student_type,
        source_note=item.source_note,
        import_batch_name=item.import_batch_name,
        is_active=item.is_active,
    )


def _serialize_province_volunteer_rule(item: ProvinceVolunteerRule) -> ProvinceVolunteerRuleRead:
    return ProvinceVolunteerRuleRead(
        id=item.id,
        province=item.province,
        year=item.year,
        exam_mode=item.exam_mode,
        batch=item.batch,
        candidate_type=item.candidate_type,
        batch_order=item.batch_order,
        total_score=item.total_score,
        volunteer_limit=item.volunteer_limit,
        volunteer_unit_type=item.volunteer_unit_type,
        subject_requirement_mode=item.subject_requirement_mode,
        required_subjects_json=item.required_subjects_json or [],
        first_choice_subjects_json=item.first_choice_subjects_json or [],
        reselect_subjects_json=item.reselect_subjects_json or [],
        score_rule_summary=item.score_rule_summary,
        parallel_rule_mode=item.parallel_rule_mode,
        max_major_per_unit=item.max_major_per_unit,
        is_parallel=item.is_parallel,
        allow_adjustment=item.allow_adjustment,
        support_collect_round=item.support_collect_round,
        special_rules_json=item.special_rules_json or [],
        note=item.note,
        is_active=item.is_active,
    )


def _serialize_province_score_transform_rule(item: ProvinceScoreTransformRule) -> ProvinceScoreTransformRuleRead:
    return ProvinceScoreTransformRuleRead(
        id=item.id,
        province=item.province,
        year=item.year,
        exam_mode=item.exam_mode,
        subject_code=item.subject_code,
        subject_name=item.subject_name,
        score_mode=item.score_mode,
        sort_order=item.sort_order,
        grade_table_json=item.grade_table_json or [],
        formula_json=item.formula_json or {},
        source_note=item.source_note,
        note=item.note,
        is_active=item.is_active,
    )


def _serialize_subject_requirement_dict(item: SubjectRequirementDict) -> SubjectRequirementDictRead:
    return SubjectRequirementDictRead(
        id=item.id,
        province=item.province,
        year=item.year,
        exam_mode=item.exam_mode,
        requirement_code=item.requirement_code,
        requirement_text=item.requirement_text,
        match_mode=item.match_mode,
        sort_order=item.sort_order,
        normalized_subjects_json=item.normalized_subjects_json or [],
        source_note=item.source_note,
        note=item.note,
        is_active=item.is_active,
    )


def _serialize_special_type_rule(item: SpecialTypeRule) -> SpecialTypeRuleRead:
    return SpecialTypeRuleRead(
        id=item.id,
        province=item.province,
        year=item.year,
        student_type=item.student_type,
        category_code=item.category_code,
        category_label=item.category_label,
        sort_order=item.sort_order,
        match_keywords_json=item.match_keywords_json or [],
        review_notes_json=item.review_notes_json or [],
        priority_bonus=item.priority_bonus,
        priority_notes_json=item.priority_notes_json or [],
        source_note=item.source_note,
        note=item.note,
        is_active=item.is_active,
    )


def _serialize_result(item: RecommendationResult) -> RecommendationResultRead:
    snapshot = item.snapshot_json or {}
    return RecommendationResultRead(
        id=item.id,
        student_id=item.student_id,
        student_name=item.student.name if item.student else None,
        exam_id=item.exam_id,
        scheme_id=item.scheme_id,
        scheme_name=item.scheme.name if item.scheme else None,
        result_type=item.result_type,
        college_id=item.college_id,
        college_name=item.college.name if item.college else None,
        major_id=item.major_id,
        major_name=item.major.name if item.major else None,
        reference_rank=item.reference_rank,
        student_rank=item.student_rank,
        score_basis=item.score_basis,
        reference_scope=_read_optional_string(snapshot.get("reference_scope")),
        reference_years_json=_read_int_list(snapshot.get("reference_years")),
        reference_record_count=_read_optional_int(snapshot.get("reference_record_count")) or 0,
        reference_source_notes_json=_read_string_list(snapshot.get("reference_source_notes_json")),
        fallback_priority_score=_read_optional_float(snapshot.get("fallback_priority_score")),
        fallback_priority_label=_read_optional_string(snapshot.get("fallback_priority_label")),
        fallback_priority_notes_json=_read_string_list(snapshot.get("fallback_priority_notes_json")),
        fallback_category_label=_read_optional_string(snapshot.get("fallback_category_label")),
        fallback_review_notes_json=_read_string_list(snapshot.get("fallback_review_notes_json")),
        ratio=item.ratio,
        career_match_score=_read_optional_float(snapshot.get("career_match_score")),
        career_match_strength=_read_optional_string(snapshot.get("career_match_strength")),
        career_match_summary=_read_optional_string(snapshot.get("career_match_summary")),
        career_match_reasons_json=_read_string_list(snapshot.get("career_match_reasons_json")),
        matched_direction_names_json=_read_string_list(snapshot.get("matched_direction_names_json")),
        requires_postgraduate_path=_read_optional_bool(snapshot.get("requires_postgraduate_path")),
        requires_certificate_path=_read_optional_bool(snapshot.get("requires_certificate_path")),
        requires_long_training_path=_read_optional_bool(snapshot.get("requires_long_training_path")),
        reason_text=item.reason_text,
        risk_flags_json=item.risk_flags_json,
        snapshot_json=item.snapshot_json,
        generated_at=item.generated_at,
        is_active=item.is_active,
    )


def _read_optional_string(value: object) -> str | None:
    if isinstance(value, str):
        current = value.strip()
        return current or None
    return None


def _read_optional_float(value: object) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _read_optional_int(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return None


def _read_optional_bool(value: object) -> bool | None:
    if isinstance(value, bool):
        return value
    return None


def _read_string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    result: list[str] = []
    for item in value:
        if isinstance(item, str):
            current = item.strip()
            if current:
                result.append(current)
    return result


def _read_int_list(value: object) -> list[int]:
    if not isinstance(value, list):
        return []
    result: list[int] = []
    for item in value:
        current = _read_optional_int(item)
        if current is not None:
            result.append(current)
    return result


def _load_recommendation_thresholds(session: Session) -> dict[str, float]:
    state = _load_recommendation_settings_state(session)
    return {
        "safe": state.safe_ratio_max,
        "steady": state.steady_ratio_max,
        "rush": state.rush_ratio_max,
    }


def _load_recommendation_settings_state(session: Session) -> RecommendationSettingsState:
    config_rows = _load_recommendation_config_rows(session)

    def read_float(key: str) -> float:
        value = config_rows.get(key).config_value if config_rows.get(key) else RECOMMENDATION_CONFIG_DEFAULTS[key][0]
        return float(value)

    def read_json_list(key: str) -> list[int]:
        raw_value = config_rows.get(key).config_value if config_rows.get(key) else RECOMMENDATION_CONFIG_DEFAULTS[key][0]
        try:
            payload = json.loads(raw_value)
        except json.JSONDecodeError:
            payload = []
        if not isinstance(payload, list):
            return []
        result: list[int] = []
        for item in payload:
            try:
                result.append(int(item))
            except (TypeError, ValueError):
                continue
        return sorted(set(result))

    return RecommendationSettingsState(
        safe_ratio_max=read_float("safe_ratio_max"),
        steady_ratio_max=read_float("steady_ratio_max"),
        rush_ratio_max=read_float("rush_ratio_max"),
        whitelist_college_ids=read_json_list("whitelist_college_ids_json"),
        blacklist_college_ids=read_json_list("blacklist_college_ids_json"),
    )


def _serialize_recommendation_settings(
    session: Session,
    state: RecommendationSettingsState,
) -> RecommendationSettingsRead:
    def load_college_options(ids: list[int]) -> list[RecommendationCollegeOption]:
        return _load_college_options(session, ids)

    return RecommendationSettingsRead(
        safe_ratio_max=state.safe_ratio_max,
        steady_ratio_max=state.steady_ratio_max,
        rush_ratio_max=state.rush_ratio_max,
        whitelist_college_ids=state.whitelist_college_ids,
        blacklist_college_ids=state.blacklist_college_ids,
        whitelist_colleges=load_college_options(state.whitelist_college_ids),
        blacklist_colleges=load_college_options(state.blacklist_college_ids),
        strategy_presets=_load_strategy_presets(session),
    )


def _load_recommendation_config_rows(session: Session) -> dict[str, ConfigItem]:
    return {
        row.config_key: row
        for row in session.scalars(select(ConfigItem).where(ConfigItem.config_group == "recommendation")).all()
    }


def _upsert_recommendation_config_values(session: Session, values: dict[str, str]) -> None:
    config_rows = _load_recommendation_config_rows(session)
    for key, (default_value, value_type, description) in RECOMMENDATION_CONFIG_DEFAULTS.items():
        row = config_rows.get(key)
        if row:
            if key in values:
                row.config_value = values[key]
            elif row.config_value is None:
                row.config_value = default_value
            row.value_type = value_type
            row.description = description
        else:
            session.add(
                ConfigItem(
                    config_group="recommendation",
                    config_key=key,
                    config_value=values.get(key, default_value),
                    value_type=value_type,
                    description=description,
                )
            )
    session.flush()


def _validate_strategy_values(
    *,
    safe_ratio_max: float,
    steady_ratio_max: float,
    rush_ratio_max: float,
    whitelist_college_ids: list[int],
    blacklist_college_ids: list[int],
) -> None:
    if not (0 < safe_ratio_max <= steady_ratio_max <= rush_ratio_max):
        raise HTTPException(status_code=400, detail="推荐阈值需要满足 保 <= 稳 <= 冲")
    if set(whitelist_college_ids).intersection(set(blacklist_college_ids)):
        raise HTTPException(status_code=400, detail="同一院校不能同时存在于黑名单和白名单")


def _load_college_options(session: Session, ids: list[int]) -> list[RecommendationCollegeOption]:
    if not ids:
        return []
    rows = session.scalars(select(College).where(College.id.in_(ids), College.is_active.is_(True))).all()
    rows.sort(key=lambda item: ids.index(item.id))
    return [RecommendationCollegeOption(id=item.id, name=item.name) for item in rows]


def _load_strategy_preset_payloads(session: Session) -> list[dict[str, object]]:
    config_rows = _load_recommendation_config_rows(session)
    raw_value = (
        config_rows.get("strategy_presets_json").config_value
        if config_rows.get("strategy_presets_json")
        else RECOMMENDATION_CONFIG_DEFAULTS["strategy_presets_json"][0]
    )
    try:
        payload = json.loads(raw_value)
    except json.JSONDecodeError:
        payload = []
    return payload if isinstance(payload, list) else []


def _load_strategy_presets(session: Session) -> list[RecommendationStrategyPresetRead]:
    rows: list[RecommendationStrategyPresetRead] = []
    for item in _load_strategy_preset_payloads(session):
        whitelist_ids = [int(value) for value in item.get("whitelist_college_ids", []) if str(value).isdigit()]
        blacklist_ids = [int(value) for value in item.get("blacklist_college_ids", []) if str(value).isdigit()]
        try:
            created_at = datetime.fromisoformat(str(item.get("created_at")))
        except (TypeError, ValueError):
            created_at = datetime.now()
        rows.append(
            RecommendationStrategyPresetRead(
                id=str(item.get("id") or uuid4().hex),
                name=str(item.get("name") or "未命名模板"),
                note=str(item.get("note")) if item.get("note") else None,
                safe_ratio_max=float(item.get("safe_ratio_max", 0.85)),
                steady_ratio_max=float(item.get("steady_ratio_max", 1.0)),
                rush_ratio_max=float(item.get("rush_ratio_max", 1.15)),
                whitelist_college_ids=whitelist_ids,
                blacklist_college_ids=blacklist_ids,
                whitelist_colleges=_load_college_options(session, whitelist_ids),
                blacklist_colleges=_load_college_options(session, blacklist_ids),
                created_at=created_at,
            )
        )
    rows.sort(key=lambda item: item.created_at, reverse=True)
    return rows
