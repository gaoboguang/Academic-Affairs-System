from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, Query, Request, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db_session, get_settings
from app.core.config import Settings
from app.schemas.archive import StoredFileRead
from app.schemas.system import (
    AuditLogRead,
    BackupCreateResponse,
    BackupRecordRead,
    BackupRestorePayload,
    DataRepairExecutePayload,
    DataRepairExecuteResponse,
    DataRepairScanRead,
    SystemConfigGroupRead,
    SystemConfigItemUpdatePayload,
    SystemTemplateRead,
)
from app.services import system as service

router = APIRouter(tags=["system"])


@router.post("/files/upload", response_model=StoredFileRead)
async def upload_file(
    file: UploadFile = File(...),
    category: str = Form(default="general"),
    session: Session = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> StoredFileRead:
    content = await file.read()
    return service.upload_file(
        session,
        settings,
        filename=file.filename,
        content=content,
        content_type=file.content_type,
        category=category,
    )


@router.get("/files/{file_id}")
def download_stored_file(
    file_id: int,
    session: Session = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> FileResponse:
    path = service.get_file_path(session, settings, file_id)
    return FileResponse(path, filename=Path(path).name)


@router.get("/system/backups", response_model=list[BackupRecordRead])
def list_backups(
    session: Session = Depends(get_db_session),
) -> list[BackupRecordRead]:
    return service.list_backups(session)


@router.post("/system/backup", response_model=BackupCreateResponse)
def create_backup(request: Request) -> BackupCreateResponse:
    return service.create_backup(request)


@router.post("/system/restore")
def restore_backup(
    payload: BackupRestorePayload,
    request: Request,
) -> dict[str, str]:
    return service.restore_backup(request, payload)


@router.get("/system/backups/{backup_id}/download")
def download_backup(
    backup_id: int,
    session: Session = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> FileResponse:
    path = service.get_backup_path(session, settings, backup_id)
    return FileResponse(path, filename=Path(path).name)


@router.get("/system/audit-logs", response_model=list[AuditLogRead])
def list_audit_logs(
    limit: int = Query(default=100, ge=1, le=500),
    session: Session = Depends(get_db_session),
) -> list[AuditLogRead]:
    return service.list_audit_logs(session, limit=limit)


@router.get("/system/config-groups", response_model=list[SystemConfigGroupRead])
def list_config_groups(
    session: Session = Depends(get_db_session),
) -> list[SystemConfigGroupRead]:
    return service.list_config_groups(session)


@router.put("/system/config-items", response_model=list[SystemConfigGroupRead])
def update_config_items(
    payload: list[SystemConfigItemUpdatePayload],
    session: Session = Depends(get_db_session),
) -> list[SystemConfigGroupRead]:
    return service.update_config_items(session, payload)


@router.get("/system/templates", response_model=list[SystemTemplateRead])
def list_templates(settings: Settings = Depends(get_settings)) -> list[SystemTemplateRead]:
    return service.list_templates(settings)


@router.get("/system/templates/{template_name}/download")
def download_template(
    template_name: str,
    settings: Settings = Depends(get_settings),
) -> FileResponse:
    path = service.get_template_path(settings, template_name)
    return FileResponse(path, filename=Path(path).name)


@router.get("/system/data-repair/scan", response_model=DataRepairScanRead)
def get_data_repair_scan(
    session: Session = Depends(get_db_session),
) -> DataRepairScanRead:
    return service.get_data_repair_scan(session)


@router.post("/system/data-repair/execute", response_model=DataRepairExecuteResponse)
def execute_data_repair(
    payload: DataRepairExecutePayload,
    session: Session = Depends(get_db_session),
) -> DataRepairExecuteResponse:
    return service.execute_data_repair(session, payload)
