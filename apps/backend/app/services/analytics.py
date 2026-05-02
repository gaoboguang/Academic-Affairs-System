from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime
import math

from fastapi import HTTPException
from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.analytics.score_contexts import effective_class_id, effective_class_name, load_exam_context_map
from app.analytics.scores import calculate_rate, safe_mean, safe_median, safe_stddev
from app.models import (
    Exam,
    Grade,
    KnowledgePoint,
    SchoolClass,
    ScoreKnowledgeSnapshot,
    ScoreRecord,
    ScoreSubjectSnapshot,
    ScoreTargetLine,
    ScoreTotalSnapshot,
    Semester,
    Student,
    Subject,
    Teacher,
    TeachingAssignment,
)
from app.repositories.exams import (
    get_exam,
    get_previous_trend_exam,
    get_score_records_for_exam,
    get_subject_snapshots_for_exam,
    get_total_snapshots_for_exam,
)
from app.services.knowledge_base import build_knowledge_paths
from app.schemas.exam import (
    ClassAnalyticsResponse,
    ExamAnalyzableStudentItem,
    ExamAnalyzableStudentListResponse,
    ClassPanoramaResponse,
    GradeAnalyticsResponse,
    GradeClassAnalyticsItem,
    GradeClassContributionItem,
    GradeCriticalStudentItem,
    GradeDistributionItem,
    GradePanoramaExamPointRead,
    GradePanoramaResponse,
    GradePanoramaSubjectPointRead,
    GradePanoramaSubjectTrendRead,
    GradePanoramaYearSummaryRead,
    GradeRankAuditSummary,
    GradeSubjectAnalyticsItem,
    GradeTargetLineSummary,
    StudentAnalyticsResponse,
    StudentActionSuggestion,
    StudentKnowledgePointAnalytics,
    StudentKnowledgeTrendAnalytics,
    StudentKnowledgeTrendPoint,
    StudentSubjectAnalytics,
    StudentSubjectEffectiveTarget,
    StudentSubjectTrendPoint,
    StudentSubjectTrendSeries,
    StudentTargetLineGap,
    StudentTotalTrendPoint,
    SubjectAggregateItem,
    TeacherAnalyticsResponse,
    TeacherAssignmentAnalytics,
    TeacherPanoramaResponse,
)
from app.schemas.knowledge import (
    ClassKnowledgeBriefingItem,
    ClassKnowledgeBriefingResponse,
    ClassKnowledgeBriefingStudent,
    KnowledgeErrorTagStat,
)


KNOWLEDGE_TREND_WINDOW = 5
KNOWLEDGE_TREND_MIN_EXAM_COUNT = 2
KNOWLEDGE_TREND_MIN_FULL_SCORE = 5.0
KNOWLEDGE_WEAK_RATE_THRESHOLD = 0.7
KNOWLEDGE_SEVERE_RATE_THRESHOLD = 0.55
KNOWLEDGE_IMPROVEMENT_DELTA = 0.15
KNOWLEDGE_VOLATILE_DELTA = 0.25


def _score_value_label(score_value_type: str | None) -> str:
    return "赋分" if score_value_type == "converted" else "原始分"


def list_exam_analyzable_students(session: Session, exam_id: int) -> ExamAnalyzableStudentListResponse:
    exam = get_exam(session, exam_id)
    if not exam:
        raise HTTPException(status_code=404, detail="考试不存在")

    total_rows = list(
        session.execute(
            select(Student, ScoreTotalSnapshot)
            .join(ScoreTotalSnapshot, ScoreTotalSnapshot.student_id == Student.id)
            .where(ScoreTotalSnapshot.exam_id == exam_id, Student.is_active.is_(True))
            .order_by(
                ScoreTotalSnapshot.grade_rank.is_(None),
                ScoreTotalSnapshot.grade_rank.asc(),
                ScoreTotalSnapshot.total_score.desc(),
                Student.student_no.asc(),
                Student.id.asc(),
            )
        ).all()
    )

    if total_rows:
        items = [
            _build_exam_analyzable_student_item(student, total_snapshot)
            for student, total_snapshot in total_rows
        ]
        return ExamAnalyzableStudentListResponse(exam_id=exam.id, total=len(items), items=items)

    fallback_rows = list(
        session.execute(
            select(Student)
            .join(ScoreSubjectSnapshot, ScoreSubjectSnapshot.student_id == Student.id)
            .where(ScoreSubjectSnapshot.exam_id == exam_id, Student.is_active.is_(True))
            .group_by(Student.id)
            .order_by(
                func.min(ScoreSubjectSnapshot.grade_rank).is_(None),
                func.min(ScoreSubjectSnapshot.grade_rank).asc(),
                Student.student_no.asc(),
                Student.id.asc(),
            )
        ).scalars()
    )
    items = [_build_exam_analyzable_student_item(student, None) for student in fallback_rows]
    return ExamAnalyzableStudentListResponse(exam_id=exam.id, total=len(items), items=items)


def _build_exam_analyzable_student_item(
    student: Student,
    total_snapshot: ScoreTotalSnapshot | None,
) -> ExamAnalyzableStudentItem:
    return ExamAnalyzableStudentItem(
        id=student.id,
        student_no=student.student_no,
        name=student.name,
        current_grade_id=student.current_grade_id,
        current_grade_name=student.current_grade.name if student.current_grade else None,
        current_class_id=student.current_class_id,
        current_class_name=student.current_class.name if student.current_class else None,
        total_score=total_snapshot.total_score if total_snapshot else None,
        class_rank=total_snapshot.class_rank if total_snapshot else None,
        grade_rank=total_snapshot.grade_rank if total_snapshot else None,
        grade_percentile=total_snapshot.grade_percentile if total_snapshot else None,
    )


def get_student_analytics(session: Session, student_id: int, exam_id: int) -> StudentAnalyticsResponse:
    exam = get_exam(session, exam_id)
    if not exam:
        raise HTTPException(status_code=404, detail="考试不存在")

    all_total_snapshots = list(get_total_snapshots_for_exam(session, exam_id))
    all_subject_snapshots = list(get_subject_snapshots_for_exam(session, exam_id))
    total_snapshot = next((item for item in all_total_snapshots if item.student_id == student_id), None)
    subject_snapshots = [
        item for item in all_subject_snapshots if item.student_id == student_id
    ]
    if not total_snapshot and not subject_snapshots:
        raise HTTPException(status_code=404, detail="该学生暂无本次考试分析数据")

    previous_exam = get_previous_trend_exam(session, exam)
    previous_total = None
    previous_subject_map: dict[int, object] = {}
    if previous_exam:
        previous_total = next((item for item in get_total_snapshots_for_exam(session, previous_exam.id) if item.student_id == student_id), None)
        previous_subject_map = {
            item.subject_id: item
            for item in get_subject_snapshots_for_exam(session, previous_exam.id)
            if item.student_id == student_id
        }

    student_name = (
        total_snapshot.student.name
        if total_snapshot and total_snapshot.student
        else (subject_snapshots[0].student.name if subject_snapshots and subject_snapshots[0].student else str(student_id))
    )
    target_lines = _list_active_target_lines(session, exam.id)
    total_line_thresholds = _resolve_target_line_score_thresholds(target_lines, all_total_snapshots)
    target_line_gaps = _build_student_target_line_gaps(target_lines, total_line_thresholds, total_snapshot)
    subject_groups = _group_subject_snapshots(all_subject_snapshots)
    subject_mean_stddev = {
        subject_id: (safe_mean([item.score for item in items if item.score is not None]), safe_stddev([item.score for item in items if item.score is not None]))
        for subject_id, items in subject_groups.items()
    }
    effective_targets_by_subject = _build_effective_score_targets_by_subject(
        subject_groups,
        subject_snapshots,
        target_lines,
        total_line_thresholds,
    )
    peer_subject_averages, peer_sample_count, peer_sample_note = _build_peer_subject_averages(
        all_total_snapshots,
        all_subject_snapshots,
        total_snapshot.grade_rank if total_snapshot else None,
    )
    trend_points, subject_trend_map = _build_student_score_trends(session, student_id, exam)

    subjects: list[StudentSubjectAnalytics] = []
    for item in sorted(subject_snapshots, key=lambda current: current.subject_id):
        previous_item = previous_subject_map.get(item.subject_id)
        score_delta = None
        rank_delta = None
        if previous_item and previous_item.score is not None and item.score is not None:
            score_delta = round(item.score - previous_item.score, 2)
        if previous_item and previous_item.grade_rank is not None and item.grade_rank is not None:
            rank_delta = previous_item.grade_rank - item.grade_rank
        subject_mean, subject_stddev = subject_mean_stddev.get(item.subject_id, (0.0, 0.0))
        z_score = _calculate_z_score(item.score, subject_mean, subject_stddev)
        t_score = _calculate_t_score(z_score)
        rank_deviation = (
            total_snapshot.grade_rank - item.grade_rank
            if total_snapshot
            and total_snapshot.grade_rank is not None
            and item.grade_rank is not None
            else None
        )
        peer_average_score = peer_subject_averages.get(item.subject_id)
        peer_average_delta = (
            round(item.score - peer_average_score, 2)
            if item.score is not None and peer_average_score is not None
            else None
        )
        subject_trend_points = subject_trend_map.get(item.subject_id, [])
        trend_rank_stddev = _rank_stddev(subject_trend_points)
        effective_targets = effective_targets_by_subject.get(item.subject_id, [])
        diagnosis_tags = _build_subject_diagnosis_tags(
            rank_deviation=rank_deviation,
            rank_sample_count=len(subject_groups.get(item.subject_id, [])),
            peer_average_delta=peer_average_delta,
            trend_rank_stddev=trend_rank_stddev,
            trend_exam_count=len([point for point in subject_trend_points if point.grade_rank is not None]),
            effective_targets=effective_targets,
        )
        subjects.append(
            StudentSubjectAnalytics(
                subject_id=item.subject_id,
                subject_name=item.subject.name if item.subject else str(item.subject_id),
                score=item.score,
                original_score=item.original_score,
                converted_score=item.converted_score,
                score_value_type=item.score_value_type,
                score_value_label=_score_value_label(item.score_value_type),
                score_status="normal" if item.score is not None else "absent",
                class_rank=item.class_rank,
                grade_rank=item.grade_rank,
                class_percentile=item.class_percentile,
                grade_percentile=item.grade_percentile,
                excellent_flag=item.excellent_flag,
                pass_flag=item.pass_flag,
                score_delta=score_delta,
                rank_delta=rank_delta,
                z_score=z_score,
                t_score=t_score,
                rank_deviation=rank_deviation,
                peer_average_score=peer_average_score,
                peer_average_delta=peer_average_delta,
                peer_sample_count=peer_sample_count,
                peer_sample_note=peer_sample_note,
                trend_rank_stddev=trend_rank_stddev,
                trend_exam_count=len([point for point in subject_trend_points if point.grade_rank is not None]),
                effective_score_targets=effective_targets,
                primary_effective_line_name=effective_targets[0].line_name if effective_targets else None,
                primary_effective_score=effective_targets[0].target_score if effective_targets else None,
                primary_effective_score_gap=effective_targets[0].gap_score if effective_targets else None,
                diagnosis=_format_subject_diagnosis(diagnosis_tags),
                diagnosis_tags=diagnosis_tags,
            )
        )

    knowledge_points = _list_student_knowledge_points(session, student_id=student_id, exam_id=exam.id)
    knowledge_trends = _list_student_knowledge_trends(session, student_id=student_id, current_exam=exam)
    action_suggestions = _merge_knowledge_action_suggestions(
        _merge_knowledge_trend_action_suggestions(
            _build_student_action_suggestions(subjects, target_line_gaps),
            knowledge_trends,
        ),
        knowledge_points,
    )
    grade_rank_delta = (
        previous_total.grade_rank - total_snapshot.grade_rank
        if total_snapshot
        and previous_total
        and previous_total.grade_rank is not None
        and total_snapshot.grade_rank is not None
        else None
    )

    return StudentAnalyticsResponse(
        exam_id=exam.id,
        exam_name=exam.name,
        student_id=student_id,
        student_name=student_name,
        total_score=total_snapshot.total_score if total_snapshot else 0.0,
        score_value_type=total_snapshot.score_value_type if total_snapshot else "original",
        score_value_label=_score_value_label(total_snapshot.score_value_type if total_snapshot else None),
        class_rank=total_snapshot.class_rank if total_snapshot else None,
        grade_rank=total_snapshot.grade_rank if total_snapshot else None,
        class_percentile=total_snapshot.class_percentile if total_snapshot else None,
        grade_percentile=total_snapshot.grade_percentile if total_snapshot else None,
        previous_exam_id=previous_exam.id if previous_exam else None,
        previous_exam_name=previous_exam.name if previous_exam else None,
        total_score_delta=(
            round(total_snapshot.total_score - previous_total.total_score, 2)
            if total_snapshot and previous_total
            else None
        ),
        class_rank_delta=(
            previous_total.class_rank - total_snapshot.class_rank
            if total_snapshot
            and previous_total
            and previous_total.class_rank is not None
            and total_snapshot.class_rank is not None
            else None
        ),
        grade_rank_delta=grade_rank_delta,
        overview_sentence=_build_student_overview_sentence(
            grade_rank_delta=grade_rank_delta,
            subjects=subjects,
            target_line_gaps=target_line_gaps,
        ),
        target_line_gaps=target_line_gaps,
        trend_points=trend_points,
        subject_trends=[
            StudentSubjectTrendSeries(
                subject_id=subject.subject_id,
                subject_name=subject.subject_name,
                points=subject_trend_map.get(subject.subject_id, []),
            )
            for subject in subjects
        ],
        knowledge_points=knowledge_points,
        knowledge_trends=knowledge_trends,
        action_suggestions=action_suggestions,
        subjects=subjects,
    )


