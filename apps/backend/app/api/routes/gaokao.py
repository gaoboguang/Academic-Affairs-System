from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, File, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db_session, get_gaokao_db_session, get_settings
from app.core.config import Settings
from app.schemas.gaokao import (
    GaokaoCollegeEvidenceRead,
    GaokaoCollegeOptionRead,
    GaokaoDataHealthRead,
    GaokaoDataOverviewRead,
    GaokaoImportBatchRead,
    GaokaoReviewSummaryRead,
    GaokaoShandongMonitorRead,
)
from app.schemas.gaokao_pathway import (
    GaokaoPathwayBootstrapResponse,
    GaokaoPathwayRead,
    GaokaoPathwayRulePayload,
    GaokaoPathwayRuleRead,
    StudentPathwayEvaluationResponse,
    StudentPathwayProfilePayload,
    StudentPathwayProfileRead,
)
from app.services import gaokao as service
from app.services import gaokao_pathways as pathway_service
from app.utils.files import resolve_allowed_file_path
from app.utils.data_health import build_data_health_report

router = APIRouter(prefix="/gaokao", tags=["gaokao"])


@router.get("/data-overview", response_model=GaokaoDataOverviewRead)
def get_data_overview(
    session: Session = Depends(get_db_session),
    gaokao_session: Session | None = Depends(get_gaokao_db_session),
    settings: Settings = Depends(get_settings),
) -> GaokaoDataOverviewRead:
    return service.get_data_overview(session, gaokao_session, settings)


@router.get("/data-health", response_model=GaokaoDataHealthRead)
def get_data_health(
    province: str = Query(default="山东"),
    settings: Settings = Depends(get_settings),
) -> GaokaoDataHealthRead:
    return GaokaoDataHealthRead.model_validate(
        build_data_health_report(settings.db_path, province=province)
    )


@router.get("/pathways", response_model=list[GaokaoPathwayRead])
def list_pathways(
    province: str = Query(default="山东"),
    include_inactive: bool = Query(default=False),
    session: Session = Depends(get_db_session),
) -> list[GaokaoPathwayRead]:
    return pathway_service.list_pathways(session, province=province, include_inactive=include_inactive)


@router.post("/pathways/bootstrap-shandong", response_model=GaokaoPathwayBootstrapResponse)
def bootstrap_shandong_pathways(
    target_year: int = Query(default=2026, ge=2020, le=2100),
    session: Session = Depends(get_db_session),
) -> GaokaoPathwayBootstrapResponse:
    return pathway_service.bootstrap_shandong_pathways(session, target_year=target_year)


@router.get("/pathways/{pathway_id}/rules", response_model=list[GaokaoPathwayRuleRead])
def list_pathway_rules(
    pathway_id: int,
    session: Session = Depends(get_db_session),
) -> list[GaokaoPathwayRuleRead]:
    return pathway_service.list_pathway_rules(session, pathway_id)


@router.post("/pathways/{pathway_id}/rules", response_model=GaokaoPathwayRuleRead)
def create_pathway_rule(
    pathway_id: int,
    payload: GaokaoPathwayRulePayload,
    session: Session = Depends(get_db_session),
) -> GaokaoPathwayRuleRead:
    return pathway_service.create_pathway_rule(session, pathway_id, payload)


@router.get("/students/{student_id}/pathway-profile", response_model=StudentPathwayProfileRead)
def get_student_pathway_profile(
    student_id: int,
    province: str = Query(default="山东"),
    session: Session = Depends(get_db_session),
) -> StudentPathwayProfileRead:
    return pathway_service.get_student_pathway_profile(session, student_id, province=province)


@router.put("/students/{student_id}/pathway-profile", response_model=StudentPathwayProfileRead)
def upsert_student_pathway_profile(
    student_id: int,
    payload: StudentPathwayProfilePayload,
    session: Session = Depends(get_db_session),
) -> StudentPathwayProfileRead:
    return pathway_service.upsert_student_pathway_profile(session, student_id, payload)


@router.get("/pathway-profiles/template")
def download_pathway_profile_template(settings: Settings = Depends(get_settings)) -> FileResponse:
    result = pathway_service.export_student_pathway_profile_template(settings)
    path = resolve_allowed_file_path(
        result["file_path"],
        allowed_roots=[settings.templates_dir],
        project_root=settings.project_root,
    )
    return FileResponse(path, filename=Path(path).name)


