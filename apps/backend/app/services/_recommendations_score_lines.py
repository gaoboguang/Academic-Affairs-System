from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models import EnrollmentPlan


SCORE_LINE_SUPPORTED_STUDENT_TYPES = {"art", "sports"}
PLAN_ONLY_REFERENCE_SUPPORTED_STUDENT_TYPES = {"spring_exam", "independent_recruitment", "comprehensive_evaluation"}

LINE_TYPE_LABELS = {
    "junior_culture_control": "专科文化控制线",
    "undergrad_culture_control": "本科文化控制线",
    "first_section_composite": "一段综合分线",
    "second_section_composite": "二段综合分线",
    "undergrad_culture_art_music_calligraphy": "本科文化控制线（美术/音乐/书法）",
    "undergrad_culture_broadcast_hosting": "本科文化控制线（播音主持）",
    "undergrad_culture_dance_performance_opera": "本科文化控制线（舞蹈/表演/戏曲）",
}


@dataclass
class ScoreLineReference:
    year: int
    province: str
    candidate_type: str
    batch_name: str
    line_type: str
    line_label: str
    score: float
    score_basis: str
    remark: str | None = None
    source_title: str | None = None
    source_url: str | None = None


def supports_score_line_reference(student_type: str) -> bool:
    return (student_type or "").strip() in SCORE_LINE_SUPPORTED_STUDENT_TYPES


def supports_plan_only_reference(student_type: str) -> bool:
    return (student_type or "").strip() in PLAN_ONLY_REFERENCE_SUPPORTED_STUDENT_TYPES


def build_plan_only_reference_evaluation(
    *,
    province: str,
    target_year: int,
    student_type: str,
    plan: EnrollmentPlan,
) -> dict[str, object] | None:
    if not supports_plan_only_reference(student_type):
        return None
    candidate_type_label = _candidate_type_label(student_type)
    reason = (
        f"当前缺少“{candidate_type_label}”专门录取结果，也未接入可直接复用的官方控制线，"
        f"先按 {province} {target_year} 年当年招生计划做方向性初筛。"
        "该结果不能直接作为冲稳保或录取把握判断。"
    )
    return {
        "result_type": "challenge",
        "reference_rank": None,
        "student_rank": None,
        "score_basis": "plan_only",
        "ratio": None,
        "reason_text": reason,
        "risk_flags_json": ["plan_only_reference", "manual_formula_check"],
        "snapshot_json": {
            "reference_years": [plan.year],
            "latest_year": plan.year,
            "latest_min_rank": None,
            "latest_min_score": None,
            "province": province,
            "college_name": plan.college.name if plan.college else None,
            "major_name": plan.major.name if plan.major else plan.major_name_snapshot,
            "student_score": None,
            "student_rank": None,
            "plan_only_reference": True,
            "reference_scope": "plan_only",
            "reference_candidate_type": student_type,
            "reference_note": "仅按当年招生计划清单初筛",
        },
        "latest_year": plan.year,
        "latest_min_rank": None,
        "latest_min_score": None,
        "career_match_score": None,
        "career_match_strength": None,
        "career_match_summary": None,
        "career_match_reasons_json": [],
        "matched_direction_names_json": [],
        "requires_postgraduate_path": None,
        "requires_certificate_path": None,
        "requires_long_training_path": None,
    }


