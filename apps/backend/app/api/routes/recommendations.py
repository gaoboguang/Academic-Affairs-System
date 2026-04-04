from __future__ import annotations

from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_db_session, get_settings
from app.core.config import Settings
from app.schemas.recommendation import (
    AdmissionImportResponse,
    AdmissionRecordRead,
    CollegePayload,
    CollegeRead,
    MajorPayload,
    MajorRead,
    RecommendationBatchGeneratePayload,
    RecommendationGeneratePayload,
    RecommendationGenerateResponse,
    RecommendationHistoryItem,
    RecommendationResultRead,
    RecommendationSettingsPayload,
    RecommendationSettingsRead,
    RecommendationStrategyPresetPayload,
)
from app.services import recommendations as service

router = APIRouter(tags=["recommendations"])


@router.get("/colleges", response_model=list[CollegeRead])
def list_colleges(
    keyword: str | None = Query(default=None),
    province: str | None = Query(default=None),
    supports_art: bool | None = Query(default=None),
    session: Session = Depends(get_db_session),
) -> list[CollegeRead]:
    return service.list_colleges(session, keyword=keyword, province=province, supports_art=supports_art)


@router.post("/colleges", response_model=CollegeRead)
def create_college(
    payload: CollegePayload,
    session: Session = Depends(get_db_session),
) -> CollegeRead:
    return service.create_college(session, payload)


@router.put("/colleges/{college_id}", response_model=CollegeRead)
def update_college(
    college_id: int,
    payload: CollegePayload,
    session: Session = Depends(get_db_session),
) -> CollegeRead:
    return service.update_college(session, college_id, payload)


@router.get("/majors", response_model=list[MajorRead])
def list_majors(
    keyword: str | None = Query(default=None),
    is_art_related: bool | None = Query(default=None),
    session: Session = Depends(get_db_session),
) -> list[MajorRead]:
    return service.list_majors(session, keyword=keyword, is_art_related=is_art_related)


@router.post("/majors", response_model=MajorRead)
def create_major(
    payload: MajorPayload,
    session: Session = Depends(get_db_session),
) -> MajorRead:
    return service.create_major(session, payload)


@router.put("/majors/{major_id}", response_model=MajorRead)
def update_major(
    major_id: int,
    payload: MajorPayload,
    session: Session = Depends(get_db_session),
) -> MajorRead:
    return service.update_major(session, major_id, payload)


@router.get("/admissions", response_model=list[AdmissionRecordRead])
def list_admission_records(
    year: int | None = Query(default=None),
    province: str | None = Query(default=None),
    college_id: int | None = Query(default=None),
    session: Session = Depends(get_db_session),
) -> list[AdmissionRecordRead]:
    return service.list_admission_records(session, year=year, province=province, college_id=college_id)


@router.post("/admissions/import", response_model=AdmissionImportResponse)
async def import_admission_records(
    file: UploadFile = File(...),
    session: Session = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> AdmissionImportResponse:
    content = await file.read()
    return service.import_admissions(session, settings, filename=file.filename, content=content)


@router.post("/recommendations/generate", response_model=RecommendationGenerateResponse)
def generate_recommendations(
    payload: RecommendationGeneratePayload,
    session: Session = Depends(get_db_session),
) -> RecommendationGenerateResponse:
    return service.generate_recommendations(session, payload)


@router.post("/recommendations/batch-generate")
def batch_generate_recommendations(
    payload: RecommendationBatchGeneratePayload,
    session: Session = Depends(get_db_session),
) -> dict[str, object]:
    return service.batch_generate_recommendations(session, payload)


@router.get("/recommendations/settings", response_model=RecommendationSettingsRead)
def get_recommendation_settings(session: Session = Depends(get_db_session)) -> RecommendationSettingsRead:
    return service.get_recommendation_settings(session)


@router.put("/recommendations/settings", response_model=RecommendationSettingsRead)
def update_recommendation_settings(
    payload: RecommendationSettingsPayload,
    session: Session = Depends(get_db_session),
) -> RecommendationSettingsRead:
    return service.update_recommendation_settings(session, payload)


@router.post("/recommendations/strategy-presets", response_model=RecommendationSettingsRead)
def create_strategy_preset(
    payload: RecommendationStrategyPresetPayload,
    session: Session = Depends(get_db_session),
) -> RecommendationSettingsRead:
    return service.create_recommendation_strategy_preset(session, payload)


@router.delete("/recommendations/strategy-presets/{preset_id}", response_model=RecommendationSettingsRead)
def delete_strategy_preset(
    preset_id: str,
    session: Session = Depends(get_db_session),
) -> RecommendationSettingsRead:
    return service.delete_recommendation_strategy_preset(session, preset_id)


@router.get("/recommendations/history", response_model=list[RecommendationHistoryItem])
def list_recommendation_history(
    student_id: int | None = Query(default=None),
    session: Session = Depends(get_db_session),
) -> list[RecommendationHistoryItem]:
    return service.list_recommendation_history(session, student_id=student_id)


@router.get("/recommendations/history/{scheme_id}/results", response_model=list[RecommendationResultRead])
def list_scheme_results(
    scheme_id: int,
    student_id: int | None = Query(default=None),
    session: Session = Depends(get_db_session),
) -> list[RecommendationResultRead]:
    return service.list_scheme_results(session, scheme_id, student_id=student_id)
