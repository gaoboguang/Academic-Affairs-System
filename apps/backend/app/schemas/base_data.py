from __future__ import annotations

from datetime import date

from pydantic import BaseModel

from app.schemas.common import ORMModel


class AcademicYearPayload(BaseModel):
    name: str
    start_date: date
    end_date: date
    is_current: bool = False
    is_active: bool = True


class AcademicYearRead(ORMModel):
    id: int
    name: str
    start_date: date
    end_date: date
    is_current: bool
    is_active: bool


class SemesterPayload(BaseModel):
    academic_year_id: int
    name: str
    start_date: date
    end_date: date
    week_count: int = 20
    is_current: bool = False
    is_active: bool = True


class SemesterRead(ORMModel):
    id: int
    academic_year_id: int
    academic_year_name: str | None = None
    name: str
    start_date: date
    end_date: date
    week_count: int
    is_current: bool
    is_active: bool


class GradePayload(BaseModel):
    name: str
    sort_order: int = 0
    is_active: bool = True


class GradeRead(ORMModel):
    id: int
    name: str
    sort_order: int
    is_active: bool


class ClassPayload(BaseModel):
    grade_id: int
    name: str
    class_type: str | None = None
    head_teacher_id: int | None = None
    student_count: int = 0
    is_active: bool = True


class ClassRead(ORMModel):
    id: int
    grade_id: int
    grade_name: str | None = None
    name: str
    class_type: str | None = None
    head_teacher_id: int | None = None
    head_teacher_name: str | None = None
    student_count: int
    is_active: bool


class SubjectPayload(BaseModel):
    code: str
    name: str
    category: str = "academic"
    sort_order: int = 0
    is_in_total_default: bool = True
    is_active: bool = True


class SubjectRead(ORMModel):
    id: int
    code: str
    name: str
    category: str
    sort_order: int
    is_in_total_default: bool
    is_active: bool


class DictTypePayload(BaseModel):
    code: str
    name: str
    is_active: bool = True


class DictTypeRead(ORMModel):
    id: int
    code: str
    name: str
    is_active: bool


class DictItemPayload(BaseModel):
    code: str
    name: str
    sort_order: int = 0
    is_active: bool = True


class DictItemRead(ORMModel):
    id: int
    dict_type_id: int
    code: str
    name: str
    sort_order: int
    is_active: bool


class ConfigItemRead(ORMModel):
    id: int
    config_group: str
    config_key: str
    config_value: str
    value_type: str
    description: str | None = None

