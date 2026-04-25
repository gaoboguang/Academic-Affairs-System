from __future__ import annotations

from dataclasses import dataclass
from fastapi import HTTPException
from sqlalchemy import desc, select, text
from sqlalchemy.orm import Session, joinedload

from app.models import AdmissionRecord, EnrollmentPlan, Student, StudentGaokaoScoreProjection
from app.schemas.recommendation import (
    ShandongRushStableSafeCandidateRead,
    ShandongRushStableSafeRecommendationPayload,
    ShandongRushStableSafeRecommendationResponse,
    ShandongRushStableSafeSummaryRead,
)

from ._recommendations_candidates import detect_student_type
from ._recommendations_score_rank import lookup_rank_for_score

B4_REFERENCE_YEARS = (2025, 2024, 2023)
B4_YEAR_WEIGHTS = {2025: 0.5, 2024: 0.3, 2023: 0.2}
B4_BUCKET_LABELS = {
    "rush": "冲",
    "stable": "稳",
    "safe": "保",
    "watch": "仅关注",
}
B4_GENERAL_TYPES = {"", "general", "common", "repeat"}
B4_SUBJECTS = ("物理", "化学", "生物", "政治", "历史", "地理", "技术")


@dataclass(frozen=True)
class ResolvedProjection:
    student_id: int | None
    student_name: str | None
    source_mode: str
    predicted_score: float | None
    predicted_rank: int
    rank_range_low: int | None
    rank_range_high: int | None
    rank_projection_basis: str | None
    input_notes: list[str]


@dataclass(frozen=True)
class PlanSummary:
    target_plan: EnrollmentPlan | None
    historical_plan_counts: dict[int, int]
    plan_change_factor: float | None
    source_document_ids: list[int]
    risk_flags: list[str]
    summary: dict[str, object]


def preview_shandong_rush_stable_safe_recommendations(
    session: Session,
    payload: ShandongRushStableSafeRecommendationPayload,
) -> ShandongRushStableSafeRecommendationResponse:
    _validate_payload(payload)
    projection = _resolve_projection(session, payload)
    student = session.get(Student, projection.student_id) if projection.student_id else None
    if student:
        _validate_student_for_general_shandong(student)

    records = _load_historical_records(session, payload)
    if not records:
        raise HTTPException(status_code=404, detail="当前条件下暂无 2023-2025 山东普通类历史投档数据")
    plans_by_key = _load_plan_lookup(session, payload)
    candidates, excluded_subject_mismatch_count = _build_candidates(
        payload=payload,
        projection=projection,
        records=records,
        plans_by_key=plans_by_key,
    )
    if not candidates:
        raise HTTPException(status_code=404, detail="当前条件下没有可进入冲稳保或仅关注的候选")

    candidates.sort(key=_candidate_sort_key)
    limit = max(1, min(payload.limit, 300))
    rush = [item for item in candidates if item.bucket == "rush"][:limit]
    stable = [item for item in candidates if item.bucket == "stable"][:limit]
    safe = [item for item in candidates if item.bucket == "safe"][:limit]
    watch = [item for item in candidates if item.bucket == "watch"][:limit]

    return ShandongRushStableSafeRecommendationResponse(
        student_id=projection.student_id,
        student_name=projection.student_name,
        province="山东",
        target_year=payload.target_year,
        student_type="general",
        source_mode=projection.source_mode,
        predicted_score=projection.predicted_score,
        predicted_rank=projection.predicted_rank,
        rank_range_low=projection.rank_range_low,
        rank_range_high=projection.rank_range_high,
        rank_projection_basis=projection.rank_projection_basis,
        risk_preference=payload.risk_preference,
        data_years=list(B4_REFERENCE_YEARS),
        input_notes=projection.input_notes,
        summary=ShandongRushStableSafeSummaryRead(
            rush_count=len([item for item in candidates if item.bucket == "rush"]),
            stable_count=len([item for item in candidates if item.bucket == "stable"]),
            safe_count=len([item for item in candidates if item.bucket == "safe"]),
            watch_count=len([item for item in candidates if item.bucket == "watch"]),
            excluded_subject_mismatch_count=excluded_subject_mismatch_count,
        ),
        rush=rush,
        stable=stable,
        safe=safe,
        watch=watch,
    )


