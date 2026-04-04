from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import timedelta
import math

from app.models import SchoolClass, TeacherWorkloadExtra, TimetableEntry, WorkloadRuleItem, WorkloadRuleVersion


@dataclass(frozen=True)
class RuleLookup:
    coefficient_map: dict[tuple[str, str], float]
    fixed_map: dict[tuple[str, str], float]


def build_rule_lookup(items: list[WorkloadRuleItem]) -> RuleLookup:
    coefficient_map: dict[tuple[str, str], float] = {}
    fixed_map: dict[tuple[str, str], float] = {}
    for item in items:
        if item.coefficient is not None:
            coefficient_map[(item.dimension_type, item.match_key)] = item.coefficient
        if item.fixed_value is not None:
            fixed_map[(item.dimension_type, item.match_key)] = item.fixed_value
    return RuleLookup(coefficient_map=coefficient_map, fixed_map=fixed_map)


def parse_active_weeks(entry: TimetableEntry, week_count: int) -> list[int]:
    if entry.week_rule == "odd":
        return [week for week in range(1, week_count + 1) if week % 2 == 1]
    if entry.week_rule == "even":
        return [week for week in range(1, week_count + 1) if week % 2 == 0]
    if entry.week_rule == "custom" and entry.week_list_json:
        return [week for week in entry.week_list_json if 1 <= week <= week_count]
    return list(range(1, week_count + 1))


def class_size_bucket(student_count: int) -> str:
    if student_count <= 35:
        return "0-35"
    if student_count <= 45:
        return "36-45"
    return "46+"


def coefficient_for_entry(entry: TimetableEntry, lookup: RuleLookup) -> tuple[float, dict[str, float]]:
    subject_key = entry.subject.code if entry.subject else ""
    grade_key = entry.school_class.grade.name if entry.school_class and entry.school_class.grade else ""
    class_type_key = entry.school_class.class_type if entry.school_class else ""
    course_type_key = entry.course_type or ""
    class_size_key = class_size_bucket(entry.school_class.student_count if entry.school_class else 0)
    breakdown = {
        "subject": lookup.coefficient_map.get(("subject", subject_key), 1.0),
        "grade": lookup.coefficient_map.get(("grade", grade_key), 1.0),
        "class_type": lookup.coefficient_map.get(("class_type", class_type_key), 1.0),
        "course_type": lookup.coefficient_map.get(("course_type", course_type_key), 1.0),
        "class_size": lookup.coefficient_map.get(("class_size", class_size_key), 1.0),
    }
    product = 1.0
    for value in breakdown.values():
        product *= value
    return round(product, 6), breakdown


def monthly_hours_from_weeks(active_weeks: list[int], weekly_hours: float, semester_start_date) -> dict[str, float]:
    monthly_counter: Counter[str] = Counter()
    for week in active_weeks:
        target_date = semester_start_date + timedelta(days=(week - 1) * 7)
        key = f"{target_date.year}-{target_date.month:02d}"
        monthly_counter[key] += weekly_hours
    return {month: round(value, 2) for month, value in sorted(monthly_counter.items())}


def extra_amount(extra: TeacherWorkloadExtra) -> float:
    if extra.amount is not None:
        return round(extra.amount, 2)
    return round(extra.quantity * extra.coefficient, 2)

