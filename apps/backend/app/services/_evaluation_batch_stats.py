from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from statistics import mean

from app.models import EvaluationResponse, EvaluationSummary
from app.schemas.evaluation import (
    EvaluationClassStatRead,
    EvaluationQuestionStatRead,
    EvaluationTeacherSummaryRead,
)


@dataclass
class _DimensionBuildResult:
    dimension_name: str
    avg_score: float
    response_count: int
    question_stats: list[EvaluationQuestionStatRead]
    class_stats: list[EvaluationClassStatRead]


class _DimensionAggregate:
    def __init__(self, dimension_name: str) -> None:
        self.dimension_name = dimension_name
        self.scores: list[float] = []
        self.question_scores: dict[str, list[float]] = defaultdict(list)
        self.question_dimension: dict[str, str] = {}
        self.class_scores: dict[tuple[int | None, str | None], list[float]] = defaultdict(list)

    def build(self) -> _DimensionBuildResult:
        question_stats = [
            EvaluationQuestionStatRead(
                question_text=question_text,
                dimension_name=self.question_dimension[question_text],
                avg_score=round(mean(values), 2),
                response_count=len(values),
            )
            for question_text, values in self.question_scores.items()
        ]
        question_stats.sort(key=lambda item: item.question_text)
        class_stats = [
            EvaluationClassStatRead(
                class_id=class_id,
                class_name=class_name,
                avg_score=round(mean(values), 2),
                response_count=len(values),
            )
            for (class_id, class_name), values in self.class_scores.items()
        ]
        class_stats.sort(key=lambda item: item.class_name or "")
        return _DimensionBuildResult(
            dimension_name=self.dimension_name,
            avg_score=round(mean(self.scores), 2),
            response_count=len(self.scores),
            question_stats=question_stats,
            class_stats=class_stats,
        )


def _normalized_score(response: EvaluationResponse) -> float:
    score_max = response.question.score_max if response.question else 0
    if score_max <= 0:
        return response.score
    return round(response.score / score_max * 100, 2)


def _overall_average(items: list[EvaluationResponse]) -> float:
    weighted_scores: list[float] = []
    weights: list[float] = []
    for item in items:
        weight = item.question.weight if item.question else 1.0
        weighted_scores.append(_normalized_score(item))
        weights.append(weight)
    if not weighted_scores:
        return 0.0
    numerator = sum(score * weight for score, weight in zip(weighted_scores, weights, strict=False))
    denominator = sum(weights) or len(weighted_scores)
    return round(numerator / denominator, 2)


def _build_dimension_rows(items: list[EvaluationResponse]) -> list[_DimensionBuildResult]:
    grouped: dict[str, _DimensionAggregate] = {}
    for item in items:
        if not item.question:
            continue
        dimension_name = item.question.dimension_name
        aggregate = grouped.setdefault(dimension_name, _DimensionAggregate(dimension_name))
        normalized = _normalized_score(item)
        aggregate.scores.append(normalized)
        aggregate.question_scores[item.question.question_text].append(normalized)
        aggregate.question_dimension[item.question.question_text] = dimension_name
        aggregate.class_scores[(item.class_id, item.school_class.name if item.school_class else None)].append(normalized)
    rows = [aggregate.build() for aggregate in grouped.values()]
    rows.sort(key=lambda item: item.dimension_name)
    return rows


def _assign_competition_rank(rows: list[EvaluationTeacherSummaryRead]) -> None:
    last_score: float | None = None
    last_rank = 0
    for index, item in enumerate(rows, start=1):
        if last_score is None or item.overall_avg_score < last_score:
            last_rank = index
            last_score = item.overall_avg_score
        item.rank = last_rank


def _build_teacher_summary_rows(summaries: list[EvaluationSummary]) -> list[EvaluationTeacherSummaryRead]:
    grouped: dict[int, dict[str, EvaluationSummary]] = defaultdict(dict)
    for item in summaries:
        grouped[item.teacher_id][item.dimension_name] = item

    overview_rows: list[EvaluationTeacherSummaryRead] = []
    for teacher_id, summary_map in grouped.items():
        overall = summary_map.get("__overall__")
        teacher = overall.teacher if overall else None
        if not overall or not teacher:
            continue
        dimension_scores = {
            key: round(value.avg_score, 2)
            for key, value in summary_map.items()
            if key != "__overall__"
        }
        overview_rows.append(
            EvaluationTeacherSummaryRead(
                teacher_id=teacher_id,
                teacher_name=teacher.name,
                overall_avg_score=round(overall.avg_score, 2),
                response_count=overall.response_count,
                dimension_scores_json=dimension_scores or None,
            )
        )
    overview_rows.sort(key=lambda item: item.overall_avg_score, reverse=True)
    _assign_competition_rank(overview_rows)
    return overview_rows
