from __future__ import annotations

from typing import Any

from app.analytics.recommendations import classify_ratio, classify_score_gap, weighted_reference_rank
from app.models import AdmissionRecord, Major, MajorEmploymentMapping, RecommendationResult, Student

from ._recommendations_candidates import is_art_like_student_type
from ._recommendations_score_input import apply_input_context_to_evaluation


career_match_strength_weights = {
    "core": 1.0,
    "high": 0.82,
    "medium": 0.64,
    "transferable": 0.46,
}

career_match_strength_order = {
    "core": 0,
    "high": 1,
    "medium": 2,
    "transferable": 3,
    "pending": 4,
}

career_match_strength_labels = {
    "core": "核心相关",
    "high": "强相关",
    "medium": "一般相关",
    "transferable": "可转化",
    "pending": "待维护",
}

career_direction_priority_weights = {
    "primary": 1.0,
    "secondary": 0.76,
    "alternative": 0.52,
}

career_direction_priority_labels = {
    "primary": "首选方向",
    "secondary": "次选方向",
    "alternative": "替代方向",
}

postgraduate_keywords = ("读研", "研究生", "硕士", "博士", "深造")
certificate_keywords = ("资格证", "执业", "注册", "持证", "证书", "法考", "注会", "医师", "教师资格")
long_training_keywords = ("规培", "长周期", "长期培养", "长期训练", "住院医师", "司法考试")
public_service_keywords = ("考公", "考编", "选调", "事业单位", "公务员")


def build_career_preference_state(
    *,
    primary_direction_id: int | None = None,
    primary_direction_name: str | None = None,
    secondary_direction_id: int | None = None,
    secondary_direction_name: str | None = None,
    alternative_direction_id: int | None = None,
    alternative_direction_name: str | None = None,
    priority_focuses_json: list[str] | None = None,
    preferred_industries_json: list[str] | None = None,
    preferred_job_types_json: list[str] | None = None,
    target_employment_cities_json: list[str] | None = None,
    accepts_postgraduate: bool = False,
    accepts_public_service: bool = False,
    accepts_certificate: bool = False,
    accepts_long_training: bool = False,
) -> dict[str, Any] | None:
    direction_sequence = [
        ("primary", primary_direction_id, primary_direction_name),
        ("secondary", secondary_direction_id, secondary_direction_name),
        ("alternative", alternative_direction_id, alternative_direction_name),
    ]
    direction_ids: list[int] = []
    direction_name_map: dict[int, str] = {}
    direction_priority_map: dict[int, str] = {}
    direction_weight_map: dict[int, float] = {}
    for priority_key, direction_id, direction_name in direction_sequence:
        if direction_id is None:
            continue
        direction_ids.append(direction_id)
        direction_name_map[direction_id] = (direction_name or "").strip() or f"方向 {direction_id}"
        direction_priority_map[direction_id] = priority_key
        direction_weight_map[direction_id] = career_direction_priority_weights[priority_key]

    priority_focuses = _dedupe_ordered_strings(priority_focuses_json)
    preferred_industries = _dedupe_ordered_strings(preferred_industries_json)
    preferred_job_types = _dedupe_ordered_strings(preferred_job_types_json)
    target_cities = _dedupe_ordered_strings(target_employment_cities_json)
    is_active = bool(direction_ids or priority_focuses or preferred_industries or preferred_job_types or target_cities)
    if not is_active:
        return None

    return {
        "direction_ids": direction_ids,
        "direction_name_map": direction_name_map,
        "direction_priority_map": direction_priority_map,
        "direction_weight_map": direction_weight_map,
        "priority_focuses_json": priority_focuses,
        "preferred_industries_json": preferred_industries,
        "preferred_job_types_json": preferred_job_types,
        "target_employment_cities_json": target_cities,
        "accepts_postgraduate": accepts_postgraduate,
        "accepts_public_service": accepts_public_service,
        "accepts_certificate": accepts_certificate,
        "accepts_long_training": accepts_long_training,
    }


