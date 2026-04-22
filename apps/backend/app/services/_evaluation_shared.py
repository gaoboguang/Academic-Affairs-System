from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models import (
    AdviserQuantRecord,
    AdviserQuantRecordAttachment,
    AdviserQuantRuleItem,
    AdviserQuantRuleVersion,
    EvaluationBatch,
    EvaluationQuestion,
    EvaluationResponse,
    EvaluationTemplate,
    Semester,
    StoredFile,
)
from app.repositories.system import get_stored_file
from app.schemas.archive import StoredFileRead
from app.schemas.evaluation import (
    AdviserQuantRecordAttachmentRead,
    AdviserQuantRecordRead,
    AdviserQuantRuleItemRead,
    AdviserQuantRuleVersionRead,
    EvaluationBatchRead,
    EvaluationQuestionRead,
    EvaluationTemplateRead,
)


DEFAULT_TEMPLATE = {
    "name": "通用课堂评教模板",
    "target_type": "teacher",
    "weight_json": {
        "教学设计": 0.35,
        "课堂组织": 0.35,
        "反馈支持": 0.30,
    },
    "questions": [
        ("教学设计", "教学目标清晰，重难点明确", 5.0, 1.0, 1),
        ("课堂组织", "课堂节奏合理，互动有效", 5.0, 1.0, 2),
        ("反馈支持", "作业讲评及时，反馈有针对性", 5.0, 1.0, 3),
    ],
}

DEFAULT_ADVISER_RULE_ITEMS = [
    ("班级常规管理", "daily_management", 5.0, False, "常规管理表现"),
    ("卫生纪律", "discipline", 3.0, False, "卫生与纪律检查"),
    ("家校沟通", "home_school", 4.0, True, "家访、沟通、回访记录"),
    ("活动组织", "activity", 4.0, True, "活动组织及总结"),
    ("学生发展指导", "guidance", 3.0, False, "个别辅导与成长跟踪"),
    ("特殊加分项", "bonus", 2.0, True, "额外加分事项"),
    ("扣分项", "penalty", -2.0, True, "违纪或管理失误扣分"),
]


def _semester_name(item: Semester | None) -> str | None:
    if not item:
        return None
    if item.academic_year:
        return f"{item.academic_year.name} {item.name}"
    return item.name


def _batch_display_name(item: EvaluationBatch) -> str:
    template_name = item.template.name if item.template else "评教批次"
    semester_name = _semester_name(item.semester)
    if semester_name:
        return f"{template_name} · {semester_name}"
    return template_name


def _load_batch(session: Session, batch_id: int) -> EvaluationBatch:
    batch = session.scalar(
        select(EvaluationBatch)
        .options(
            joinedload(EvaluationBatch.template),
            joinedload(EvaluationBatch.semester).joinedload(Semester.academic_year),
        )
        .where(EvaluationBatch.id == batch_id)
    )
    if not batch:
        raise HTTPException(status_code=404, detail="评教批次不存在")
    return batch


def _serialize_file(item: StoredFile) -> StoredFileRead:
    return StoredFileRead(
        id=item.id,
        original_filename=item.original_filename,
        file_path=item.file_path,
        content_type=item.content_type,
        file_size=item.file_size,
        category=item.category,
        created_at=item.created_at,
        download_url=f"/api/files/{item.id}",
    )


def _serialize_template(item: EvaluationTemplate) -> EvaluationTemplateRead:
    questions = sorted(
        (question for question in item.questions if question.is_active),
        key=lambda question: (question.sort_order, question.id),
    )
    return EvaluationTemplateRead(
        id=item.id,
        name=item.name,
        target_type=item.target_type,
        weight_json=item.weight_json,
        is_active=item.is_active,
        questions=[EvaluationQuestionRead.model_validate(question) for question in questions],
    )


def _serialize_batch(session: Session, item: EvaluationBatch) -> EvaluationBatchRead:
    responses = session.scalars(
        select(EvaluationResponse.teacher_id).where(
            EvaluationResponse.batch_id == item.id,
            EvaluationResponse.is_active.is_(True),
        )
    ).all()
    return EvaluationBatchRead(
        id=item.id,
        template_id=item.template_id,
        template_name=item.template.name if item.template else None,
        semester_id=item.semester_id,
        semester_name=_semester_name(item.semester),
        source_filename=item.source_filename,
        import_time=item.import_time,
        status=item.status,
        response_count=len(responses),
        teacher_count=len(set(responses)),
        is_active=item.is_active,
    )


