from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.repositories.recommendations import list_province_volunteer_rules
from app.schemas.recommendation import (
    VolunteerGuideArtScoreFormulaRead,
    VolunteerGuideOptionItemRead,
    VolunteerGuideOptionsRead,
)


ART_LEGACY_CANDIDATE_TYPE_TO_TRACK = {
    "art": "fine_art_design",
    "fine_art": "fine_art_design",
    "fine_art_design": "fine_art_design",
    "美术": "fine_art_design",
    "美术类": "fine_art_design",
    "美术与设计类": "fine_art_design",
    "music": "music",
    "音乐类": "music",
    "dance": "dance",
    "舞蹈类": "dance",
    "media": "broadcast_hosting",
    "传媒类": "broadcast_hosting",
    "broadcast": "broadcast_hosting",
    "broadcast_hosting": "broadcast_hosting",
    "播音与主持类": "broadcast_hosting",
    "calligraphy": "calligraphy",
    "书法类": "calligraphy",
    "performance": "performance_directing",
    "performance_directing": "performance_directing",
    "表导演": "performance_directing",
    "表（导）演类": "performance_directing",
    "opera": "opera",
    "戏曲类": "opera",
}

ART_TRACK_LABELS = {
    "fine_art_design": "美术与设计类",
    "music": "音乐类",
    "dance": "舞蹈类",
    "performance_directing": "表（导）演类",
    "calligraphy": "书法类",
    "broadcast_hosting": "播音与主持类",
    "opera": "戏曲类",
}

ART_SCORE_FORMULAS = {
    "fine_art_design": (0.5, 0.5, "文化成绩 * 50% + 专业成绩 * 750 / 300 * 50%"),
    "music": (0.5, 0.5, "文化成绩 * 50% + 专业成绩 * 750 / 300 * 50%"),
    "dance": (0.5, 0.5, "文化成绩 * 50% + 专业成绩 * 750 / 300 * 50%"),
    "performance_directing": (0.5, 0.5, "文化成绩 * 50% + 专业成绩 * 750 / 300 * 50%"),
    "calligraphy": (0.6, 0.4, "文化成绩 * 60% + 专业成绩 * 750 / 300 * 40%"),
    "broadcast_hosting": (0.7, 0.3, "文化成绩 * 70% + 专业成绩 * 750 / 300 * 30%"),
}

ART_MANUAL_REVIEW_TRACKS = {"opera"}

SHANDONG_BATCH_ALIASES = {
    "艺术本科批": "艺术类本科批统考",
    "艺术类本科批": "艺术类本科批统考",
    "艺术类本科统考批": "艺术类本科批统考",
    "艺术本科统考批": "艺术类本科批统考",
    "艺术专科批": "艺术类专科批",
    "体育常规批": "常规批",
    "普通类常规批": "常规批",
}

SHANDONG_COMPATIBLE_BATCHES = {
    "艺术类本科批统考": ("艺术类本科批统考", "艺术类本科批", "艺术本科批", "本科批"),
    "艺术类专科批": ("艺术类专科批", "艺术专科批", "专科批"),
    "常规批": ("常规批", "普通类常规批", "体育常规批"),
}


@dataclass(frozen=True)
class NormalizedVolunteerFields:
    candidate_type: str
    art_track: str | None
    batch: str | None
    batch_alias_applied: bool = False
    input_batch: str | None = None
    input_candidate_type: str | None = None
    notes: tuple[str, ...] = ()


def normalize_art_track(value: str | None) -> str | None:
    normalized = (value or "").strip()
    if not normalized:
        return None
    return ART_LEGACY_CANDIDATE_TYPE_TO_TRACK.get(normalized, normalized)


def normalize_batch(province: str, batch: str | None) -> tuple[str | None, bool]:
    normalized = (batch or "").strip()
    if not normalized:
        return None, False
    if province.strip() == "山东" and normalized in SHANDONG_BATCH_ALIASES:
        return SHANDONG_BATCH_ALIASES[normalized], True
    return normalized, False


def compatible_batches(province: str, batch: str | None, candidate_type: str | None = None) -> tuple[str, ...]:
    normalized_batch, _ = normalize_batch(province, batch)
    if not normalized_batch:
        return ()
    if province.strip() == "山东":
        if (candidate_type or "").strip() == "art" and normalized_batch == "本科批":
            return ("本科批", "艺术类本科批统考", "艺术类本科批", "艺术本科批")
        return SHANDONG_COMPATIBLE_BATCHES.get(normalized_batch, (normalized_batch,))
    return (normalized_batch,)


