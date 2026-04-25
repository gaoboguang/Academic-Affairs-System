from __future__ import annotations

from dataclasses import dataclass
from statistics import pstdev
from typing import Any

from fastapi import HTTPException
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.models import Exam, ExamSubject, ScoreTotalSnapshot, Student, StudentGaokaoScoreProjection
from app.repositories.system import write_audit_log
from app.schemas.recommendation import (
    StudentGaokaoScoreProjectionPayload,
    StudentGaokaoScoreProjectionRead,
)

SUPPORTED_SOURCE_MODES = {"manual_score", "manual_rank", "exam_projection"}
DEFAULT_GAOKAO_TOTAL_SCORE = 750


@dataclass(frozen=True)
class ScoreRankLookup:
    year: int
    score: float
    rank: int
    basis: str
    source_note: str


def calculate_gaokao_score_projection(
    session: Session,
    payload: StudentGaokaoScoreProjectionPayload,
) -> StudentGaokaoScoreProjectionRead:
    student = _get_student(session, payload.student_id)
    source_mode = _normalize_source_mode(payload.source_mode)
    if source_mode == "manual_score":
        projection = _calculate_manual_score_projection(session, payload, student)
    elif source_mode == "manual_rank":
        projection = _calculate_manual_rank_projection(payload, student)
    else:
        projection = _calculate_exam_projection(session, payload, student)
    return projection


def create_gaokao_score_projection(
    session: Session,
    payload: StudentGaokaoScoreProjectionPayload,
) -> StudentGaokaoScoreProjectionRead:
    preview = calculate_gaokao_score_projection(session, payload)
    item = StudentGaokaoScoreProjection(
        student_id=preview.student_id,
        target_year=preview.target_year,
        province=preview.province,
        source_mode=preview.source_mode,
        predicted_score=preview.predicted_score,
        predicted_rank=preview.predicted_rank,
        rank_range_low=preview.rank_range_low,
        rank_range_high=preview.rank_range_high,
        confidence_level=preview.confidence_level,
        rank_projection_basis=preview.rank_projection_basis,
        selected_exam_ids_json=preview.selected_exam_ids_json,
        calculation_detail_json=preview.calculation_detail_json,
        note=preview.note,
    )
    session.add(item)
    session.flush()
    write_audit_log(
        session,
        module="recommendations",
        action="create_gaokao_score_projection",
        target_type="student_gaokao_score_projection",
        target_id=str(item.id),
        detail_json={
            "student_id": item.student_id,
            "target_year": item.target_year,
            "source_mode": item.source_mode,
            "predicted_rank": item.predicted_rank,
        },
    )
    session.refresh(item)
    return _serialize_projection(item)


def list_gaokao_score_projections(
    session: Session,
    *,
    student_id: int | None = None,
    target_year: int | None = None,
) -> list[StudentGaokaoScoreProjectionRead]:
    statement = select(StudentGaokaoScoreProjection).where(StudentGaokaoScoreProjection.is_active.is_(True))
    if student_id is not None:
        statement = statement.where(StudentGaokaoScoreProjection.student_id == student_id)
    if target_year is not None:
        statement = statement.where(StudentGaokaoScoreProjection.target_year == target_year)
    statement = statement.order_by(StudentGaokaoScoreProjection.updated_at.desc(), StudentGaokaoScoreProjection.id.desc())
    return [_serialize_projection(item) for item in session.scalars(statement).all()]


def get_gaokao_score_projection(
    session: Session,
    projection_id: int,
) -> StudentGaokaoScoreProjectionRead:
    item = session.get(StudentGaokaoScoreProjection, projection_id)
    if not item or not item.is_active:
        raise HTTPException(status_code=404, detail="预估记录不存在")
    return _serialize_projection(item)


