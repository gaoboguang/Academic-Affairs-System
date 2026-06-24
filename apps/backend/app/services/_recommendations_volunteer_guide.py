from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import Student
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
from ._recommendations_volunteer_options import normalize_volunteer_fields

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

MISSING_TARGET_YEAR_PLAN_CODES = {
    "missing_target_year_enrollment_plan",
}


def preview_volunteer_guide(
    session: Session,
    payload: VolunteerWorkbenchPreviewPayload,
) -> VolunteerGuidePreviewResponse:
    normalized = _normalize_payload_for_readiness(session, payload)
    try:
        preview = preview_volunteer_workbench(session, payload)
    except HTTPException as exc:
        art_items = _build_art_blocking_items(session, normalized, payload)
        if art_items:
            return _build_blocked_response(payload, normalized, art_items)
        if exc.status_code not in {400, 404}:
            raise
        return _build_error_response(payload, exc, normalized)

    readiness = _build_readiness(payload, preview.rule_alerts, preview.candidate_count, normalized, session)
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
        art_track=preview.art_track,
        normalized_batch=preview.normalized_batch,
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
            culture_score=preview.culture_score,
            professional_score=preview.professional_score,
            art_comprehensive_score=preview.art_comprehensive_score,
        ),
        groups=groups,
        next_actions=_build_next_actions(readiness, preview.candidate_count),
    )


def _build_error_response(
    payload: VolunteerWorkbenchPreviewPayload,
    exc: HTTPException,
    normalized=None,
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
        student_type=normalized.candidate_type if normalized else payload.candidate_type or "",
        candidate_type=normalized.candidate_type if normalized else payload.candidate_type or "",
        art_track=normalized.art_track if normalized else payload.art_track,
        normalized_batch=normalized.batch if normalized else payload.batch,
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


def _build_blocked_response(
    payload: VolunteerWorkbenchPreviewPayload,
    normalized,
    items: list[VolunteerGuideReadinessItemRead],
) -> VolunteerGuidePreviewResponse:
    readiness = _summarize_readiness(items)
    return VolunteerGuidePreviewResponse(
        student_id=payload.student_id,
        student_name="",
        exam_id=payload.exam_id,
        exam_name="",
        province=payload.province,
        target_year=payload.target_year or 0,
        student_type=normalized.candidate_type,
        candidate_type=normalized.candidate_type,
        art_track=normalized.art_track,
        normalized_batch=normalized.batch,
        score_input_mode=payload.score_input_mode,
        input_notes=list(normalized.notes),
        rule_alerts=[
            VolunteerWorkbenchRuleAlertRead(
                code=item.code,
                level="warning",
                title=item.title,
                detail=item.detail,
            )
            for item in items
        ],
        applicable_rule_count=0,
        applicable_rules=[],
        readiness=readiness,
        source_preview=VolunteerGuideSourcePreviewRead(
            score_input_mode=payload.score_input_mode,
            score_input_label=payload.score_input_mode,
            score_confidence="blocked",
            culture_score=payload.culture_score,
            professional_score=payload.professional_score,
        ),
        groups=_empty_groups(),
        next_actions=_build_next_actions(readiness, 0),
    )


def _build_readiness(
    payload: VolunteerWorkbenchPreviewPayload,
    rule_alerts: list,
    candidate_count: int,
    normalized=None,
    session: Session | None = None,
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
    items.extend(_build_art_blocking_items(session, normalized, payload))
    student_type = (normalized.candidate_type if normalized else payload.candidate_type or "").strip()
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
                level=_readiness_level_for_rule_alert(alert),
                title=alert.title,
                detail=alert.detail,
            )
        )
    if candidate_count <= 0:
        missing_plan_item = next(
            (item for item in items if item.code in MISSING_TARGET_YEAR_PLAN_CODES),
            None,
        )
        items.append(
            VolunteerGuideReadinessItemRead(
                code="no_candidates",
                level="blocking",
                title="暂无可推荐候选",
                detail=(
                    "当前目标年份招生计划尚未导入；可开启“历年映射估算”做历史计划模拟，或导入当年正式计划后再生成。"
                    if missing_plan_item
                    else "当前条件没有匹配到可加入志愿表的计划，请调整批次、科类、地区或专业条件。"
                ),
            )
        )
    return _summarize_readiness(items)


def _readiness_level_for_rule_alert(alert) -> str:
    if alert.code in MISSING_TARGET_YEAR_PLAN_CODES:
        return "blocking"
    if str(alert.code).startswith("missing_rule_"):
        return "blocking"
    return "warning" if alert.level == "warning" else "info"


def _requires_rank(payload: VolunteerWorkbenchPreviewPayload) -> bool:
    if payload.score_input_mode == "estimated_score":
        return False
    if payload.score_input_mode == "actual_rank" and not payload.student_rank_override:
        return True
    if payload.score_input_mode == "estimated_score_and_rank" and not payload.student_rank_override:
        return True
    if payload.score_input_mode == "rank_range" and (not payload.rank_range_min or not payload.rank_range_max):
        return True
    return False


