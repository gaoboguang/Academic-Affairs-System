from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.schemas.common import ImportResult, ORMModel


class TimetableBatchRead(ORMModel):
    id: int
    semester_id: int
    semester_name: str | None = None
    source_filename: str | None = None
    import_time: datetime
    status: str
    remark: str | None = None
    entry_count: int = 0
    unresolved_count: int = 0
    is_active: bool


class TimetableEntryUpdatePayload(BaseModel):
    teacher_id: int | None = None
    class_id: int | None = None
    subject_id: int | None = None
    course_type: str | None = None
    note: str | None = None
    is_active: bool = True


class TimetableEntryRead(ORMModel):
    id: int
    batch_id: int
    semester_id: int
    weekday: int
    period_no: int
    teacher_id: int | None = None
    teacher_name: str | None = None
    class_id: int | None = None
    class_name: str | None = None
    subject_id: int | None = None
    subject_name: str | None = None
    course_type: str | None = None
    week_rule: str
    week_list_json: list[int] | None = None
    note: str | None = None
    mapping_status: str
    raw_teacher_name: str | None = None
    raw_class_name: str | None = None
    raw_subject_name: str | None = None
    raw_course_type: str | None = None
    is_active: bool


class TimetableImportResponse(ImportResult):
    batch_id: int
    unresolved_rows: int = 0


class WorkloadRuleVersionPayload(BaseModel):
    name: str
    semester_id: int | None = None
    is_default: bool = False
    status: str = "active"
    note: str | None = None
    is_active: bool = True


class WorkloadRuleVersionRead(ORMModel):
    id: int
    name: str
    semester_id: int | None = None
    semester_name: str | None = None
    is_default: bool
    status: str
    note: str | None = None
    is_active: bool


class WorkloadRuleItemPayload(BaseModel):
    dimension_type: str
    match_key: str
    coefficient: float | None = None
    fixed_value: float | None = None
    note: str | None = None
    is_active: bool = True


class WorkloadRuleItemRead(ORMModel):
    id: int
    rule_version_id: int
    dimension_type: str
    match_key: str
    coefficient: float | None = None
    fixed_value: float | None = None
    note: str | None = None
    is_active: bool


class TeacherWorkloadExtraPayload(BaseModel):
    teacher_id: int
    semester_id: int
    item_name: str
    quantity: float = 0
    coefficient: float = 1
    amount: float | None = None
    note: str | None = None
    is_active: bool = True


class TeacherWorkloadExtraRead(ORMModel):
    id: int
    teacher_id: int
    teacher_name: str | None = None
    semester_id: int
    item_name: str
    quantity: float
    coefficient: float
    amount: float | None = None
    note: str | None = None
    is_active: bool


class WorkloadCalculatePayload(BaseModel):
    semester_id: int
    rule_version_id: int
    batch_id: int | None = None


class TeacherWorkloadResultRead(ORMModel):
    id: int
    teacher_id: int
    teacher_name: str | None = None
    semester_id: int
    semester_name: str | None = None
    rule_version_id: int
    rule_version_name: str | None = None
    weekly_hours: float
    monthly_hours_json: dict | None = None
    semester_hours: float
    semester_workload: float
    snapshot_json: dict | None = None
    calculated_at: datetime
    is_active: bool


class WorkloadCalculateResponse(BaseModel):
    message: str
    result_count: int
