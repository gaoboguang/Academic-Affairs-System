from __future__ import annotations

from collections import defaultdict

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.analytics.scores import calculate_rate, safe_mean, safe_median, safe_stddev
from app.models import Exam, Grade, SchoolClass, ScoreRecord, Subject, Teacher, TeachingAssignment
from app.repositories.exams import (
    get_exam,
    get_previous_trend_exam,
    get_score_records_for_exam,
    get_subject_snapshots_for_exam,
    get_total_snapshots_for_exam,
)
from app.schemas.exam import (
    ClassAnalyticsResponse,
    GradeAnalyticsResponse,
    GradeClassAnalyticsItem,
    GradeDistributionItem,
    GradeSubjectAnalyticsItem,
    StudentAnalyticsResponse,
    StudentSubjectAnalytics,
    SubjectAggregateItem,
    TeacherAnalyticsResponse,
    TeacherAssignmentAnalytics,
)


def get_student_analytics(session: Session, student_id: int, exam_id: int) -> StudentAnalyticsResponse:
    exam = get_exam(session, exam_id)
    if not exam:
        raise HTTPException(status_code=404, detail="考试不存在")

    total_snapshot = next(
        (item for item in get_total_snapshots_for_exam(session, exam_id) if item.student_id == student_id),
        None,
    )
    subject_snapshots = [
        item for item in get_subject_snapshots_for_exam(session, exam_id) if item.student_id == student_id
    ]
    if not total_snapshot and not subject_snapshots:
        raise HTTPException(status_code=404, detail="该学生暂无本次考试分析数据")

    previous_exam = get_previous_trend_exam(session, exam)
    previous_total = None
    previous_subject_map: dict[int, object] = {}
    if previous_exam:
        previous_total = next(
            (item for item in get_total_snapshots_for_exam(session, previous_exam.id) if item.student_id == student_id),
            None,
        )
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
    subjects = []
    for item in sorted(subject_snapshots, key=lambda current: current.subject_id):
        previous_item = previous_subject_map.get(item.subject_id)
        score_delta = None
        rank_delta = None
        if previous_item and previous_item.score is not None and item.score is not None:
            score_delta = round(item.score - previous_item.score, 2)
        if previous_item and previous_item.grade_rank is not None and item.grade_rank is not None:
            rank_delta = previous_item.grade_rank - item.grade_rank
        subjects.append(
            StudentSubjectAnalytics(
                subject_id=item.subject_id,
                subject_name=item.subject.name if item.subject else str(item.subject_id),
                score=item.score,
                score_status="normal" if item.score is not None else "absent",
                class_rank=item.class_rank,
                grade_rank=item.grade_rank,
                class_percentile=item.class_percentile,
                grade_percentile=item.grade_percentile,
                excellent_flag=item.excellent_flag,
                pass_flag=item.pass_flag,
                score_delta=score_delta,
                rank_delta=rank_delta,
            )
        )

    return StudentAnalyticsResponse(
        exam_id=exam.id,
        exam_name=exam.name,
        student_id=student_id,
        student_name=student_name,
        total_score=total_snapshot.total_score if total_snapshot else 0.0,
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
        subjects=subjects,
    )


def get_class_analytics(session: Session, class_id: int, exam_id: int) -> ClassAnalyticsResponse:
    exam = get_exam(session, exam_id)
    school_class = session.get(SchoolClass, class_id)
    if not exam:
        raise HTTPException(status_code=404, detail="考试不存在")
    if not school_class:
        raise HTTPException(status_code=404, detail="班级不存在")

    total_snapshots = [
        item
        for item in get_total_snapshots_for_exam(session, exam_id)
        if item.student and item.student.current_class_id == class_id
    ]
    if not total_snapshots:
        raise HTTPException(status_code=404, detail="该班级暂无本次考试总分数据")

    total_scores = [item.total_score for item in total_snapshots]
    grade_id = school_class.grade_id
    grade_total_scores = [
        item.total_score
        for item in get_total_snapshots_for_exam(session, exam_id)
        if item.student and item.student.current_grade_id == grade_id
    ]

    subject_snapshots = [
        item
        for item in get_subject_snapshots_for_exam(session, exam_id)
        if item.student and item.student.current_class_id == class_id and item.score is not None
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

    score_records = [
        item for item in get_score_records_for_exam(session, exam_id) if item.score is not None
    ]
    subject_meta_map = {item.subject_id: item for item in exam.subjects}
    assignment_breakdown: list[TeacherAssignmentAnalytics] = []
    overall_scores: list[float] = []

    for assignment in assignments:
        matched = [
            record
            for record in score_records
            if record.student
            and record.student.current_class_id == assignment.class_id
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


def get_grade_analytics(session: Session, grade_id: int, exam_id: int) -> GradeAnalyticsResponse:
    exam = get_exam(session, exam_id)
    grade = session.get(Grade, grade_id)
    if not exam:
        raise HTTPException(status_code=404, detail="考试不存在")
    if not grade:
        raise HTTPException(status_code=404, detail="年级不存在")

    total_snapshots = [
        item
        for item in get_total_snapshots_for_exam(session, exam_id)
        if item.student and item.student.current_grade_id == grade_id
    ]
    if not total_snapshots:
        raise HTTPException(status_code=404, detail="该年级暂无本次考试总分数据")

    total_scores = [item.total_score for item in total_snapshots]
    total_full_score = sum(item.full_score for item in exam.subjects if item.is_active and item.is_in_total)
    excellent_total_line = _resolve_total_excellent_line(exam)

    class_group: dict[int | None, list] = defaultdict(list)
    for item in total_snapshots:
        class_group[item.student.current_class_id if item.student else None].append(item)

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
                    items[0].student.current_class.name
                    if items[0].student and items[0].student.current_class
                    else "未分班"
                ),
                student_count=len(items),
                average_score=safe_mean(scores),
                median_score=safe_median(scores),
                max_score=max(scores) if scores else 0.0,
                min_score=min(scores) if scores else 0.0,
                excellent_rate=excellent_rate,
            )
        )
    class_breakdown.sort(key=lambda item: item.average_score, reverse=True)

    subject_snapshots = [
        item
        for item in get_subject_snapshots_for_exam(session, exam_id)
        if item.student and item.student.current_grade_id == grade_id and item.score is not None
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