def _normalize_payload_for_readiness(session: Session, payload: VolunteerWorkbenchPreviewPayload):
    student = session.get(Student, payload.student_id)
    detected_candidate_type = "general"
    if student:
        from ._recommendations_candidates import detect_student_type

        detected_candidate_type = detect_student_type(student)
    profile_candidate_type = ""
    profile_art_track = None
    try:
        from app.models import StudentPathwayProfile
        from sqlalchemy import select

        profile = session.scalar(
            select(StudentPathwayProfile)
            .where(
                StudentPathwayProfile.student_id == payload.student_id,
                StudentPathwayProfile.is_active.is_(True),
            )
            .order_by((StudentPathwayProfile.province == payload.province).desc(), StudentPathwayProfile.id.desc())
        )
        if profile:
            profile_candidate_type = (profile.candidate_type or "").strip()
            profile_art_track = profile.art_track
    except Exception:
        profile_candidate_type = ""
        profile_art_track = None
    return normalize_volunteer_fields(
        province=payload.province,
        candidate_type=payload.candidate_type or profile_candidate_type,
        art_track=payload.art_track or profile_art_track,
        batch=payload.batch,
        detected_candidate_type=detected_candidate_type,
    )


def _build_art_blocking_items(session: Session | None, normalized, payload: VolunteerWorkbenchPreviewPayload) -> list[VolunteerGuideReadinessItemRead]:
    if not normalized or normalized.candidate_type != "art":
        return []
    items: list[VolunteerGuideReadinessItemRead] = []
    if not normalized.art_track:
        items.append(
            VolunteerGuideReadinessItemRead(
                code="invalid_art_track" if payload.art_track else "missing_art_track",
                level="blocking",
                title="艺术类别不可用" if payload.art_track else "缺少艺术类别",
                detail=(
                    "当前艺术类别不是系统可识别的山东省统考类别；请重新选择音乐类、美术与设计类等标准类别。"
                    if payload.art_track
                    else "艺术类学生需要选择音乐类、美术与设计类等艺术类别后，才能按对应公式计算综合分。"
                ),
            )
        )
    if normalized.art_track in {"opera"}:
        items.append(
            VolunteerGuideReadinessItemRead(
                code="art_manual_review_required",
                level="blocking",
                title="该艺术类别需人工复核",
                detail="戏曲类、校考或省际联考录取原则差异较大，暂不自动包装成录取把握。",
            )
        )
    if payload.culture_score is None and payload.comprehensive_score is None:
        items.append(
            VolunteerGuideReadinessItemRead(
                code="missing_art_culture_score",
                level="blocking",
                title="缺少文化成绩",
                detail="艺术类推荐需要文化成绩；可选择参考考试自动带入校内总分，或手动填写文化分。",
            )
        )
    has_profile_professional_score = False
    if payload.professional_score is None and session is not None:
        profile = None
        try:
            from app.models import StudentPathwayProfile
            from sqlalchemy import select

            profile = session.scalar(
                select(StudentPathwayProfile)
                .where(
                    StudentPathwayProfile.student_id == payload.student_id,
                    StudentPathwayProfile.is_active.is_(True),
                )
                .order_by((StudentPathwayProfile.province == payload.province).desc(), StudentPathwayProfile.id.desc())
            )
        except Exception:
            profile = None
        has_profile_professional_score = bool(profile and profile.art_professional_score is not None)
    if payload.professional_score is None and not has_profile_professional_score:
        items.append(
            VolunteerGuideReadinessItemRead(
                code="missing_art_professional_score",
                level="blocking",
                title="缺少艺术专业分",
                detail="艺术类推荐必须维护专业统考分；请在学生升学画像中补齐，或本次手动填写专业分。",
            )
        )
    return items


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
        missing_plan_item = next(
            (item for item in readiness.items if item.code in MISSING_TARGET_YEAR_PLAN_CODES),
            None,
        )
        actions = [
            VolunteerGuideNextActionRead(
                code="fix_blocking_items",
                level="warning",
                title="先补齐阻断项" if not missing_plan_item else "先处理招生计划",
                detail=(
                    "可开启“历年映射估算”做历史计划模拟，或先导入当年正式招生计划。"
                    if missing_plan_item
                    else "补齐位次、规则或候选数据后再生成志愿草稿。"
                ),
            ),
            VolunteerGuideNextActionRead(
                code="no_candidates",
                level="warning",
                title="暂无可加入候选",
                detail=(
                    "当前缺少目标年份正式计划，不能直接生成正式志愿候选。"
                    if missing_plan_item
                    else "当前不能直接加入志愿表，请调整条件或补充招生计划/录取数据。"
                ),
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