def _validate_payload(payload: ShandongRushStableSafeRecommendationPayload) -> None:
    if payload.province.strip() != "山东":
        raise HTTPException(status_code=400, detail="B4 冲稳保推荐当前只支持山东生源地")
    if (payload.student_type or "general").strip() not in B4_GENERAL_TYPES:
        raise HTTPException(status_code=400, detail="B4 冲稳保推荐当前只支持普通类夏季高考")
    if payload.risk_preference not in {"conservative", "balanced", "aggressive"}:
        raise HTTPException(status_code=400, detail="风险偏好只能是 conservative / balanced / aggressive")
    if payload.source_mode not in {"manual_score", "manual_rank", "projection"}:
        raise HTTPException(status_code=400, detail="推荐入口只能使用 projection / manual_score / manual_rank")
    if payload.source_mode == "projection" and payload.projection_id is None:
        raise HTTPException(status_code=400, detail="使用学生预估快照时必须提供 projection_id")
    if payload.source_mode == "manual_rank" and payload.manual_rank is None:
        raise HTTPException(status_code=400, detail="手动位次推荐必须填写 manual_rank")
    if payload.source_mode == "manual_score" and payload.manual_score is None:
        raise HTTPException(status_code=400, detail="手动分数推荐必须填写 manual_score")


def _validate_student_for_general_shandong(student: Student) -> None:
    student_type = detect_student_type(student)
    if student_type not in {"general", "repeat"}:
        raise HTTPException(status_code=400, detail="B4 冲稳保推荐当前只支持普通类学生")
    origin_province = (student.origin_province or "").strip()
    if origin_province and origin_province != "山东":
        raise HTTPException(status_code=400, detail="B4 冲稳保推荐当前只支持山东生源地学生")


def _resolve_projection(
    session: Session,
    payload: ShandongRushStableSafeRecommendationPayload,
) -> ResolvedProjection:
    if payload.source_mode == "projection":
        if not _table_exists(session, "student_gaokao_score_projection"):
            raise HTTPException(status_code=400, detail="缺少学生高考预估快照表，请先运行后端迁移")
        projection = session.get(StudentGaokaoScoreProjection, payload.projection_id)
        if not projection or not projection.is_active:
            raise HTTPException(status_code=404, detail="学生高考预估快照不存在")
        if projection.province != "山东":
            raise HTTPException(status_code=400, detail="该预估快照不是山东生源地")
        rank = projection.predicted_rank or _average_rank_range(projection.rank_range_low, projection.rank_range_high)
        if not rank:
            raise HTTPException(status_code=400, detail="该预估快照缺少可用于推荐的预估位次")
        return ResolvedProjection(
            student_id=projection.student_id,
            student_name=projection.student.name if projection.student else None,
            source_mode=projection.source_mode,
            predicted_score=projection.predicted_score,
            predicted_rank=rank,
            rank_range_low=projection.rank_range_low,
            rank_range_high=projection.rank_range_high,
            rank_projection_basis=projection.rank_projection_basis,
            input_notes=_projection_notes(projection.rank_projection_basis, projection.calculation_detail_json),
        )

    student = session.get(Student, payload.student_id) if payload.student_id else None
    if payload.student_id and not student:
        raise HTTPException(status_code=404, detail="学生不存在")
    if payload.source_mode == "manual_rank":
        rank = int(payload.manual_rank or 0)
        if rank <= 0:
            raise HTTPException(status_code=400, detail="手动位次必须大于 0")
        return ResolvedProjection(
            student_id=payload.student_id,
            student_name=student.name if student else None,
            source_mode="manual_rank",
            predicted_score=payload.manual_score,
            predicted_rank=rank,
            rank_range_low=rank,
            rank_range_high=rank,
            rank_projection_basis="manual_rank",
            input_notes=["当前按手动填写的全省位次作为主排序依据。"],
        )

    score = payload.manual_score or 0
    if score <= 0:
        raise HTTPException(status_code=400, detail="手动预估分数必须大于 0")
    lookup = lookup_rank_for_score(session, province="山东", target_year=payload.target_year, score=score)
    notes = [f"当前按 {lookup.year} 年一分一段把 {score:g} 分换算为约 {lookup.rank} 位。"]
    if lookup.basis == "previous_year_score_rank_segment":
        notes.append(f"{payload.target_year} 年一分一段暂缺，当前按上一年一分一段估算。")
    return ResolvedProjection(
        student_id=payload.student_id,
        student_name=student.name if student else None,
        source_mode="manual_score",
        predicted_score=payload.manual_score,
        predicted_rank=lookup.rank,
        rank_range_low=lookup.rank,
        rank_range_high=lookup.rank,
        rank_projection_basis=lookup.basis,
        input_notes=notes,
    )