def _list_student_knowledge_points(
    session: Session,
    *,
    student_id: int,
    exam_id: int,
    limit: int = 10,
) -> list[StudentKnowledgePointAnalytics]:
    rows = session.scalars(
        select(ScoreKnowledgeSnapshot)
        .options(joinedload(ScoreKnowledgeSnapshot.subject), joinedload(ScoreKnowledgeSnapshot.knowledge_point))
        .where(
            ScoreKnowledgeSnapshot.exam_id == exam_id,
            ScoreKnowledgeSnapshot.student_id == student_id,
            ScoreKnowledgeSnapshot.is_active.is_(True),
        )
        .order_by(
            ScoreKnowledgeSnapshot.priority_score.desc(),
            ScoreKnowledgeSnapshot.lost_score.desc(),
            ScoreKnowledgeSnapshot.full_score.desc(),
            ScoreKnowledgeSnapshot.id.asc(),
        )
        .limit(limit)
    ).all()
    paths = _knowledge_paths_for_snapshots(session, rows)
    return [
        StudentKnowledgePointAnalytics(
            subject_id=item.subject_id,
            subject_name=item.subject.name if item.subject else str(item.subject_id),
            knowledge_point_id=item.knowledge_point_id,
            knowledge_point_name=item.knowledge_point.name if item.knowledge_point else str(item.knowledge_point_id),
            knowledge_path=paths.get(item.knowledge_point_id),
            score=item.score,
            full_score=item.full_score,
            score_rate=item.score_rate,
            grade_average_rate=item.grade_average_rate,
            grade_gap_rate=item.grade_gap_rate,
            lost_score=item.lost_score,
            priority_score=item.priority_score,
            diagnosis_label=item.diagnosis_label,
            error_tag_stats=item.error_tags_json or [],
            dominant_error_tag=item.dominant_error_tag,
            question_count=item.question_count,
            question_numbers=item.question_numbers_json or [],
            suggestion=item.suggestion,
        )
        for item in rows
    ]


def _list_student_knowledge_trends(
    session: Session,
    *,
    student_id: int,
    current_exam: Exam,
    limit: int = 10,
) -> list[StudentKnowledgeTrendAnalytics]:
    exam_boundary = or_(
        Exam.exam_date < current_exam.exam_date,
        and_(Exam.exam_date == current_exam.exam_date, Exam.id <= current_exam.id),
    )
    snapshot_exam_rows = list(
        session.execute(
            select(
                ScoreKnowledgeSnapshot.exam_id,
                func.max(Exam.exam_date).label("exam_date"),
            )
            .join(Exam, Exam.id == ScoreKnowledgeSnapshot.exam_id)
            .where(
                ScoreKnowledgeSnapshot.student_id == student_id,
                ScoreKnowledgeSnapshot.is_active.is_(True),
                Exam.is_active.is_(True),
                Exam.is_trend_enabled.is_(True),
                exam_boundary,
            )
            .group_by(ScoreKnowledgeSnapshot.exam_id)
            .order_by(func.max(Exam.exam_date).desc(), ScoreKnowledgeSnapshot.exam_id.desc())
            .limit(KNOWLEDGE_TREND_WINDOW)
        ).all()
    )
    if not snapshot_exam_rows:
        return []
    exam_ids = [row.exam_id for row in snapshot_exam_rows]
    exams = list(session.scalars(select(Exam).where(Exam.id.in_(exam_ids))).all())
    exam_map = {exam.id: exam for exam in exams}
    rows = list(
        session.scalars(
            select(ScoreKnowledgeSnapshot)
            .options(
                joinedload(ScoreKnowledgeSnapshot.subject),
                joinedload(ScoreKnowledgeSnapshot.knowledge_point),
            )
            .where(
                ScoreKnowledgeSnapshot.student_id == student_id,
                ScoreKnowledgeSnapshot.exam_id.in_(exam_ids),
                ScoreKnowledgeSnapshot.is_active.is_(True),
            )
        ).all()
    )
    grouped: dict[tuple[int, int], list[ScoreKnowledgeSnapshot]] = defaultdict(list)
    for row in rows:
        grouped[(row.subject_id, row.knowledge_point_id)].append(row)

    trends: list[StudentKnowledgeTrendAnalytics] = []
    for items in grouped.values():
        ordered_items = sorted(
            items,
            key=lambda item: (
                exam_map[item.exam_id].exam_date if item.exam_id in exam_map else current_exam.exam_date,
                item.exam_id,
            ),
        )
        total_full_score = round(sum(item.full_score for item in ordered_items), 4)
        if len(ordered_items) < KNOWLEDGE_TREND_MIN_EXAM_COUNT and total_full_score < KNOWLEDGE_TREND_MIN_FULL_SCORE:
            continue
        trend = _build_student_knowledge_trend(ordered_items, exam_map, session=session)
        if trend.trend_label == "样本不足" and trend.priority_score <= 0:
            continue
        trends.append(trend)

    return sorted(
        trends,
        key=lambda item: (
            item.priority_score,
            item.weak_exam_count,
            item.total_lost_score,
            item.trend_exam_count,
        ),
        reverse=True,
    )[:limit]


