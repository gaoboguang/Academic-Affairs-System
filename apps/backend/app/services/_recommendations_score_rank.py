from __future__ import annotations

from dataclasses import dataclass

from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session


@dataclass(frozen=True)
class ScoreRankLookup:
    year: int
    score: float
    rank: int
    basis: str
    source_note: str


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
    columns = score_rank_columns(session)
    if not columns or "score" not in columns or "year" not in columns:
        return None
    rank_column = "rank_value" if "rank_value" in columns else "cumulative_count" if "cumulative_count" in columns else None
    if rank_column is None:
        return None
    used_year = select_score_rank_year(session, target_year, province, columns)
    if used_year is None:
        return None
    subject_filter = _subject_group_filter(columns)
    score_type_filter = _score_type_filter(columns)
    province_filter = _province_filter(columns)
    base_sql = f"""
        SELECT year, score, {rank_column} AS rank_value
        FROM score_rank_segment
        WHERE year = :year
          AND score IS NOT NULL
          AND {rank_column} IS NOT NULL
          {province_filter}
          {subject_filter}
          {score_type_filter}
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
    source_note = "按目标年份一分一段换算" if used_year == target_year else f"目标年份一分一段缺失，按 {used_year} 年一分一段估算"
    return ScoreRankLookup(
        year=int(row["year"]),
        score=float(row["score"]),
        rank=int(row["rank_value"]),
        basis=basis,
        source_note=source_note,
    )


def latest_rank_population(session: Session, province: str, target_year: int) -> int | None:
    columns = score_rank_columns(session)
    if not columns:
        return None
    rank_column = "rank_value" if "rank_value" in columns else "cumulative_count" if "cumulative_count" in columns else None
    if rank_column is None:
        return None
    used_year = select_score_rank_year(session, target_year, province, columns)
    if used_year is None:
        return None
    province_filter = _province_filter(columns)
    subject_filter = _subject_group_filter(columns)
    score_type_filter = _score_type_filter(columns)
    row = session.execute(
        text(
            f"""
            SELECT MAX({rank_column}) AS population
            FROM score_rank_segment
            WHERE year = :year
              {province_filter}
              {subject_filter}
              {score_type_filter}
            """
        ),
        _province_params(province) | {"year": used_year},
    ).mappings().first()
    return int(row["population"]) if row and row["population"] is not None else None


def score_rank_columns(session: Session) -> set[str]:
    try:
        rows = session.execute(text("PRAGMA table_info(score_rank_segment)")).mappings().all()
    except Exception:
        return set()
    return {str(row["name"]) for row in rows}


def select_score_rank_year(
    session: Session,
    target_year: int,
    province: str,
    columns: set[str],
) -> int | None:
    province_filter = _province_filter(columns)
    subject_filter = _subject_group_filter(columns)
    score_type_filter = _score_type_filter(columns)
    params = _province_params(province) | {"target_year": target_year}
    row = session.execute(
        text(
            f"""
            SELECT MAX(year) AS year
            FROM score_rank_segment
            WHERE year <= :target_year
              {province_filter}
              {subject_filter}
              {score_type_filter}
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
              {province_filter}
              {subject_filter}
              {score_type_filter}
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


def _province_filter(columns: set[str]) -> str:
    if "province" not in columns:
        return ""
    return "AND province IN (:province, :province_alias, :province_alias_cn, :province_alias_en)"


def _subject_group_filter(columns: set[str]) -> str:
    if "subject_group" not in columns:
        return ""
    return "AND (subject_group IS NULL OR subject_group = '' OR subject_group IN ('all', '全体'))"


def _score_type_filter(columns: set[str]) -> str:
    if "score_type" not in columns:
        return ""
    return "AND (score_type IS NULL OR score_type = '' OR score_type IN ('summer_total', '总分', '普通类'))"
