from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models import EvaluationQuestion, EvaluationTemplate
from app.repositories.system import write_audit_log
from app.schemas.evaluation import EvaluationTemplatePayload, EvaluationTemplateRead

from ._evaluation_shared import _serialize_template, ensure_default_evaluation_template


def list_evaluation_templates(session: Session) -> list[EvaluationTemplateRead]:
    ensure_default_evaluation_template(session)
    items = session.scalars(
        select(EvaluationTemplate)
        .options(joinedload(EvaluationTemplate.questions))
        .where(EvaluationTemplate.is_active.is_(True))
        .order_by(EvaluationTemplate.id)
    ).unique().all()
    return [_serialize_template(item) for item in items]


def create_evaluation_template(session: Session, payload: EvaluationTemplatePayload) -> EvaluationTemplateRead:
    existing = session.scalar(select(EvaluationTemplate).where(EvaluationTemplate.name == payload.name.strip()))
    if existing:
        raise HTTPException(status_code=400, detail="评教模板名称已存在")
    template = EvaluationTemplate()
    session.add(template)
    session.flush()
    _apply_template_payload(template, payload)
    session.flush()
    write_audit_log(
        session,
        module="evaluation",
        action="create_template",
        target_type="evaluation_template",
        target_id=str(template.id),
    )
    session.refresh(template)
    return _serialize_template(template)


def update_evaluation_template(session: Session, template_id: int, payload: EvaluationTemplatePayload) -> EvaluationTemplateRead:
    template = session.scalar(
        select(EvaluationTemplate)
        .options(joinedload(EvaluationTemplate.questions), joinedload(EvaluationTemplate.batches))
        .where(EvaluationTemplate.id == template_id)
    )
    if not template:
        raise HTTPException(status_code=404, detail="评教模板不存在")
    existing = session.scalar(select(EvaluationTemplate).where(EvaluationTemplate.name == payload.name.strip()))
    if existing and existing.id != template_id:
        raise HTTPException(status_code=400, detail="评教模板名称已存在")
    if template.batches:
        raise HTTPException(status_code=400, detail="模板已有导入批次，请新建模板以保留历史")
    _apply_template_payload(template, payload)
    session.flush()
    write_audit_log(
        session,
        module="evaluation",
        action="update_template",
        target_type="evaluation_template",
        target_id=str(template.id),
    )
    session.refresh(template)
    return _serialize_template(template)


def _apply_template_payload(template: EvaluationTemplate, payload: EvaluationTemplatePayload) -> None:
    template.name = payload.name.strip()
    template.target_type = payload.target_type.strip()
    template.weight_json = payload.weight_json
    template.is_active = payload.is_active
    template.questions.clear()
    for question in sorted(payload.questions, key=lambda item: (item.sort_order, item.question_text)):
        template.questions.append(
            EvaluationQuestion(
                dimension_name=question.dimension_name.strip(),
                question_text=question.question_text.strip(),
                score_max=question.score_max,
                weight=question.weight,
                sort_order=question.sort_order,
                is_active=question.is_active,
            )
        )
