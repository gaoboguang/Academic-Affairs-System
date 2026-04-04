from __future__ import annotations

from app.analytics.scores import RankedValue, assign_ranks, calculate_percentile


def test_assign_ranks_competition_mode() -> None:
    ranks = assign_ranks(
        [
            RankedValue(key=1, score=100),
            RankedValue(key=2, score=95),
            RankedValue(key=3, score=95),
            RankedValue(key=4, score=90),
        ],
        rank_mode="competition",
    )

    assert ranks == {1: 1, 2: 2, 3: 2, 4: 4}


def test_assign_ranks_dense_mode() -> None:
    ranks = assign_ranks(
        [
            RankedValue(key=1, score=100),
            RankedValue(key=2, score=95),
            RankedValue(key=3, score=95),
            RankedValue(key=4, score=90),
        ],
        rank_mode="dense",
    )

    assert ranks == {1: 1, 2: 2, 3: 2, 4: 3}


def test_calculate_percentile() -> None:
    assert calculate_percentile(1, 10) == 1.0
    assert calculate_percentile(4, 10) == 0.7

