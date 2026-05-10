from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.schemas.recommendation import (
    VolunteerGuideCandidateGroupRead,
    VolunteerGuideCandidateRead,
    VolunteerGuideEvidenceRead,
    VolunteerGuideNextActionRead,
    VolunteerGuidePreviewResponse,
    VolunteerGuideReadinessItemRead,
    VolunteerGuideReadinessRead,
    VolunteerGuideSourcePreviewRead,
    VolunteerWorkbenchCandidateRead,
    VolunteerWorkbenchPreviewPayload,
    VolunteerWorkbenchRuleAlertRead,
)

from ._recommendations_workbench import preview_volunteer_workbench

GROUP_LABELS = {
    "challenge": "冲刺",
    "steady": "稳妥",
    "safe": "保底",
    "watch": "仅关注",
}

SPECIAL_INITIAL_SCREENING_TYPES = {
    "art",
    "sports",
    "fine_art",
    "music",
    "dance",
    "media",
    "spring_exam",
    "independent_recruitment",
    "comprehensive_evaluation",
}


def preview_volunteer_guide(
    session: Session,
    payload: VolunteerWorkbenchPreviewPayload,
) -> VolunteerGuidePreviewResponse:
    try:
        preview = preview_volunteer_workbench(session, payload)
    except HTTPException as exc:
        if exc.status_code not in {400, 404}:
            raise
        return _build_error_response(payload, exc)

    readiness = _build_readiness(payload, preview.rule_alerts, preview.candidate_count)
    groups = _build_groups(preview.candidates)
    return VolunteerGuidePreviewResponse(
        student_id=preview.student_id,
        student_name=preview.student_name,
        exam_id=preview.exam_id,
        exam_name=preview.exam_name,
        province=preview.province,
        target_year=preview.target_year,
        student_type=preview.student_type,
        candidate_type=preview.candidate_type,
        score_input_mode=preview.score_input_mode,
        input_notes=preview.input_notes,
        rule_alerts=preview.rule_alerts,
        applicable_rule_count=preview.applicable_rule_count,
        applicable_rules=preview.applicable_rules,
        readiness=readiness,
        source_preview=VolunteerGuideSourcePreviewRead(
            candidate_count=preview.candidate_count,
            returned_candidate_count=preview.returned_candidate_count,
            applicable_rule_count=preview.applicable_rule_count,
            is_candidate_truncated=preview.is_candidate_truncated,
            score_input_mode=preview.score_input_mode,
            score_input_label=preview.score_input_label,
            score_confidence=preview.score_confidence,
            effective_rank=preview.effective_rank,
            total_score=preview.total_score,
        ),
        groups=groups,
        next_actions=_build_next_actions(readiness, preview.candidate_count),
    )


def _build_error_response(
    payload: VolunteerWorkbenchPreviewPayload,
    exc: HTTPException,
) -> VolunteerGuidePreviewResponse:
    item = VolunteerGuideReadinessItemRead(
        code="preview_unavailable",
        level="blocking",
        title="暂时不能生成推荐",
        detail=str(exc.detail),
    )
    readiness = _summarize_readiness([item])
    return VolunteerGuidePreviewResponse(
        student_id=payload.student_id,
        student_name="",
        exam_id=payload.exam_id,
        exam_name="",
        province=payload.province,
        target_year=payload.target_year or 0,
        student_type=payload.candidate_type or "",
        candidate_type=payload.candidate_type or "",
        score_input_mode=payload.score_input_mode,
        input_notes=[str(exc.detail)],
        rule_alerts=[
            VolunteerWorkbenchRuleAlertRead(
                code=item.code,
                level="warning",
                title=item.title,
                detail=item.detail,
            )
        ],
        applicable_rule_count=0,
        applicable_rules=[],
        readiness=readiness,
        source_preview=VolunteerGuideSourcePreviewRead(
            score_input_mode=payload.score_input_mode,
            score_input_label=payload.score_input_mode,
            score_confidence="unknown",
        ),
        groups=_empty_groups(),
        next_actions=_build_next_actions(readiness, 0),
    )


