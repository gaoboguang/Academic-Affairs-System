from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from app.analytics.workload import (
    RuleLookup,
    coefficient_for_entry,
    extra_amount,
    monthly_hours_from_weeks,
    parse_active_weeks,
)
from app.models import Semester, Teacher, TeacherWorkloadExtra, TimetableBatch, TimetableEntry


@dataclass
class TeacherWorkloadComputation:
    weekly_hours: float
    monthly_hours_json: dict[str, float]
    semester_hours: float
    semester_workload: float
    snapshot_json: dict[str, object]


def build_teacher_workload_computation(
    *,
    teacher: Teacher,
    teacher_entries: list[TimetableEntry],
    extras: list[TeacherWorkloadExtra],
    lookup: RuleLookup,
    semester: Semester,
    batch: TimetableBatch,
) -> TeacherWorkloadComputation:
    weekly_hours = 0.0
    semester_hours = 0.0
    semester_workload = 0.0
    monthly_hours: dict[str, float] = defaultdict(float)
    detail_rows: list[dict[str, object]] = []

    for entry in teacher_entries:
        active_weeks = parse_active_weeks(entry, semester.week_count)
        average_weekly = len(active_weeks) / semester.week_count
        semester_periods = float(len(active_weeks))
        coefficient, breakdown = coefficient_for_entry(entry, lookup)

        weekly_hours += average_weekly
        semester_hours += semester_periods
        contribution = round(semester_periods * coefficient, 2)
        semester_workload += contribution
        for month, hours in monthly_hours_from_weeks(active_weeks, 1.0, semester.start_date).items():
            monthly_hours[month] += hours
        detail_rows.append(
            {
                "weekday": entry.weekday,
                "period_no": entry.period_no,
                "class_name": entry.school_class.name if entry.school_class else None,
                "subject_name": entry.subject.name if entry.subject else None,
                "course_type": entry.course_type,
                "active_week_count": len(active_weeks),
                "coefficient": coefficient,
                "coefficient_breakdown": breakdown,
                "semester_contribution": contribution,
            }
        )

    fixed_head_teacher = 0.0
    if teacher.is_head_teacher:
        fixed_head_teacher = lookup.fixed_map.get(("head_teacher", "true"), 0.0)
        semester_workload += fixed_head_teacher

    extra_rows: list[dict[str, object]] = []
    for extra in extras:
        amount = extra_amount(extra)
        semester_workload += amount
        extra_rows.append(
            {
                "item_name": extra.item_name,
                "quantity": extra.quantity,
                "coefficient": extra.coefficient,
                "amount": amount,
            }
        )

    return TeacherWorkloadComputation(
        weekly_hours=round(weekly_hours, 2),
        monthly_hours_json={month: round(value, 2) for month, value in sorted(monthly_hours.items())},
        semester_hours=round(semester_hours, 2),
        semester_workload=round(semester_workload, 2),
        snapshot_json={
            "batch_id": batch.id,
            "batch_filename": batch.source_filename,
            "entry_count": len(teacher_entries),
            "head_teacher_bonus": fixed_head_teacher,
            "details": detail_rows,
            "extras": extra_rows,
        },
    )