def evaluate_career_alignment(
    *,
    major: Major | None,
    mappings: list[MajorEmploymentMapping],
    preference: dict[str, Any] | None,
    training_location: str | None = None,
    college_location: str | None = None,
) -> dict[str, object] | None:
    if not preference:
        return None

    profile_text = " ".join(
        segment.strip()
        for segment in [major.direction if major else None, major.career_path if major else None, major.note if major else None]
        if segment and segment.strip()
    )
    direction_ids = preference["direction_ids"]
    direction_name_map = preference["direction_name_map"]
    direction_priority_map = preference["direction_priority_map"]
    direction_weight_map = preference["direction_weight_map"]
    preferred_industries = preference["preferred_industries_json"]
    preferred_job_types = preference["preferred_job_types_json"]
    target_cities = preference["target_employment_cities_json"]

    matched_direction_entries: list[dict[str, object]] = []
    best_mapping: MajorEmploymentMapping | None = None
    best_mapping_score = 0.0
    best_strength = "pending"
    best_industry_hits: list[str] = []
    best_job_hits: list[str] = []
    best_direction_selected = False

    for mapping in mappings:
        direction = mapping.direction
        if not direction or not direction.is_active:
            continue
        strength_weight = career_match_strength_weights.get(mapping.strength, career_match_strength_weights["medium"])
        direction_score = 0.0
        direction_selected = False
        if mapping.direction_id in direction_weight_map:
            direction_selected = True
            direction_score = 64.0 * direction_weight_map[mapping.direction_id] * strength_weight
            matched_direction_entries.append(
                {
                    "direction_id": mapping.direction_id,
                    "direction_name": direction_name_map.get(mapping.direction_id, direction.name),
                    "priority": direction_priority_map.get(mapping.direction_id, "secondary"),
                    "mapping_strength": mapping.strength,
                    "score": direction_score,
                }
            )

        industry_hits = _match_keywords(
            preferred_industries,
            direction.common_industries_json or [],
            direction.description,
            direction.source_note,
            direction.risk_note,
            profile_text,
        )
        job_hits = _match_keywords(
            preferred_job_types,
            direction.common_job_types_json or [],
            direction.description,
            direction.source_note,
            direction.risk_note,
            profile_text,
        )
        industry_score = 14.0 * strength_weight * _coverage_ratio(industry_hits, preferred_industries)
        job_score = 14.0 * strength_weight * _coverage_ratio(job_hits, preferred_job_types)
        mapping_score = direction_score + industry_score + job_score
        if mapping_score <= 0:
            continue
        if (
            mapping_score > best_mapping_score
            or (
                mapping_score == best_mapping_score
                and career_match_strength_order.get(mapping.strength, 99) < career_match_strength_order.get(best_strength, 99)
            )
        ):
            best_mapping = mapping
            best_mapping_score = mapping_score
            best_strength = mapping.strength if direction_selected else "transferable"
            best_industry_hits = industry_hits
            best_job_hits = job_hits
            best_direction_selected = direction_selected

    text_industry_hits = _match_keywords(preferred_industries, [], profile_text)
    text_job_hits = _match_keywords(preferred_job_types, [], profile_text)
    fallback_text_score = 8.0 * _coverage_ratio(text_industry_hits, preferred_industries) + 8.0 * _coverage_ratio(
        text_job_hits,
        preferred_job_types,
    )
    if best_mapping is None and fallback_text_score > 0:
        best_mapping_score = fallback_text_score
        best_strength = "transferable"
        best_industry_hits = text_industry_hits
        best_job_hits = text_job_hits

    location_text = " ".join(
        segment.strip() for segment in [training_location, college_location] if segment and segment.strip()
    )
    city_hits = _match_keywords(target_cities, [], location_text)
    city_score = 8.0 if city_hits else 0.0

    matched_direction_entries.sort(
        key=lambda item: (
            -float(item["score"]),
            career_match_strength_order.get(str(item["mapping_strength"]), 99),
            direction_ids.index(int(item["direction_id"])) if int(item["direction_id"]) in direction_ids else 99,
        )
    )
    matched_direction_names = [str(item["direction_name"]) for item in matched_direction_entries]

    strongest_direction = best_mapping.direction if best_mapping and best_mapping.direction else None
    requires_postgraduate = _resolve_path_requirement(
        explicit=(
            (best_mapping.requires_postgraduate if best_mapping else False)
            or (strongest_direction.prefers_postgraduate if strongest_direction else False)
        ),
        text_segments=[profile_text, strongest_direction.description if strongest_direction else None],
        keywords=postgraduate_keywords,
    )
    requires_certificate = _resolve_path_requirement(
        explicit=(
            (best_mapping.requires_certificate if best_mapping else False)
            or (strongest_direction.requires_certificate if strongest_direction else False)
        ),
        text_segments=[profile_text, strongest_direction.description if strongest_direction else None],
        keywords=certificate_keywords,
    )
    requires_long_training = _resolve_path_requirement(
        explicit=(strongest_direction.requires_long_cycle if strongest_direction else False),
        text_segments=[
            profile_text,
            strongest_direction.description if strongest_direction else None,
            strongest_direction.risk_note if strongest_direction else None,
        ],
        keywords=long_training_keywords,
    )
    requires_public_service = _resolve_path_requirement(
        explicit=False,
        text_segments=[
            profile_text,
            strongest_direction.description if strongest_direction else None,
            strongest_direction.risk_note if strongest_direction else None,
        ],
        keywords=public_service_keywords,
    )

    reasons: list[str] = []
    risk_flags: list[str] = []
    if matched_direction_entries:
        strongest_match = matched_direction_entries[0]
        reasons.append(
            f"命中{career_direction_priority_labels[str(strongest_match['priority'])]}“{strongest_match['direction_name']}”，"
            f"专业路径为{career_match_strength_labels.get(str(strongest_match['mapping_strength']), '可转化')}。"
        )
    elif direction_ids:
        reasons.append("当前专业未直接命中目标方向映射，先按专业画像和行业/岗位偏好做可转化参考。")
        risk_flags.append("career_mapping_pending")
    elif best_mapping and strongest_direction:
        reasons.append(f"当前专业与“{strongest_direction.name}”存在可转化职业路径。")
    else:
        reasons.append("当前专业与目标职业路径的结构化映射仍待补充。")
        risk_flags.append("career_mapping_pending")

    if best_industry_hits:
        reasons.append(f"覆盖目标行业：{'、'.join(best_industry_hits)}。")
    if best_job_hits:
        reasons.append(f"覆盖目标岗位：{'、'.join(best_job_hits)}。")
    if city_hits:
        reasons.append(f"培养地点/院校所在地贴近目标城市：{'、'.join(city_hits)}。")

    if requires_postgraduate:
        reasons.append("该路径常见读研后竞争力增强。")
        if not preference["accepts_postgraduate"]:
            risk_flags.append("postgraduate_path_mismatch")
            reasons.append("但当前偏好暂不接受读研路径。")
    if requires_certificate:
        reasons.append("该路径常见资格证/执照要求。")
        if not preference["accepts_certificate"]:
            risk_flags.append("certificate_path_mismatch")
            reasons.append("但当前偏好暂不接受资格证路径。")
    if requires_long_training:
        reasons.append("该方向培养周期相对较长。")
        if not preference["accepts_long_training"]:
            risk_flags.append("long_training_path_mismatch")
            reasons.append("但当前偏好暂不接受长培养周期。")
    if requires_public_service and not preference["accepts_public_service"]:
        risk_flags.append("public_service_path_mismatch")
        reasons.append("该路径可能涉及考公/考编等公共服务通道，需结合个人接受度判断。")

    score = max(best_mapping_score + city_score, 0.0)
    if requires_postgraduate and not preference["accepts_postgraduate"]:
        score = max(score - 12.0, 0.0)
    if requires_certificate and not preference["accepts_certificate"]:
        score = max(score - 10.0, 0.0)
    if requires_long_training and not preference["accepts_long_training"]:
        score = max(score - 10.0, 0.0)
    if requires_public_service and not preference["accepts_public_service"]:
        score = max(score - 6.0, 0.0)

    if score <= 0 and not matched_direction_entries and not best_industry_hits and not best_job_hits and not city_hits:
        best_strength = "pending"

    return {
        "career_match_score": round(score, 2),
        "career_match_strength": best_strength,
        "career_match_summary": " ".join(_dedupe_ordered_strings(reasons)),
        "career_match_reasons_json": _dedupe_ordered_strings(reasons),
        "matched_direction_names_json": _dedupe_ordered_strings(matched_direction_names),
        "requires_postgraduate_path": requires_postgraduate,
        "requires_certificate_path": requires_certificate,
        "requires_long_training_path": requires_long_training,
        "risk_flags_json": _dedupe_ordered_strings(risk_flags),
        "matched_direction_count": len(matched_direction_entries),
        "used_direction_mapping": bool(best_mapping and best_direction_selected),
    }