def _build_student_knowledge_trend(
    items: list[ScoreKnowledgeSnapshot],
    exam_map: dict[int, Exam],
    *,
    session: Session,
) -> StudentKnowledgeTrendAnalytics:
    latest = items[-1]
    rates = [item.score_rate for item in items if item.score_rate is not None]
    gaps = [item.grade_gap_rate for item in items if item.grade_gap_rate is not None]
    weak_exam_count = sum(1 for item in items if _knowledge_snapshot_is_weak(item))
    total_full_score = round(sum(item.full_score for item in items), 4)
    total_lost_score = round(sum(item.lost_score for item in items), 4)
    latest_score_rate = latest.score_rate
    average_score_rate = round(sum(rates) / len(rates), 4) if rates else None
    latest_grade_gap_rate = latest.grade_gap_rate
    average_grade_gap_rate = round(sum(gaps) / len(gaps), 4) if gaps else None
    trend_delta = (
        round(rates[-1] - rates[0], 4)
        if len(rates) >= KNOWLEDGE_TREND_MIN_EXAM_COUNT
        else None
    )
    trend_label = _diagnose_knowledge_trend(
        exam_count=len(items),
        total_full_score=total_full_score,
        weak_exam_count=weak_exam_count,
        rates=rates,
        latest_score_rate=latest_score_rate,
        trend_delta=trend_delta,
    )
    priority_score = _calculate_knowledge_trend_priority(
        trend_label=trend_label,
        total_lost_score=total_lost_score,
        average_score_rate=average_score_rate,
        weak_exam_count=weak_exam_count,
        exam_count=len(items),
    )
    points = [
        StudentKnowledgeTrendPoint(
            exam_id=item.exam_id,
            exam_name=exam_map[item.exam_id].name if item.exam_id in exam_map else str(item.exam_id),
            exam_date=exam_map[item.exam_id].exam_date if item.exam_id in exam_map else latest.exam.exam_date,
            score_rate=item.score_rate,
            grade_average_rate=item.grade_average_rate,
            grade_gap_rate=item.grade_gap_rate,
            full_score=item.full_score,
            lost_score=item.lost_score,
            diagnosis_label=item.diagnosis_label,
            dominant_error_tag=item.dominant_error_tag,
            question_numbers=item.question_numbers_json or [],
        )
        for item in items
    ]
    subject_name = latest.subject.name if latest.subject else str(latest.subject_id)
    point_name = latest.knowledge_point.name if latest.knowledge_point else str(latest.knowledge_point_id)
    paths = build_knowledge_paths(
        list(session.scalars(select(KnowledgePoint).where(KnowledgePoint.subject_id == latest.subject_id)).all())
    )
    error_tags = _merge_error_tag_stats([item.error_tags_json for item in items])
    return StudentKnowledgeTrendAnalytics(
        subject_id=latest.subject_id,
        subject_name=subject_name,
        knowledge_point_id=latest.knowledge_point_id,
        knowledge_point_name=point_name,
        knowledge_path=paths.get(latest.knowledge_point_id),
        trend_exam_count=len(items),
        weak_exam_count=weak_exam_count,
        latest_score_rate=latest_score_rate,
        average_score_rate=average_score_rate,
        latest_grade_gap_rate=latest_grade_gap_rate,
        average_grade_gap_rate=average_grade_gap_rate,
        trend_delta=trend_delta,
        total_full_score=total_full_score,
        total_lost_score=total_lost_score,
        priority_score=priority_score,
        trend_label=trend_label,
        error_tag_stats=error_tags,
        dominant_error_tag=error_tags[0]["tag"] if error_tags else None,
        points=points,
        suggestion=_build_knowledge_trend_suggestion(trend_label, subject_name, point_name),
    )


def get_class_knowledge_briefing(
    session: Session,
    class_id: int,
    exam_id: int,
    subject_id: int | None = None,
) -> ClassKnowledgeBriefingResponse:
    exam = get_exam(session, exam_id)
    school_class = session.get(SchoolClass, class_id)
    if not exam:
        raise HTTPException(status_code=404, detail="考试不存在")
    if not school_class:
        raise HTTPException(status_code=404, detail="班级不存在")
    context_map = load_exam_context_map(session, exam_id)
    stmt = (
        select(ScoreKnowledgeSnapshot)
        .options(
            joinedload(ScoreKnowledgeSnapshot.student).joinedload(Student.current_class),
            joinedload(ScoreKnowledgeSnapshot.subject),
            joinedload(ScoreKnowledgeSnapshot.knowledge_point),
        )
        .where(
            ScoreKnowledgeSnapshot.exam_id == exam_id,
            ScoreKnowledgeSnapshot.is_active.is_(True),
        )
    )
    if subject_id is not None:
        stmt = stmt.where(ScoreKnowledgeSnapshot.subject_id == subject_id)
    snapshots = [
        item
        for item in session.scalars(stmt).all()
        if item.student and effective_class_id(item.student, context_map.get(item.student_id)) == class_id
    ]
    if not snapshots:
        return ClassKnowledgeBriefingResponse(
            exam_id=exam.id,
            exam_name=exam.name,
            class_id=school_class.id,
            class_name=school_class.name,
            subject_id=subject_id,
            generated_at=datetime.now(),
            notices=["当前班级暂无题分知识点快照，请先导入题分明细。"],
        )

    point_paths = _knowledge_paths_for_snapshots(session, snapshots)
    grouped: dict[tuple[int, int], list[ScoreKnowledgeSnapshot]] = defaultdict(list)
    for item in snapshots:
        grouped[(item.subject_id, item.knowledge_point_id)].append(item)

    rows: list[ClassKnowledgeBriefingItem] = []
    for items in grouped.values():
        weak_items = [item for item in items if _knowledge_snapshot_is_weak(item) and item.priority_score > 0]
        if not weak_items:
            continue
        total_student_count = len({item.student_id for item in items})
        weak_student_count = len({item.student_id for item in weak_items})
        lost_score_total = round(sum(item.lost_score for item in weak_items), 4)
        average_score_rate = _safe_average([item.score_rate for item in weak_items])
        grade_average_rate = _safe_average([item.grade_average_rate for item in items])
        question_numbers = sorted({number for item in weak_items for number in (item.question_numbers_json or [])})
        error_tags = _merge_error_tag_stats([item.error_tags_json for item in weak_items])
        latest = weak_items[0]
        priority_score = round(weak_student_count * 1.5 + lost_score_total + len(error_tags) * 0.5, 4)
        priority_label = "高" if priority_score >= 12 or weak_student_count >= 3 else ("中" if priority_score >= 6 else "低")
        subject_name = latest.subject.name if latest.subject else str(latest.subject_id)
        point_name = latest.knowledge_point.name if latest.knowledge_point else str(latest.knowledge_point_id)
        rows.append(
            ClassKnowledgeBriefingItem(
                subject_id=latest.subject_id,
                subject_name=subject_name,
                knowledge_point_id=latest.knowledge_point_id,
                knowledge_point_name=point_name,
                knowledge_path=point_paths.get(latest.knowledge_point_id),
                weak_student_count=weak_student_count,
                total_student_count=total_student_count,
                average_score_rate=average_score_rate,
                grade_average_rate=grade_average_rate,
                lost_score_total=lost_score_total,
                question_numbers=question_numbers,
                error_tag_stats=[KnowledgeErrorTagStat(tag=str(item["tag"]), count=int(item["count"])) for item in error_tags],
                priority_score=priority_score,
                priority_label=priority_label,
                suggestion=_build_class_knowledge_suggestion(subject_name, point_name, weak_student_count, error_tags),
                weak_students=[
                    ClassKnowledgeBriefingStudent(
                        student_id=item.student_id,
                        student_name=item.student.name if item.student else str(item.student_id),
                        student_no=item.student.student_no if item.student else None,
                        class_name=effective_class_name(item.student, context_map.get(item.student_id)) if item.student else None,
                        score_rate=item.score_rate,
                        lost_score=item.lost_score,
                        diagnosis_label=item.diagnosis_label,
                        main_error_tag=item.dominant_error_tag,
                    )
                    for item in sorted(weak_items, key=lambda current: (current.score_rate or 1.0, -current.lost_score, current.student_id))
                ],
            )
        )
    rows.sort(key=lambda item: (item.priority_score, item.weak_student_count, item.lost_score_total), reverse=True)
    return ClassKnowledgeBriefingResponse(
        exam_id=exam.id,
        exam_name=exam.name,
        class_id=school_class.id,
        class_name=school_class.name,
        subject_id=subject_id,
        generated_at=datetime.now(),
        items=rows,
        notices=[] if rows else ["当前班级暂无达到阈值的薄弱知识点。"],
    )


def _knowledge_snapshot_is_weak(item: ScoreKnowledgeSnapshot) -> bool:
    if item.diagnosis_label in {"优先补弱", "需要巩固", "低于年级"}:
        return True
    return item.score_rate is not None and item.score_rate < KNOWLEDGE_WEAK_RATE_THRESHOLD


def _knowledge_paths_for_snapshots(
    session: Session,
    snapshots: list[ScoreKnowledgeSnapshot],
) -> dict[int, str]:
    subject_ids = list({item.subject_id for item in snapshots})
    if not subject_ids:
        return {}
    points = list(
        session.scalars(
            select(KnowledgePoint).where(
                KnowledgePoint.subject_id.in_(subject_ids),
                KnowledgePoint.is_active.is_(True),
            )
        ).all()
    )
    return build_knowledge_paths(points)


def _merge_error_tag_stats(values: list[object]) -> list[dict[str, object]]:
    counter: Counter[str] = Counter()
    for value in values:
        if not isinstance(value, list):
            continue
        for item in value:
            if isinstance(item, dict):
                tag = item.get("tag") or item.get("name")
                count = item.get("count", 1)
                if tag:
                    counter[str(tag)] += int(count or 1)
            elif isinstance(item, str):
                counter[item] += 1
    return [{"tag": tag, "count": count} for tag, count in counter.most_common() if tag and count > 0]


def _safe_average(values: list[float | None]) -> float | None:
    numbers = [value for value in values if value is not None]
    if not numbers:
        return None
    return round(sum(numbers) / len(numbers), 4)


def _build_class_knowledge_suggestion(
    subject_name: str,
    point_name: str,
    weak_student_count: int,
    error_tags: list[dict[str, object]],
) -> str:
    error_text = f"，集中错因为{error_tags[0]['tag']}" if error_tags else ""
    return f"{subject_name}-{point_name} 有 {weak_student_count} 名学生达到薄弱阈值{error_text}。建议先做 10 分钟共性讲评，再给弱项学生布置同类补弱任务。"


def _diagnose_knowledge_trend(
    *,
    exam_count: int,
    total_full_score: float,
    weak_exam_count: int,
    rates: list[float],
    latest_score_rate: float | None,
    trend_delta: float | None,
) -> str:
    if exam_count < KNOWLEDGE_TREND_MIN_EXAM_COUNT or total_full_score < KNOWLEDGE_TREND_MIN_FULL_SCORE:
        return "样本不足"
    if trend_delta is not None and latest_score_rate is not None and trend_delta >= KNOWLEDGE_IMPROVEMENT_DELTA and latest_score_rate >= KNOWLEDGE_WEAK_RATE_THRESHOLD:
        return "正在改善"
    if len(rates) >= 3 and max(rates) - min(rates) >= KNOWLEDGE_VOLATILE_DELTA and weak_exam_count >= 2:
        return "波动反复"
    if weak_exam_count >= max(2, math.ceil(exam_count * 0.6)):
        return "持续薄弱"
    if weak_exam_count == 1:
        return "偶发失误"
    return "保持观察"