def _build_readiness(
    payload: VolunteerWorkbenchPreviewPayload,
    rule_alerts: list,
    candidate_count: int,
) -> VolunteerGuideReadinessRead:
    items: list[VolunteerGuideReadinessItemRead] = []
    if not payload.subject_combination:
        items.append(
            VolunteerGuideReadinessItemRead(
                code="missing_subject_combination",
                level="warning",
                title="缺少选科组合",
                detail="未填写选科组合时，选科要求只能提示人工核对，建议先补齐学生选科。",
            )
        )
    if _requires_rank(payload):
        items.append(
            VolunteerGuideReadinessItemRead(
                code="missing_rank",
                level="blocking",
                title="缺少可用位次",
                detail="当前分数模式需要全省位次或位次区间；请补正式位次、预估位次或先做分数换算。",
            )
        )
    student_type = (payload.candidate_type or "").strip()
    if student_type in SPECIAL_INITIAL_SCREENING_TYPES:
        items.append(
            VolunteerGuideReadinessItemRead(
                code="special_type_initial_screening",
                level="warning",
                title="特殊类型仅作初筛",
                detail="当前类别缺少完整专门录取结果时，只能按计划、省控线或普通类参考做初筛，不能当作录取把握。",
            )
        )
    for alert in rule_alerts:
        items.append(
            VolunteerGuideReadinessItemRead(
                code=alert.code,
                level="blocking" if alert.level == "warning" else "info",
                title=alert.title,
                detail=alert.detail,
            )
        )
    if candidate_count <= 0:
        items.append(
            VolunteerGuideReadinessItemRead(
                code="no_candidates",
                level="blocking",
                title="暂无可推荐候选",
                detail="当前条件没有匹配到可加入志愿表的计划，请调整批次、科类、地区或专业条件。",
            )
        )
    return _summarize_readiness(items)


def _requires_rank(payload: VolunteerWorkbenchPreviewPayload) -> bool:
    if payload.score_input_mode == "actual_rank" and not payload.student_rank_override:
        return True
    if payload.score_input_mode == "estimated_score_and_rank" and not payload.student_rank_override:
        return True
    if payload.score_input_mode == "rank_range" and (not payload.rank_range_min or not payload.rank_range_max):
        return True
    return False


def _summarize_readiness(items: list[VolunteerGuideReadinessItemRead]) -> VolunteerGuideReadinessRead:
    blocking_count = len([item for item in items if item.level == "blocking"])
    warning_count = len([item for item in items if item.level == "warning"])
    info_count = len([item for item in items if item.level == "info"])
    status = "blocked" if blocking_count else "warning" if warning_count else "ready"
    return VolunteerGuideReadinessRead(
        status=status,
        blocking_count=blocking_count,
        warning_count=warning_count,
        info_count=info_count,
        items=items,
    )


def _build_groups(
    candidates: list[VolunteerWorkbenchCandidateRead],
) -> dict[str, VolunteerGuideCandidateGroupRead]:
    groups = _empty_groups()
    for candidate in candidates:
        key = _group_key(candidate.result_type)
        groups[key].candidates.append(
            VolunteerGuideCandidateRead(
                candidate=candidate,
                evidence=_build_evidence(candidate),
            )
        )
    for key, group in groups.items():
        group.count = len(group.candidates)
    return groups


def _empty_groups() -> dict[str, VolunteerGuideCandidateGroupRead]:
    return {
        key: VolunteerGuideCandidateGroupRead(key=key, label=label)
        for key, label in GROUP_LABELS.items()
    }


def _group_key(value: str) -> str:
    if value in GROUP_LABELS:
        return value
    return "watch"