def _calculate_manual_score_projection(
    session: Session,
    payload: StudentGaokaoScoreProjectionPayload,
    student: Student,
) -> StudentGaokaoScoreProjectionRead:
    if payload.manual_score is None:
        raise HTTPException(status_code=400, detail="手动分数模式需要填写预估高考分数")
    if payload.manual_score < 0:
        raise HTTPException(status_code=400, detail="预估高考分数不能为负数")
    lookup = _lookup_rank_for_score(
        session,
        province=payload.province,
        target_year=payload.target_year,
        score=float(payload.manual_score),
    )
    margin = _rank_margin(lookup.rank, "medium" if lookup.year != payload.target_year else "high")
    confidence = "high" if lookup.year == payload.target_year else "medium"
    detail = {
        "input_mode": "manual_score",
        "manual_score": float(payload.manual_score),
        "score_rank_segment": {
            "target_year": payload.target_year,
            "used_year": lookup.year,
            "used_score": lookup.score,
            "used_rank": lookup.rank,
            "basis": lookup.basis,
            "source_note": lookup.source_note,
        },
        "notes": _build_score_rank_notes(lookup, payload.target_year),
    }
    return StudentGaokaoScoreProjectionRead(
        student_id=student.id,
        student_name=student.name,
        target_year=payload.target_year,
        province=payload.province,
        source_mode="manual_score",
        predicted_score=round(float(payload.manual_score), 2),
        predicted_rank=lookup.rank,
        rank_range_low=max(1, lookup.rank - margin),
        rank_range_high=lookup.rank + margin,
        confidence_level=confidence,
        rank_projection_basis=lookup.basis,
        selected_exam_ids_json=[],
        calculation_detail_json=detail,
        note=payload.note,
    )


def _calculate_manual_rank_projection(
    payload: StudentGaokaoScoreProjectionPayload,
    student: Student,
) -> StudentGaokaoScoreProjectionRead:
    if payload.manual_rank is None:
        raise HTTPException(status_code=400, detail="手动位次模式需要填写预估全省位次")
    if payload.manual_rank <= 0:
        raise HTTPException(status_code=400, detail="预估全省位次必须大于 0")
    detail = {
        "input_mode": "manual_rank",
        "manual_score": payload.manual_score,
        "manual_rank": payload.manual_rank,
        "notes": ["当前直接使用手动填写的山东全省位次，位次将作为后续推荐主依据。"],
    }
    return StudentGaokaoScoreProjectionRead(
        student_id=student.id,
        student_name=student.name,
        target_year=payload.target_year,
        province=payload.province,
        source_mode="manual_rank",
        predicted_score=round(float(payload.manual_score), 2) if payload.manual_score is not None else None,
        predicted_rank=int(payload.manual_rank),
        rank_range_low=int(payload.manual_rank),
        rank_range_high=int(payload.manual_rank),
        confidence_level="high",
        rank_projection_basis="manual_rank",
        selected_exam_ids_json=[],
        calculation_detail_json=detail,
        note=payload.note,
    )