def _calculate_knowledge_trend_priority(
    *,
    trend_label: str,
    total_lost_score: float,
    average_score_rate: float | None,
    weak_exam_count: int,
    exam_count: int,
) -> float:
    if trend_label == "样本不足":
        return 0.0
    improvement_space = max(1.0 - (average_score_rate if average_score_rate is not None else 1.0), 0.0)
    persistence = weak_exam_count / exam_count if exam_count else 0.0
    label_weight = {
        "持续薄弱": 1.25,
        "波动反复": 1.1,
        "正在改善": 0.75,
        "偶发失误": 0.35,
        "保持观察": 0.2,
    }.get(trend_label, 0.0)
    return round(total_lost_score * improvement_space * (1.0 + persistence) * label_weight, 4)


def _build_knowledge_trend_suggestion(trend_label: str, subject_name: str, point_name: str) -> str:
    label = f"{subject_name}-{point_name}"
    if trend_label == "持续薄弱":
        return f"{label} 已连续暴露短板，建议列为下一阶段固定补弱专题，先补概念和基础模型。"
    if trend_label == "波动反复":
        return f"{label} 表现不稳定，建议复盘不同题型下的失分步骤，建立易错清单。"
    if trend_label == "正在改善":
        return f"{label} 已有改善迹象，建议保持同类题巩固，避免训练中断。"
    if trend_label == "偶发失误":
        return f"{label} 本次更像偶发失误，先复盘本次题目，不必扩大训练量。"
    if trend_label == "样本不足":
        return "题分样本不足，暂不作为连续补弱重点。"
    return f"{label} 暂保持观察，后续结合下一次题分明细再判断。"


def _merge_knowledge_action_suggestions(
    suggestions: list[StudentActionSuggestion],
    knowledge_points: list[StudentKnowledgePointAnalytics],
) -> list[StudentActionSuggestion]:
    focus_points = [
        item for item in knowledge_points
        if item.diagnosis_label in {"优先补弱", "需要巩固", "低于年级"} and item.priority_score > 0
    ][:3]
    if not focus_points:
        return suggestions
    subject_names = list(dict.fromkeys(item.subject_name for item in focus_points))
    point_names = [f"{item.subject_name}-{item.knowledge_point_name}" for item in focus_points]
    suggestions.append(
        StudentActionSuggestion(
            category="knowledge_focus",
            title="知识点清单",
            summary=f"下一阶段优先处理 {'、'.join(point_names)}，先复盘涉及题号，再补同类题巩固。",
            subject_names=subject_names,
            priority=4,
        )
    )
    return sorted(suggestions, key=lambda item: item.priority)


def _merge_knowledge_trend_action_suggestions(
    suggestions: list[StudentActionSuggestion],
    knowledge_trends: list[StudentKnowledgeTrendAnalytics],
) -> list[StudentActionSuggestion]:
    focus_points = [
        item for item in knowledge_trends
        if item.trend_label in {"持续薄弱", "波动反复"} and item.priority_score > 0
    ][:3]
    if not focus_points:
        return suggestions
    subject_names = list(dict.fromkeys(item.subject_name for item in focus_points))
    point_names = [f"{item.subject_name}-{item.knowledge_point_name}" for item in focus_points]
    suggestions.append(
        StudentActionSuggestion(
            category="knowledge_trend_focus",
            title="连续薄弱",
            summary=f"{'、'.join(point_names)} 在多次题分明细中反复暴露，建议列入阶段固定补弱清单。",
            subject_names=subject_names,
            priority=4,
        )
    )
    return sorted(suggestions, key=lambda item: item.priority)


def _list_active_target_lines(session: Session, exam_id: int) -> list[ScoreTargetLine]:
    return list(
        session.scalars(
            select(ScoreTargetLine)
            .where(ScoreTargetLine.exam_id == exam_id, ScoreTargetLine.is_active.is_(True))
            .order_by(ScoreTargetLine.sort_order.asc(), ScoreTargetLine.id.asc())
        ).all()
    )


def _resolve_target_line_score_thresholds(
    target_lines: list[ScoreTargetLine],
    total_snapshots,
) -> dict[int, float]:
    thresholds: dict[int, float] = {}
    ranked_snapshots = sorted(
        [item for item in total_snapshots if item.grade_rank is not None],
        key=lambda item: (item.grade_rank or 0, -item.total_score),
    )
    for line in target_lines:
        threshold: float | None = None
        if line.score_value is not None:
            threshold = float(line.score_value)
        elif line.line_type == "rank" and line.rank_value is not None:
            candidates = [item for item in ranked_snapshots if item.grade_rank is not None and item.grade_rank <= line.rank_value]
            if candidates:
                threshold = min(item.total_score for item in candidates)
        if threshold is not None:
            thresholds[line.id] = round(threshold, 2)
    return thresholds


def _build_student_target_line_gaps(
    target_lines: list[ScoreTargetLine],
    thresholds: dict[int, float],
    total_snapshot,
) -> list[StudentTargetLineGap]:
    if not total_snapshot:
        return []
    rows: list[StudentTargetLineGap] = []
    for line in target_lines:
        reached = _line_reached(line, total_snapshot)
        threshold_score = thresholds.get(line.id)
        gap_score = (
            round(total_snapshot.total_score - threshold_score, 2)
            if threshold_score is not None
            else None
        )
        gap_rank = (
            line.rank_value - total_snapshot.grade_rank
            if line.rank_value is not None and total_snapshot.grade_rank is not None
            else None
        )
        status = "reached" if reached else "below"
        if _line_near_below(line, total_snapshot):
            status = "near_below"
        elif _line_near_above(line, total_snapshot):
            status = "near_above"
        rows.append(
            StudentTargetLineGap(
                line_id=line.id,
                line_name=line.name,
                line_type=line.line_type,
                threshold_label=_line_threshold_label(line),
                threshold_score=threshold_score,
                reached=reached,
                gap_score=gap_score,
                gap_rank=gap_rank,
                status=status,
            )
        )
    return rows


def _group_subject_snapshots(subject_snapshots) -> dict[int, list]:
    grouped: dict[int, list] = defaultdict(list)
    for item in subject_snapshots:
        if item.score is not None:
            grouped[item.subject_id].append(item)
    return grouped


def _build_effective_score_targets_by_subject(
    subject_groups: dict[int, list],
    student_subjects,
    target_lines: list[ScoreTargetLine],
    total_line_thresholds: dict[int, float],
) -> dict[int, list[StudentSubjectEffectiveTarget]]:
    student_subject_ids = [item.subject_id for item in student_subjects if item.score is not None]
    subject_averages = {
        subject_id: safe_mean([item.score for item in items if item.score is not None])
        for subject_id, items in subject_groups.items()
        if subject_id in student_subject_ids
    }
    average_denominator = sum(value for value in subject_averages.values() if value > 0)
    if average_denominator <= 0:
        return {}

    student_subject_map = {item.subject_id: item for item in student_subjects}
    target_line_name_map = {item.id: item.name for item in target_lines}
    rows: dict[int, list[StudentSubjectEffectiveTarget]] = defaultdict(list)
    for subject_id, average_score in subject_averages.items():
        if average_score <= 0:
            continue
        student_subject = student_subject_map.get(subject_id)
        for line_id, threshold in total_line_thresholds.items():
            target_score = round(threshold * average_score / average_denominator, 2)
            actual_score = student_subject.score if student_subject and student_subject.score is not None else None
            rows[subject_id].append(
                StudentSubjectEffectiveTarget(
                    line_id=line_id,
                    line_name=target_line_name_map.get(line_id, f"目标线 {line_id}"),
                    target_score=target_score,
                    actual_score=actual_score,
                    gap_score=round(actual_score - target_score, 2) if actual_score is not None else None,
                )
            )
    return rows


def _build_peer_subject_averages(
    total_snapshots,
    subject_snapshots,
    student_grade_rank: int | None,
) -> tuple[dict[int, float], int, str | None]:
    if student_grade_rank is None:
        return {}, 0, "缺少总分校内名次，无法计算同档群体。"
    total_by_rank = [
        item for item in total_snapshots if item.grade_rank is not None and item.student_id is not None
    ]
    selected = _select_peer_total_snapshots(total_by_rank, student_grade_rank, 10)
    note = None
    if len(selected) < 10:
        selected = _select_peer_total_snapshots(total_by_rank, student_grade_rank, 20)
    if len(selected) < 10:
        note = f"同档样本仅 {len(selected)} 人，结论需谨慎。"
    student_ids = {item.student_id for item in selected}
    grouped: dict[int, list[float]] = defaultdict(list)
    for item in subject_snapshots:
        if item.student_id in student_ids and item.score is not None:
            grouped[item.subject_id].append(item.score)
    return {
        subject_id: safe_mean(values)
        for subject_id, values in grouped.items()
        if values
    }, len(selected), note


def _select_peer_total_snapshots(total_snapshots, grade_rank: int, radius: int) -> list:
    low = max(1, grade_rank - radius)
    high = grade_rank + radius
    return [
        item
        for item in total_snapshots
        if item.grade_rank is not None and low <= item.grade_rank <= high
    ]


def _build_student_score_trends(
    session: Session,
    student_id: int,
    current_exam: Exam,
) -> tuple[list[StudentTotalTrendPoint], dict[int, list[StudentSubjectTrendPoint]]]:
    exams = [
        exam
        for exam in _list_panorama_exams(session)
        if exam.is_trend_enabled and exam.exam_date <= current_exam.exam_date
    ][-5:]
    total_points: list[StudentTotalTrendPoint] = []
    subject_points: dict[int, list[StudentSubjectTrendPoint]] = defaultdict(list)
    for exam in exams:
        total_snapshot = next(
            (item for item in get_total_snapshots_for_exam(session, exam.id) if item.student_id == student_id),
            None,
        )
        total_points.append(
            StudentTotalTrendPoint(
                exam_id=exam.id,
                exam_name=exam.name,
                exam_date=exam.exam_date,
                total_score=total_snapshot.total_score if total_snapshot else None,
                class_rank=total_snapshot.class_rank if total_snapshot else None,
                grade_rank=total_snapshot.grade_rank if total_snapshot else None,
                grade_percentile=total_snapshot.grade_percentile if total_snapshot else None,
            )
        )
        for item in get_subject_snapshots_for_exam(session, exam.id):
            if item.student_id != student_id:
                continue
            subject_points[item.subject_id].append(
                StudentSubjectTrendPoint(
                    exam_id=exam.id,
                    exam_name=exam.name,
                    exam_date=exam.exam_date,
                    score=item.score,
                    grade_rank=item.grade_rank,
                    grade_percentile=item.grade_percentile,
                )
            )
    return total_points, subject_points


