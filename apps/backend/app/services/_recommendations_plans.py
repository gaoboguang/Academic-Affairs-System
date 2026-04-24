from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.importers.enrollment_plans import EnrollmentPlanImporter
from app.repositories.recommendations import list_enrollment_plans as repo_list_enrollment_plans
from app.repositories.system import create_import_job, write_audit_log
from app.schemas.recommendation import EnrollmentPlanImportResponse, EnrollmentPlanRead

from ._recommendations_shared import _serialize_enrollment_plan


def list_enrollment_plans(
    session: Session,
    *,
    year: int | None = None,
    province: str | None = None,
    batch: str | None = None,
    college_id: int | None = None,
    student_type: str | None = None,
    keyword: str | None = None,
) -> list[EnrollmentPlanRead]:
    return [
        _serialize_enrollment_plan(item)
        for item in repo_list_enrollment_plans(
            session,
            year=year,
            province=province,
            batch=batch,
            college_id=college_id,
            student_type=student_type,
            keyword=keyword,
        )
    ]


def import_enrollment_plans(
    session: Session,
    settings: Settings,
    *,
    filename: str | None,
    content: bytes,
) -> EnrollmentPlanImportResponse:
    job = create_import_job(session, "enrollment_plans", filename)
    job.started_at = datetime.now()
    importer = EnrollmentPlanImporter(session, settings)
    result, created_colleges, created_majors = importer.execute(filename=filename, content=content)
    job.finished_at = datetime.now()
    job.status = "success" if result.failed_rows == 0 else "partial_success"
    job.result_json = {
        **result.model_dump(),
        "created_college_count": created_colleges,
        "created_major_count": created_majors,
    }
    write_audit_log(
        session,
        module="recommendations",
        action="import_enrollment_plans",
        target_type="import_job",
        target_id=str(job.id),
        detail_json=job.result_json,
    )
    return EnrollmentPlanImportResponse(
        created_college_count=created_colleges,
        created_major_count=created_majors,
        **result.model_dump(),
    )