def build_score_line_reference_evaluation(
    session: Session,
    *,
    province: str,
    target_year: int,
    student_type: str,
    plan: EnrollmentPlan,
    score_value: float | None,
    score_source: str | None,
) -> tuple[dict[str, object], ScoreLineReference] | None:
    if score_value is None or not supports_score_line_reference(student_type):
        return None
    reference = get_best_score_line_reference(
        session,
        province=province,
        target_year=target_year,
        student_type=student_type,
        batch=plan.batch,
        major_name=plan.major.name if plan.major else plan.major_name_snapshot,
        score_source=score_source,
    )
    if not reference or float(score_value) < float(reference.score):
        return None

    reference_years = [reference.year]
    reason_parts = [
        f"当前缺少“{student_type}”专门录取结果，先按 {province} {reference.year} 年{reference.candidate_type}{reference.batch_name}{reference.line_label} {reference.score:g} 分做资格参考。",
        "该结果仅用于初筛，不代表院校或专业录取把握。",
    ]
    if reference.remark:
        reason_parts.append(reference.remark)

    risk_flags = ["score_line_reference_only"]
    if reference.year != target_year:
        risk_flags.append("cross_year_score_line_reference")
    if reference.score_basis != "score":
        risk_flags.append("manual_formula_check")

    evaluation = {
        "result_type": "challenge",
        "reference_rank": None,
        "student_rank": None,
        "score_basis": reference.score_basis,
        "ratio": None,
        "reason_text": " ".join(reason_parts),
        "risk_flags_json": sorted(set(risk_flags)),
        "snapshot_json": {
            "reference_years": reference_years,
            "latest_year": reference.year,
            "latest_min_rank": None,
            "latest_min_score": reference.score,
            "province": province,
            "college_name": plan.college.name if plan.college else None,
            "major_name": plan.major.name if plan.major else plan.major_name_snapshot,
            "student_score": score_value,
            "student_rank": None,
            "score_line_reference": True,
            "score_line_candidate_type": reference.candidate_type,
            "score_line_batch_name": reference.batch_name,
            "score_line_line_type": reference.line_type,
            "score_line_line_label": reference.line_label,
            "score_line_score": reference.score,
            "score_line_year": reference.year,
            "score_line_remark": reference.remark,
            "score_line_source_title": reference.source_title,
            "score_line_source_url": reference.source_url,
            "score_line_score_basis": reference.score_basis,
        },
        "latest_year": reference.year,
        "latest_min_rank": None,
        "latest_min_score": reference.score,
        "career_match_score": None,
        "career_match_strength": None,
        "career_match_summary": None,
        "career_match_reasons_json": [],
        "matched_direction_names_json": [],
        "requires_postgraduate_path": None,
        "requires_certificate_path": None,
        "requires_long_training_path": None,
    }
    return evaluation, reference


def get_best_score_line_reference(
    session: Session,
    *,
    province: str,
    target_year: int,
    student_type: str,
    batch: str | None,
    major_name: str | None,
    score_source: str | None,
) -> ScoreLineReference | None:
    candidate_type = _score_line_candidate_type(student_type)
    if not candidate_type:
        return None
    rows = _load_score_line_rows(session, province=province, candidate_type=candidate_type)
    if not rows:
        return None

    available_years = sorted({int(row["year"]) for row in rows if row.get("year") is not None}, reverse=True)
    preferred_years = [year for year in available_years if year <= target_year] or available_years
    preferred_pairs = _preferred_score_line_pairs(
        student_type=student_type,
        batch=batch,
        major_name=major_name,
        score_source=score_source,
    )
    for year in preferred_years:
        for batch_name, line_type in preferred_pairs:
            row = next(
                (
                    item
                    for item in rows
                    if int(item["year"]) == year
                    and str(item["batch_name"] or "").strip() == batch_name
                    and str(item["line_type"] or "").strip() == line_type
                ),
                None,
            )
            if not row:
                continue
            current_line_type = str(row["line_type"]).strip()
            return ScoreLineReference(
                year=int(row["year"]),
                province=province,
                candidate_type=candidate_type,
                batch_name=str(row["batch_name"]).strip(),
                line_type=current_line_type,
                line_label=LINE_TYPE_LABELS.get(current_line_type, current_line_type),
                score=float(row["score"]),
                score_basis=_score_basis_for_line_type(current_line_type),
                remark=_clean_optional_text(row["remark"]),
                source_title=_clean_optional_text(row["source_title"]),
                source_url=_clean_optional_text(row["source_url"]),
            )
    return None