def _calculate_exam_projection(
    session: Session,
    payload: StudentGaokaoScoreProjectionPayload,
    student: Student,
) -> StudentGaokaoScoreProjectionRead:
    selected_exam_ids = _normalize_exam_ids(payload.selected_exam_ids)
    if not selected_exam_ids:
        raise HTTPException(status_code=400, detail="历次考试估算需要选择至少一次考试")
    rows = _load_exam_snapshot_rows(session, student.id, selected_exam_ids)
    missing_ids = [exam_id for exam_id in selected_exam_ids if exam_id not in {row["exam_id"] for row in rows}]
    if missing_ids:
        raise HTTPException(status_code=400, detail=f"所选考试缺少该学生总分快照: {missing_ids}")

    weighted_score = _weighted_average([row["normalized_score"] for row in rows])
    grade_rank_values = [float(row["grade_rank"]) for row in rows if row["grade_rank"] is not None]
    weighted_grade_rank = _weighted_average(grade_rank_values) if grade_rank_values else None
    rank_lookup = _try_lookup_rank_for_score(
        session,
        province=payload.province,
        target_year=payload.target_year,
        score=weighted_score,
    )
    rank_from_school = _estimate_rank_from_school_position(session, rows, payload.province, payload.target_year)
    predicted_rank = rank_lookup.rank if rank_lookup else rank_from_school
    if predicted_rank is None and weighted_grade_rank is not None:
        predicted_rank = round(weighted_grade_rank)
    confidence = _exam_projection_confidence(rows, bool(rank_lookup))
    margin = _exam_projection_margin(predicted_rank, rows, confidence) if predicted_rank else None
    rank_trend = _trend([float(row["grade_rank"]) for row in rows if row["grade_rank"] is not None])
    score_trend = _trend([row["normalized_score"] for row in rows])
    notes = [
        "缺少本校历届高考校准数据，当前为校内估算，不能把校内名次直接当作山东全省位次。",
        "最近考试权重更高，估算同时参考总分、年级名次、趋势和波动。",
    ]
    if rank_lookup:
        notes.extend(_build_score_rank_notes(rank_lookup, payload.target_year))
    elif rank_from_school:
        notes.append("当前缺少可用一分一段换算，已按校内年级位置生成粗略全省位次区间。")
    else:
        notes.append("当前缺少一分一段和可用年级名次，只能保留校内预估分。")
    detail = {
        "input_mode": "exam_projection",
        "gaokao_total_score": DEFAULT_GAOKAO_TOTAL_SCORE,
        "weighted_score": weighted_score,
        "weighted_grade_rank": round(weighted_grade_rank, 2) if weighted_grade_rank is not None else None,
        "rank_trend": rank_trend,
        "score_trend": score_trend,
        "rank_volatility": _volatility([float(row["grade_rank"]) for row in rows if row["grade_rank"] is not None]),
        "score_volatility": _volatility([row["normalized_score"] for row in rows]),
        "calibration_status": "missing_school_gaokao_calibration",
        "score_rank_segment": _score_rank_detail(rank_lookup, payload.target_year),
        "exam_items": rows,
        "notes": notes,
    }
    return StudentGaokaoScoreProjectionRead(
        student_id=student.id,
        student_name=student.name,
        target_year=payload.target_year,
        province=payload.province,
        source_mode="exam_projection",
        predicted_score=weighted_score,
        predicted_rank=predicted_rank,
        rank_range_low=max(1, predicted_rank - margin) if predicted_rank and margin is not None else None,
        rank_range_high=predicted_rank + margin if predicted_rank and margin is not None else None,
        confidence_level=confidence,
        rank_projection_basis=rank_lookup.basis if rank_lookup else "school_exam_projection",
        selected_exam_ids_json=selected_exam_ids,
        calculation_detail_json=detail,
        note=payload.note,
    )


def _load_exam_snapshot_rows(session: Session, student_id: int, exam_ids: list[int]) -> list[dict[str, Any]]:
    full_score_by_exam = _load_exam_full_scores(session, exam_ids)
    grade_size_by_exam = _load_grade_sizes(session, exam_ids)
    statement = (
        select(ScoreTotalSnapshot, Exam)
        .join(Exam, ScoreTotalSnapshot.exam_id == Exam.id)
        .where(
            ScoreTotalSnapshot.student_id == student_id,
            ScoreTotalSnapshot.exam_id.in_(exam_ids),
            ScoreTotalSnapshot.is_active.is_(True),
        )
        .order_by(Exam.exam_date.asc(), Exam.id.asc())
    )
    loaded = session.execute(statement).all()
    rows: list[dict[str, Any]] = []
    for index, (snapshot, exam) in enumerate(loaded, start=1):
        total_full_score = full_score_by_exam.get(exam.id) or DEFAULT_GAOKAO_TOTAL_SCORE
        normalized_score = round((snapshot.total_score / total_full_score) * DEFAULT_GAOKAO_TOTAL_SCORE, 2)
        rows.append(
            {
                "exam_id": exam.id,
                "exam_name": exam.name,
                "exam_date": exam.exam_date.isoformat(),
                "total_score": snapshot.total_score,
                "total_full_score": total_full_score,
                "normalized_score": normalized_score,
                "class_rank": snapshot.class_rank,
                "grade_rank": snapshot.grade_rank,
                "class_percentile": snapshot.class_percentile,
                "grade_percentile": snapshot.grade_percentile,
                "grade_size": grade_size_by_exam.get(exam.id),
                "weight": index,
            }
        )
    return rows


