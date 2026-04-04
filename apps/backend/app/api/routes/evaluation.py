from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_db_session, get_settings
from app.core.config import Settings
from app.schemas.evaluation import (
    AdviserQuantRecordPayload,
    AdviserQuantRecordRead,
    AdviserQuantRuleItemPayload,
    AdviserQuantRuleItemRead,
    AdviserQuantRuleVersionPayload,
    AdviserQuantRuleVersionRead,
    AdviserQuantSummaryRead,
    EvaluationBatchCompareRead,
    EvaluationBatchOverviewRead,
    EvaluationBatchRead,
    EvaluationImportResponse,
    EvaluationTeacherDetailRead,
    EvaluationTeacherTrendRead,
    EvaluationTemplatePayload,
    EvaluationTemplateRead,
)
from app.services import evaluation as service

router = APIRouter(tags=["evaluation"])


@router.get("/evaluation/templates", response_model=list[EvaluationTemplateRead])
def list_templates(session: Session = Depends(get_db_session)) -> list[EvaluationTemplateRead]:
    return service.list_evaluation_templates(session)


@router.post("/evaluation/templates", response_model=EvaluationTemplateRead)
def create_template(
    payload: EvaluationTemplatePayload,
    session: Session = Depends(get_db_session),
) -> EvaluationTemplateRead:
    return service.create_evaluation_template(session, payload)


@router.put("/evaluation/templates/{template_id}", response_model=EvaluationTemplateRead)
def update_template(
    template_id: int,
    payload: EvaluationTemplatePayload,
    session: Session = Depends(get_db_session),
) -> EvaluationTemplateRead:
    return service.update_evaluation_template(session, template_id, payload)


@router.get("/evaluation/batches", response_model=list[EvaluationBatchRead])
def list_batches(
    semester_id: int | None = None,
    session: Session = Depends(get_db_session),
) -> list[EvaluationBatchRead]:
    return service.list_evaluation_batches(session, semester_id=semester_id)


@router.post("/evaluation/import", response_model=EvaluationImportResponse)
async def import_batch(
    template_id: int = Form(...),
    semester_id: int = Form(...),
    file: UploadFile = File(...),
    session: Session = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> EvaluationImportResponse:
    content = await file.read()
    return service.import_evaluation_batch(
        session,
        settings,
        template_id=template_id,
        semester_id=semester_id,
        filename=file.filename,
        content=content,
    )


@router.get("/evaluation/batches/{batch_id}/overview", response_model=EvaluationBatchOverviewRead)
def get_batch_overview(
    batch_id: int,
    session: Session = Depends(get_db_session),
) -> EvaluationBatchOverviewRead:
    return service.get_evaluation_batch_overview(session, batch_id)


@router.get("/evaluation/batches/{batch_id}/compare", response_model=EvaluationBatchCompareRead)
def get_batch_compare(
    batch_id: int,
    compare_batch_id: int,
    session: Session = Depends(get_db_session),
) -> EvaluationBatchCompareRead:
    return service.get_evaluation_batch_compare(session, batch_id, compare_batch_id)


@router.get("/evaluation/batches/{batch_id}/teachers/{teacher_id}", response_model=EvaluationTeacherDetailRead)
def get_teacher_detail(
    batch_id: int,
    teacher_id: int,
    session: Session = Depends(get_db_session),
) -> EvaluationTeacherDetailRead:
    return service.get_evaluation_teacher_detail(session, batch_id, teacher_id)


@router.get("/evaluation/teachers/{teacher_id}/trend", response_model=EvaluationTeacherTrendRead)
def get_teacher_trend(
    teacher_id: int,
    template_id: int | None = None,
    session: Session = Depends(get_db_session),
) -> EvaluationTeacherTrendRead:
    return service.get_evaluation_teacher_trend(session, teacher_id, template_id=template_id)


@router.get("/adviser-quant/rules", response_model=list[AdviserQuantRuleVersionRead])
def list_rule_versions(session: Session = Depends(get_db_session)) -> list[AdviserQuantRuleVersionRead]:
    return service.list_adviser_rule_versions(session)


@router.post("/adviser-quant/rules", response_model=AdviserQuantRuleVersionRead)
def create_rule_version(
    payload: AdviserQuantRuleVersionPayload,
    session: Session = Depends(get_db_session),
) -> AdviserQuantRuleVersionRead:
    return service.create_adviser_rule_version(session, payload)


@router.put("/adviser-quant/rules/{rule_version_id}", response_model=AdviserQuantRuleVersionRead)
def update_rule_version(
    rule_version_id: int,
    payload: AdviserQuantRuleVersionPayload,
    session: Session = Depends(get_db_session),
) -> AdviserQuantRuleVersionRead:
    return service.update_adviser_rule_version(session, rule_version_id, payload)


@router.get("/adviser-quant/rules/{rule_version_id}/items", response_model=list[AdviserQuantRuleItemRead])
def list_rule_items(
    rule_version_id: int,
    session: Session = Depends(get_db_session),
) -> list[AdviserQuantRuleItemRead]:
    return service.list_adviser_rule_items(session, rule_version_id)


@router.post("/adviser-quant/rules/{rule_version_id}/items", response_model=list[AdviserQuantRuleItemRead])
def save_rule_items(
    rule_version_id: int,
    payload: list[AdviserQuantRuleItemPayload],
    session: Session = Depends(get_db_session),
) -> list[AdviserQuantRuleItemRead]:
    return service.save_adviser_rule_items(session, rule_version_id, payload)


@router.get("/adviser-quant/records", response_model=list[AdviserQuantRecordRead])
def list_records(
    semester_id: int | None = None,
    teacher_id: int | None = None,
    session: Session = Depends(get_db_session),
) -> list[AdviserQuantRecordRead]:
    return service.list_adviser_records(session, semester_id=semester_id, teacher_id=teacher_id)


@router.post("/adviser-quant/records", response_model=AdviserQuantRecordRead)
def create_record(
    payload: AdviserQuantRecordPayload,
    session: Session = Depends(get_db_session),
) -> AdviserQuantRecordRead:
    return service.create_adviser_record(session, payload)


@router.put("/adviser-quant/records/{record_id}", response_model=AdviserQuantRecordRead)
def update_record(
    record_id: int,
    payload: AdviserQuantRecordPayload,
    session: Session = Depends(get_db_session),
) -> AdviserQuantRecordRead:
    return service.update_adviser_record(session, record_id, payload)


@router.get("/adviser-quant/summary", response_model=list[AdviserQuantSummaryRead])
def list_summary(
    semester_id: int,
    rule_version_id: int | None = None,
    teacher_id: int | None = None,
    session: Session = Depends(get_db_session),
) -> list[AdviserQuantSummaryRead]:
    return service.list_adviser_summary(
        session,
        semester_id=semester_id,
        rule_version_id=rule_version_id,
        teacher_id=teacher_id,
    )