def evaluate_recommendation_candidate(
    *,
    student: Student,
    student_type: str,
    student_rank: int | None,
    score_value: float | None,
    records: list[AdmissionRecord],
    thresholds: dict[str, float],
    is_whitelisted: bool = False,
    career_alignment: dict[str, object] | None = None,
) -> dict[str, object] | None:
    if not records:
        return None

    first = sorted(records, key=lambda item: item.year, reverse=True)[0]
    rank_values = [(item.year, item.min_rank) for item in records if item.min_rank]
    reference_rank = weighted_reference_rank([(year, rank) for year, rank in rank_values if rank is not None])
    risk_flags: list[str] = []
    ratio = None
    result_type = None
    score_basis = "rank"

    if reference_rank and student_rank:
        ratio = round(student_rank / reference_rank, 4)
        result_type = classify_ratio(
            ratio,
            safe_max=thresholds["safe"],
            steady_max=thresholds["steady"],
            rush_max=thresholds["rush"],
        )
        if len(rank_values) < 2:
            risk_flags.append("sample_insufficient")
    elif first.min_score is not None and score_value is not None:
        result_type = classify_score_gap(round(score_value - first.min_score, 2))
        score_basis = "comprehensive_score" if is_art_like_student_type(student_type) else "score"
        risk_flags.append("rank_missing")
    else:
        return None

    if not result_type:
        return None
    if is_art_like_student_type(student_type):
        risk_flags.append("art_recommendation")
        if first.art_track is None:
            risk_flags.append("track_unconfirmed")
        if score_basis != "rank":
            risk_flags.append("manual_formula_check")
    if is_whitelisted:
        risk_flags.append("whitelist_override")

    reference_years = sorted({item.year for item in records}, reverse=True)[:3]
    reason = (
        f"近{len(reference_years)}年参考数据，院校/专业参考位次约为 {reference_rank}。"
        if reference_rank
        else f"缺少位次，采用分数参考，最近最低分 {first.min_score}。"
    )
    if is_whitelisted:
        reason = f"{reason} 当前院校命中白名单关注。"

    snapshot = {
        "reference_years": reference_years,
        "latest_year": first.year,
        "latest_min_rank": first.min_rank,
        "latest_min_score": first.min_score,
        "province": first.province,
        "college_name": first.college.name if first.college else None,
        "major_name": first.major.name if first.major else None,
        "student_score": score_value,
        "student_rank": student_rank,
    }
    if career_alignment:
        risk_flags.extend(career_alignment.get("risk_flags_json") or [])
        career_summary = str(career_alignment.get("career_match_summary") or "").strip()
        if career_summary:
            reason = f"{reason} {career_summary}"
        snapshot.update(
            {
                "career_match_score": career_alignment.get("career_match_score"),
                "career_match_strength": career_alignment.get("career_match_strength"),
                "career_match_summary": career_alignment.get("career_match_summary"),
                "career_match_reasons_json": career_alignment.get("career_match_reasons_json"),
                "matched_direction_names_json": career_alignment.get("matched_direction_names_json"),
                "requires_postgraduate_path": career_alignment.get("requires_postgraduate_path"),
                "requires_certificate_path": career_alignment.get("requires_certificate_path"),
                "requires_long_training_path": career_alignment.get("requires_long_training_path"),
            }
        )
    return {
        "result_type": result_type,
        "reference_rank": reference_rank,
        "student_rank": student_rank,
        "score_basis": score_basis,
        "ratio": ratio,
        "reason_text": reason,
        "risk_flags_json": _dedupe_ordered_strings(risk_flags) or None,
        "snapshot_json": snapshot,
        "latest_year": first.year,
        "latest_min_rank": first.min_rank,
        "latest_min_score": first.min_score,
        "career_match_score": career_alignment.get("career_match_score") if career_alignment else None,
        "career_match_strength": career_alignment.get("career_match_strength") if career_alignment else None,
        "career_match_summary": career_alignment.get("career_match_summary") if career_alignment else None,
        "career_match_reasons_json": career_alignment.get("career_match_reasons_json") if career_alignment else [],
        "matched_direction_names_json": career_alignment.get("matched_direction_names_json") if career_alignment else [],
        "requires_postgraduate_path": career_alignment.get("requires_postgraduate_path") if career_alignment else None,
        "requires_certificate_path": career_alignment.get("requires_certificate_path") if career_alignment else None,
        "requires_long_training_path": career_alignment.get("requires_long_training_path") if career_alignment else None,
    }


