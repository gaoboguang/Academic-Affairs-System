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
    EmploymentDirectionPayload,
    EmploymentDirectionRead,
    EmploymentDirectionBootstrapResponse,
    EnrollmentPlanImportResponse,
    EnrollmentPlanRead,
    MajorPayload,
    MajorRead,
    MajorEmploymentMappingPayload,
    MajorEmploymentMappingRead,
    MajorEmploymentMappingBootstrapResponse,
    ProvinceVolunteerRuleBootstrapResponse,
    ProvinceVolunteerRulePayload,
    ProvinceVolunteerRuleRead,
    ProvinceScoreTransformRuleBootstrapResponse,
    ProvinceScoreTransformRulePayload,
    ProvinceScoreTransformRuleRead,
    RecommendationBatchGeneratePayload,
    RecommendationBatchGenerateResponse,
    RecommendationGeneratePayload,
    RecommendationGenerateResponse,
    RecommendationHistoryItem,
    SubjectRequirementDictBootstrapResponse,
    SubjectRequirementDictPayload,
    SubjectRequirementDictRead,
    RecommendationResultRead,
    RecommendationSettingsPayload,
    RecommendationSettingsRead,
    RecommendationStrategyPresetPayload,
    ShandongRushStableSafeRecommendationPayload,
    ShandongRushStableSafeRecommendationResponse,
    SpecialTypeRuleBootstrapResponse,
    SpecialTypeRulePayload,
    SpecialTypeRuleRead,
    StudentGaokaoScoreProjectionPayload,
    StudentGaokaoScoreProjectionRead,
    VolunteerDraftPayload,
    VolunteerDraftRead,
    VolunteerDraftSummaryRead,
    VolunteerWorkbenchPreviewPayload,
    VolunteerWorkbenchPreviewResponse,
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


@router.get("/employment-directions", response_model=list[EmploymentDirectionRead])
def list_employment_directions(
    keyword: str | None = Query(default=None),
    category: str | None = Query(default=None),
    session: Session = Depends(get_db_session),
) -> list[EmploymentDirectionRead]:
    return service.list_employment_directions(session, keyword=keyword, category=category)


@router.post("/employment-directions", response_model=EmploymentDirectionRead)
def create_employment_direction(
    payload: EmploymentDirectionPayload,
    session: Session = Depends(get_db_session),
) -> EmploymentDirectionRead:
    return service.create_employment_direction(session, payload)


@router.post("/employment-directions/bootstrap", response_model=EmploymentDirectionBootstrapResponse)
def bootstrap_employment_directions(
    session: Session = Depends(get_db_session),
) -> EmploymentDirectionBootstrapResponse:
    return service.bootstrap_employment_directions(session)


@router.put("/employment-directions/{direction_id}", response_model=EmploymentDirectionRead)
def update_employment_direction(
    direction_id: int,
    payload: EmploymentDirectionPayload,
    session: Session = Depends(get_db_session),
) -> EmploymentDirectionRead:
    return service.update_employment_direction(session, direction_id, payload)


@router.get("/major-employment-maps", response_model=list[MajorEmploymentMappingRead])
def list_major_employment_mappings(
    major_id: int | None = Query(default=None),
    direction_id: int | None = Query(default=None),
    strength: str | None = Query(default=None),
    keyword: str | None = Query(default=None),
    session: Session = Depends(get_db_session),
) -> list[MajorEmploymentMappingRead]:
    return service.list_major_employment_mappings(
        session,
        major_id=major_id,
        direction_id=direction_id,
        strength=strength,
        keyword=keyword,
    )


@router.post("/major-employment-maps", response_model=MajorEmploymentMappingRead)
def create_major_employment_mapping(
    payload: MajorEmploymentMappingPayload,
    session: Session = Depends(get_db_session),
) -> MajorEmploymentMappingRead:
    return service.create_major_employment_mapping(session, payload)


@router.post("/major-employment-maps/bootstrap", response_model=MajorEmploymentMappingBootstrapResponse)
def bootstrap_major_employment_mappings(
    session: Session = Depends(get_db_session),
) -> MajorEmploymentMappingBootstrapResponse:
    return service.bootstrap_major_employment_mappings(session)