def normalize_volunteer_fields(
    *,
    province: str,
    candidate_type: str | None,
    art_track: str | None,
    batch: str | None,
    detected_candidate_type: str,
) -> NormalizedVolunteerFields:
    notes: list[str] = []
    input_candidate_type = (candidate_type or "").strip() or None
    normalized_candidate_type = input_candidate_type or detected_candidate_type
    normalized_art_track = normalize_art_track(art_track)
    legacy_track = normalize_art_track(normalized_candidate_type)
    if legacy_track and normalized_candidate_type not in {"art", "sports", "general", "spring_exam", "independent_recruitment", "comprehensive_evaluation", "repeat"}:
        normalized_candidate_type = "art"
        normalized_art_track = normalized_art_track or legacy_track
        notes.append("已将旧版艺术细分类别归一为艺术类，并单独记录艺术类别。")
    if normalized_candidate_type == "art":
        normalized_art_track = normalized_art_track or normalize_art_track(art_track)
    normalized_batch, alias_applied = normalize_batch(province, batch)
    input_batch = (batch or "").strip() or None
    if alias_applied and input_batch and normalized_batch:
        notes.append(f"已将批次“{input_batch}”按规则口径归一为“{normalized_batch}”。")
    return NormalizedVolunteerFields(
        candidate_type=normalized_candidate_type,
        art_track=normalized_art_track,
        batch=normalized_batch,
        batch_alias_applied=alias_applied,
        input_batch=input_batch,
        input_candidate_type=input_candidate_type,
        notes=tuple(notes),
    )


def calculate_art_comprehensive_score(
    *,
    art_track: str,
    culture_score: float,
    professional_score: float,
    professional_full_score: float | None = None,
) -> float | None:
    normalized_track = normalize_art_track(art_track)
    if not normalized_track or normalized_track not in ART_SCORE_FORMULAS:
        return None
    full_score = professional_full_score or 300
    if full_score <= 0:
        full_score = 300
    culture_weight, professional_weight, _ = ART_SCORE_FORMULAS[normalized_track]
    return round(float(culture_score) * culture_weight + float(professional_score) * 750 / full_score * professional_weight, 2)


def get_volunteer_guide_options(
    session: Session,
    *,
    province: str = "山东",
    year: int | None = None,
) -> VolunteerGuideOptionsRead:
    target_year = year or 2026
    rules = list_province_volunteer_rules(session, province=province, year=target_year)
    maintained = sorted({item.batch for item in rules})
    rule_batches = {item.batch for item in rules}
    canonical_batches = []
    for batch in ["常规批", "本科批", "艺术类本科批统考", "专科批", "艺术类专科批", *maintained]:
        if batch in rule_batches and batch not in canonical_batches:
            canonical_batches.append(batch)
    formulas = {
        key: VolunteerGuideArtScoreFormulaRead(
            art_track=key,
            label=ART_TRACK_LABELS[key],
            culture_weight=value[0],
            professional_weight=value[1],
            professional_full_score=300,
            formula_text=value[2],
            requires_manual_review=False,
        )
        for key, value in ART_SCORE_FORMULAS.items()
    }
    formulas["opera"] = VolunteerGuideArtScoreFormulaRead(
        art_track="opera",
        label=ART_TRACK_LABELS["opera"],
        culture_weight=None,
        professional_weight=None,
        professional_full_score=300,
        formula_text="戏曲类、校考或省际联考按当年公告和院校章程人工复核。",
        requires_manual_review=True,
    )
    return VolunteerGuideOptionsRead(
        province=province,
        year=target_year,
        candidate_types=[
            VolunteerGuideOptionItemRead(value="general", label="普通类"),
            VolunteerGuideOptionItemRead(value="art", label="艺术类"),
            VolunteerGuideOptionItemRead(value="sports", label="体育类"),
            VolunteerGuideOptionItemRead(value="spring_exam", label="春季高考"),
            VolunteerGuideOptionItemRead(value="independent_recruitment", label="高职单招"),
            VolunteerGuideOptionItemRead(value="comprehensive_evaluation", label="高职综评"),
        ],
        art_tracks=[VolunteerGuideOptionItemRead(value=key, label=label) for key, label in ART_TRACK_LABELS.items()],
        batches=[VolunteerGuideOptionItemRead(value=batch, label=batch) for batch in canonical_batches],
        batch_aliases=dict(SHANDONG_BATCH_ALIASES if province == "山东" else {}),
        score_input_modes=[
            VolunteerGuideOptionItemRead(value="actual_rank", label="正式位次（高考省位次）"),
            VolunteerGuideOptionItemRead(value="actual_score", label="正式分数"),
            VolunteerGuideOptionItemRead(value="estimated_score", label="校内分数估算"),
            VolunteerGuideOptionItemRead(value="estimated_score_and_rank", label="预估分 + 预估位次（本次考试/模拟推荐）"),
            VolunteerGuideOptionItemRead(value="score_range", label="分数区间"),
            VolunteerGuideOptionItemRead(value="rank_range", label="位次区间"),
        ],
        art_score_formulas=formulas,
        maintained_rule_batches=maintained,
    )