def _load_exam_full_scores(session: Session, exam_ids: list[int]) -> dict[int, float]:
    rows = session.execute(
        select(ExamSubject.exam_id, func.sum(ExamSubject.full_score))
        .where(
            ExamSubject.exam_id.in_(exam_ids),
            ExamSubject.is_active.is_(True),
            ExamSubject.is_in_total.is_(True),
        )
        .group_by(ExamSubject.exam_id)
    ).all()
    return {int(exam_id): float(total or 0) for exam_id, total in rows}


def _load_grade_sizes(session: Session, exam_ids: list[int]) -> dict[int, int]:
    rows = session.execute(
        select(ScoreTotalSnapshot.exam_id, func.count(ScoreTotalSnapshot.id))
        .where(ScoreTotalSnapshot.exam_id.in_(exam_ids), ScoreTotalSnapshot.is_active.is_(True))
        .group_by(ScoreTotalSnapshot.exam_id)
    ).all()
    return {int(exam_id): int(count or 0) for exam_id, count in rows}


def _lookup_rank_for_score(
    session: Session,
    *,
    province: str,
    target_year: int,
    score: float,
) -> ScoreRankLookup:
    lookup = _try_lookup_rank_for_score(session, province=province, target_year=target_year, score=score)
    if lookup is None:
        raise HTTPException(status_code=400, detail="缺少可用一分一段表，无法把预估分数换算为位次")
    return lookup


def _try_lookup_rank_for_score(
    session: Session,
    *,
    province: str,
    target_year: int,
    score: float,
) -> ScoreRankLookup | None:
    columns = _score_rank_columns(session)
    if not columns or "score" not in columns or "year" not in columns:
        return None
    rank_column = "rank_value" if "rank_value" in columns else "cumulative_count" if "cumulative_count" in columns else None
    if rank_column is None:
        return None
    used_year = _select_score_rank_year(session, target_year, province, columns)
    if used_year is None:
        return None
    subject_filter = _subject_group_filter(columns)
    score_type_filter = _score_type_filter(columns)
    province_filter = _province_filter(province, columns)
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
    params = {"year": used_year, "score": score, "province": province, "province_alias": _province_alias(province)}
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


def _select_score_rank_year(
    session: Session,
    target_year: int,
    province: str,
    columns: set[str],
) -> int | None:
    province_filter = _province_filter(province, columns)
    subject_filter = _subject_group_filter(columns)
    score_type_filter = _score_type_filter(columns)
    params = {"target_year": target_year, "province": province, "province_alias": _province_alias(province)}
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


def _estimate_rank_from_school_position(
    session: Session,
    rows: list[dict[str, Any]],
    province: str,
    target_year: int,
) -> int | None:
    population = _latest_rank_population(session, province, target_year)
    if population is None:
        return None
    ratios = [
        float(row["grade_rank"]) / float(row["grade_size"])
        for row in rows
        if row.get("grade_rank") is not None and row.get("grade_size")
    ]
    if not ratios:
        return None
    return max(1, round(_weighted_average(ratios) * population))


def _latest_rank_population(session: Session, province: str, target_year: int) -> int | None:
    columns = _score_rank_columns(session)
    if not columns:
        return None
    rank_column = "rank_value" if "rank_value" in columns else "cumulative_count" if "cumulative_count" in columns else None
    if rank_column is None:
        return None
    used_year = _select_score_rank_year(session, target_year, province, columns)
    if used_year is None:
        return None
    province_filter = _province_filter(province, columns)
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
        {"year": used_year, "province": province, "province_alias": _province_alias(province)},
    ).mappings().first()
    return int(row["population"]) if row and row["population"] is not None else None


def _score_rank_columns(session: Session) -> set[str]:
    try:
        rows = session.execute(text("PRAGMA table_info(score_rank_segment)")).mappings().all()
    except Exception:
        return set()
    return {str(row["name"]) for row in rows}


def _province_filter(province: str, columns: set[str]) -> str:
    if "province" not in columns:
        return ""
    return "AND province IN (:province, :province_alias)"


