from __future__ import annotations

from collections import defaultdict

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import RecommendationResult
from app.repositories.recommendations import get_scheme, list_recommendation_results
from app.schemas.recommendation import RecommendationHistoryItem, RecommendationResultRead

from ._recommendations_result_builder import build_recommendation_sort_key
from ._recommendations_shared import _serialize_result


def list_recommendation_history(session: Session, student_id: int | None = None) -> list[RecommendationHistoryItem]:
    rows = list_recommendation_results(session, student_id=student_id)
    grouped: dict[tuple[int, int], list[RecommendationResult]] = defaultdict(list)
    for row in rows:
        grouped[(row.scheme_id, row.student_id)].append(row)

    history: list[RecommendationHistoryItem] = []
    for items in grouped.values():
        first = items[0]
        counts = defaultdict(int)
        for item in items:
            counts[item.result_type] += 1
        history.append(
            RecommendationHistoryItem(
                scheme_id=first.scheme_id,
                scheme_name=first.scheme.name if first.scheme else str(first.scheme_id),
                student_id=first.student_id,
                student_name=first.student.name if first.student else str(first.student_id),
                exam_id=first.exam_id,
                province=first.scheme.province if first.scheme else "",
                target_year=_read_optional_int(first.snapshot_json, "target_year"),
                student_type=first.scheme.student_type if first.scheme else "",
                score_input_mode=_read_optional_string(first.snapshot_json, "score_input_mode") or "actual_rank",
                score_input_label=_read_optional_string(first.snapshot_json, "score_input_label"),
                score_confidence=_read_optional_string(first.snapshot_json, "score_confidence"),
                reference_exam_name=_read_optional_string(first.snapshot_json, "reference_exam_name"),
                use_historical_mapping=_read_optional_bool(first.snapshot_json, "use_historical_mapping"),
                generated_at=max(item.generated_at for item in items),
                result_count=len(items),
                challenge_count=counts["challenge"],
                steady_count=counts["steady"],
                safe_count=counts["safe"],
            )
        )
    history.sort(key=lambda item: item.generated_at, reverse=True)
    return history


def list_scheme_results(session: Session, scheme_id: int, student_id: int | None = None) -> list[RecommendationResultRead]:
    scheme = get_scheme(session, scheme_id)
    if not scheme:
        raise HTTPException(status_code=404, detail="推荐方案不存在")
    items = [_serialize_result(item) for item in list_recommendation_results(session, student_id=student_id, scheme_id=scheme_id)]
    items.sort(
        key=lambda item: build_recommendation_sort_key(
            result_type=item.result_type,
            career_match_score=item.career_match_score,
            career_match_strength=item.career_match_strength,
            ratio=item.ratio,
            reference_rank=item.reference_rank,
            college_name=item.college_name,
            major_name=item.major_name,
            fallback_priority_score=item.fallback_priority_score,
        )
    )
    return items


def _read_optional_string(snapshot: dict | None, key: str) -> str | None:
    if not isinstance(snapshot, dict):
        return None
    value = snapshot.get(key)
    if isinstance(value, str):
        current = value.strip()
        return current or None
    return None


def _read_optional_int(snapshot: dict | None, key: str) -> int | None:
    if not isinstance(snapshot, dict):
        return None
    value = snapshot.get(key)
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    return None


def _read_optional_bool(snapshot: dict | None, key: str) -> bool:
    if not isinstance(snapshot, dict):
        return False
    value = snapshot.get(key)
    return bool(value) if isinstance(value, bool) else False