def _serialize_rule_version(item: AdviserQuantRuleVersion) -> AdviserQuantRuleVersionRead:
    return AdviserQuantRuleVersionRead(
        id=item.id,
        name=item.name,
        semester_id=item.semester_id,
        semester_name=_semester_name(item.semester),
        is_default=item.is_default,
        status=item.status,
        note=item.note,
        is_active=item.is_active,
    )


def _serialize_rule_item(item: AdviserQuantRuleItem) -> AdviserQuantRuleItemRead:
    return AdviserQuantRuleItemRead.model_validate(item)


def _serialize_quant_attachment(item: AdviserQuantRecordAttachment) -> AdviserQuantRecordAttachmentRead:
    return AdviserQuantRecordAttachmentRead(
        id=item.id,
        stored_file_id=item.stored_file_id,
        note=item.note,
        file=_serialize_file(item.stored_file),
    )


def _serialize_quant_record(item: AdviserQuantRecord) -> AdviserQuantRecordRead:
    snapshot = item.snapshot_json or {}
    return AdviserQuantRecordRead(
        id=item.id,
        teacher_id=item.teacher_id,
        teacher_name=item.teacher.name if item.teacher else None,
        class_id=item.class_id,
        class_name=item.school_class.name if item.school_class else None,
        semester_id=item.semester_id,
        semester_name=_semester_name(item.semester),
        rule_version_id=item.rule_item.rule_version_id if item.rule_item else 0,
        rule_version_name=item.rule_item.rule_version.name if item.rule_item and item.rule_item.rule_version else None,
        rule_item_id=item.rule_item_id,
        item_name=item.rule_item.item_name if item.rule_item else snapshot.get("item_name", "-"),
        item_type=item.rule_item.item_type if item.rule_item else snapshot.get("item_type", "-"),
        record_month=item.record_month,
        score=item.score,
        requires_attachment=item.rule_item.requires_attachment if item.rule_item else bool(snapshot.get("requires_attachment")),
        description=item.description,
        recorded_at=item.recorded_at,
        is_active=item.is_active,
        attachments=[_serialize_quant_attachment(attachment) for attachment in item.attachments if attachment.is_active],
    )


def ensure_default_evaluation_template(session: Session) -> EvaluationTemplate:
    existing = session.scalar(
        select(EvaluationTemplate)
        .options(joinedload(EvaluationTemplate.questions))
        .order_by(EvaluationTemplate.id)
    )
    if existing:
        return existing
    template = EvaluationTemplate(
        name=DEFAULT_TEMPLATE["name"],
        target_type=DEFAULT_TEMPLATE["target_type"],
        weight_json=DEFAULT_TEMPLATE["weight_json"],
        is_active=True,
    )
    session.add(template)
    session.flush()
    for dimension_name, question_text, score_max, weight, sort_order in DEFAULT_TEMPLATE["questions"]:
        session.add(
            EvaluationQuestion(
                template_id=template.id,
                dimension_name=dimension_name,
                question_text=question_text,
                score_max=score_max,
                weight=weight,
                sort_order=sort_order,
            )
        )
    session.flush()
    session.refresh(template)
    return template


def ensure_default_adviser_rule_version(session: Session) -> AdviserQuantRuleVersion:
    existing = session.scalar(
        select(AdviserQuantRuleVersion)
        .options(joinedload(AdviserQuantRuleVersion.items))
        .where(AdviserQuantRuleVersion.is_default.is_(True), AdviserQuantRuleVersion.is_active.is_(True))
    )
    if existing:
        return existing
    version = AdviserQuantRuleVersion(
        name="默认班主任量化规则",
        semester_id=None,
        is_default=True,
        status="active",
        note="系统初始化生成",
    )
    session.add(version)
    session.flush()
    for sort_order, (item_name, item_type, default_score, requires_attachment, note) in enumerate(
        DEFAULT_ADVISER_RULE_ITEMS,
        start=1,
    ):
        session.add(
            AdviserQuantRuleItem(
                rule_version_id=version.id,
                item_name=item_name,
                item_type=item_type,
                default_score=default_score,
                requires_attachment=requires_attachment,
                note=note,
                sort_order=sort_order,
            )
        )
    session.flush()
    session.refresh(version)
    return version