def _load_historical_records(
    session: Session,
    payload: ShandongRushStableSafeRecommendationPayload,
) -> list[AdmissionRecord]:
    stmt = (
        select(AdmissionRecord)
        .options(joinedload(AdmissionRecord.college), joinedload(AdmissionRecord.major))
        .where(
            AdmissionRecord.is_active.is_(True),
            AdmissionRecord.province == "山东",
            AdmissionRecord.year.in_(B4_REFERENCE_YEARS),
            AdmissionRecord.student_type.in_(("general", "common", "")),
        )
        .order_by(desc(AdmissionRecord.year), AdmissionRecord.college_id, AdmissionRecord.major_id)
    )
    if payload.batch:
        stmt = stmt.where(AdmissionRecord.batch.contains(_normalize_batch_keyword(payload.batch)))
    records = list(session.scalars(stmt).unique().all())
    return [
        item
        for item in records
        if _matches_candidate_filters(
            college=item.college,
            major_name=item.major.name if item.major else None,
            target_regions=payload.target_regions_json,
            school_levels=payload.school_level_tags_json,
            major_keyword=payload.major_keyword,
        )
    ]


def _load_plan_lookup(
    session: Session,
    payload: ShandongRushStableSafeRecommendationPayload,
) -> dict[tuple[int, int | None], dict[int, EnrollmentPlan]]:
    years = sorted({payload.target_year, *B4_REFERENCE_YEARS})
    stmt = (
        select(EnrollmentPlan)
        .options(joinedload(EnrollmentPlan.college), joinedload(EnrollmentPlan.major))
        .where(
            EnrollmentPlan.is_active.is_(True),
            EnrollmentPlan.province == "山东",
            EnrollmentPlan.year.in_(years),
            EnrollmentPlan.student_type.in_(("general", "common", "")),
        )
        .order_by(desc(EnrollmentPlan.year), EnrollmentPlan.id)
    )
    if payload.batch:
        stmt = stmt.where(EnrollmentPlan.batch.contains(_normalize_batch_keyword(payload.batch)))
    plans = [
        item
        for item in session.scalars(stmt).unique().all()
        if _matches_candidate_filters(
            college=item.college,
            major_name=item.major.name if item.major else item.major_name_snapshot or None,
            target_regions=payload.target_regions_json,
            school_levels=payload.school_level_tags_json,
            major_keyword=payload.major_keyword,
        )
    ]
    lookup: dict[tuple[int, int | None], dict[int, EnrollmentPlan]] = {}
    for item in plans:
        key = (item.college_id, item.major_id)
        lookup.setdefault(key, {})
        lookup[key].setdefault(item.year, item)
    return lookup


def _build_candidates(
    *,
    payload: ShandongRushStableSafeRecommendationPayload,
    projection: ResolvedProjection,
    records: list[AdmissionRecord],
    plans_by_key: dict[tuple[int, int | None], dict[int, EnrollmentPlan]],
) -> tuple[list[ShandongRushStableSafeCandidateRead], int]:
    grouped: dict[tuple[int, int | None], list[AdmissionRecord]] = {}
    for item in records:
        grouped.setdefault((item.college_id, item.major_id), []).append(item)

    candidates: list[ShandongRushStableSafeCandidateRead] = []
    excluded_subject_mismatch_count = 0
    for key, group_records in grouped.items():
        group_records.sort(key=lambda item: item.year, reverse=True)
        plan_summary = _build_plan_summary(plans_by_key.get(key, {}), payload.target_year)
        requirement = _resolve_subject_requirement(group_records, plan_summary.target_plan)
        if requirement and payload.subject_combination and not _subject_requirement_satisfied(requirement, payload.subject_combination):
            excluded_subject_mismatch_count += 1
            continue
        candidate = _build_candidate(
            payload=payload,
            projection=projection,
            records=group_records,
            plan_summary=plan_summary,
            subject_requirement=requirement,
        )
        if candidate:
            candidates.append(candidate)
    return candidates, excluded_subject_mismatch_count


