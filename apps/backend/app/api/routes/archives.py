from __future__ import annotations

from datetime import date
from pathlib import Path

from fastapi import APIRouter, Depends, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db_session, get_settings
from app.core.config import Settings
from app.schemas.archive import StudentGrowthRecordPayload, StudentGrowthRecordRead, StudentGrowthTimelineResponse
from app.services import archive as service

router = APIRouter(prefix="/archives", tags=["growth-archive"])


@router.get("/students/{student_id}/records", response_model=StudentGrowthTimelineResponse)
def list_growth_records(
    student_id: int,
    record_type: str | None = Query(default=None),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    session: Session = Depends(get_db_session),
) -> StudentGrowthTimelineResponse:
    return service.list_growth_records(
        session,
        student_id,
        record_type=record_type,
        start_date=start_date,
        end_date=end_date,
    )


@router.post("/students/{student_id}/records", response_model=StudentGrowthRecordRead)
def create_growth_record(
    student_id: int,
    payload: StudentGrowthRecordPayload,
    session: Session = Depends(get_db_session),
) -> StudentGrowthRecordRead:
    return service.create_growth_record(session, student_id, payload)


@router.put("/records/{record_id}", response_model=StudentGrowthRecordRead)
def update_growth_record(
    record_id: int,
    payload: StudentGrowthRecordPayload,
    session: Session = Depends(get_db_session),
) -> StudentGrowthRecordRead:
    return service.update_growth_record(session, record_id, payload)


@router.delete("/records/{record_id}")
def delete_growth_record(
    record_id: int,
    session: Session = Depends(get_db_session),
) -> dict[str, str]:
    return service.delete_growth_record(session, record_id)


@router.get("/students/{student_id}/summary/export")
def export_growth_summary(
    student_id: int,
    session: Session = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> FileResponse:
    result = service.export_student_growth_summary(session, settings, student_id)
    path = settings.project_root / result["file_path"]
    return FileResponse(path, filename=Path(path).name)