def _calculate_z_score(score: float | None, mean_score: float, stddev: float) -> float | None:
    if score is None or stddev <= 0:
        return None
    return round((score - mean_score) / stddev, 2)


def _calculate_t_score(z_score: float | None) -> float | None:
    if z_score is None:
        return None
    return round(50 + 10 * z_score, 2)


def _rank_stddev(points: list[StudentSubjectTrendPoint]) -> float | None:
    ranks = [point.grade_rank for point in points if point.grade_rank is not None]
    if len(ranks) < 3:
        return None
    avg = sum(ranks) / len(ranks)
    return round(math.sqrt(sum((rank - avg) ** 2 for rank in ranks) / len(ranks)), 2)


def _build_subject_diagnosis_tags(
    *,
    rank_deviation: int | None,
    rank_sample_count: int,
    peer_average_delta: float | None,
    trend_rank_stddev: float | None,
    trend_exam_count: int,
    effective_targets: list[StudentSubjectEffectiveTarget],
) -> list[str]:
    tags: list[str] = []
    if rank_deviation is not None:
        weak_gap = _rank_deviation_weak_threshold(rank_sample_count)
        severe_gap = _rank_deviation_severe_threshold(rank_sample_count)
        if rank_deviation <= -severe_gap:
            tags.append("严重拖后腿")
        elif rank_deviation <= -weak_gap:
            tags.append("偏科弱项")
        elif rank_deviation >= weak_gap:
            tags.append("优势学科")
    if peer_average_delta is not None:
        if peer_average_delta <= -10:
            tags.append("低于同档")
        elif peer_average_delta >= 10:
            tags.append("高于同档")
    if trend_exam_count < 3:
        tags.append("趋势样本不足")
    elif trend_rank_stddev is not None and trend_rank_stddev >= 30:
        tags.append("波动偏大")
    if any(item.gap_score is not None and item.gap_score < 0 for item in effective_targets):
        tags.append("有效分未达")
    return tags or ["正常"]


def _rank_deviation_weak_threshold(sample_count: int) -> int:
    if sample_count <= 0:
        return 30
    return min(30, max(3, math.ceil(sample_count * 0.1)))


def _rank_deviation_severe_threshold(sample_count: int) -> int:
    if sample_count <= 0:
        return 100
    return min(100, max(6, math.ceil(sample_count * 0.25)))


def _format_subject_diagnosis(tags: list[str]) -> str:
    if "严重拖后腿" in tags:
        return "严重拖后腿"
    if "偏科弱项" in tags or "低于同档" in tags or "有效分未达" in tags:
        return "重点补弱"
    if "优势学科" in tags or "高于同档" in tags:
        return "优势学科"
    if "波动偏大" in tags:
        return "稳定性关注"
    return "正常"


def _build_student_action_suggestions(
    subjects: list[StudentSubjectAnalytics],
    target_line_gaps: list[StudentTargetLineGap],
) -> list[StudentActionSuggestion]:
    suggestions: list[StudentActionSuggestion] = []
    rank_threshold = _rank_deviation_weak_threshold(
        max((item.grade_rank or 0 for item in subjects), default=0)
    )
    strengths = [
        item for item in subjects
        if item.rank_deviation is not None and item.rank_deviation >= rank_threshold and item.trend_rank_stddev is not None and item.trend_rank_stddev < 30
    ]
    if not strengths:
        strengths = [
            item for item in subjects
            if item.rank_deviation is not None and item.rank_deviation >= rank_threshold
        ]
    if strengths:
        subject_names = [item.subject_name for item in sorted(strengths, key=lambda item: item.rank_deviation or 0, reverse=True)[:2]]
        suggestions.append(
            StudentActionSuggestion(
                category="keep_strength",
                title="保优",
                summary=f"{'、'.join(subject_names)} 当前相对总分位置更靠前，建议保持稳定投入。",
                subject_names=subject_names,
                priority=1,
            )
        )

    weakness = sorted(
        [item for item in subjects if item.rank_deviation is not None and item.rank_deviation < 0],
        key=lambda item: item.rank_deviation or 0,
    )[:2]
    if weakness:
        subject_names = [item.subject_name for item in weakness]
        suggestions.append(
            StudentActionSuggestion(
                category="fix_weakness",
                title="补弱",
                summary=f"{'、'.join(subject_names)} 与总分名次差距最大，是当前抢分空间优先方向。",
                subject_names=subject_names,
                priority=2,
            )
        )

    near_lines = [item for item in target_line_gaps if item.status in {"near_below", "near_above"}]
    if near_lines:
        line_names = [item.line_name for item in near_lines[:2]]
        suggestions.append(
            StudentActionSuggestion(
                category="target_warning",
                title="临界预警",
                summary=f"总分处在 {'、'.join(line_names)} 附近，建议结合有效分差距优先处理短板科目。",
                priority=3,
            )
        )
    return suggestions


def _build_student_overview_sentence(
    *,
    grade_rank_delta: int | None,
    subjects: list[StudentSubjectAnalytics],
    target_line_gaps: list[StudentTargetLineGap],
) -> str:
    segments: list[str] = []
    if grade_rank_delta is not None:
        if grade_rank_delta > 0:
            segments.append("本次考试总排名上升")
        elif grade_rank_delta < 0:
            segments.append("本次考试总排名回落")
        else:
            segments.append("本次考试总排名基本稳定")
    strengths = [item.subject_name for item in subjects if item.diagnosis == "优势学科"]
    weakness = [item.subject_name for item in subjects if item.diagnosis in {"严重拖后腿", "重点补弱"}]
    if strengths:
        segments.append(f"优势学科为{'、'.join(strengths[:2])}")
    if weakness:
        segments.append(f"{'、'.join(weakness[:2])}存在明显补弱空间")
    if any(item.status == "near_below" for item in target_line_gaps):
        segments.append("目标线临界生特征明显")
    return "，".join(segments) + "。" if segments else "本次考试画像以校内名次、PR 和学科相对位置为主，暂无明显异常。"


def get_class_analytics(session: Session, class_id: int, exam_id: int) -> ClassAnalyticsResponse:
    exam = get_exam(session, exam_id)
    school_class = session.get(SchoolClass, class_id)
    if not exam:
        raise HTTPException(status_code=404, detail="考试不存在")
    if not school_class:
        raise HTTPException(status_code=404, detail="班级不存在")

    context_map = load_exam_context_map(session, exam_id)
    total_snapshots = [
        item
        for item in get_total_snapshots_for_exam(session, exam_id)
        if item.student and _snapshot_effective_class_id(item, context_map) == class_id
    ]
    if not total_snapshots:
        raise HTTPException(status_code=404, detail="该班级暂无本次考试总分数据")

    total_scores = [item.total_score for item in total_snapshots]
    grade_id = school_class.grade_id
    grade_total_scores = [
        item.total_score
        for item in get_total_snapshots_for_exam(session, exam_id)
        if item.student and _snapshot_matches_grade(item, exam, grade_id, context_map)
    ]

    subject_snapshots = [
        item
        for item in get_subject_snapshots_for_exam(session, exam_id)
        if item.student and _snapshot_effective_class_id(item, context_map) == class_id and item.score is not None
    ]
    grouped: dict[int, list] = defaultdict(list)
    for item in subject_snapshots:
        grouped[item.subject_id].append(item)

    subject_breakdown = []
    for subject_id, items in grouped.items():
        scores = [item.score for item in items if item.score is not None]
        valid_count = len(scores)
        subject_breakdown.append(
            SubjectAggregateItem(
                subject_id=subject_id,
                subject_name=items[0].subject.name if items[0].subject else str(subject_id),
                average_score=safe_mean(scores),
                median_score=safe_median(scores),
                max_score=max(scores) if scores else 0.0,
                min_score=min(scores) if scores else 0.0,
                standard_deviation=safe_stddev(scores),
                excellent_rate=calculate_rate(sum(1 for item in items if item.excellent_flag), valid_count),
                pass_rate=calculate_rate(sum(1 for item in items if item.pass_flag), valid_count),
                valid_count=valid_count,
            )
        )
    subject_breakdown.sort(key=lambda item: item.subject_id)

    return ClassAnalyticsResponse(
        exam_id=exam.id,
        exam_name=exam.name,
        class_id=class_id,
        class_name=school_class.name,
        student_count=len(total_snapshots),
        total_average=safe_mean(total_scores),
        total_median=safe_median(total_scores),
        total_max=max(total_scores) if total_scores else 0.0,
        total_min=min(total_scores) if total_scores else 0.0,
        total_standard_deviation=safe_stddev(total_scores),
        grade_average=safe_mean(grade_total_scores) if grade_total_scores else None,
        subject_breakdown=subject_breakdown,
    )


def get_teacher_analytics(session: Session, teacher_id: int, exam_id: int) -> TeacherAnalyticsResponse:
    exam = get_exam(session, exam_id)
    teacher = session.get(Teacher, teacher_id)
    if not exam:
        raise HTTPException(status_code=404, detail="考试不存在")
    if not teacher:
        raise HTTPException(status_code=404, detail="教师不存在")

    assignments = session.scalars(
        select(TeachingAssignment)
        .options(
            joinedload(TeachingAssignment.school_class),
            joinedload(TeachingAssignment.subject),
        )
        .where(
            TeachingAssignment.teacher_id == teacher_id,
            TeachingAssignment.semester_id == exam.semester_id,
            TeachingAssignment.is_active.is_(True),
        )
    ).all()
    if not assignments:
        raise HTTPException(status_code=404, detail="该教师在本考试所属学期暂无任教关系")

    score_records = [item for item in get_score_records_for_exam(session, exam_id) if item.score is not None]
    context_map = load_exam_context_map(session, exam_id)
    subject_meta_map = {item.subject_id: item for item in exam.subjects}
    assignment_breakdown: list[TeacherAssignmentAnalytics] = []
    overall_scores: list[float] = []

    for assignment in assignments:
        matched = [
            record
            for record in score_records
            if record.student
            and effective_class_id(record.student, context_map.get(record.student_id)) == assignment.class_id
            and record.subject_id == assignment.subject_id
            and record.score_status == "normal"
        ]
        if not matched:
            continue
        scores = [record.score for record in matched if record.score is not None]
        overall_scores.extend(scores)
        meta = subject_meta_map.get(assignment.subject_id)
        excellent_count = 0
        pass_count = 0
        for record in matched:
            if meta and meta.excellent_line is not None and record.score is not None and record.score >= meta.excellent_line:
                excellent_count += 1
            if meta and meta.pass_line is not None and record.score is not None and record.score >= meta.pass_line:
                pass_count += 1
        assignment_breakdown.append(
            TeacherAssignmentAnalytics(
                assignment_id=assignment.id,
                class_id=assignment.class_id,
                class_name=assignment.school_class.name if assignment.school_class else None,
                subject_id=assignment.subject_id,
                subject_name=assignment.subject.name if assignment.subject else None,
                average_score=safe_mean(scores),
                excellent_rate=calculate_rate(excellent_count, len(scores)),
                pass_rate=calculate_rate(pass_count, len(scores)),
                valid_count=len(scores),
            )
        )

    if not assignment_breakdown:
        raise HTTPException(status_code=404, detail="该教师暂无可用于分析的成绩数据")

    return TeacherAnalyticsResponse(
        exam_id=exam.id,
        exam_name=exam.name,
        teacher_id=teacher_id,
        teacher_name=teacher.name,
        overall_average=safe_mean(overall_scores) if overall_scores else None,
        assignment_breakdown=assignment_breakdown,
    )