def _build_candidate(
    *,
    payload: ShandongRushStableSafeRecommendationPayload,
    projection: ResolvedProjection,
    records: list[AdmissionRecord],
    plan_summary: PlanSummary,
    subject_requirement: str | None,
) -> ShandongRushStableSafeCandidateRead | None:
    rank_values = [(item.year, item.min_rank) for item in records if item.min_rank]
    if not rank_values:
        return None
    reference_rank = _weighted_reference_rank(rank_values)
    if not reference_rank:
        return None
    latest_record = records[0]
    years_used = sorted({year for year, _ in rank_values}, reverse=True)
    rank_margin = int(round(reference_rank - projection.predicted_rank))
    rank_margin_ratio = round(rank_margin / reference_rank, 4) if reference_rank else None
    risk_flags = _risk_flags_for_projection(projection.rank_projection_basis)
    risk_flags.extend(plan_summary.risk_flags)
    data_confidence = "high"
    if len(years_used) < 3:
        risk_flags.append("three_year_data_incomplete")
        data_confidence = "medium"
    if len(years_used) < 2:
        risk_flags.append("historical_data_missing")
        data_confidence = "low"
    if subject_requirement and not payload.subject_combination:
        risk_flags.append("subject_requirement_check")
    if rank_margin_ratio is None:
        bucket = "watch"
    elif data_confidence == "low":
        bucket = "watch"
    else:
        bucket = _classify_bucket(rank_margin_ratio, payload.risk_preference, risk_flags)
    historical_summary = _build_historical_summary(records, reference_rank, plan_summary)
    score_summary = {
        "predicted_score": projection.predicted_score,
        "predicted_rank": projection.predicted_rank,
        "rank_range_low": projection.rank_range_low,
        "rank_range_high": projection.rank_range_high,
        "rank_projection_basis": projection.rank_projection_basis,
        "reference_rank": reference_rank,
        "latest_min_score": latest_record.min_score,
        "latest_min_rank": latest_record.min_rank,
    }
    source_document_ids = _dedupe_ints(
        [
            *[item.source_document_id for item in records],
            *plan_summary.source_document_ids,
        ]
    )
    explanation = _build_explanation_text(
        bucket=bucket,
        rank_margin=rank_margin,
        rank_margin_ratio=rank_margin_ratio,
        years_used=years_used,
        data_confidence=data_confidence,
        risk_flags=risk_flags,
        subject_requirement=subject_requirement,
    )
    return ShandongRushStableSafeCandidateRead(
        college_id=latest_record.college_id,
        college_name=latest_record.college.name if latest_record.college else "",
        college_code_snapshot=latest_record.college.college_code if latest_record.college else None,
        major_id=latest_record.major_id,
        major_name=latest_record.major.name if latest_record.major else None,
        major_code_snapshot=latest_record.major.major_code if latest_record.major else None,
        bucket=bucket,
        bucket_label=B4_BUCKET_LABELS[bucket],
        rank_margin=rank_margin,
        rank_margin_ratio=rank_margin_ratio,
        score_summary=score_summary,
        years_used=years_used,
        historical_summary=historical_summary,
        plan_count=plan_summary.target_plan.plan_count if plan_summary.target_plan else latest_record.plan_count,
        subject_requirement=subject_requirement,
        data_confidence=data_confidence,
        risk_flags=_dedupe_strings(risk_flags),
        explanation_text=explanation,
        source_document_ids=source_document_ids,
    )


def _build_plan_summary(plans_by_year: dict[int, EnrollmentPlan], target_year: int) -> PlanSummary:
    target_plan = plans_by_year.get(target_year)
    historical_counts = {
        year: plans_by_year[year].plan_count
        for year in B4_REFERENCE_YEARS
        if year in plans_by_year and plans_by_year[year].plan_count is not None
    }
    latest_historical_year = max(historical_counts) if historical_counts else None
    latest_historical_count = historical_counts.get(latest_historical_year) if latest_historical_year else None
    factor = None
    risk_flags: list[str] = []
    if target_plan and latest_historical_count:
        factor = round(target_plan.plan_count / latest_historical_count, 4)
        if factor < 0.85:
            risk_flags.append("plan_decreased")
    elif not target_plan:
        risk_flags.append("plan_missing")
    historical_years = sorted(historical_counts, reverse=True)
    if len(historical_years) >= 2:
        newest_count = historical_counts[historical_years[0]]
        previous_count = historical_counts[historical_years[1]]
        if previous_count and newest_count / previous_count < 0.85:
            risk_flags.append("plan_decreased")
    return PlanSummary(
        target_plan=target_plan,
        historical_plan_counts=historical_counts,
        plan_change_factor=factor,
        source_document_ids=_dedupe_ints([item.source_document_id for item in plans_by_year.values()]),
        risk_flags=_dedupe_strings(risk_flags),
        summary={
            "target_year_plan_count": target_plan.plan_count if target_plan else None,
            "latest_historical_plan_count": latest_historical_count,
            "historical_plan_counts": historical_counts,
            "plan_change_factor": factor,
        },
    )


