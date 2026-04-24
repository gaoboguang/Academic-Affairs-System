from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.orm import Session


@dataclass
class BatchDictContext:
    pathway_code: str | None = None
    note: str | None = None
    sort_order: int | None = None


@dataclass
class ProvincePolicyContext:
    title: str | None = None
    url: str | None = None
    summary: str | None = None
    policy_type: str | None = None
    year: int | None = None


def load_batch_dict_context(
    session: Session,
    *,
    province: str,
    batch: str,
    student_type: str,
) -> BatchDictContext | None:
    has_table = session.execute(
        text(
            """
            SELECT COUNT(*)
            FROM sqlite_master
            WHERE type = 'table' AND name = 'gaokao_batch_dict'
            """
        )
    ).scalar()
    if not has_table:
        return None
    province_aliases = _province_aliases(province)
    province_placeholders = ", ".join(f":province_{index}" for index in range(len(province_aliases)))
    params = {f"province_{index}": value for index, value in enumerate(province_aliases)}
    params["batch_name"] = (batch or "").strip()
    pathway_code = _resolve_pathway_code(student_type)
    params["pathway_code"] = pathway_code
    available_columns = {
        row[1]
        for row in session.execute(text('PRAGMA table_info("gaokao_batch_dict")')).all()
    }
    rows = session.execute(
        text(
            f"""
            SELECT pathway_code, note, {_select_optional_column("sort_order", available_columns)}
            FROM gaokao_batch_dict
            WHERE province_scope IN ({province_placeholders})
              AND batch_name = :batch_name
            ORDER BY
              CASE
                WHEN pathway_code = :pathway_code THEN 0
                WHEN pathway_code IS NULL OR trim(pathway_code) = '' THEN 1
                ELSE 2
              END,
              sort_order ASC,
              id ASC
            """
        ),
        params,
    ).mappings().all()
    if not rows:
        return None
    row = rows[0]
    return BatchDictContext(
        pathway_code=_clean_optional_text(row["pathway_code"]),
        note=_clean_optional_text(row["note"]),
        sort_order=int(row["sort_order"]) if row["sort_order"] is not None else None,
    )


def load_province_policy_context(
    session: Session,
    *,
    province: str,
    target_year: int,
) -> ProvincePolicyContext | None:
    has_table = session.execute(
        text(
            """
            SELECT COUNT(*)
            FROM sqlite_master
            WHERE type = 'table' AND name = 'gaokao_policy_reference'
            """
        )
    ).scalar()
    if not has_table:
        return None
    province_aliases = _province_aliases(province)
    province_placeholders = ", ".join(f":province_{index}" for index in range(len(province_aliases)))
    params = {f"province_{index}": value for index, value in enumerate(province_aliases)}
    params["target_year"] = target_year
    row = session.execute(
        text(
            f"""
            SELECT year, policy_type, title, url, summary
            FROM gaokao_policy_reference
            WHERE province IN ({province_placeholders})
              AND year <= :target_year
              AND status = 'active'
            ORDER BY year DESC, id DESC
            LIMIT 1
            """
        ),
        params,
    ).mappings().first()
    if not row:
        return None
    return ProvincePolicyContext(
        title=_clean_optional_text(row["title"]),
        url=_clean_optional_text(row["url"]),
        summary=_clean_optional_text(row["summary"]),
        policy_type=_clean_optional_text(row["policy_type"]),
        year=int(row["year"]) if row["year"] is not None else None,
    )


def _province_aliases(province: str) -> list[str]:
    normalized = (province or "").strip()
    if normalized == "山东":
        return ["山东", "山东省", "sd", "shandong"]
    return [normalized]


def _resolve_pathway_code(student_type: str) -> str | None:
    mapping = {
        "general": "ordinary",
        "repeat": "ordinary",
        "art": "art",
        "sports": "sports",
        "spring_exam": "spring",
    }
    return mapping.get((student_type or "").strip())


def _clean_optional_text(value: object) -> str | None:
    if value is None:
        return None
    current = str(value).strip()
    return current or None


def _select_optional_column(column: str, available_columns: set[str]) -> str:
    if column in available_columns:
        return f"{column} AS {column}"
    return f"NULL AS {column}"
