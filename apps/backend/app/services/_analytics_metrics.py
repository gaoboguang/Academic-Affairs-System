"""Reusable analytics metrics: trend shape, stability, peer radius, anomaly.

These primitives stay framework-free and serializable so they can be
unit-tested directly against fixture data.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
import statistics


# Trend shape thresholds. These work on rank-style series where lower number
# = better. For score-style series the caller flips the sign before calling.
_RANK_VOLATILE_RATIO = 0.18  # stddev / mean ratio above which we call it volatile when slope is weak
_RANK_EXTREME_VOLATILE_RATIO = 0.30  # extreme noise dominates even a clear slope
_RANK_FLAT_SLOPE = 1.5  # absolute slope (rank change per exam) below which we call it flat
_U_SHAPE_RECOVERY = 0.6  # last point has recovered ≥ 60% of the worst-point dip


@dataclass(frozen=True)
class TrendShape:
    label: str  # 稳步上升 / 稳定 / 下滑 / 剧烈波动 / U型反弹 / 数据不足
    slope: float | None  # average change per exam (rank: negative = improving)
    summary: str  # one-line caption like "近 5 次校排稳步上升（平均每次 -8 名）"


@dataclass(frozen=True)
class StabilityMetric:
    level: str  # high / medium / low / unknown
    rank_stddev: float | None
    score_cv: float | None  # coefficient of variation = stddev / mean
    sample_count: int
    summary: str  # "近 5 次校排波动 ±25 名，稳定性偏低"


def _linear_slope(values: list[float]) -> float | None:
    """OLS slope for evenly spaced points. None when fewer than 2 points."""
    if len(values) < 2:
        return None
    n = len(values)
    x_mean = (n - 1) / 2
    y_mean = sum(values) / n
    numerator = sum((i - x_mean) * (v - y_mean) for i, v in enumerate(values))
    denominator = sum((i - x_mean) ** 2 for i in range(n))
    if denominator == 0:
        return None
    return numerator / denominator


def _coerce_floats(values: list[int | float | None]) -> list[float]:
    return [float(v) for v in values if v is not None]


def compute_rank_trend_shape(ranks: list[int | float | None]) -> TrendShape:
    """Classify a school-rank series. Lower number = better rank."""
    series = _coerce_floats(ranks)
    if len(series) < 3:
        return TrendShape(label="数据不足", slope=None, summary="历史样本不足，至少需要 3 次考试。")

    slope = _linear_slope(series)
    mean = sum(series) / len(series)
    stddev = statistics.pstdev(series) if len(series) > 1 else 0.0
    volatility_ratio = stddev / mean if mean else 0.0

    minimum = min(series)
    maximum = max(series)
    last = series[-1]
    minimum_index = series.index(minimum)
    maximum_index = series.index(maximum)

    is_volatile_weak_trend = volatility_ratio > _RANK_VOLATILE_RATIO and abs(slope or 0) < _RANK_FLAT_SLOPE
    is_extreme_volatile = volatility_ratio > _RANK_EXTREME_VOLATILE_RATIO
    is_u_shape = (
        len(series) >= 4
        and 0 < maximum_index < len(series) - 1
        and (maximum - last) >= _U_SHAPE_RECOVERY * (maximum - minimum)
        and (maximum - last) >= 8
    )

    if is_u_shape:
        label = "U型反弹"
    elif is_extreme_volatile or is_volatile_weak_trend:
        label = "剧烈波动"
    elif slope is not None and slope <= -_RANK_FLAT_SLOPE:
        label = "稳步上升"
    elif slope is not None and slope >= _RANK_FLAT_SLOPE:
        label = "下滑"
    else:
        label = "稳定"

    summary = _format_rank_trend_summary(label=label, slope=slope, sample_count=len(series))
    return TrendShape(
        label=label,
        slope=round(slope, 2) if slope is not None else None,
        summary=summary,
    )


def _format_rank_trend_summary(*, label: str, slope: float | None, sample_count: int) -> str:
    base = f"近 {sample_count} 次校排"
    if label == "稳步上升" and slope is not None:
        return f"{base}稳步上升（平均每次 {slope:+.1f} 名，越小越好）"
    if label == "下滑" and slope is not None:
        return f"{base}有下滑趋势（平均每次 {slope:+.1f} 名）"
    if label == "剧烈波动":
        return f"{base}波动较大，稳定性偏弱"
    if label == "U型反弹":
        return f"{base}先下滑后回升，最近一次明显反弹"
    if label == "稳定":
        return f"{base}维持稳定区间"
    return f"{base}样本不足"


def compute_stability(
    *,
    ranks: list[int | float | None],
    scores: list[int | float | None] | None = None,
) -> StabilityMetric:
    """Combine rank and score variability into a high/medium/low rating."""
    rank_series = _coerce_floats(ranks)
    score_series = _coerce_floats(scores or [])
    sample_count = len(rank_series) or len(score_series)

    if sample_count < 3:
        return StabilityMetric(
            level="unknown",
            rank_stddev=None,
            score_cv=None,
            sample_count=sample_count,
            summary="历史样本不足，无法判断稳定性。",
        )

    rank_stddev = statistics.pstdev(rank_series) if len(rank_series) >= 3 else None
    score_cv: float | None = None
    if len(score_series) >= 3:
        score_mean = sum(score_series) / len(score_series)
        if score_mean:
            score_cv = statistics.pstdev(score_series) / score_mean

    rank_mean = sum(rank_series) / len(rank_series) if rank_series else 0.0
    rank_volatility_ratio = (rank_stddev / rank_mean) if (rank_stddev and rank_mean) else None

    score_signal = score_cv if score_cv is not None else 0.0
    rank_signal = rank_volatility_ratio if rank_volatility_ratio is not None else 0.0

    if max(score_signal, rank_signal) >= 0.18:
        level = "low"
    elif max(score_signal, rank_signal) >= 0.10:
        level = "medium"
    else:
        level = "high"

    summary_parts: list[str] = []
    if rank_stddev is not None:
        summary_parts.append(f"近 {len(rank_series)} 次校排波动 ±{rank_stddev:.0f} 名")
    if score_cv is not None:
        summary_parts.append(f"分数变异系数 {score_cv * 100:.1f}%")
    summary_parts.append({"high": "稳定性高", "medium": "稳定性中等", "low": "稳定性偏弱"}[level])
    return StabilityMetric(
        level=level,
        rank_stddev=round(rank_stddev, 2) if rank_stddev is not None else None,
        score_cv=round(score_cv, 4) if score_cv is not None else None,
        sample_count=sample_count,
        summary="；".join(summary_parts),
    )


def compute_peer_radius(grade_rank: int | None, total_count: int) -> int:
    """Adaptive radius around the student's school rank for peer comparisons.

    Tighten on dense fields, loosen when the cohort is small.
    """
    if grade_rank is None or total_count <= 0:
        return 10
    base = max(8, round(total_count * 0.025))
    return min(base, 30)


@dataclass(frozen=True)
class ExamAnomaly:
    is_outlier: bool
    median_drop: float | None
    spread_change: float | None
    reason: str
    recommendation: str


def detect_exam_anomaly(
    *,
    current_median: float | None,
    current_stddev: float | None,
    history_medians: list[float],
    history_stddevs: list[float],
) -> ExamAnomaly:
    """Compare an exam's group statistics against recent history.

    Returns is_outlier=True when the median or spread differs by more than 1
    historical stddev. The caller decides what to do with that flag.
    """
    if (
        current_median is None
        or len(history_medians) < 3
    ):
        return ExamAnomaly(
            is_outlier=False,
            median_drop=None,
            spread_change=None,
            reason="历史样本不足，未做异常检测。",
            recommendation="累积更多历史考试后再做对比。",
        )

    history_mean = sum(history_medians) / len(history_medians)
    history_stddev = statistics.pstdev(history_medians)
    median_drop = round(current_median - history_mean, 2)

    spread_change: float | None = None
    if current_stddev is not None and len(history_stddevs) >= 3:
        history_spread_mean = sum(history_stddevs) / len(history_stddevs)
        spread_change = round(current_stddev - history_spread_mean, 2)

    is_outlier = bool(history_stddev) and abs(median_drop) > history_stddev
    if not is_outlier:
        return ExamAnomaly(
            is_outlier=False,
            median_drop=median_drop,
            spread_change=spread_change,
            reason="本次考试整体表现处于历史正常区间。",
            recommendation="可放心解读个体波动。",
        )

    direction = "下降" if median_drop < 0 else "升高"
    reason = (
        f"整体中位较前 {len(history_medians)} 次平均{direction} {abs(median_drop):.1f} 分"
        f"（历史波动 ±{history_stddev:.1f}）"
    )
    if spread_change is not None and abs(spread_change) >= history_stddev * 0.5:
        reason += f"，分数离散度同时变化 {spread_change:+.1f}"
    return ExamAnomaly(
        is_outlier=True,
        median_drop=median_drop,
        spread_change=spread_change,
        reason=reason,
        recommendation="解读个体波动前先校准群体基线，避免把题目难度变化误读为学生退步。",
    )


def estimate_target_reach_probability(
    *,
    target_score: float,
    recent_scores: list[float],
) -> tuple[str, float | None]:
    """Rough P(score >= target) using Gaussian assumption on recent scores.

    Returns ("high"/"medium"/"low"/"unknown", probability).
    The probability is intentionally pessimistic by 0.05 to discourage
    over-confident calls when the sample is small.
    """
    series = [float(s) for s in recent_scores if s is not None]
    if len(series) < 3:
        return "unknown", None
    mean = sum(series) / len(series)
    stddev = statistics.pstdev(series)
    if stddev <= 0:
        probability = 1.0 if mean >= target_score else 0.0
    else:
        # Standard-normal CDF via erfc (Python stdlib has math.erfc)
        z = (target_score - mean) / stddev
        probability = 0.5 * math.erfc(z / math.sqrt(2))
    probability = max(0.0, probability - 0.05)
    if probability >= 0.7:
        level = "high"
    elif probability >= 0.4:
        level = "medium"
    else:
        level = "low"
    return level, round(probability, 2)