def build_recommendation_result(
    *,
    student: Student,
    exam_id: int,
    scheme_id: int,
    student_type: str,
    student_rank: int | None,
    score_value: float | None,
    records: list[AdmissionRecord],
    thresholds: dict[str, float],
    is_whitelisted: bool = False,
    career_alignment: dict[str, object] | None = None,
    input_context: dict[str, object] | None = None,
) -> RecommendationResult | None:
    evaluation = evaluate_recommendation_candidate(
        student=student,
        student_type=student_type,
        student_rank=student_rank,
        score_value=score_value,
        records=records,
        thresholds=thresholds,
        is_whitelisted=is_whitelisted,
        career_alignment=career_alignment,
    )
    if not evaluation:
        return None
    if input_context:
        apply_input_context_to_evaluation(evaluation, input_context)
    return RecommendationResult(
        student_id=student.id,
        exam_id=exam_id,
        scheme_id=scheme_id,
        result_type=evaluation["result_type"],
        college_id=records[0].college_id,
        major_id=records[0].major_id,
        reference_rank=evaluation["reference_rank"],
        student_rank=evaluation["student_rank"],
        score_basis=evaluation["score_basis"],
        ratio=evaluation["ratio"],
        reason_text=evaluation["reason_text"],
        risk_flags_json=evaluation["risk_flags_json"],
        snapshot_json=evaluation["snapshot_json"],
    )


