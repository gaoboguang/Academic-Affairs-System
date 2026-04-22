from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.schemas.common import ORMModel


class ReportExportPayload(BaseModel):
    report_type: str
    exam_id: int | None = None
    student_id: int | None = None
    batch_id: int | None = None
    class_id: int | None = None
    grade_id: int | None = None
    teacher_id: int | None = None
    semester_id: int | None = None
    rule_version_id: int | None = None
    scheme_id: int | None = None
    draft_id: int | None = None


class ReportExportRecordRead(ORMModel):
    id: int
    report_type: str
    report_name: str
    params_json: dict | None = None
    file_path: str
    exported_at: datetime
    status: str
    download_url: str | None = None
