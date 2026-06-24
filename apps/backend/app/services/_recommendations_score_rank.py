from __future__ import annotations

from dataclasses import dataclass

from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session


@dataclass(frozen=True)
class ScoreRankLookup:
    year: int
    score: float
    rank: int
    basis: str
    source_note: str


# `score_rank_segment` 字段已稳定（schema 见 docs/database-field-mapping.md §3.3）。
# 不再做运行时 PRAGMA 探测，所有过滤条件固定写死。
PROVINCE_FILTER = (
    "AND province IN (:province, :province_alias, :province_alias_cn, :province_alias_en)"
)
SUBJECT_GROUP_FILTER = (
    "AND (subject_group IS NULL OR subject_group = '' OR subject_group IN ('all', '全体'))"
)
SCORE_TYPE_FILTER = (
    "AND (score_type IS NULL OR score_type = '' OR score_type IN ('summer_total', '总分', '普通类'))"
)


def lookup_rank_for_score(
    session: Session,
    *,
    province: str,
    target_year: int,
    score: float,
) -> ScoreRankLookup:
    lookup = try_lookup_rank_for_score(session, province=province, target_year=target_year, score=score)
    if lookup is None:
        raise HTTPException(status_code=400, detail="缺少可用一分一段表，无法把预估分数换算为位次")
    return lookup


def try_lookup_rank_for_score(
    session: Session,
    *,
    province: str,
    target_year: int,
    score: float,
) -> ScoreRankLookup | None:
    try:
        used_year = select_score_rank_year(session, target_year, province)
    except OperationalError:
        return None
    if used_year is None:
        return None
    base_sql = f"""
        SELECT year, score, COALESCE(rank_value, cumulative_count) AS rank_value
        FROM score_rank_segment
        WHERE year = :year
          AND score IS NOT NULL
          AND COALESCE(rank_value, cumulative_count) IS NOT NULL
          {PROVINCE_FILTER}
          {SUBJECT_GROUP_FILTER}
          {SCORE_TYPE_FILTER}
    """
    params = _province_params(province) | {"year": used_year, "score": score}
    row = session.execute(
        text(
            f"""
            {base_sql}
              AND score <= :score
            ORDER BY score DESC
            LIMIT 1
            """
        ),
        params,
    ).mappings().first()
    if row is None:
        row = session.execute(
            text(
                f"""
                {base_sql}
                ORDER BY score ASC
                LIMIT 1
                """
            ),
            params,
        ).mappings().first()
    if row is None:
        return None
    basis = "target_year_score_rank_segment" if used_year == target_year else "previous_year_score_rank_segment"
    source_note = (
        "按目标年份一分一段换算"
        if used_year == target_year
        else f"目标年份一分一段缺失，按 {used_year} 年一分一段估算"
    )
    return ScoreRankLookup(
        year=int(row["year"]),
        score=float(row["score"]),
        rank=int(row["rank_value"]),
        basis=basis,
        source_note=source_note,
    )


def latest_rank_population(session: Session, province: str, target_year: int) -> int | None:
    try:
        used_year = select_score_rank_year(session, target_year, province)
    except OperationalError:
        return None
    if used_year is None:
        return None
    row = session.execute(
        text(
            f"""
            SELECT MAX(COALESCE(rank_value, cumulative_count)) AS population
            FROM score_rank_segment
            WHERE year = :year
              {PROVINCE_FILTER}
              {SUBJECT_GROUP_FILTER}
              {SCORE_TYPE_FILTER}
            """
        ),
        _province_params(province) | {"year": used_year},
    ).mappings().first()
    return int(row["population"]) if row and row["population"] is not None else None


def score_rank_columns(session: Session) -> set[str]:
    """Backwards-compatible accessor; schema is now fixed.

    Some external tests still call this; keep the signature stable but return
    the canonical column set without hitting PRAGMA.
    """
    return {
        "id",
        "province",
        "year",
        "score_type",
        "subject_group",
        "score",
        "segment_count",
        "cumulative_count",
        "rank_value",
        "source_level",
        "source_title",
        "source_url",
        "local_source_path",
        "parser_script_name",
        "published_at",
        "review_status",
        "source_record_hash",
        "data_version_label",
        "import_batch_id",
        "source_document_id",
        "import_run_id",
        "created_at",
        "updated_at",
    }


def select_score_rank_year(
    session: Session,
    target_year: int,
    province: str,
    columns: set[str] | None = None,
) -> int | None:
    params = _province_params(province) | {"target_year": target_year}
    row = session.execute(
        text(
            f"""
            SELECT MAX(year) AS year
            FROM score_rank_segment
            WHERE year <= :target_year
              {PROVINCE_FILTER}
              {SUBJECT_GROUP_FILTER}
              {SCORE_TYPE_FILTER}
            """
        ),
        params,
    ).mappings().first()
    if row and row["year"] is not None:
        return int(row["year"])
    row = session.execute(
        text(
            f"""
            SELECT MAX(year) AS year
            FROM score_rank_segment
            WHERE 1 = 1
              {PROVINCE_FILTER}
              {SUBJECT_GROUP_FILTER}
              {SCORE_TYPE_FILTER}
            """
        ),
        params,
    ).mappings().first()
    return int(row["year"]) if row and row["year"] is not None else None


def province_alias(province: str) -> str:
    if province in {"山东", "sd", "SD", "山东省", "shandong", "Shandong"}:
        return "sd" if province == "山东" else "山东"
    return province


def _province_params(province: str) -> dict[str, str]:
    normalized = (province or "").strip()
    if normalized in {"山东", "sd", "SD", "山东省", "shandong", "Shandong"}:
        return {
            "province": normalized or "山东",
            "province_alias": province_alias(normalized or "山东"),
            "province_alias_cn": "山东省",
            "province_alias_en": "shandong",
        }
    return {
        "province": normalized,
        "province_alias": normalized,
        "province_alias_cn": normalized,
        "province_alias_en": normalized,
    }