def _build_historical_summary(
    records: list[AdmissionRecord],
    reference_rank: int,
    plan_summary: PlanSummary,
) -> dict[str, object]:
    rows = [
        {
            "year": item.year,
            "min_rank": item.min_rank,
            "min_score": item.min_score,
            "plan_count": item.plan_count,
            "source_note": item.source_note,
        }
        for item in sorted(records, key=lambda item: item.year, reverse=True)
    ]
    ranks = [int(item.min_rank) for item in records if item.min_rank]
    volatility = None
    if ranks:
        volatility = {
            "min_rank": min(ranks),
            "max_rank": max(ranks),
            "range": max(ranks) - min(ranks),
        }
    return {
        "weighted_reference_rank": reference_rank,
        "rank_rows": rows,
        "rank_volatility": volatility,
        "plan_change": plan_summary.summary,
    }


def _classify_bucket(rank_margin_ratio: float, risk_preference: str, risk_flags: list[str]) -> str:
    thresholds = {
        "conservative": {"rush_min": -0.06, "stable_min": 0.06, "safe_min": 0.22},
        "balanced": {"rush_min": -0.12, "stable_min": 0.03, "safe_min": 0.18},
        "aggressive": {"rush_min": -0.16, "stable_min": 0.0, "safe_min": 0.15},
    }[risk_preference]
    if rank_margin_ratio >= thresholds["safe_min"] and "plan_decreased" not in risk_flags:
        return "safe"
    if rank_margin_ratio >= thresholds["stable_min"]:
        return "stable"
    if rank_margin_ratio >= thresholds["rush_min"]:
        return "rush"
    return "watch"


def _weighted_reference_rank(values: list[tuple[int, int]]) -> int | None:
    available = [(year, rank) for year, rank in values if year in B4_YEAR_WEIGHTS and rank]
    if not available:
        return None
    available.sort(key=lambda item: item[0], reverse=True)
    weight_sum = sum(B4_YEAR_WEIGHTS[year] for year, _ in available)
    if weight_sum <= 0:
        return None
    weighted = sum(rank * (B4_YEAR_WEIGHTS[year] / weight_sum) for year, rank in available)
    return int(round(weighted))


def _build_explanation_text(
    *,
    bucket: str,
    rank_margin: int,
    rank_margin_ratio: float | None,
    years_used: list[int],
    data_confidence: str,
    risk_flags: list[str],
    subject_requirement: str | None,
) -> str:
    ratio_text = f"{rank_margin_ratio:.2%}" if rank_margin_ratio is not None else "无法计算"
    if rank_margin > 0:
        margin_text = f"预估位次优于历史加权参考位次约 {rank_margin} 位"
    elif rank_margin < 0:
        margin_text = f"预估位次弱于历史加权参考位次约 {abs(rank_margin)} 位"
    else:
        margin_text = "预估位次与历史加权参考位次基本持平"
    segments = [
        f"按 {'、'.join(str(year) for year in years_used)} 年山东普通类投档数据计算，{margin_text}，位次边际 {ratio_text}，归为“{B4_BUCKET_LABELS[bucket]}”。",
        f"数据置信度：{_confidence_label(data_confidence)}。",
    ]
    if subject_requirement:
        segments.append(f"选科要求：{subject_requirement}。")
    if "plan_missing" in risk_flags:
        segments.append("当前缺少目标年份正式招生计划，计划变化不能降低风险。")
    if "plan_decreased" in risk_flags:
        segments.append("计划数存在缩招迹象，已提高风险口径。")
    if "three_year_data_incomplete" in risk_flags:
        segments.append("近三年样本不完整，结果需要人工复核。")
    if "rank_projection_from_previous_year" in risk_flags:
        segments.append("预估位次来自上一年一分一段换算。")
    if "rank_projection_from_school_exam" in risk_flags:
        segments.append("预估位次来自校内考试估算，不能直接等同于山东全省位次。")
    return " ".join(segments)