def _province_alias(province: str) -> str:
    if province in {"山东", "sd", "SD"}:
        return "sd" if province == "山东" else "山东"
    return province


def _subject_group_filter(columns: set[str]) -> str:
    if "subject_group" not in columns:
        return ""
    return "AND (subject_group IS NULL OR subject_group IN ('all', '全体'))"


def _score_type_filter(columns: set[str]) -> str:
    if "score_type" not in columns:
        return ""
    return "AND (score_type IS NULL OR score_type IN ('summer_total', '总分', '普通类'))"


def _get_student(session: Session, student_id: int) -> Student:
    student = session.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="学生不存在")
    return student


def _normalize_source_mode(value: str) -> str:
    normalized = (value or "").strip()
    if normalized not in SUPPORTED_SOURCE_MODES:
        raise HTTPException(status_code=400, detail="暂不支持的预估来源模式")
    return normalized


def _normalize_exam_ids(values: list[int]) -> list[int]:
    normalized: list[int] = []
    for value in values:
        if value not in normalized:
            normalized.append(value)
    return normalized


def _weighted_average(values: list[float]) -> float:
    if not values:
        return 0.0
    weights = list(range(1, len(values) + 1))
    return round(sum(value * weight for value, weight in zip(values, weights, strict=True)) / sum(weights), 2)


def _trend(values: list[float]) -> float | None:
    if len(values) < 2:
        return None
    return round(values[-1] - values[0], 2)


def _volatility(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    return round(float(pstdev(values)), 2)


def _rank_margin(rank: int, confidence: str) -> int:
    rate = {"high": 0.02, "medium": 0.06, "low": 0.12}.get(confidence, 0.1)
    return max(200, round(rank * rate))


def _exam_projection_margin(rank: int | None, rows: list[dict[str, Any]], confidence: str) -> int:
    if rank is None:
        return 0
    base = _rank_margin(rank, confidence)
    grade_ranks = [float(row["grade_rank"]) for row in rows if row.get("grade_rank") is not None]
    if len(grade_ranks) < 2:
        return base
    avg_rank = sum(grade_ranks) / len(grade_ranks)
    volatility_rate = min(0.08, (_volatility(grade_ranks) / avg_rank) if avg_rank else 0)
    return max(base, round(rank * (0.06 + volatility_rate)))


def _exam_projection_confidence(rows: list[dict[str, Any]], has_score_rank_lookup: bool) -> str:
    if not has_score_rank_lookup:
        return "low"
    if len(rows) >= 2 and all(row.get("grade_rank") is not None for row in rows):
        return "medium"
    return "low"


def _score_rank_detail(lookup: ScoreRankLookup | None, target_year: int) -> dict[str, object] | None:
    if lookup is None:
        return None
    return {
        "target_year": target_year,
        "used_year": lookup.year,
        "used_score": lookup.score,
        "used_rank": lookup.rank,
        "basis": lookup.basis,
        "source_note": lookup.source_note,
    }


def _build_score_rank_notes(lookup: ScoreRankLookup, target_year: int) -> list[str]:
    if lookup.year == target_year:
        return ["已按目标年份一分一段表换算山东全省位次。"]
    return [f"{target_year} 年一分一段暂缺，已按 {lookup.year} 年一分一段临时估算，正式出分后需要重新计算。"]


def _serialize_projection(item: StudentGaokaoScoreProjection) -> StudentGaokaoScoreProjectionRead:
    return StudentGaokaoScoreProjectionRead(
        id=item.id,
        student_id=item.student_id,
        student_name=item.student.name if item.student else None,
        target_year=item.target_year,
        province=item.province,
        source_mode=item.source_mode,
        predicted_score=item.predicted_score,
        predicted_rank=item.predicted_rank,
        rank_range_low=item.rank_range_low,
        rank_range_high=item.rank_range_high,
        confidence_level=item.confidence_level,
        rank_projection_basis=item.rank_projection_basis,
        selected_exam_ids_json=item.selected_exam_ids_json or [],
        calculation_detail_json=item.calculation_detail_json or {},
        note=item.note,
        created_at=item.created_at,
        updated_at=item.updated_at,
        is_active=item.is_active,
    )