def _build_evidence(candidate: VolunteerWorkbenchCandidateRead) -> VolunteerGuideEvidenceRead:
    strength, strength_label = _evidence_strength(candidate)
    rank_margin = _rank_margin(candidate)
    summary_parts = [
        strength_label,
        _format_years(candidate.reference_years_json),
        _format_min_rank(candidate),
        f"计划 {candidate.plan_count} 人",
    ]
    if candidate.career_match_summary:
        summary_parts.append(f"职业匹配 {candidate.career_match_summary}")
    if candidate.match_tags_json:
        summary_parts.append("、".join(candidate.match_tags_json[:3]))
    return VolunteerGuideEvidenceRead(
        strength=strength,
        strength_label=strength_label,
        summary="；".join(part for part in summary_parts if part),
        rank_margin=rank_margin,
        rank_margin_label=_format_rank_margin(rank_margin),
        reference_years=candidate.reference_years_json,
        reference_scope=candidate.reference_scope,
        risk_flags=candidate.risk_flags_json,
        source_notes=candidate.reference_source_notes_json,
    )


def _evidence_strength(candidate: VolunteerWorkbenchCandidateRead) -> tuple[str, str]:
    if candidate.reference_scope == "major":
        return "major_history", "专业历史线"
    if candidate.reference_scope == "college":
        return "college_history", "院校历史线"
    if candidate.reference_scope == "score_line":
        return "score_line", "省控线参考"
    if candidate.reference_scope == "plan_only":
        return "plan_only", "计划清单初筛"
    return "unknown", "参考证据待复核"


def _format_years(years: list[int]) -> str:
    if not years:
        return ""
    return f"参考 {'/'.join(str(year) for year in years)}"


def _format_min_rank(candidate: VolunteerWorkbenchCandidateRead) -> str:
    rank = candidate.latest_min_rank or candidate.reference_rank
    if rank:
        return f"最低位次 {rank}"
    if candidate.latest_min_score is not None:
        return f"最低分 {candidate.latest_min_score:g}"
    return ""


def _rank_margin(candidate: VolunteerWorkbenchCandidateRead) -> int | None:
    student_rank = None
    if candidate.ratio and candidate.reference_rank:
        student_rank = round(candidate.ratio * candidate.reference_rank)
    reference_rank = candidate.reference_rank or candidate.latest_min_rank
    if student_rank is None or reference_rank is None:
        return None
    return reference_rank - student_rank


def _format_rank_margin(value: int | None) -> str | None:
    if value is None:
        return None
    if value > 0:
        return f"比参考位次靠前 {value} 名"
    if value < 0:
        return f"比参考位次靠后 {abs(value)} 名"
    return "与参考位次基本持平"


def _build_next_actions(
    readiness: VolunteerGuideReadinessRead,
    candidate_count: int,
) -> list[VolunteerGuideNextActionRead]:
    is_special_initial_screening = any(item.code == "special_type_initial_screening" for item in readiness.items)
    if readiness.blocking_count:
        actions = [
            VolunteerGuideNextActionRead(
                code="fix_blocking_items",
                level="warning",
                title="先补齐阻断项",
                detail="补齐位次、规则或候选数据后再生成志愿草稿。",
            ),
            VolunteerGuideNextActionRead(
                code="no_candidates",
                level="warning",
                title="暂无可加入候选",
                detail="当前不能直接加入志愿表，请调整条件或补充招生计划/录取数据。",
            ),
        ]
        if is_special_initial_screening:
            actions.append(_manual_review_action())
        return actions
    actions = [
        VolunteerGuideNextActionRead(
            code="add_to_draft",
            level="info",
            title="加入志愿草稿",
            detail="可先把稳妥和保底候选加入志愿表，再逐条复核章程、选科和计划变化。",
        )
    ]
    if is_special_initial_screening:
        actions.append(_manual_review_action())
    if candidate_count <= 0:
        actions.append(
            VolunteerGuideNextActionRead(
                code="no_candidates",
                level="warning",
                title="暂无可加入候选",
                detail="当前条件下没有可加入志愿表的计划。",
            )
        )
    return actions


def _manual_review_action() -> VolunteerGuideNextActionRead:
    return VolunteerGuideNextActionRead(
        code="manual_review_required",
        level="warning",
        title="特殊类型需人工复核",
        detail="正式填报前必须逐校核对章程、报名资格、测试方式和专门录取规则。",
    )