def get_teacher_panorama(
    session: Session,
    teacher_id: int,
    academic_year_ids: list[int] | None = None,
) -> TeacherPanoramaResponse:
    teacher = session.get(Teacher, teacher_id)
    if not teacher:
        raise HTTPException(status_code=404, detail="教师不存在")

    assignments = session.scalars(
        select(TeachingAssignment)
        .options(
            joinedload(TeachingAssignment.school_class),
            joinedload(TeachingAssignment.subject),
        )
        .where(
            TeachingAssignment.teacher_id == teacher_id,
            TeachingAssignment.is_active.is_(True),
        )
    ).all()
    if not assignments:
        raise HTTPException(status_code=404, detail="该教师暂无可用于全景对比的任教关系")

    assignments_by_semester: dict[int, list[TeachingAssignment]] = defaultdict(list)
    for item in assignments:
        assignments_by_semester[item.semester_id].append(item)

    exam_points: list[GradePanoramaExamPointRead] = []
    subject_points_by_id: dict[int, list[GradePanoramaSubjectPointRead]] = defaultdict(list)
    subject_name_by_id: dict[int, str] = {}

    for exam in _list_panorama_exams(session):
        academic_year = exam.semester.academic_year if exam.semester else None
        if academic_year_ids and (not academic_year or academic_year.id not in academic_year_ids):
            continue

        semester_assignments = assignments_by_semester.get(exam.semester_id, [])
        assignment_pairs = {
            (item.class_id, item.subject_id): item
            for item in semester_assignments
            if item.class_id is not None and item.subject_id is not None
        }
        if not assignment_pairs:
            continue

        score_records = [item for item in get_score_records_for_exam(session, exam.id) if item.score is not None]
        context_map = load_exam_context_map(session, exam.id)
        total_snapshot_map = {
            item.student_id: item
            for item in get_total_snapshots_for_exam(session, exam.id)
            if item.student_id is not None
        }
        subject_meta_map = {item.subject_id: item for item in exam.subjects}

        matched_scores: list[float] = []
        teacher_student_ids: set[int] = set()
        excellent_count = 0
        subject_grouped_records: dict[int, list[ScoreRecord]] = defaultdict(list)

        for class_id, subject_id in assignment_pairs:
            matched = [
                record
                for record in score_records
                if record.student
                and effective_class_id(record.student, context_map.get(record.student_id)) == class_id
                and record.subject_id == subject_id
                and record.score_status == "normal"
            ]
            if not matched:
                continue

            meta = subject_meta_map.get(subject_id)
            for record in matched:
                if record.score is None:
                    continue
                matched_scores.append(record.score)
                teacher_student_ids.add(record.student_id)
                subject_grouped_records[subject_id].append(record)
                if meta and meta.excellent_line is not None and record.score >= meta.excellent_line:
                    excellent_count += 1

            subject_name_by_id.setdefault(
                subject_id,
                matched[0].subject.name if matched[0].subject else str(subject_id),
            )

        if not matched_scores:
            continue

        teacher_total_snapshots = [
            total_snapshot_map[student_id]
            for student_id in teacher_student_ids
            if student_id in total_snapshot_map
        ]
        exam_points.append(
            GradePanoramaExamPointRead(
                exam_id=exam.id,
                exam_name=exam.name,
                exam_date=exam.exam_date,
                academic_year_id=academic_year.id if academic_year else None,
                academic_year_name=academic_year.name if academic_year else None,
                semester_name=exam.semester.name if exam.semester else None,
                student_count=len(teacher_student_ids),
                total_average=safe_mean(matched_scores),
                total_median=safe_median(matched_scores),
                excellent_rate=calculate_rate(excellent_count, len(matched_scores)),
                top10_count=sum(
                    1 for item in teacher_total_snapshots if item.grade_rank is not None and item.grade_rank <= 10
                ),
                top30_count=sum(
                    1 for item in teacher_total_snapshots if item.grade_rank is not None and item.grade_rank <= 30
                ),
            )
        )

        for subject_id, records in subject_grouped_records.items():
            scores = [record.score for record in records if record.score is not None]
            if not scores:
                continue
            meta = subject_meta_map.get(subject_id)
            subject_points_by_id[subject_id].append(
                GradePanoramaSubjectPointRead(
                    exam_id=exam.id,
                    exam_name=exam.name,
                    exam_date=exam.exam_date,
                    academic_year_name=academic_year.name if academic_year else None,
                    average_score=safe_mean(scores),
                    excellent_rate=(
                        calculate_rate(
                            sum(
                                1
                                for record in records
                                if record.score is not None
                                and meta
                                and meta.excellent_line is not None
                                and record.score >= meta.excellent_line
                            ),
                            len(scores),
                        )
                        if meta and meta.excellent_line is not None
                        else 0.0
                    ),
                    valid_count=len(scores),
                )
            )

    if not exam_points:
        raise HTTPException(status_code=404, detail="该教师当前暂无全景对比数据")

    year_grouped: dict[int, list[GradePanoramaExamPointRead]] = defaultdict(list)
    for point in exam_points:
        if point.academic_year_id is not None:
            year_grouped[point.academic_year_id].append(point)

    year_summaries = [
        GradePanoramaYearSummaryRead(
            academic_year_id=academic_year_id,
            academic_year_name=items[0].academic_year_name or str(academic_year_id),
            exam_count=len(items),
            average_score=safe_mean([item.total_average for item in items]),
            average_excellent_rate=(
                safe_mean([item.excellent_rate for item in items if item.excellent_rate is not None])
                if any(item.excellent_rate is not None for item in items)
                else None
            ),
            best_exam_name=max(items, key=lambda item: item.total_average).exam_name,
            latest_exam_name=max(items, key=lambda item: item.exam_date).exam_name,
        )
        for academic_year_id, items in sorted(year_grouped.items(), key=lambda current: current[1][0].academic_year_name or "")
    ]

    subject_trends = [
        GradePanoramaSubjectTrendRead(
            subject_id=subject_id,
            subject_name=subject_name_by_id.get(subject_id, str(subject_id)),
            points=sorted(items, key=lambda point: (point.exam_date, point.exam_id)),
        )
        for subject_id, items in subject_points_by_id.items()
    ]
    subject_trends.sort(key=lambda item: item.subject_name)

    return TeacherPanoramaResponse(
        teacher_id=teacher.id,
        teacher_name=teacher.name,
        academic_year_count=len(year_summaries),
        exam_count=len(exam_points),
        year_summaries=year_summaries,
        exam_points=exam_points,
        subject_trends=subject_trends,
    )


def get_grade_panorama(
    session: Session,
    grade_id: int,
    academic_year_ids: list[int] | None = None,
) -> GradePanoramaResponse:
    grade = session.get(Grade, grade_id)
    if not grade:
        raise HTTPException(status_code=404, detail="年级不存在")

    exam_points, year_summaries, subject_trends = _build_panorama_components(
        session,
        entity_id=grade_id,
        academic_year_ids=academic_year_ids,
        exam_filter=lambda exam: _exam_matches_grade_scope(exam, grade_id),
        total_filter=_filter_grade_total_snapshots,
        subject_filter=_filter_grade_subject_snapshots,
    )

    return GradePanoramaResponse(
        grade_id=grade.id,
        grade_name=grade.name,
        academic_year_count=len(year_summaries),
        exam_count=len(exam_points),
        year_summaries=year_summaries,
        exam_points=exam_points,
        subject_trends=subject_trends,
    )


def get_class_panorama(
    session: Session,
    class_id: int,
    academic_year_ids: list[int] | None = None,
) -> ClassPanoramaResponse:
    school_class = session.get(SchoolClass, class_id)
    if not school_class:
        raise HTTPException(status_code=404, detail="班级不存在")

    exam_points, year_summaries, subject_trends = _build_panorama_components(
        session,
        entity_id=class_id,
        academic_year_ids=academic_year_ids,
        exam_filter=lambda exam: _exam_matches_grade_scope(exam, school_class.grade_id),
        total_filter=_filter_class_total_snapshots,
        subject_filter=_filter_class_subject_snapshots,
    )

    return ClassPanoramaResponse(
        class_id=school_class.id,
        class_name=school_class.name,
        academic_year_count=len(year_summaries),
        exam_count=len(exam_points),
        year_summaries=year_summaries,
        exam_points=exam_points,
        subject_trends=subject_trends,
    )


def _list_panorama_exams(session: Session) -> list[Exam]:
    return session.scalars(
        select(Exam)
        .options(
            joinedload(Exam.semester).joinedload(Semester.academic_year),
            joinedload(Exam.subjects),
        )
        .where(Exam.is_active.is_(True), Exam.is_trend_enabled.is_(True))
        .order_by(Exam.exam_date.asc(), Exam.id.asc())
    ).unique().all()