@router.put("/major-employment-maps/{mapping_id}", response_model=MajorEmploymentMappingRead)
def update_major_employment_mapping(
    mapping_id: int,
    payload: MajorEmploymentMappingPayload,
    session: Session = Depends(get_db_session),
) -> MajorEmploymentMappingRead:
    return service.update_major_employment_mapping(session, mapping_id, payload)


@router.get("/admissions", response_model=list[AdmissionRecordRead])
def list_admission_records(
    year: int | None = Query(default=None),
    province: str | None = Query(default=None),
    college_id: int | None = Query(default=None),
    student_type: str | None = Query(default=None),
    session: Session = Depends(get_db_session),
) -> list[AdmissionRecordRead]:
    return service.list_admission_records(
        session,
        year=year,
        province=province,
        college_id=college_id,
        student_type=student_type,
    )


@router.post("/admissions/import", response_model=AdmissionImportResponse)
async def import_admission_records(
    file: UploadFile = File(...),
    session: Session = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> AdmissionImportResponse:
    content = await file.read()
    return service.import_admissions(session, settings, filename=file.filename, content=content)


@router.get("/enrollment-plans", response_model=list[EnrollmentPlanRead])
def list_enrollment_plans(
    year: int | None = Query(default=None),
    province: str | None = Query(default=None),
    batch: str | None = Query(default=None),
    college_id: int | None = Query(default=None),
    student_type: str | None = Query(default=None),
    keyword: str | None = Query(default=None),
    session: Session = Depends(get_db_session),
) -> list[EnrollmentPlanRead]:
    return service.list_enrollment_plans(
        session,
        year=year,
        province=province,
        batch=batch,
        college_id=college_id,
        student_type=student_type,
        keyword=keyword,
    )


@router.post("/enrollment-plans/import", response_model=EnrollmentPlanImportResponse)
async def import_enrollment_plans(
    file: UploadFile = File(...),
    session: Session = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> EnrollmentPlanImportResponse:
    content = await file.read()
    return service.import_enrollment_plans(session, settings, filename=file.filename, content=content)


@router.get("/province-volunteer-rules", response_model=list[ProvinceVolunteerRuleRead])
def list_province_volunteer_rules(
    province: str | None = Query(default=None),
    year: int | None = Query(default=None),
    exam_mode: str | None = Query(default=None),
    candidate_type: str | None = Query(default=None),
    session: Session = Depends(get_db_session),
) -> list[ProvinceVolunteerRuleRead]:
    return service.list_province_volunteer_rules(
        session,
        province=province,
        year=year,
        exam_mode=exam_mode,
        candidate_type=candidate_type,
    )


@router.post("/province-volunteer-rules", response_model=ProvinceVolunteerRuleRead)
def create_province_volunteer_rule(
    payload: ProvinceVolunteerRulePayload,
    session: Session = Depends(get_db_session),
) -> ProvinceVolunteerRuleRead:
    return service.create_province_volunteer_rule(session, payload)


@router.post("/province-volunteer-rules/bootstrap", response_model=ProvinceVolunteerRuleBootstrapResponse)
def bootstrap_province_volunteer_rules(
    year: int | None = Query(default=None, ge=2020, le=2100),
    session: Session = Depends(get_db_session),
) -> ProvinceVolunteerRuleBootstrapResponse:
    return service.bootstrap_province_volunteer_rules(session, year=year)


@router.put("/province-volunteer-rules/{rule_id}", response_model=ProvinceVolunteerRuleRead)
def update_province_volunteer_rule(
    rule_id: int,
    payload: ProvinceVolunteerRulePayload,
    session: Session = Depends(get_db_session),
) -> ProvinceVolunteerRuleRead:
    return service.update_province_volunteer_rule(session, rule_id, payload)


@router.get("/province-score-transform-rules", response_model=list[ProvinceScoreTransformRuleRead])
def list_province_score_transform_rules(
    province: str | None = Query(default=None),
    year: int | None = Query(default=None),
    exam_mode: str | None = Query(default=None),
    subject_name: str | None = Query(default=None),
    session: Session = Depends(get_db_session),
) -> list[ProvinceScoreTransformRuleRead]:
    return service.list_province_score_transform_rules(
        session,
        province=province,
        year=year,
        exam_mode=exam_mode,
        subject_name=subject_name,
    )


@router.post("/province-score-transform-rules", response_model=ProvinceScoreTransformRuleRead)
def create_province_score_transform_rule(
    payload: ProvinceScoreTransformRulePayload,
    session: Session = Depends(get_db_session),
) -> ProvinceScoreTransformRuleRead:
    return service.create_province_score_transform_rule(session, payload)


@router.post("/province-score-transform-rules/bootstrap", response_model=ProvinceScoreTransformRuleBootstrapResponse)
def bootstrap_province_score_transform_rules(
    year: int | None = Query(default=None, ge=2020, le=2100),
    session: Session = Depends(get_db_session),
) -> ProvinceScoreTransformRuleBootstrapResponse:
    return service.bootstrap_province_score_transform_rules(session, year=year)


@router.put("/province-score-transform-rules/{rule_id}", response_model=ProvinceScoreTransformRuleRead)
def update_province_score_transform_rule(
    rule_id: int,
    payload: ProvinceScoreTransformRulePayload,
    session: Session = Depends(get_db_session),
) -> ProvinceScoreTransformRuleRead:
    return service.update_province_score_transform_rule(session, rule_id, payload)


@router.get("/subject-requirement-dicts", response_model=list[SubjectRequirementDictRead])
def list_subject_requirement_dicts(
    province: str | None = Query(default=None),
    year: int | None = Query(default=None),
    exam_mode: str | None = Query(default=None),
    requirement_code: str | None = Query(default=None),
    session: Session = Depends(get_db_session),
) -> list[SubjectRequirementDictRead]:
    return service.list_subject_requirement_dicts(
        session,
        province=province,
        year=year,
        exam_mode=exam_mode,
        requirement_code=requirement_code,
    )


@router.post("/subject-requirement-dicts", response_model=SubjectRequirementDictRead)
def create_subject_requirement_dict(
    payload: SubjectRequirementDictPayload,
    session: Session = Depends(get_db_session),
) -> SubjectRequirementDictRead:
    return service.create_subject_requirement_dict(session, payload)


@router.post("/subject-requirement-dicts/bootstrap", response_model=SubjectRequirementDictBootstrapResponse)
def bootstrap_subject_requirement_dicts(
    year: int | None = Query(default=None, ge=2020, le=2100),
    session: Session = Depends(get_db_session),
) -> SubjectRequirementDictBootstrapResponse:
    return service.bootstrap_subject_requirement_dicts(session, year=year)


@router.put("/subject-requirement-dicts/{dict_id}", response_model=SubjectRequirementDictRead)
def update_subject_requirement_dict(
    dict_id: int,
    payload: SubjectRequirementDictPayload,
    session: Session = Depends(get_db_session),
) -> SubjectRequirementDictRead:
    return service.update_subject_requirement_dict(session, dict_id, payload)


@router.get("/special-type-rules", response_model=list[SpecialTypeRuleRead])
def list_special_type_rules(
    province: str | None = Query(default=None),
    year: int | None = Query(default=None),
    student_type: str | None = Query(default=None),
    session: Session = Depends(get_db_session),
) -> list[SpecialTypeRuleRead]:
    return service.list_special_type_rules(
        session,
        province=province,
        year=year,
        student_type=student_type,
    )


@router.post("/special-type-rules", response_model=SpecialTypeRuleRead)
def create_special_type_rule(
    payload: SpecialTypeRulePayload,
    session: Session = Depends(get_db_session),
) -> SpecialTypeRuleRead:
    return service.create_special_type_rule(session, payload)


@router.post("/special-type-rules/bootstrap", response_model=SpecialTypeRuleBootstrapResponse)
def bootstrap_special_type_rules(
    year: int | None = Query(default=None, ge=2020, le=2100),
    session: Session = Depends(get_db_session),
) -> SpecialTypeRuleBootstrapResponse:
    return service.bootstrap_special_type_rules(session, year=year)


@router.put("/special-type-rules/{rule_id}", response_model=SpecialTypeRuleRead)
def update_special_type_rule(
    rule_id: int,
    payload: SpecialTypeRulePayload,
    session: Session = Depends(get_db_session),
) -> SpecialTypeRuleRead:
    return service.update_special_type_rule(session, rule_id, payload)


@router.post("/recommendations/gaokao-score-projections/calculate", response_model=StudentGaokaoScoreProjectionRead)
def calculate_gaokao_score_projection(
    payload: StudentGaokaoScoreProjectionPayload,
    session: Session = Depends(get_db_session),
) -> StudentGaokaoScoreProjectionRead:
    return service.calculate_gaokao_score_projection(session, payload)


@router.post("/recommendations/gaokao-score-projections", response_model=StudentGaokaoScoreProjectionRead)
def create_gaokao_score_projection(
    payload: StudentGaokaoScoreProjectionPayload,
    session: Session = Depends(get_db_session),
) -> StudentGaokaoScoreProjectionRead:
    return service.create_gaokao_score_projection(session, payload)


@router.get("/recommendations/gaokao-score-projections", response_model=list[StudentGaokaoScoreProjectionRead])
def list_gaokao_score_projections(
    student_id: int | None = Query(default=None),
    target_year: int | None = Query(default=None),
    session: Session = Depends(get_db_session),
) -> list[StudentGaokaoScoreProjectionRead]:
    return service.list_gaokao_score_projections(session, student_id=student_id, target_year=target_year)


@router.get("/recommendations/gaokao-score-projections/{projection_id}", response_model=StudentGaokaoScoreProjectionRead)
def get_gaokao_score_projection(
    projection_id: int,
    session: Session = Depends(get_db_session),
) -> StudentGaokaoScoreProjectionRead:
    return service.get_gaokao_score_projection(session, projection_id)


@router.post(
    "/recommendations/shandong-rush-stable-safe/preview",
    response_model=ShandongRushStableSafeRecommendationResponse,
)
def preview_shandong_rush_stable_safe_recommendations(
    payload: ShandongRushStableSafeRecommendationPayload,
    session: Session = Depends(get_db_session),
) -> ShandongRushStableSafeRecommendationResponse:
    return service.preview_shandong_rush_stable_safe_recommendations(session, payload)


@router.post("/recommendations/volunteer-workbench/preview", response_model=VolunteerWorkbenchPreviewResponse)
def preview_volunteer_workbench(
    payload: VolunteerWorkbenchPreviewPayload,
    session: Session = Depends(get_db_session),
) -> VolunteerWorkbenchPreviewResponse:
    return service.preview_volunteer_workbench(session, payload)


@router.get("/recommendations/volunteer-drafts", response_model=list[VolunteerDraftSummaryRead])
def list_volunteer_drafts(
    student_id: int | None = Query(default=None),
    exam_id: int | None = Query(default=None),
    session: Session = Depends(get_db_session),
) -> list[VolunteerDraftSummaryRead]:
    return service.list_volunteer_drafts(session, student_id=student_id, exam_id=exam_id)


@router.get("/recommendations/volunteer-drafts/{draft_id}", response_model=VolunteerDraftRead)
def get_volunteer_draft_detail(
    draft_id: int,
    session: Session = Depends(get_db_session),
) -> VolunteerDraftRead:
    return service.get_volunteer_draft_detail(session, draft_id)


@router.post("/recommendations/volunteer-drafts", response_model=VolunteerDraftRead)
def create_volunteer_draft(
    payload: VolunteerDraftPayload,
    session: Session = Depends(get_db_session),
) -> VolunteerDraftRead:
    return service.create_volunteer_draft(session, payload)


@router.put("/recommendations/volunteer-drafts/{draft_id}", response_model=VolunteerDraftRead)
def update_volunteer_draft(
    draft_id: int,
    payload: VolunteerDraftPayload,
    session: Session = Depends(get_db_session),
) -> VolunteerDraftRead:
    return service.update_volunteer_draft(session, draft_id, payload)


@router.delete("/recommendations/volunteer-drafts/{draft_id}")
def delete_volunteer_draft(
    draft_id: int,
    session: Session = Depends(get_db_session),
) -> dict[str, str]:
    service.delete_volunteer_draft(session, draft_id)
    return {"message": "志愿草稿已删除"}


@router.post("/recommendations/generate", response_model=RecommendationGenerateResponse)
def generate_recommendations(
    payload: RecommendationGeneratePayload,
    session: Session = Depends(get_db_session),
) -> RecommendationGenerateResponse:
    return service.generate_recommendations(session, payload)


@router.post("/recommendations/batch-generate", response_model=RecommendationBatchGenerateResponse)
def batch_generate_recommendations(
    payload: RecommendationBatchGeneratePayload,
    session: Session = Depends(get_db_session),
) -> RecommendationBatchGenerateResponse:
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
