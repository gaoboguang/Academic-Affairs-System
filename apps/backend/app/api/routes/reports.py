from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db_session, get_settings
from app.core.config import Settings
from app.schemas.report import ReportExportPayload, ReportExportRecordRead, ShandongRecommendationReportExportPayload
from app.services import reports as service
from app.utils.files import resolve_allowed_file_path

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("/export", response_model=ReportExportRecordRead)
def export_report(
    payload: ReportExportPayload,
    session: Session = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> ReportExportRecordRead:
    return service.export_report(session, settings, payload)


@router.post("/shandong-recommendation/export", response_model=ReportExportRecordRead)
def export_shandong_recommendation_report(
    payload: ShandongRecommendationReportExportPayload,
    session: Session = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> ReportExportRecordRead:
    return service.export_shandong_recommendation_report_record(session, settings, payload)


@router.get("/exports", response_model=list[ReportExportRecordRead])
def list_report_exports(session: Session = Depends(get_db_session)) -> list[ReportExportRecordRead]:
    return service.list_report_exports(session)


@router.get("/exports/{export_id}/download")
def download_report_export(
    export_id: int,
    session: Session = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> FileResponse:
    record = service.get_report_export_record(session, export_id)
    path = resolve_allowed_file_path(
        record.file_path,
        allowed_roots=[settings.exports_dir],
        project_root=settings.project_root,
    )
    return FileResponse(path, filename=Path(path).name)