def _risk_flags_for_projection(rank_projection_basis: str | None) -> list[str]:
    if rank_projection_basis == "previous_year_score_rank_segment":
        return ["rank_projection_from_previous_year"]
    if rank_projection_basis and "exam" in rank_projection_basis:
        return ["rank_projection_from_school_exam"]
    return []


def _resolve_subject_requirement(records: list[AdmissionRecord], target_plan: EnrollmentPlan | None) -> str | None:
    if target_plan and _clean_optional_text(target_plan.subject_requirement):
        return _clean_optional_text(target_plan.subject_requirement)
    for item in sorted(records, key=lambda item: item.year, reverse=True):
        requirement = _clean_optional_text(item.subject_requirement)
        if requirement:
            return requirement
    return None


def _subject_requirement_satisfied(requirement: str, subject_combination: str) -> bool:
    requirement_text = requirement.strip()
    if not requirement_text or any(token in requirement_text for token in ("不限", "不提", "无科目要求")):
        return True
    selected = {subject for subject in B4_SUBJECTS if subject in subject_combination}
    required_subjects = [subject for subject in B4_SUBJECTS if subject in requirement_text]
    if not required_subjects:
        return True
    if "或" in requirement_text or "其中" in requirement_text:
        return any(subject in selected for subject in required_subjects)
    return all(subject in selected for subject in required_subjects)


def _matches_candidate_filters(
    *,
    college,
    major_name: str | None,
    target_regions: list[str],
    school_levels: list[str],
    major_keyword: str | None,
) -> bool:
    if target_regions and college and college.province not in target_regions and college.city not in target_regions:
        return False
    if school_levels:
        level_tags = set(college.school_level_tags_json or []) if college else set()
        if not level_tags.intersection(set(school_levels)):
            return False
    if major_keyword and (not major_name or major_keyword not in major_name):
        return False
    return True


def _table_exists(session: Session, table_name: str) -> bool:
    return bool(
        session.execute(
            text(
                """
                SELECT COUNT(*)
                FROM sqlite_master
                WHERE type = 'table' AND name = :table_name
                """
            ),
            {"table_name": table_name},
        ).scalar()
    )


def _projection_notes(rank_projection_basis: str | None, detail: dict | None) -> list[str]:
    notes = []
    for item in (detail or {}).get("notes") or []:
        if isinstance(item, str) and item.strip():
            notes.append(item.strip())
    if rank_projection_basis == "previous_year_score_rank_segment":
        notes.append("当前预估位次按上一年一分一段换算。")
    elif rank_projection_basis and "exam" in rank_projection_basis:
        notes.append("当前预估来自校内考试估算，不能直接等同于山东全省位次。")
    return _dedupe_strings(notes)


def _candidate_sort_key(item: ShandongRushStableSafeCandidateRead) -> tuple[int, float, int, str, str]:
    bucket_order = {"rush": 0, "stable": 1, "safe": 2, "watch": 3}
    return (
        bucket_order.get(item.bucket, 9),
        abs(item.rank_margin_ratio) if item.rank_margin_ratio is not None else 999.0,
        item.historical_summary.get("weighted_reference_rank") or 999999,
        item.college_name,
        item.major_name or "",
    )


def _normalize_batch_keyword(batch: str) -> str:
    if "常规" in batch:
        return "常规"
    return batch


def _average_rank_range(low: int | None, high: int | None) -> int | None:
    if low and high:
        return int(round((low + high) / 2))
    return low or high


def _confidence_label(value: str) -> str:
    return {"high": "较高", "medium": "中等", "low": "较低"}.get(value, value)


def _clean_optional_text(value: object) -> str | None:
    if value is None:
        return None
    text_value = str(value).strip()
    return text_value or None


def _dedupe_strings(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        item = value.strip()
        if not item or item in seen:
            continue
        seen.add(item)
        result.append(item)
    return result


def _dedupe_ints(values: list[int | None]) -> list[int]:
    result: list[int] = []
    seen: set[int] = set()
    for value in values:
        if value is None or value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result
