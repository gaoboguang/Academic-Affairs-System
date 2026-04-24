from __future__ import annotations

from fastapi import APIRouter, Depends, Query
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
from app.services import gaokao as service
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