def _build_panorama_components(
    session: Session,
    entity_id: int,
    academic_year_ids: list[int] | None,
    exam_filter,
    total_filter,
    subject_filter,
):
    exams = _list_panorama_exams(session)

    exam_points: list[GradePanoramaExamPointRead] = []
    subject_points_by_id: dict[int, list[GradePanoramaSubjectPointRead]] = defaultdict(list)
    subject_name_by_id: dict[int, str] = {}

    for exam in exams:
        if not exam_filter(exam):
            continue
        academic_year = exam.semester.academic_year if exam.semester else None
        if academic_year_ids and (not academic_year or academic_year.id not in academic_year_ids):
            continue

        context_map = load_exam_context_map(session, exam.id)
        total_snapshots = total_filter(get_total_snapshots_for_exam(session, exam.id), exam, entity_id, context_map)
        if not total_snapshots:
            continue
        total_scores = [item.total_score for item in total_snapshots]
        excellent_total_line = _resolve_total_excellent_line(exam)
        excellent_rate = (
            calculate_rate(sum(1 for item in total_snapshots if item.total_score >= excellent_total_line), len(total_snapshots))
            if excellent_total_line is not None
            else None
        )
        exam_points.append(
            GradePanoramaExamPointRead(
                exam_id=exam.id,
                exam_name=exam.name,
                exam_date=exam.exam_date,
                academic_year_id=academic_year.id if academic_year else None,
                academic_year_name=academic_year.name if academic_year else None,
                semester_name=exam.semester.name if exam.semester else None,
                student_count=len(total_snapshots),
                total_average=safe_mean(total_scores),
                total_median=safe_median(total_scores),
                excellent_rate=excellent_rate,
                top10_count=sum(1 for item in total_snapshots if item.grade_rank is not None and item.grade_rank <= 10),
                top30_count=sum(1 for item in total_snapshots if item.grade_rank is not None and item.grade_rank <= 30),
            )
        )

        subject_snapshots = subject_filter(get_subject_snapshots_for_exam(session, exam.id), exam, entity_id, context_map)
        grouped_subjects: dict[int, list] = defaultdict(list)
        for item in subject_snapshots:
            grouped_subjects[item.subject_id].append(item)
        for subject_id, items in grouped_subjects.items():
            scores = [item.score for item in items if item.score is not None]
            if not scores:
                continue
            subject_name_by_id.setdefault(
                subject_id,
                items[0].subject.name if items[0].subject else str(subject_id),
            )
            subject_points_by_id[subject_id].append(
                GradePanoramaSubjectPointRead(
                    exam_id=exam.id,
                    exam_name=exam.name,
                    exam_date=exam.exam_date,
                    academic_year_name=academic_year.name if academic_year else None,
                    average_score=safe_mean(scores),
                    excellent_rate=calculate_rate(sum(1 for item in items if item.excellent_flag), len(scores)),
                    valid_count=len(scores),
                )
            )

    if not exam_points:
        raise HTTPException(status_code=404, detail="当前条件下暂无全景对比数据")

    year_grouped: dict[int, list[GradePanoramaExamPointRead]] = defaultdict(list)
    for point in exam_points:
        if point.academic_year_id is not None:
            year_grouped[point.academic_year_id].append(point)

    year_summaries = [
        GradePanoramaYearSummaryRead(
            academic_year_id=academic_year_id,
            academic_year_name=items[0].academic_year_name or str(academic_year_id),
            exam_count=len(items),
            average_score=safe_mean([item.total_average for item in items]),
            average_excellent_rate=safe_mean([item.excellent_rate for item in items if item.excellent_rate is not None]) if any(item.excellent_rate is not None for item in items) else None,
            best_exam_name=max(items, key=lambda item: item.total_average).exam_name,
            latest_exam_name=max(items, key=lambda item: item.exam_date).exam_name,
        )
        for academic_year_id, items in sorted(year_grouped.items(), key=lambda current: current[1][0].academic_year_name or "")
    ]

    subject_trends = [
        GradePanoramaSubjectTrendRead(
            subject_id=subject_id,
            subject_name=subject_name_by_id.get(subject_id, str(subject_id)),
            points=sorted(items, key=lambda point: (point.exam_date, point.exam_id)),
        )
        for subject_id, items in subject_points_by_id.items()
    ]
    subject_trends.sort(key=lambda item: item.subject_name)

    return exam_points, year_summaries, subject_trends


def get_grade_analytics(session: Session, grade_id: int, exam_id: int) -> GradeAnalyticsResponse:
    exam = get_exam(session, exam_id)
    grade = session.get(Grade, grade_id)
    if not exam:
        raise HTTPException(status_code=404, detail="考试不存在")
    if not grade:
        raise HTTPException(status_code=404, detail="年级不存在")

    context_map = load_exam_context_map(session, exam_id)
    total_snapshots = [
        item
        for item in get_total_snapshots_for_exam(session, exam_id)
        if item.student and _snapshot_matches_grade(item, exam, grade_id, context_map)
    ]
    if not total_snapshots:
        raise HTTPException(status_code=404, detail="该年级暂无本次考试总分数据")

    total_scores = [item.total_score for item in total_snapshots]
    total_full_score = sum(item.full_score for item in exam.subjects if item.is_active and item.is_in_total)
    excellent_total_line = _resolve_total_excellent_line(exam)
    target_lines = list(
        session.scalars(
            select(ScoreTargetLine)
            .where(ScoreTargetLine.exam_id == exam.id, ScoreTargetLine.is_active.is_(True))
            .order_by(ScoreTargetLine.sort_order.asc(), ScoreTargetLine.id.asc())
        ).all()
    )

    class_group: dict[int | None, list] = defaultdict(list)
    for item in total_snapshots:
        class_group[_snapshot_effective_class_id(item, context_map)].append(item)

    class_breakdown: list[GradeClassAnalyticsItem] = []
    for class_id, items in class_group.items():
        scores = [item.total_score for item in items]
        excellent_rate = (
            calculate_rate(sum(1 for item in items if item.total_score >= excellent_total_line), len(items))
            if excellent_total_line is not None
            else None
        )
        class_breakdown.append(
            GradeClassAnalyticsItem(
                class_id=class_id,
                class_name=(
                    _snapshot_effective_class_name(items[0], context_map)
                    or "未分班"
                ),
                student_count=len(items),
                average_score=safe_mean(scores),
                median_score=safe_median(scores),
                max_score=max(scores) if scores else 0.0,
                min_score=min(scores) if scores else 0.0,
                excellent_rate=excellent_rate,
                target_line_counts={
                    line.name: sum(1 for snapshot in items if _line_reached(line, snapshot))
                    for line in target_lines
                },
                target_line_rates={
                    line.name: calculate_rate(sum(1 for snapshot in items if _line_reached(line, snapshot)), len(items))
                    for line in target_lines
                },
            )
        )
    class_breakdown.sort(key=lambda item: item.average_score, reverse=True)

    subject_snapshots = [
        item
        for item in get_subject_snapshots_for_exam(session, exam_id)
        if item.student and _snapshot_matches_grade(item, exam, grade_id, context_map) and item.score is not None
    ]
    grouped_subjects: dict[int, list] = defaultdict(list)
    for item in subject_snapshots:
        grouped_subjects[item.subject_id].append(item)
    subject_breakdown: list[GradeSubjectAnalyticsItem] = []
    for subject_id, items in grouped_subjects.items():
        scores = [item.score for item in items if item.score is not None]
        average_score = safe_mean(scores)
        contribution_rate = None
        if total_scores and average_score and safe_mean(total_scores) > 0:
            contribution_rate = round((average_score / safe_mean(total_scores)) * 100, 2)
        subject_breakdown.append(
            GradeSubjectAnalyticsItem(
                subject_id=subject_id,
                subject_name=items[0].subject.name if items[0].subject else str(subject_id),
                valid_count=len(scores),
                average_score=average_score,
                excellent_rate=calculate_rate(sum(1 for item in items if item.excellent_flag), len(scores)),
                pass_rate=calculate_rate(sum(1 for item in items if item.pass_flag), len(scores)),
                contribution_rate=contribution_rate,
            )
        )
    subject_breakdown.sort(key=lambda item: item.average_score, reverse=True)

    excellent_rate = (
        calculate_rate(sum(1 for item in total_snapshots if item.total_score >= excellent_total_line), len(total_snapshots))
        if excellent_total_line is not None
        else None
    )
    target_line_summaries = _build_target_line_summaries(target_lines, total_snapshots)
    critical_students = _build_critical_students(target_lines, total_snapshots, context_map)
    class_contributions = _build_class_contributions(class_group, subject_snapshots, target_lines, context_map)
    rank_audit_summary = _build_rank_audit_summary(session, exam, len(total_snapshots), context_map)

    return GradeAnalyticsResponse(
        exam_id=exam.id,
        exam_name=exam.name,
        grade_id=grade.id,
        grade_name=grade.name,
        student_count=len(total_snapshots),
        total_average=safe_mean(total_scores),
        total_median=safe_median(total_scores),
        total_max=max(total_scores) if total_scores else 0.0,
        total_min=min(total_scores) if total_scores else 0.0,
        total_standard_deviation=safe_stddev(total_scores),
        excellent_rate=excellent_rate,
        class_breakdown=class_breakdown,
        subject_breakdown=subject_breakdown,
        score_bands=_build_score_bands(total_scores, total_full_score),
        rank_bands=_build_rank_bands(total_snapshots),
        target_line_summaries=target_line_summaries,
        critical_students=critical_students,
        class_contributions=class_contributions,
        rank_audit_summary=rank_audit_summary,
    )


def _resolve_total_excellent_line(exam: Exam) -> float | None:
    in_total_subjects = [item for item in exam.subjects if item.is_active and item.is_in_total]
    if not in_total_subjects:
        return None
    if any(item.excellent_line is None for item in in_total_subjects):
        return None
    return sum(float(item.excellent_line or 0) for item in in_total_subjects)


def _build_score_bands(total_scores: list[float], total_full_score: float) -> list[GradeDistributionItem]:
    if not total_scores or total_full_score <= 0:
        return []
    counters = {
        "90%以上": 0,
        "80%-89%": 0,
        "70%-79%": 0,
        "70%以下": 0,
    }
    for score in total_scores:
        ratio = score / total_full_score
        if ratio >= 0.9:
            counters["90%以上"] += 1
        elif ratio >= 0.8:
            counters["80%-89%"] += 1
        elif ratio >= 0.7:
            counters["70%-79%"] += 1
        else:
            counters["70%以下"] += 1
    return [GradeDistributionItem(label=label, count=count) for label, count in counters.items()]