def build_recommendation_sort_key(
    *,
    result_type: str,
    career_match_score: float | None,
    career_match_strength: str | None,
    ratio: float | None,
    reference_rank: int | None,
    college_name: str | None,
    major_name: str | None,
    fallback_priority_score: float | None = None,
) -> tuple[int, float, float, int, float, int, str, str]:
    result_order = {
        "challenge": 0,
        "steady": 1,
        "safe": 2,
        "watch": 3,
    }
    return (
        result_order.get(result_type, 9),
        -(fallback_priority_score if fallback_priority_score is not None else -1.0),
        -(career_match_score if career_match_score is not None else -1.0),
        career_match_strength_order.get(career_match_strength or "pending", 99),
        ratio if ratio is not None else 999.0,
        reference_rank or 999999,
        college_name or "",
        major_name or "",
    )


def _coverage_ratio(hits: list[str], expected: list[str]) -> float:
    if not hits or not expected:
        return 0.0
    return min(len(hits) / len(expected), 1.0)


def _dedupe_ordered_strings(values: list[str] | None) -> list[str]:
    if not values:
        return []
    seen: set[str] = set()
    normalized: list[str] = []
    for value in values:
        current = (value or "").strip()
        if not current or current in seen:
            continue
        seen.add(current)
        normalized.append(current)
    return normalized


def _match_keywords(preferences: list[str], options: list[str], *texts: str | None) -> list[str]:
    if not preferences:
        return []
    normalized_options = _dedupe_ordered_strings(options)
    searchable_text = " ".join(segment.strip() for segment in texts if segment and segment.strip())
    hits: list[str] = []
    for keyword in preferences:
        if any(keyword in option or option in keyword for option in normalized_options) or (searchable_text and keyword in searchable_text):
            hits.append(keyword)
    return _dedupe_ordered_strings(hits)


def _resolve_path_requirement(
    *,
    explicit: bool,
    text_segments: list[str | None],
    keywords: tuple[str, ...],
) -> bool:
    if explicit:
        return True
    text = " ".join(segment.strip() for segment in text_segments if segment and segment.strip())
    return any(keyword in text for keyword in keywords)
