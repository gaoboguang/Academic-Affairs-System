from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db_session, get_settings
from app.core.config import Settings
from app.schemas.workload import (
    TeacherWorkloadExtraPayload,
    TeacherWorkloadExtraRead,
    TeacherWorkloadResultRead,
    TimetableBatchRead,
    TimetableEntryRead,
    TimetableEntryUpdatePayload,
    TimetableImportResponse,
    WorkloadCalculatePayload,
    WorkloadCalculateResponse,
    WorkloadRuleItemPayload,
    WorkloadRuleItemRead,
    WorkloadRuleVersionPayload,
    WorkloadRuleVersionRead,
)
from app.services import workload as service

router = APIRouter(tags=["workload"])


@router.post("/timetable/import", response_model=TimetableImportResponse)
async def import_timetable(
    semester_id: int = Form(...),
    file: UploadFile = File(...),
    remark: str | None = Form(default=None),
    session: Session = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> TimetableImportResponse:
    content = await file.read()
    return service.import_timetable(
        session,
        settings,
        semester_id=semester_id,
        filename=file.filename,
        content=content,
        remark=remark,
    )


@router.get("/timetable/batches", response_model=list[TimetableBatchRead])
def list_timetable_batches(
    semester_id: int | None = Query(default=None),
    session: Session = Depends(get_db_session),
) -> list[TimetableBatchRead]:
    return service.list_timetable_batches(session, semester_id=semester_id)


@router.get("/timetable/batches/{batch_id}/entries", response_model=list[TimetableEntryRead])
def list_timetable_entries(
    batch_id: int,
    unresolved_only: bool = Query(default=False),
    session: Session = Depends(get_db_session),
) -> list[TimetableEntryRead]:
    return service.list_timetable_entries(session, batch_id=batch_id, unresolved_only=unresolved_only)


@router.put("/timetable/entries/{entry_id}", response_model=TimetableEntryRead)
def update_timetable_entry(
    entry_id: int,
    payload: TimetableEntryUpdatePayload,
    session: Session = Depends(get_db_session),
) -> TimetableEntryRead:
    return service.update_timetable_entry(session, entry_id, payload)


@router.get("/workload/rules", response_model=list[WorkloadRuleVersionRead])
def list_rule_versions(session: Session = Depends(get_db_session)) -> list[WorkloadRuleVersionRead]:
    return service.list_rule_versions(session)


@router.post("/workload/rules", response_model=WorkloadRuleVersionRead)
def create_rule_version(
    payload: WorkloadRuleVersionPayload,
    session: Session = Depends(get_db_session),
) -> WorkloadRuleVersionRead:
    return service.create_rule_version(session, payload)


@router.get("/workload/rules/{rule_version_id}/items", response_model=list[WorkloadRuleItemRead])
def list_rule_items(
    rule_version_id: int,
    session: Session = Depends(get_db_session),
) -> list[WorkloadRuleItemRead]:
    return service.list_rule_items_read(session, rule_version_id)


@router.post("/workload/rules/{rule_version_id}/items", response_model=list[WorkloadRuleItemRead])
def replace_rule_items(
    rule_version_id: int,
    payload: list[WorkloadRuleItemPayload],
    session: Session = Depends(get_db_session),
) -> list[WorkloadRuleItemRead]:
    return service.replace_rule_items(session, rule_version_id, payload)


@router.get("/workload/extras", response_model=list[TeacherWorkloadExtraRead])
def list_workload_extras(
    semester_id: int | None = Query(default=None),
    session: Session = Depends(get_db_session),
) -> list[TeacherWorkloadExtraRead]:
    return service.list_workload_extras(session, semester_id=semester_id)


@router.post("/workload/extras", response_model=TeacherWorkloadExtraRead)
def create_workload_extra(
    payload: TeacherWorkloadExtraPayload,
    session: Session = Depends(get_db_session),
) -> TeacherWorkloadExtraRead:
    return service.create_workload_extra(session, payload)


@router.post("/workload/calculate", response_model=WorkloadCalculateResponse)
def calculate_workload(
    payload: WorkloadCalculatePayload,
    session: Session = Depends(get_db_session),
) -> WorkloadCalculateResponse:
    return service.calculate_workload(session, payload)


@router.get("/workload/results", response_model=list[TeacherWorkloadResultRead])
def list_workload_results(
    semester_id: int | None = Query(default=None),
    rule_version_id: int | None = Query(default=None),
    session: Session = Depends(get_db_session),
) -> list[TeacherWorkloadResultRead]:
    return service.list_workload_results(session, semester_id=semester_id, rule_version_id=rule_version_id)


@router.get("/workload/results/export")
def export_workload_results(
    semester_id: int | None = Query(default=None),
    rule_version_id: int | None = Query(default=None),
    session: Session = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> FileResponse:
    result = service.export_workload(session, settings, semester_id=semester_id, rule_version_id=rule_version_id)
    path = settings.project_root / result["file_path"]
    return FileResponse(path, filename=Path(path).name)

