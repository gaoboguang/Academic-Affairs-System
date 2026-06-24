from app.services._analytics_metrics import (
    compute_peer_radius,
    compute_rank_trend_shape,
    compute_stability,
    detect_exam_anomaly,
    estimate_target_reach_probability,
)


class TestRankTrendShape:
    def test_returns_insufficient_when_fewer_than_three_points(self) -> None:
        result = compute_rank_trend_shape([100, 90])
        assert result.label == "数据不足"
        assert result.slope is None

    def test_treats_all_none_as_insufficient(self) -> None:
        assert compute_rank_trend_shape([None, None, None]).label == "数据不足"

    def test_steady_climb_in_rank_means_improving(self) -> None:
        result = compute_rank_trend_shape([200, 180, 160, 140, 120])
        assert result.label == "稳步上升"
        assert result.slope is not None and result.slope < 0
        assert "上升" in result.summary

    def test_steady_drop_in_rank_means_decline(self) -> None:
        result = compute_rank_trend_shape([100, 120, 140, 160, 180])
        assert result.label == "下滑"
        assert result.slope is not None and result.slope > 0

    def test_volatile_when_high_variance_with_flat_trend(self) -> None:
        result = compute_rank_trend_shape([150, 80, 200, 60, 140])
        assert result.label == "剧烈波动"

    def test_u_shape_when_dips_then_recovers(self) -> None:
        result = compute_rank_trend_shape([100, 130, 180, 200, 110])
        assert result.label == "U型反弹"

    def test_stable_when_no_meaningful_drift(self) -> None:
        result = compute_rank_trend_shape([100, 102, 99, 101, 100])
        assert result.label == "稳定"


class TestStability:
    def test_unknown_when_too_few_points(self) -> None:
        result = compute_stability(ranks=[100, 90], scores=[600, 590])
        assert result.level == "unknown"
        assert result.rank_stddev is None

    def test_high_when_low_variance(self) -> None:
        result = compute_stability(
            ranks=[100, 102, 98, 101, 99],
            scores=[600, 605, 595, 602, 598],
        )
        assert result.level == "high"

    def test_low_when_score_cv_above_threshold(self) -> None:
        result = compute_stability(
            ranks=[100, 200, 50, 300, 80],
            scores=[400, 600, 350, 700, 380],
        )
        assert result.level == "low"

    def test_handles_missing_score_series(self) -> None:
        result = compute_stability(ranks=[100, 110, 95, 105, 100])
        assert result.level in {"high", "medium"}
        assert result.score_cv is None


class TestPeerRadius:
    def test_default_when_rank_missing(self) -> None:
        assert compute_peer_radius(None, 500) == 10

    def test_widens_with_cohort(self) -> None:
        assert compute_peer_radius(50, 1200) == 30

    def test_floor_for_small_cohort(self) -> None:
        assert compute_peer_radius(10, 100) >= 8

    def test_caps_at_thirty(self) -> None:
        assert compute_peer_radius(500, 5000) == 30


class TestExamAnomaly:
    def test_no_outlier_when_history_short(self) -> None:
        result = detect_exam_anomaly(
            current_median=580.0,
            current_stddev=40.0,
            history_medians=[600.0, 595.0],
            history_stddevs=[35.0, 38.0],
        )
        assert result.is_outlier is False
        assert "样本不足" in result.reason

    def test_outlier_when_median_drops_more_than_stddev(self) -> None:
        result = detect_exam_anomaly(
            current_median=520.0,
            current_stddev=42.0,
            history_medians=[600.0, 605.0, 598.0, 602.0],
            history_stddevs=[35.0, 36.0, 38.0, 37.0],
        )
        assert result.is_outlier is True
        assert "下降" in result.reason
        assert "校准" in result.recommendation

    def test_within_band_returns_normal(self) -> None:
        result = detect_exam_anomaly(
            current_median=601.0,
            current_stddev=37.0,
            history_medians=[600.0, 605.0, 598.0, 602.0],
            history_stddevs=[35.0, 36.0, 38.0, 37.0],
        )
        assert result.is_outlier is False
        assert "正常区间" in result.reason


class TestReachProbability:
    def test_unknown_when_short_history(self) -> None:
        level, probability = estimate_target_reach_probability(
            target_score=600,
            recent_scores=[580, 595],
        )
        assert level == "unknown"
        assert probability is None

    def test_high_when_well_above_target(self) -> None:
        level, probability = estimate_target_reach_probability(
            target_score=550,
            recent_scores=[600, 605, 595, 602, 598],
        )
        assert level == "high"
        assert probability is not None and probability > 0.7

    def test_low_when_well_below_target(self) -> None:
        level, probability = estimate_target_reach_probability(
            target_score=650,
            recent_scores=[580, 575, 590, 585, 580],
        )
        assert level == "low"
        assert probability is not None and probability < 0.4