@router.post("/pathway-profiles/import")
async def import_pathway_profiles(
    file: UploadFile = File(...),
    session: Session = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> dict:
    content = await file.read()
    return pathway_service.import_student_pathway_profiles(
        session,
        settings,
        filename=file.filename,
        content=content,
    )


@router.get("/pathway-profiles/export")
def export_pathway_profiles(
    session: Session = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> FileResponse:
    result = pathway_service.export_student_pathway_profiles(session, settings)
    path = resolve_allowed_file_path(
        result["file_path"],
        allowed_roots=[settings.exports_dir],
        project_root=settings.project_root,
    )
    return FileResponse(path, filename=Path(path).name)


@router.post("/students/{student_id}/pathway-evaluations/preview", response_model=StudentPathwayEvaluationResponse)
def preview_student_pathway_evaluations(
    student_id: int,
    target_year: int = Query(default=2026, ge=2020, le=2100),
    province: str = Query(default="山东"),
    session: Session = Depends(get_db_session),
) -> StudentPathwayEvaluationResponse:
    return pathway_service.preview_student_pathway_evaluations(
        session,
        student_id,
        target_year=target_year,
        province=province,
    )


@router.post("/students/{student_id}/pathway-evaluations", response_model=StudentPathwayEvaluationResponse)
def persist_student_pathway_evaluations(
    student_id: int,
    target_year: int = Query(default=2026, ge=2020, le=2100),
    province: str = Query(default="山东"),
    session: Session = Depends(get_db_session),
) -> StudentPathwayEvaluationResponse:
    return pathway_service.persist_student_pathway_evaluations(
        session,
        student_id,
        target_year=target_year,
        province=province,
    )


@router.get("/import-batches", response_model=list[GaokaoImportBatchRead])
def list_import_batches(
    session: Session = Depends(get_db_session),
    gaokao_session: Session | None = Depends(get_gaokao_db_session),
    settings: Settings = Depends(get_settings),
) -> list[GaokaoImportBatchRead]:
    return service.list_import_batches(session, gaokao_session, settings)


@router.get("/college-options", response_model=list[GaokaoCollegeOptionRead])
def list_college_options(
    q: str | None = Query(default=None),
    limit: int = Query(default=10, ge=1, le=50),
    session: Session = Depends(get_db_session),
    gaokao_session: Session | None = Depends(get_gaokao_db_session),
    settings: Settings = Depends(get_settings),
) -> list[GaokaoCollegeOptionRead]:
    return service.list_college_options(session, gaokao_session, settings, query=q, limit=limit)


@router.get("/review-summary", response_model=GaokaoReviewSummaryRead)
def get_review_summary(
    status: str | None = Query(default=None),
    focus: str | None = Query(default=None),
    sort: str | None = Query(default=None),
    keyword: str | None = Query(default=None),
    session: Session = Depends(get_db_session),
    gaokao_session: Session | None = Depends(get_gaokao_db_session),
    settings: Settings = Depends(get_settings),
) -> GaokaoReviewSummaryRead:
    return service.get_review_summary(
        session,
        gaokao_session,
        settings,
        status=status,
        focus=focus,
        sort=sort,
        keyword=keyword,
    )


@router.get("/college-evidence/{college_id}", response_model=GaokaoCollegeEvidenceRead)
def get_college_evidence(
    college_id: int,
    session: Session = Depends(get_db_session),
    gaokao_session: Session | None = Depends(get_gaokao_db_session),
    settings: Settings = Depends(get_settings),
) -> GaokaoCollegeEvidenceRead:
    return service.get_college_evidence(session, gaokao_session, settings, college_id)


@router.get("/shandong-monitor", response_model=GaokaoShandongMonitorRead)
def get_shandong_monitor(
    session: Session = Depends(get_db_session),
    gaokao_session: Session | None = Depends(get_gaokao_db_session),
    settings: Settings = Depends(get_settings),
) -> GaokaoShandongMonitorRead:
    return service.get_shandong_monitor(session, gaokao_session, settings)