def _preferred_score_line_pairs(
    *,
    student_type: str,
    batch: str | None,
    major_name: str | None,
    score_source: str | None,
) -> list[tuple[str, str]]:
    normalized_batch = (batch or "").strip()
    normalized_major_name = (major_name or "").strip()
    normalized_score_source = (score_source or "").strip()
    if student_type == "art":
        if "专科" in normalized_batch:
            return [("专科", "junior_culture_control")]
        if _is_broadcast_hosting_major(normalized_major_name):
            return [("本科", "undergrad_culture_broadcast_hosting")]
        if _is_art_music_calligraphy_major(normalized_major_name):
            return [("本科", "undergrad_culture_art_music_calligraphy")]
        if _is_dance_performance_major(normalized_major_name):
            return [("本科", "undergrad_culture_dance_performance_opera")]
        return [("本科", "undergrad_culture_art_music_calligraphy")]
    if student_type == "sports":
        if "专科" in normalized_batch:
            if normalized_score_source == "comprehensive_score":
                return [("本科/专科", "second_section_composite"), ("专科", "junior_culture_control")]
            return [("专科", "junior_culture_control"), ("本科/专科", "second_section_composite")]
        if "本科" in normalized_batch:
            if normalized_score_source == "comprehensive_score":
                return [("本科/专科", "first_section_composite"), ("本科", "undergrad_culture_control")]
            return [("本科", "undergrad_culture_control"), ("本科/专科", "first_section_composite")]
        if normalized_score_source == "comprehensive_score":
            return [("本科/专科", "first_section_composite"), ("本科/专科", "second_section_composite")]
        return [("本科", "undergrad_culture_control"), ("专科", "junior_culture_control")]
    return []


def _load_score_line_rows(session: Session, *, province: str, candidate_type: str) -> list[dict[str, object]]:
    has_table = session.execute(
        text(
            """
            SELECT COUNT(*)
            FROM sqlite_master
            WHERE type = 'table' AND name = 'gaokao_score_line'
            """
        )
    ).scalar()
    if not has_table:
        return []
    province_aliases = _province_aliases(province)
    province_placeholders = ", ".join(f":province_{index}" for index in range(len(province_aliases)))
    params = {f"province_{index}": value for index, value in enumerate(province_aliases)}
    params["candidate_type"] = candidate_type
    return [
        dict(row)
        for row in session.execute(
            text(
                f"""
                SELECT year, batch_name, line_type, score, remark, source_title, source_url
                FROM gaokao_score_line
                WHERE province IN ({province_placeholders})
                  AND candidate_type = :candidate_type
                ORDER BY year DESC, id DESC
                """
            ),
            params,
        ).mappings().all()
    ]


def _score_line_candidate_type(student_type: str) -> str | None:
    mapping = {
        "art": "艺术类",
        "sports": "体育类",
    }
    return mapping.get((student_type or "").strip())


def _score_basis_for_line_type(line_type: str) -> str:
    if line_type in {"first_section_composite", "second_section_composite"}:
        return "comprehensive_score"
    if "culture" in line_type:
        return "culture_score"
    return "score"


def _is_broadcast_hosting_major(major_name: str) -> bool:
    return any(keyword in major_name for keyword in ("播音", "主持"))


def _is_art_music_calligraphy_major(major_name: str) -> bool:
    return any(keyword in major_name for keyword in ("音乐", "书法", "设计", "美术", "绘画", "雕塑"))


def _is_dance_performance_major(major_name: str) -> bool:
    return any(keyword in major_name for keyword in ("舞蹈", "表演", "戏曲", "导演"))


def _candidate_type_label(student_type: str) -> str:
    mapping = {
        "spring_exam": "春季高考",
        "independent_recruitment": "单独招生",
        "comprehensive_evaluation": "综合评价招生",
    }
    return mapping.get((student_type or "").strip(), student_type)


def _province_aliases(province: str) -> list[str]:
    normalized = (province or "").strip()
    if normalized == "山东":
        return ["山东", "山东省", "sd", "shandong"]
    return [normalized]


def _clean_optional_text(value: object) -> str | None:
    if value is None:
        return None
    current = str(value).strip()
    return current or None
