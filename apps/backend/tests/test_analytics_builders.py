"""Unit tests for the M3/M4/M5 analytics builder helpers.

These hit the pure-function builders directly with fixture objects so we can
exercise edge cases (no data, partial data, full data) without spinning up the
full scoring pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace

from app.schemas.exam import (
    StudentKnowledgePointAnalytics,
    StudentSubjectAnalytics,
    StudentSubjectLossConcentration,
    StudentSubjectStructure,
    StudentTargetLineGap,
    StudentTotalTrendPoint,
)
from app.services.analytics import (
    _build_peer_comparison,
    _build_required_subject_combos,
    _build_student_target_progress,
    _build_subject_structure,
)


def _make_subject(
    *,
    subject_id: int,
    name: str,
    score: float | None = 80.0,
    z: float | None = 0.5,
    t: float | None = 55.0,
) -> StudentSubjectAnalytics:
    return StudentSubjectAnalytics(
        subject_id=subject_id,
        subject_name=name,
        score=score,
        score_status="normal" if score is not None else "absent",
        z_score=z,
        t_score=t,
    )


def _make_kp(
    *,
    subject_id: int,
    point_id: int,
    point_name: str,
    knowledge_path: str | None,
    lost_score: float = 5.0,
    score_rate: float = 0.7,
) -> StudentKnowledgePointAnalytics:
    return StudentKnowledgePointAnalytics(
        subject_id=subject_id,
        subject_name=f"sub-{subject_id}",
        knowledge_point_id=point_id,
        knowledge_point_name=point_name,
        knowledge_path=knowledge_path,
        score=score_rate * 10,
        full_score=10.0,
        score_rate=score_rate,
        lost_score=lost_score,
        priority_score=lost_score * 1.5,
        diagnosis_label="needs-work",
        question_count=1,
    )


class TestSubjectStructure:
    def test_empty_subjects_yields_friendly_summary(self) -> None:
        result = _build_subject_structure([], [])
        assert result.summary
        assert result.radar_points == []
        assert result.strengths == []
        assert result.weaknesses == []

    def test_marks_strengths_and_weaknesses_using_z_score(self) -> None:
        subjects = [
            _make_subject(subject_id=1, name="语文", z=1.4, t=64.0),
            _make_subject(subject_id=2, name="数学", z=-1.3, t=37.0),
            _make_subject(subject_id=3, name="英语", z=0.2, t=52.0),
        ]
        result = _build_subject_structure(subjects, [])
        assert "语文" in result.strengths
        assert "数学" in result.weaknesses
        assert "英语" not in result.strengths
        assert "英语" not in result.weaknesses
        assert len(result.radar_points) == 3

    def test_loss_concentration_picks_top_three_paths(self) -> None:
        subjects = [_make_subject(subject_id=1, name="语文")]
        kps = [
            _make_kp(subject_id=1, point_id=10, point_name="阅读", knowledge_path="阅读>说明文", lost_score=12.0),
            _make_kp(subject_id=1, point_id=11, point_name="作文", knowledge_path="作文>记叙文", lost_score=8.0),
            _make_kp(subject_id=1, point_id=12, point_name="字音", knowledge_path="基础>字音", lost_score=4.0),
            _make_kp(subject_id=1, point_id=13, point_name="字形", knowledge_path="基础>字形", lost_score=2.0),
        ]
        result = _build_subject_structure(subjects, kps)
        assert len(result.loss_concentration) == 1
        loss = result.loss_concentration[0]
        assert len(loss.top_paths) == 3
        assert loss.top_paths[0] == "阅读>说明文"
        # top 3 = 12 + 8 + 4 = 24, total = 26, share ≈ 0.923
        assert loss.loss_share is not None and 0.9 <= loss.loss_share <= 1.0

    def test_loss_concentration_skipped_when_no_kp(self) -> None:
        subjects = [_make_subject(subject_id=1, name="语文")]
        result = _build_subject_structure(subjects, [])
        assert result.loss_concentration == []

    def test_balanced_summary_when_no_strong_or_weak(self) -> None:
        subjects = [
            _make_subject(subject_id=1, name="语文", z=0.3),
            _make_subject(subject_id=2, name="数学", z=-0.4),
        ]
        result = _build_subject_structure(subjects, [])
        assert "均衡" in result.summary


class TestPeerComparison:
    def test_handles_missing_grade_rank(self) -> None:
        snapshot = SimpleNamespace(grade_rank=None, total_score=520, student_id=1)
        result = _build_peer_comparison(
            student_total_snapshot=snapshot,
            all_total_snapshots=[snapshot],
            all_subject_snapshots=[],
            subjects=[],
            peer_subject_averages={},
            peer_sample_count=0,
            peer_sample_note="缺少校内名次",
        )
        assert result.peer_count == 0
        assert result.subject_gaps == []
        assert "缺少校内名次" in (result.peer_sample_note or "")

    def test_marks_laggards_when_gap_below_eight(self) -> None:
        student_snapshot = SimpleNamespace(grade_rank=10, total_score=600, student_id=1)
        peer_snapshots = [
            SimpleNamespace(grade_rank=8 + offset, total_score=605, student_id=100 + offset)
            for offset in range(20)
        ]
        all_total = [student_snapshot, *peer_snapshots]
        subject_snaps: list[SimpleNamespace] = []
        for offset in range(20):
            subject_snaps.append(
                SimpleNamespace(student_id=100 + offset, subject_id=1, score=90.0)
            )
        subjects = [_make_subject(subject_id=1, name="语文", score=80.0)]
        result = _build_peer_comparison(
            student_total_snapshot=student_snapshot,
            all_total_snapshots=all_total,
            all_subject_snapshots=subject_snaps,
            subjects=subjects,
            peer_subject_averages={1: 90.0},
            peer_sample_count=20,
            peer_sample_note=None,
        )
        assert result.peer_count == 20
        assert result.peer_radius >= 8
        assert "语文" in result.laggard_subjects
        gap_row = result.subject_gaps[0]
        assert gap_row.gap == -10.0
        # All cohort members beat the student, so student ranks last among them.
        assert gap_row.gap_rank_in_peers is not None and gap_row.gap_rank_in_peers > 1


class TestRequiredSubjectCombos:
    def test_returns_empty_when_no_subjects(self) -> None:
        plans = _build_required_subject_combos(
            target_gap=-12.0,
            structure_lookup={},
            subject_lookup={},
        )
        assert plans == []

    def test_picks_subjects_by_loss_share_priority(self) -> None:
        subjects = {
            1: _make_subject(subject_id=1, name="数学", score=70),
            2: _make_subject(subject_id=2, name="语文", score=80),
            3: _make_subject(subject_id=3, name="英语", score=85),
        }
        structure = {
            1: StudentSubjectLossConcentration(
                subject_id=1, subject_name="数学", top_paths=["函数"], loss_share=0.7
            ),
            2: StudentSubjectLossConcentration(
                subject_id=2, subject_name="语文", top_paths=["阅读"], loss_share=0.4
            ),
            3: StudentSubjectLossConcentration(
                subject_id=3, subject_name="英语", top_paths=["完形"], loss_share=0.2
            ),
        }
        plans = _build_required_subject_combos(
            target_gap=-15.0,
            structure_lookup=structure,
            subject_lookup=subjects,
        )
        assert plans
        # Highest headroom should come first
        assert plans[0].subject_name == "数学"
        assert plans[0].feasibility == "high"
        assert plans[0].gain_needed > 0

    def test_caps_at_three_plans(self) -> None:
        subjects = {
            i: _make_subject(subject_id=i, name=f"科目{i}", score=80)
            for i in range(1, 6)
        }
        plans = _build_required_subject_combos(
            target_gap=-50.0,
            structure_lookup={},
            subject_lookup=subjects,
        )
        assert len(plans) <= 3


class TestTargetProgress:
    def test_returns_empty_when_no_target_gaps(self) -> None:
        result = _build_student_target_progress(
            target_line_gaps=[],
            total_trend_points=[],
            subject_structure=StudentSubjectStructure(),
            subjects=[],
        )
        assert result == []

    def test_handles_target_without_threshold(self) -> None:
        gaps = [
            StudentTargetLineGap(
                line_id=1,
                line_name="本科线",
                line_type="rank",
                threshold_label="位次",
                threshold_score=None,
                reached=False,
                gap_score=None,
                gap_rank=20,
                status="below",
            )
        ]
        result = _build_student_target_progress(
            target_line_gaps=gaps,
            total_trend_points=[],
            subject_structure=StudentSubjectStructure(),
            subjects=[],
        )
        assert len(result) == 1
        assert result[0].target_score is None
        assert "校排" in result[0].note

    def test_estimates_reach_probability_with_history(self) -> None:
        gaps = [
            StudentTargetLineGap(
                line_id=1,
                line_name="本科线",
                line_type="score",
                threshold_label="本科",
                threshold_score=500.0,
                reached=False,
                gap_score=-20.0,
                gap_rank=None,
                status="below",
            )
        ]
        trend = [
            StudentTotalTrendPoint(
                exam_id=i, exam_name=f"考试{i}", exam_date=f"2024-0{i}-01", total_score=score, grade_rank=200
            )
            for i, score in enumerate([475, 478, 480], start=1)
        ]
        subjects = [_make_subject(subject_id=1, name="数学", score=70)]
        result = _build_student_target_progress(
            target_line_gaps=gaps,
            total_trend_points=trend,
            subject_structure=StudentSubjectStructure(),
            subjects=subjects,
        )
        assert len(result) == 1
        entry = result[0]
        assert entry.reach_probability_level in {"high", "medium", "low"}
        assert entry.trend_estimate is not None
        assert entry.required_subject_combos  # because gap < 0
