from __future__ import annotations

from datetime import datetime
import json
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.repositories.system import write_audit_log
from app.schemas.recommendation import RecommendationSettingsPayload, RecommendationSettingsRead, RecommendationStrategyPresetPayload

from ._recommendations_shared import (
    _load_recommendation_settings_state,
    _load_strategy_preset_payloads,
    _serialize_recommendation_settings,
    _upsert_recommendation_config_values,
    _validate_strategy_values,
)


def get_recommendation_settings(session: Session) -> RecommendationSettingsRead:
    state = _load_recommendation_settings_state(session)
    return _serialize_recommendation_settings(session, state)


def update_recommendation_settings(
    session: Session,
    payload: RecommendationSettingsPayload,
) -> RecommendationSettingsRead:
    _validate_strategy_values(
        safe_ratio_max=payload.safe_ratio_max,
        steady_ratio_max=payload.steady_ratio_max,
        rush_ratio_max=payload.rush_ratio_max,
        whitelist_college_ids=payload.whitelist_college_ids,
        blacklist_college_ids=payload.blacklist_college_ids,
    )
    values = {
        "safe_ratio_max": str(payload.safe_ratio_max),
        "steady_ratio_max": str(payload.steady_ratio_max),
        "rush_ratio_max": str(payload.rush_ratio_max),
        "whitelist_college_ids_json": json.dumps(sorted(set(payload.whitelist_college_ids)), ensure_ascii=False),
        "blacklist_college_ids_json": json.dumps(sorted(set(payload.blacklist_college_ids)), ensure_ascii=False),
    }
    _upsert_recommendation_config_values(session, values)
    write_audit_log(
        session,
        module="recommendations",
        action="update_settings",
        target_type="config_group",
        target_id="recommendation",
        detail_json=payload.model_dump(),
    )
    return get_recommendation_settings(session)


def create_recommendation_strategy_preset(
    session: Session,
    payload: RecommendationStrategyPresetPayload,
) -> RecommendationSettingsRead:
    _validate_strategy_values(
        safe_ratio_max=payload.safe_ratio_max,
        steady_ratio_max=payload.steady_ratio_max,
        rush_ratio_max=payload.rush_ratio_max,
        whitelist_college_ids=payload.whitelist_college_ids,
        blacklist_college_ids=payload.blacklist_college_ids,
    )
    if not payload.name.strip():
        raise HTTPException(status_code=400, detail="模板名称不能为空")

    presets = _load_strategy_preset_payloads(session)
    preset = {
        "id": uuid4().hex,
        "name": payload.name.strip(),
        "note": payload.note.strip() if payload.note else None,
        "safe_ratio_max": payload.safe_ratio_max,
        "steady_ratio_max": payload.steady_ratio_max,
        "rush_ratio_max": payload.rush_ratio_max,
        "whitelist_college_ids": sorted(set(payload.whitelist_college_ids)),
        "blacklist_college_ids": sorted(set(payload.blacklist_college_ids)),
        "created_at": datetime.now().isoformat(),
    }
    presets.append(preset)
    _upsert_recommendation_config_values(
        session,
        {"strategy_presets_json": json.dumps(presets, ensure_ascii=False)},
    )
    write_audit_log(
        session,
        module="recommendations",
        action="create_strategy_preset",
        target_type="recommendation_strategy_preset",
        target_id=preset["id"],
        detail_json=preset,
    )
    return get_recommendation_settings(session)


def delete_recommendation_strategy_preset(session: Session, preset_id: str) -> RecommendationSettingsRead:
    presets = _load_strategy_preset_payloads(session)
    remaining = [item for item in presets if str(item.get("id")) != preset_id]
    if len(remaining) == len(presets):
        raise HTTPException(status_code=404, detail="推荐策略模板不存在")
    _upsert_recommendation_config_values(
        session,
        {"strategy_presets_json": json.dumps(remaining, ensure_ascii=False)},
    )
    write_audit_log(
        session,
        module="recommendations",
        action="delete_strategy_preset",
        target_type="recommendation_strategy_preset",
        target_id=preset_id,
    )
    return get_recommendation_settings(session)