def _build_rank_bands(total_snapshots) -> list[GradeDistributionItem]:
    counters = {
        "前10名": 0,
        "11-30名": 0,
        "31-50名": 0,
        "50名后": 0,
    }
    for item in total_snapshots:
        if item.grade_rank is None:
            continue
        if item.grade_rank <= 10:
            counters["前10名"] += 1
        elif item.grade_rank <= 30:
            counters["11-30名"] += 1
        elif item.grade_rank <= 50:
            counters["31-50名"] += 1
        else:
            counters["50名后"] += 1
    return [GradeDistributionItem(label=label, count=count) for label, count in counters.items()]


def _snapshot_effective_class_id(snapshot, context_map: dict) -> int | None:
    return effective_class_id(snapshot.student, context_map.get(snapshot.student_id))


def _snapshot_effective_class_name(snapshot, context_map: dict) -> str | None:
    return effective_class_name(snapshot.student, context_map.get(snapshot.student_id))


def _snapshot_matches_grade(snapshot, exam: Exam | None, grade_id: int, context_map: dict) -> bool:
    if exam:
        scope = exam.grade_scope_json or []
        if scope and len(scope) == 1 and scope[0] == grade_id:
            return True
    context = context_map.get(snapshot.student_id)
    if context and context.mapped_class:
        return context.mapped_class.grade_id == grade_id
    return bool(snapshot.student and snapshot.student.current_grade_id == grade_id)


def _build_target_line_summaries(target_lines: list[ScoreTargetLine], total_snapshots) -> list[GradeTargetLineSummary]:
    summaries: list[GradeTargetLineSummary] = []
    for line in target_lines:
        reached = [item for item in total_snapshots if _line_reached(line, item)]
        near_below = [item for item in total_snapshots if _line_near_below(line, item)]
        near_above = [item for item in total_snapshots if _line_near_above(line, item)]
        summaries.append(
            GradeTargetLineSummary(
                line_id=line.id,
                line_name=line.name,
                line_type=line.line_type,
                threshold_label=_line_threshold_label(line),
                reached_count=len(reached),
                reached_rate=calculate_rate(len(reached), len(total_snapshots)),
                near_below_count=len(near_below),
                near_above_count=len(near_above),
            )
        )
    return summaries


def _build_critical_students(target_lines: list[ScoreTargetLine], total_snapshots, context_map: dict) -> list[GradeCriticalStudentItem]:
    rows: list[GradeCriticalStudentItem] = []
    for line in target_lines:
        for snapshot in total_snapshots:
            status = None
            gap_label = ""
            if _line_near_below(line, snapshot):
                status = "near_below"
                gap_label = _line_gap_label(line, snapshot, below=True)
            elif _line_near_above(line, snapshot):
                status = "near_above"
                gap_label = _line_gap_label(line, snapshot, below=False)
            if status is None or not snapshot.student:
                continue
            rows.append(
                GradeCriticalStudentItem(
                    student_id=snapshot.student_id,
                    student_no=snapshot.student.student_no,
                    student_name=snapshot.student.name,
                    class_id=_snapshot_effective_class_id(snapshot, context_map),
                    class_name=_snapshot_effective_class_name(snapshot, context_map),
                    total_score=snapshot.total_score,
                    school_rank=snapshot.grade_rank,
                    line_name=line.name,
                    status=status,
                    gap_label=gap_label,
                )
            )
    rows.sort(key=lambda item: (item.line_name, item.status, abs(float(item.gap_label.split()[0])) if item.gap_label.split() and item.gap_label.split()[0].replace(".", "", 1).lstrip("-").isdigit() else 9999))
    return rows[:80]


def _build_class_contributions(class_group: dict[int | None, list], subject_snapshots, target_lines: list[ScoreTargetLine], context_map: dict) -> list[GradeClassContributionItem]:
    subjects_by_class: dict[int | None, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for item in subject_snapshots:
        if item.score is None:
            continue
        class_id = _snapshot_effective_class_id(item, context_map)
        subject_name = item.subject.name if item.subject else str(item.subject_id)
        subjects_by_class[class_id][subject_name].append(item.score)

    rows: list[GradeClassContributionItem] = []
    for class_id, items in class_group.items():
        scores = [item.total_score for item in items]
        target_line_counts = {
            line.name: sum(1 for item in items if _line_reached(line, item))
            for line in target_lines
        }
        subject_averages = {
            subject_name: safe_mean(values)
            for subject_name, values in subjects_by_class.get(class_id, {}).items()
            if values
        }
        strongest = max(subject_averages.items(), key=lambda item: item[1])[0] if subject_averages else None
        weakest = min(subject_averages.items(), key=lambda item: item[1])[0] if subject_averages else None
        rows.append(
            GradeClassContributionItem(
                class_id=class_id,
                class_name=_snapshot_effective_class_name(items[0], context_map) or "未分班",
                student_count=len(items),
                average_score=safe_mean(scores),
                top30_count=sum(1 for item in items if item.grade_rank is not None and item.grade_rank <= 30),
                target_line_counts=target_line_counts,
                strongest_subject=strongest,
                weakest_subject=weakest,
            )
        )
    rows.sort(key=lambda item: item.average_score, reverse=True)
    return rows


def _build_rank_audit_summary(session: Session, exam: Exam, snapshot_count: int, context_map: dict) -> GradeRankAuditSummary:
    context_count = len(context_map)
    mapped_count = sum(1 for item in context_map.values() if item.mapped_class_id is not None)
    diff_count = 0
    snapshot_map = {
        item.student_id: item
        for item in get_total_snapshots_for_exam(session, exam.id)
    }
    for context in context_map.values():
        snapshot = snapshot_map.get(context.student_id)
        if snapshot is None:
            continue
        source_school_rank = context.source_school_rank or context.source_grade_rank
        class_diff = (
            snapshot.class_rank != context.source_class_rank
            if snapshot.class_rank is not None and context.source_class_rank is not None
            else False
        )
        school_diff = (
            snapshot.grade_rank != source_school_rank
            if snapshot.grade_rank is not None and source_school_rank is not None
            else False
        )
        if class_diff or school_diff:
            diff_count += 1
    warnings: list[str] = []
    if context_count and mapped_count < context_count:
        warnings.append(f"{context_count - mapped_count} 名学生缺少考试时点班级映射。")
    if snapshot_count != context_count:
        warnings.append("总分快照样本数与考试时点归属样本数不一致。")
    if diff_count:
        warnings.append(f"{diff_count} 名学生的平台原始名次与系统重算名次不同。")
    return GradeRankAuditSummary(
        mapping_rate=round(mapped_count / context_count, 4) if context_count else 0.0,
        unmapped_context_count=context_count - mapped_count,
        rank_diff_count=diff_count,
        warnings=warnings,
    )


def _line_threshold_label(line: ScoreTargetLine) -> str:
    if line.line_type == "rank":
        return f"前 {line.rank_value} 名"
    return f"{line.score_value} 分"


def _line_reached(line: ScoreTargetLine, snapshot) -> bool:
    if line.line_type == "rank":
        return snapshot.grade_rank is not None and line.rank_value is not None and snapshot.grade_rank <= line.rank_value
    return line.score_value is not None and snapshot.total_score >= line.score_value


def _line_near_below(line: ScoreTargetLine, snapshot) -> bool:
    if _line_reached(line, snapshot):
        return False
    if line.line_type == "rank":
        margin = line.near_margin_rank if line.near_margin_rank is not None else 20
        return snapshot.grade_rank is not None and line.rank_value is not None and line.rank_value < snapshot.grade_rank <= line.rank_value + margin
    margin = line.near_margin_score if line.near_margin_score is not None else 10
    return line.score_value is not None and line.score_value - margin <= snapshot.total_score < line.score_value


def _line_near_above(line: ScoreTargetLine, snapshot) -> bool:
    if not _line_reached(line, snapshot):
        return False
    if line.line_type == "rank":
        margin = line.near_margin_rank if line.near_margin_rank is not None else 10
        return snapshot.grade_rank is not None and line.rank_value is not None and max(1, line.rank_value - margin) <= snapshot.grade_rank <= line.rank_value
    margin = line.near_margin_score if line.near_margin_score is not None else 5
    return line.score_value is not None and line.score_value <= snapshot.total_score <= line.score_value + margin


def _line_gap_label(line: ScoreTargetLine, snapshot, *, below: bool) -> str:
    if line.line_type == "rank" and snapshot.grade_rank is not None and line.rank_value is not None:
        gap = snapshot.grade_rank - line.rank_value
        return f"{gap} 名"
    if line.score_value is not None:
        gap = round(snapshot.total_score - line.score_value, 2)
        return f"{gap} 分"
    return "暂无"


def _filter_grade_total_snapshots(total_snapshots, exam: Exam, grade_id: int, context_map=None):
    scope = exam.grade_scope_json or []
    if scope and len(scope) == 1 and scope[0] == grade_id:
        return [item for item in total_snapshots if item.student_id is not None]
    return [
        item
        for item in total_snapshots
        if item.student and _snapshot_matches_grade(item, exam, grade_id, context_map or {})
    ]


def _filter_grade_subject_snapshots(subject_snapshots, exam: Exam | None, grade_id: int, context_map=None):
    scope = exam.grade_scope_json if exam else []
    if scope and len(scope) == 1 and scope[0] == grade_id:
        return [item for item in subject_snapshots if item.score is not None]
    return [
        item
        for item in subject_snapshots
        if item.student and _snapshot_matches_grade(item, exam, grade_id, context_map or {}) and item.score is not None
    ]


def _filter_class_total_snapshots(total_snapshots, exam: Exam, class_id: int, context_map=None):
    return [
        item
        for item in total_snapshots
        if item.student and _snapshot_effective_class_id(item, context_map or {}) == class_id
    ]


def _filter_class_subject_snapshots(subject_snapshots, exam: Exam | None, class_id: int, context_map=None):
    return [
        item
        for item in subject_snapshots
        if item.student and _snapshot_effective_class_id(item, context_map or {}) == class_id and item.score is not None
    ]


def _exam_matches_grade_scope(exam: Exam, grade_id: int) -> bool:
    scope = exam.grade_scope_json or []
    return not scope or grade_id in scope
