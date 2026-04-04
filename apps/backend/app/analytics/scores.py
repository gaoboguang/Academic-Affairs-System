from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
import math
from statistics import median

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, joinedload

from app.models import Exam, ExamSubject, ScoreRecord, ScoreSubjectSnapshot, ScoreTotalSnapshot, Student


VALID_SCORE_STATUS = {"normal"}


@dataclass(frozen=True)
class RankedValue:
    key: int
    score: float


def assign_ranks(values: list[RankedValue], rank_mode: str = "competition") -> dict[int, int]:
    ordered = sorted(values, key=lambda item: (-item.score, item.key))
    ranks: dict[int, int] = {}
    previous_score: float | None = None
    previous_rank = 0

    for index, item in enumerate(ordered, start=1):
        if previous_score is None or item.score != previous_score:
            if rank_mode == "dense":
                previous_rank = previous_rank + 1 if previous_score is not None else 1
            else:
                previous_rank = index
            previous_score = item.score
        ranks[item.key] = previous_rank
    return ranks


def calculate_percentile(rank: int, total_count: int) -> float:
    if total_count <= 0:
        return 0.0
    return round(1 - (rank - 1) / total_count, 4)


def safe_mean(values: list[float]) -> float:
    return round(sum(values) / len(values), 2) if values else 0.0


def safe_median(values: list[float]) -> float:
    return round(float(median(values)), 2) if values else 0.0


def safe_stddev(values: list[float]) -> float:
    if not values:
        return 0.0
    avg = sum(values) / len(values)
    variance = sum((value - avg) ** 2 for value in values) / len(values)
    return round(math.sqrt(variance), 2)


def calculate_rate(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round(numerator / denominator, 4)


def rebuild_exam_snapshots(session: Session, exam: Exam, rank_mode: str) -> None:
    session.execute(delete(ScoreSubjectSnapshot).where(ScoreSubjectSnapshot.exam_id == exam.id))
    session.execute(delete(ScoreTotalSnapshot).where(ScoreTotalSnapshot.exam_id == exam.id))
    session.flush()

    exam_subjects = {
        item.subject_id: item
        for item in session.scalars(
            select(ExamSubject).where(ExamSubject.exam_id == exam.id, ExamSubject.is_active.is_(True))
        ).all()
    }
    score_records = session.scalars(
        select(ScoreRecord)
        .where(ScoreRecord.exam_id == exam.id, ScoreRecord.is_active.is_(True))
        .options(
            joinedload(ScoreRecord.student).joinedload(Student.current_class),
            joinedload(ScoreRecord.student).joinedload(Student.current_grade),
        )
    ).all()

    subject_group_all: dict[int, list[RankedValue]] = defaultdict(list)
    subject_group_by_class: dict[tuple[int, int], list[RankedValue]] = defaultdict(list)
    student_total_map: dict[int, float] = defaultdict(float)
    total_group_all: list[RankedValue] = []
    total_group_by_class: dict[int, list[RankedValue]] = defaultdict(list)
    student_group_cache: dict[int, tuple[int | None, int | None]] = {}

    # Gather subject ranking inputs.
    for record in score_records:
        student = record.student
        if student is None:
            continue
        class_id = student.current_class_id
        grade_id = student.current_grade_id
        student_group_cache[student.id] = (class_id, grade_id)
        if record.score_status in VALID_SCORE_STATUS and record.score is not None:
            subject_group_all[record.subject_id].append(RankedValue(record.student_id, record.score))
            if class_id is not None:
                subject_group_by_class[(record.subject_id, class_id)].append(
                    RankedValue(record.student_id, record.score)
                )
        exam_subject = exam_subjects.get(record.subject_id)
        if (
            exam_subject
            and exam_subject.is_in_total
            and record.score_status in VALID_SCORE_STATUS
            and record.score is not None
        ):
            student_total_map[record.student_id] += record.score

    for student_id, total_score in student_total_map.items():
        class_id, _grade_id = student_group_cache.get(student_id, (None, None))
        total_group_all.append(RankedValue(student_id, total_score))
        if class_id is not None:
            total_group_by_class[class_id].append(RankedValue(student_id, total_score))

    subject_ranks_all = {
        subject_id: assign_ranks(values, rank_mode)
        for subject_id, values in subject_group_all.items()
    }
    subject_ranks_by_class = {
        key: assign_ranks(values, rank_mode)
        for key, values in subject_group_by_class.items()
    }
    total_ranks_all = assign_ranks(total_group_all, rank_mode)
    total_ranks_by_class = {
        class_id: assign_ranks(values, rank_mode)
        for class_id, values in total_group_by_class.items()
    }

    # Subject snapshots keep all imported records, but only valid scores get ranks.
    for record in score_records:
        student = record.student
        if student is None:
            continue
        class_id = student.current_class_id
        subject_meta = exam_subjects.get(record.subject_id)
        excellent_flag = False
        pass_flag = False
        class_rank = None
        grade_rank = None
        class_percentile = None
        grade_percentile = None
        if record.score_status in VALID_SCORE_STATUS and record.score is not None:
            if subject_meta and subject_meta.excellent_line is not None:
                excellent_flag = record.score >= subject_meta.excellent_line
            if subject_meta and subject_meta.pass_line is not None:
                pass_flag = record.score >= subject_meta.pass_line
            class_rank = (
                subject_ranks_by_class.get((record.subject_id, class_id), {}).get(record.student_id)
                if class_id is not None
                else None
            )
            grade_rank = subject_ranks_all.get(record.subject_id, {}).get(record.student_id)
            if class_rank is not None and class_id is not None:
                class_percentile = calculate_percentile(
                    class_rank,
                    len(subject_group_by_class.get((record.subject_id, class_id), [])),
                )
            if grade_rank is not None:
                grade_percentile = calculate_percentile(
                    grade_rank,
                    len(subject_group_all.get(record.subject_id, [])),
                )
        session.add(
            ScoreSubjectSnapshot(
                exam_id=exam.id,
                student_id=record.student_id,
                subject_id=record.subject_id,
                score=record.score,
                class_rank=class_rank,
                grade_rank=grade_rank,
                class_percentile=class_percentile,
                grade_percentile=grade_percentile,
                excellent_flag=excellent_flag,
                pass_flag=pass_flag,
            )
        )

    # Total snapshots only for students with at least one valid total score.
    for student_id, total_score in student_total_map.items():
        class_id, _grade_id = student_group_cache.get(student_id, (None, None))
        class_rank = (
            total_ranks_by_class.get(class_id, {}).get(student_id) if class_id is not None else None
        )
        grade_rank = total_ranks_all.get(student_id)
        class_percentile = (
            calculate_percentile(class_rank, len(total_group_by_class.get(class_id, [])))
            if class_id is not None and class_rank is not None
            else None
        )
        grade_percentile = (
            calculate_percentile(grade_rank, len(total_group_all)) if grade_rank is not None else None
        )
        session.add(
            ScoreTotalSnapshot(
                exam_id=exam.id,
                student_id=student_id,
                total_score=round(total_score, 2),
                class_rank=class_rank,
                grade_rank=grade_rank,
                class_percentile=class_percentile,
                grade_percentile=grade_percentile,
                rank_mode=rank_mode,
                rebuilt_at=datetime.now(),
            )
        )

    session.flush()
