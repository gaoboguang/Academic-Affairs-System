from __future__ import annotations

from statistics import median


def weighted_reference_rank(values: list[tuple[int, int]]) -> int | None:
    if not values:
        return None
    sorted_values = sorted(values, key=lambda item: item[0], reverse=True)[:3]
    if len(sorted_values) == 1:
        return sorted_values[0][1]
    if len(sorted_values) == 2:
        weights = [0.6, 0.4]
    else:
        weights = [0.5, 0.3, 0.2]
    result = sum(rank * weight for (_, rank), weight in zip(sorted_values, weights))
    return int(round(result))


def median_reference_rank(values: list[int]) -> int | None:
    if not values:
        return None
    return int(median(values))


def classify_ratio(ratio: float, *, safe_max: float, steady_max: float, rush_max: float) -> str | None:
    if ratio <= safe_max:
        return "safe"
    if ratio <= steady_max:
        return "steady"
    if ratio <= rush_max:
        return "challenge"
    return None


def classify_score_gap(gap: float) -> str | None:
    if gap >= 30:
        return "safe"
    if gap >= 0:
        return "steady"
    if gap >= -20:
        return "challenge"
    return None
