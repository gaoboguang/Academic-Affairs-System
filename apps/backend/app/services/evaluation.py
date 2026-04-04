from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from statistics import mean

from fastapi import HTTPException
from sqlalchemy import delete, desc, select
from sqlalchemy.orm import Session, joinedload

from app.core.config import Settings
from app.importers.base import RowError, save_error_report
from app.importers.evaluation import EXPECTED_HEADERS, read_evaluation_rows
from app.models import (
    AdviserQuantRecord,
    AdviserQuantRecordAttachment,
    AdviserQuantRuleItem,
    AdviserQuantRuleVersion,
    ClassAdviserAssignment,
    EvaluationBatch,
    EvaluationQuestion,
    EvaluationResponse,
    EvaluationSummary,
    EvaluationTemplate,
    SchoolClass,
    Semester,
    StoredFile,
    Teacher,
)
from app.repositories.system import create_import_job, get_stored_file, write_audit_log
from app.schemas.archive import StoredFileRead
from app.schemas.common import ImportResult
from app.schemas.evaluation import (
    AdviserQuantRecordAttachmentRead,
    AdviserQuantRecordPayload,
    AdviserQuantRecordRead,
    AdviserQuantRuleItemPayload,
    AdviserQuantRuleItemRead,
    AdviserQuantRuleVersionPayload,
    AdviserQuantRuleVersionRead,
    AdviserQuantSummaryRead,
    EvaluationBatchCompareRead,
    EvaluationBatchCompareTeacherRead,
    EvaluationBatchOverviewRead,
    EvaluationBatchRead,
    EvaluationClassStatRead,
    EvaluationDimensionSummaryRead,
    EvaluationImportResponse,
    EvaluationQuestionRead,
    EvaluationQuestionStatRead,
    EvaluationTeacherDetailRead,
    EvaluationTeacherSummaryRead,
    EvaluationTeacherTrendPointRead,
    EvaluationTeacherTrendRead,
    EvaluationTemplatePayload,
    EvaluationTemplateRead,
)
from app.utils.parsers import clean_text


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
        .options(joinedload(EvaluationBatch.template), joinedload(EvaluationBatch.semester).joinedload(Semester.academic_year))
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


def list_evaluation_batches(session: Session, semester_id: int | None = None) -> list[EvaluationBatchRead]:
    query = (
        select(EvaluationBatch)
        .options(joinedload(EvaluationBatch.template), joinedload(EvaluationBatch.semester).joinedload(Semester.academic_year))
        .where(EvaluationBatch.is_active.is_(True))
        .order_by(desc(EvaluationBatch.import_time), desc(EvaluationBatch.id))
    )
    if semester_id:
        query = query.where(EvaluationBatch.semester_id == semester_id)
    items = session.scalars(query).unique().all()
    return [_serialize_batch(session, item) for item in items]


def import_evaluation_batch(
    session: Session,
    settings: Settings,
    *,
    template_id: int,
    semester_id: int,
    filename: str | None,
    content: bytes,
) -> EvaluationImportResponse:
    template = session.scalar(
        select(EvaluationTemplate)
        .options(joinedload(EvaluationTemplate.questions))
        .where(EvaluationTemplate.id == template_id)
    )
    semester = session.scalar(
        select(Semester)
        .options(joinedload(Semester.academic_year))
        .where(Semester.id == semester_id)
    )
    if not template:
        raise HTTPException(status_code=404, detail="评教模板不存在")
    if not semester:
        raise HTTPException(status_code=404, detail="学期不存在")

    batch = EvaluationBatch(
        template_id=template_id,
        semester_id=semester_id,
        source_filename=filename,
        import_time=datetime.now(),
        status="processing",
    )
    session.add(batch)
    session.flush()
    job = create_import_job(session, "evaluation", filename)
    job.started_at = datetime.now()

    headers, rows = read_evaluation_rows(filename, content)
    if headers[: len(EXPECTED_HEADERS)] != EXPECTED_HEADERS:
        raise HTTPException(status_code=400, detail="评教导入模板表头不匹配，请先下载系统模板。")

    question_map = {
        question.question_text: question
        for question in template.questions
        if question.is_active
    }
    teacher_map = {
        item.name: item
        for item in session.scalars(select(Teacher).where(Teacher.is_active.is_(True))).all()
    }
    class_map = {
        item.name: item
        for item in session.scalars(select(SchoolClass).where(SchoolClass.is_active.is_(True))).all()
    }

    success_rows = 0
    failed_rows = 0
    row_errors: list[RowError] = []

    for row_number, row in rows:
        try:
            template_name = clean_text(row.get("模板名称"))
            teacher_name = clean_text(row.get("教师"))
            class_name = clean_text(row.get("班级"))
            question_text = clean_text(row.get("题目"))
            respondent_type = clean_text(row.get("评价对象类型")) or "student"
            score = float(str(row.get("分值")).strip()) if row.get("分值") not in (None, "") else None

            if template_name and template_name != template.name:
                raise ValueError("模板名称与所选模板不一致")
            if not teacher_name or teacher_name not in teacher_map:
                raise ValueError("教师不存在")
            if not question_text or question_text not in question_map:
                raise ValueError("题目不存在")
            if score is None:
                raise ValueError("分值不能为空")

            teacher = teacher_map[teacher_name]
            question = question_map[question_text]
            school_class = class_map.get(class_name) if class_name else None
            if score < 0 or score > question.score_max:
                raise ValueError("分值超出题目最大分值")

            session.add(
                EvaluationResponse(
                    batch_id=batch.id,
                    teacher_id=teacher.id,
                    class_id=school_class.id if school_class else None,
                    question_id=question.id,
                    score=score,
                    respondent_type=respondent_type,
                    raw_json={
                        "template_name": template_name or template.name,
                        "teacher_name": teacher_name,
                        "class_name": class_name,
                        "question_text": question_text,
                        "score": score,
                        "respondent_type": respondent_type,
                    },
                )
            )
            success_rows += 1
        except Exception as exc:
            failed_rows += 1
            row_errors.append(RowError(row_number=row_number, values=row, message=str(exc)))

    error_report_path = save_error_report(
        settings=settings,
        prefix="evaluation_import_errors",
        headers=EXPECTED_HEADERS,
        errors=row_errors,
    )

    if success_rows == 0:
        batch.status = "failed"
        job.finished_at = datetime.now()
        job.status = "failed"
        job.result_json = {"batch_id": batch.id, "failed_rows": failed_rows, "error_report_path": error_report_path}
        raise HTTPException(status_code=400, detail="评教导入失败，未导入任何有效数据")

    session.flush()
    rebuild_evaluation_summary(session, batch.id)
    batch.status = "completed" if failed_rows == 0 else "partial_success"
    job.finished_at = datetime.now()
    job.status = batch.status
    job.result_json = {
        "batch_id": batch.id,
        "success_rows": success_rows,
        "failed_rows": failed_rows,
        "error_report_path": error_report_path,
    }
    write_audit_log(
        session,
        module="evaluation",
        action="import_batch",
        target_type="evaluation_batch",
        target_id=str(batch.id),
        detail_json=job.result_json,
    )
    return EvaluationImportResponse(
        batch_id=batch.id,
        total_rows=len(rows),
        success_rows=success_rows,
        failed_rows=failed_rows,
        skipped_rows=0,
        error_report_path=error_report_path,
        message=f"评教数据导入完成，成功 {success_rows} 条，失败 {failed_rows} 条。",
    )


def rebuild_evaluation_summary(session: Session, batch_id: int) -> None:
    batch = session.scalar(
        select(EvaluationBatch)
        .options(joinedload(EvaluationBatch.template).joinedload(EvaluationTemplate.questions))
        .where(EvaluationBatch.id == batch_id)
    )
    if not batch:
        raise HTTPException(status_code=404, detail="评教批次不存在")
    session.execute(delete(EvaluationSummary).where(EvaluationSummary.batch_id == batch_id))
    responses = _get_batch_responses(session, batch_id)
    if not responses:
        return

    for teacher_id, items in _group_by_teacher(responses).items():
        dimension_rows = _build_dimension_rows(items)
        overall_avg = _overall_average(items)
        session.add(
            EvaluationSummary(
                batch_id=batch_id,
                teacher_id=teacher_id,
                dimension_name="__overall__",
                avg_score=overall_avg,
                response_count=len(items),
                summary_json={
                    "dimension_scores": {row.dimension_name: row.avg_score for row in dimension_rows},
                },
            )
        )
        for row in dimension_rows:
            session.add(
                EvaluationSummary(
                    batch_id=batch_id,
                    teacher_id=teacher_id,
                    dimension_name=row.dimension_name,
                    avg_score=row.avg_score,
                    response_count=row.response_count,
                    summary_json={
                        "question_stats": [item.model_dump() for item in row.question_stats],
                        "class_stats": [item.model_dump() for item in row.class_stats],
                    },
                )
            )
    session.flush()


def get_evaluation_batch_overview(session: Session, batch_id: int) -> EvaluationBatchOverviewRead:
    batch = _load_batch(session, batch_id)
    summaries = session.scalars(
        select(EvaluationSummary)
        .options(joinedload(EvaluationSummary.teacher))
        .where(EvaluationSummary.batch_id == batch_id, EvaluationSummary.is_active.is_(True))
        .order_by(EvaluationSummary.teacher_id, EvaluationSummary.dimension_name)
    ).all()
    overview_rows = _build_teacher_summary_rows(summaries)
    return EvaluationBatchOverviewRead(
        batch_id=batch.id,
        template_name=batch.template.name if batch.template else "-",
        semester_name=_semester_name(batch.semester),
        teacher_count=len(overview_rows),
        teacher_summaries=overview_rows,
    )


def get_evaluation_batch_compare(session: Session, batch_id: int, compare_batch_id: int) -> EvaluationBatchCompareRead:
    if batch_id == compare_batch_id:
        raise HTTPException(status_code=400, detail="对比批次不能与当前批次相同")

    current_batch = _load_batch(session, batch_id)
    compare_batch = _load_batch(session, compare_batch_id)
    current_overview = get_evaluation_batch_overview(session, batch_id)
    compare_overview = get_evaluation_batch_overview(session, compare_batch_id)

    current_map = {item.teacher_id: item for item in current_overview.teacher_summaries}
    compare_map = {item.teacher_id: item for item in compare_overview.teacher_summaries}
    overlap_ids = sorted(set(current_map).intersection(compare_map))

    improved_count = 0
    declined_count = 0
    unchanged_count = 0
    teacher_deltas: list[EvaluationBatchCompareTeacherRead] = []

    for teacher_id in overlap_ids:
        current = current_map[teacher_id]
        compare = compare_map[teacher_id]
        score_delta = round(current.overall_avg_score - compare.overall_avg_score, 2)
        rank_delta = compare.rank - current.rank if current.rank and compare.rank else None
        if score_delta > 0.01:
            improved_count += 1
        elif score_delta < -0.01:
            declined_count += 1
        else:
            unchanged_count += 1
        teacher_deltas.append(
            EvaluationBatchCompareTeacherRead(
                teacher_id=teacher_id,
                teacher_name=current.teacher_name,
                current_score=current.overall_avg_score,
                compare_score=compare.overall_avg_score,
                score_delta=score_delta,
                current_rank=current.rank,
                compare_rank=compare.rank,
                rank_delta=rank_delta,
                response_count_delta=current.response_count - compare.response_count,
            )
        )

    teacher_deltas.sort(key=lambda item: (item.score_delta, item.current_score), reverse=True)
    return EvaluationBatchCompareRead(
        batch_id=batch_id,
        compare_batch_id=compare_batch_id,
        batch_name=_batch_display_name(current_batch),
        compare_batch_name=_batch_display_name(compare_batch),
        overlap_teacher_count=len(overlap_ids),
        improved_count=improved_count,
        declined_count=declined_count,
        unchanged_count=unchanged_count,
        only_current_count=len(set(current_map).difference(compare_map)),
        only_compare_count=len(set(compare_map).difference(current_map)),
        teacher_deltas=teacher_deltas,
    )


def get_evaluation_teacher_detail(session: Session, batch_id: int, teacher_id: int) -> EvaluationTeacherDetailRead:
    overview = get_evaluation_batch_overview(session, batch_id)
    teacher_summary = next((item for item in overview.teacher_summaries if item.teacher_id == teacher_id), None)
    if not teacher_summary:
        raise HTTPException(status_code=404, detail="当前评教批次下未找到教师数据")

    summaries = session.scalars(
        select(EvaluationSummary)
        .where(
            EvaluationSummary.batch_id == batch_id,
            EvaluationSummary.teacher_id == teacher_id,
            EvaluationSummary.is_active.is_(True),
            EvaluationSummary.dimension_name != "__overall__",
        )
        .order_by(EvaluationSummary.dimension_name)
    ).all()
    dimension_rows: list[EvaluationDimensionSummaryRead] = []
    question_rows: list[EvaluationQuestionStatRead] = []
    class_rows_map: dict[tuple[int | None, str | None], list[float]] = defaultdict(list)

    for item in summaries:
        dimension_rows.append(
            EvaluationDimensionSummaryRead(
                dimension_name=item.dimension_name,
                avg_score=round(item.avg_score, 2),
                response_count=item.response_count,
            )
        )
        for question_stat in item.summary_json.get("question_stats", []) if item.summary_json else []:
            question_rows.append(EvaluationQuestionStatRead.model_validate(question_stat))
        for class_stat in item.summary_json.get("class_stats", []) if item.summary_json else []:
            key = (class_stat.get("class_id"), class_stat.get("class_name"))
            class_rows_map[key].append(float(class_stat.get("avg_score") or 0))

    class_rows = [
        EvaluationClassStatRead(
            class_id=class_id,
            class_name=class_name,
            avg_score=round(mean(scores), 2),
            response_count=len(scores),
        )
        for (class_id, class_name), scores in class_rows_map.items()
    ]
    class_rows.sort(key=lambda item: item.class_name or "")
    question_rows.sort(key=lambda item: (item.dimension_name, item.question_text))

    return EvaluationTeacherDetailRead(
        batch_id=batch_id,
        teacher_id=teacher_id,
        teacher_name=teacher_summary.teacher_name,
        overall_avg_score=teacher_summary.overall_avg_score,
        response_count=teacher_summary.response_count,
        dimension_summaries=dimension_rows,
        question_stats=question_rows,
        class_stats=class_rows,
    )


def get_evaluation_teacher_trend(
    session: Session,
    teacher_id: int,
    *,
    template_id: int | None = None,
) -> EvaluationTeacherTrendRead:
    teacher = session.get(Teacher, teacher_id)
    if not teacher:
        raise HTTPException(status_code=404, detail="教师不存在")

    query = (
        select(EvaluationSummary)
        .join(EvaluationBatch, EvaluationSummary.batch_id == EvaluationBatch.id)
        .options(
            joinedload(EvaluationSummary.batch).joinedload(EvaluationBatch.template),
            joinedload(EvaluationSummary.batch).joinedload(EvaluationBatch.semester).joinedload(Semester.academic_year),
        )
        .where(
            EvaluationSummary.teacher_id == teacher_id,
            EvaluationSummary.dimension_name == "__overall__",
            EvaluationSummary.is_active.is_(True),
            EvaluationBatch.is_active.is_(True),
        )
        .order_by(EvaluationBatch.import_time, EvaluationBatch.id)
    )
    if template_id:
        query = query.where(EvaluationBatch.template_id == template_id)
    summaries = session.scalars(query).all()
    if not summaries:
        return EvaluationTeacherTrendRead(teacher_id=teacher_id, teacher_name=teacher.name, points=[])

    batch_ids = [item.batch_id for item in summaries]
    all_batch_summaries = session.scalars(
        select(EvaluationSummary)
        .options(joinedload(EvaluationSummary.teacher))
        .where(
            EvaluationSummary.batch_id.in_(batch_ids),
            EvaluationSummary.dimension_name == "__overall__",
            EvaluationSummary.is_active.is_(True),
        )
        .order_by(EvaluationSummary.batch_id, EvaluationSummary.teacher_id)
    ).all()
    summaries_by_batch: dict[int, list[EvaluationSummary]] = defaultdict(list)
    for item in all_batch_summaries:
        summaries_by_batch[item.batch_id].append(item)

    rank_by_batch: dict[int, int | None] = {}
    for batch_id_key, batch_summaries in summaries_by_batch.items():
        rows = _build_teacher_summary_rows(batch_summaries)
        teacher_row = next((row for row in rows if row.teacher_id == teacher_id), None)
        rank_by_batch[batch_id_key] = teacher_row.rank if teacher_row else None

    points = [
        EvaluationTeacherTrendPointRead(
            batch_id=item.batch_id,
            template_name=item.batch.template.name if item.batch and item.batch.template else "-",
            semester_name=_semester_name(item.batch.semester) if item.batch else None,
            overall_avg_score=round(item.avg_score, 2),
            response_count=item.response_count,
            rank=rank_by_batch.get(item.batch_id),
            import_time=item.batch.import_time if item.batch else datetime.now(),
        )
        for item in summaries
    ]
    return EvaluationTeacherTrendRead(teacher_id=teacher_id, teacher_name=teacher.name, points=points)


@dataclass
class _DimensionBuildResult:
    dimension_name: str
    avg_score: float
    response_count: int
    question_stats: list[EvaluationQuestionStatRead]
    class_stats: list[EvaluationClassStatRead]


class _DimensionAggregate:
    def __init__(self, dimension_name: str) -> None:
        self.dimension_name = dimension_name
        self.scores: list[float] = []
        self.question_scores: dict[str, list[float]] = defaultdict(list)
        self.question_dimension: dict[str, str] = {}
        self.class_scores: dict[tuple[int | None, str | None], list[float]] = defaultdict(list)

    def build(self) -> _DimensionBuildResult:
        question_stats = [
            EvaluationQuestionStatRead(
                question_text=question_text,
                dimension_name=self.question_dimension[question_text],
                avg_score=round(mean(values), 2),
                response_count=len(values),
            )
            for question_text, values in self.question_scores.items()
        ]
        question_stats.sort(key=lambda item: item.question_text)
        class_stats = [
            EvaluationClassStatRead(
                class_id=class_id,
                class_name=class_name,
                avg_score=round(mean(values), 2),
                response_count=len(values),
            )
            for (class_id, class_name), values in self.class_scores.items()
        ]
        class_stats.sort(key=lambda item: item.class_name or "")
        return _DimensionBuildResult(
            dimension_name=self.dimension_name,
            avg_score=round(mean(self.scores), 2),
            response_count=len(self.scores),
            question_stats=question_stats,
            class_stats=class_stats,
        )


def _get_batch_responses(session: Session, batch_id: int) -> list[EvaluationResponse]:
    return session.scalars(
        select(EvaluationResponse)
        .options(
            joinedload(EvaluationResponse.teacher),
            joinedload(EvaluationResponse.school_class),
            joinedload(EvaluationResponse.question),
        )
        .where(EvaluationResponse.batch_id == batch_id, EvaluationResponse.is_active.is_(True))
        .order_by(EvaluationResponse.teacher_id, EvaluationResponse.id)
    ).unique().all()


def _group_by_teacher(responses: list[EvaluationResponse]) -> dict[int, list[EvaluationResponse]]:
    grouped: dict[int, list[EvaluationResponse]] = defaultdict(list)
    for item in responses:
        grouped[item.teacher_id].append(item)
    return grouped


def _normalized_score(response: EvaluationResponse) -> float:
    score_max = response.question.score_max if response.question else 0
    if score_max <= 0:
        return response.score
    return round(response.score / score_max * 100, 2)


def _overall_average(items: list[EvaluationResponse]) -> float:
    weighted_scores: list[float] = []
    weights: list[float] = []
    for item in items:
        weight = item.question.weight if item.question else 1.0
        weighted_scores.append(_normalized_score(item))
        weights.append(weight)
    if not weighted_scores:
        return 0.0
    numerator = sum(score * weight for score, weight in zip(weighted_scores, weights, strict=False))
    denominator = sum(weights) or len(weighted_scores)
    return round(numerator / denominator, 2)


def _build_dimension_rows(items: list[EvaluationResponse]) -> list[_DimensionBuildResult]:
    grouped: dict[str, _DimensionAggregate] = {}
    for item in items:
        if not item.question:
            continue
        dimension_name = item.question.dimension_name
        aggregate = grouped.setdefault(dimension_name, _DimensionAggregate(dimension_name))
        normalized = _normalized_score(item)
        aggregate.scores.append(normalized)
        aggregate.question_scores[item.question.question_text].append(normalized)
        aggregate.question_dimension[item.question.question_text] = dimension_name
        aggregate.class_scores[(item.class_id, item.school_class.name if item.school_class else None)].append(normalized)
    rows = [aggregate.build() for aggregate in grouped.values()]
    rows.sort(key=lambda item: item.dimension_name)
    return rows


def _assign_competition_rank(rows: list[EvaluationTeacherSummaryRead]) -> None:
    last_score: float | None = None
    last_rank = 0
    for index, item in enumerate(rows, start=1):
        if last_score is None or item.overall_avg_score < last_score:
            last_rank = index
            last_score = item.overall_avg_score
        item.rank = last_rank


def _build_teacher_summary_rows(summaries: list[EvaluationSummary]) -> list[EvaluationTeacherSummaryRead]:
    grouped: dict[int, dict[str, EvaluationSummary]] = defaultdict(dict)
    for item in summaries:
        grouped[item.teacher_id][item.dimension_name] = item

    overview_rows: list[EvaluationTeacherSummaryRead] = []
    for teacher_id, summary_map in grouped.items():
        overall = summary_map.get("__overall__")
        teacher = overall.teacher if overall else None
        if not overall or not teacher:
            continue
        dimension_scores = {
            key: round(value.avg_score, 2)
            for key, value in summary_map.items()
            if key != "__overall__"
        }
        overview_rows.append(
            EvaluationTeacherSummaryRead(
                teacher_id=teacher_id,
                teacher_name=teacher.name,
                overall_avg_score=round(overall.avg_score, 2),
                response_count=overall.response_count,
                dimension_scores_json=dimension_scores or None,
            )
        )
    overview_rows.sort(key=lambda item: item.overall_avg_score, reverse=True)
    _assign_competition_rank(overview_rows)
    return overview_rows


def list_adviser_rule_versions(session: Session) -> list[AdviserQuantRuleVersionRead]:
    ensure_default_adviser_rule_version(session)
    items = session.scalars(
        select(AdviserQuantRuleVersion)
        .options(joinedload(AdviserQuantRuleVersion.semester).joinedload(Semester.academic_year))
        .where(AdviserQuantRuleVersion.is_active.is_(True))
        .order_by(desc(AdviserQuantRuleVersion.id))
    ).unique().all()
    return [_serialize_rule_version(item) for item in items]


def create_adviser_rule_version(session: Session, payload: AdviserQuantRuleVersionPayload) -> AdviserQuantRuleVersionRead:
    if payload.semester_id and not session.get(Semester, payload.semester_id):
        raise HTTPException(status_code=404, detail="学期不存在")
    if payload.is_default:
        for item in session.scalars(select(AdviserQuantRuleVersion).where(AdviserQuantRuleVersion.is_default.is_(True))).all():
            item.is_default = False
    version = AdviserQuantRuleVersion(**payload.model_dump())
    session.add(version)
    session.flush()
    write_audit_log(
        session,
        module="adviser_quant",
        action="create_rule_version",
        target_type="rule_version",
        target_id=str(version.id),
    )
    session.refresh(version)
    return _serialize_rule_version(version)


def update_adviser_rule_version(
    session: Session,
    rule_version_id: int,
    payload: AdviserQuantRuleVersionPayload,
) -> AdviserQuantRuleVersionRead:
    version = session.scalar(
        select(AdviserQuantRuleVersion)
        .options(joinedload(AdviserQuantRuleVersion.semester).joinedload(Semester.academic_year))
        .where(AdviserQuantRuleVersion.id == rule_version_id)
    )
    if not version:
        raise HTTPException(status_code=404, detail="量化规则版本不存在")
    if payload.semester_id and not session.get(Semester, payload.semester_id):
        raise HTTPException(status_code=404, detail="学期不存在")
    if payload.is_default:
        for item in session.scalars(select(AdviserQuantRuleVersion).where(AdviserQuantRuleVersion.is_default.is_(True))).all():
            item.is_default = False
    for key, value in payload.model_dump().items():
        setattr(version, key, value)
    session.flush()
    write_audit_log(
        session,
        module="adviser_quant",
        action="update_rule_version",
        target_type="rule_version",
        target_id=str(version.id),
    )
    session.refresh(version)
    return _serialize_rule_version(version)


def list_adviser_rule_items(session: Session, rule_version_id: int) -> list[AdviserQuantRuleItemRead]:
    version = session.scalar(
        select(AdviserQuantRuleVersion)
        .options(joinedload(AdviserQuantRuleVersion.items))
        .where(AdviserQuantRuleVersion.id == rule_version_id)
    )
    if not version:
        raise HTTPException(status_code=404, detail="量化规则版本不存在")
    items = sorted((item for item in version.items if item.is_active), key=lambda item: (item.sort_order, item.id))
    return [_serialize_rule_item(item) for item in items]


def save_adviser_rule_items(
    session: Session,
    rule_version_id: int,
    payload: list[AdviserQuantRuleItemPayload],
) -> list[AdviserQuantRuleItemRead]:
    version = session.scalar(
        select(AdviserQuantRuleVersion)
        .options(joinedload(AdviserQuantRuleVersion.items))
        .where(AdviserQuantRuleVersion.id == rule_version_id)
    )
    if not version:
        raise HTTPException(status_code=404, detail="量化规则版本不存在")
    record_count = session.scalar(
        select(AdviserQuantRecord.id)
        .join(AdviserQuantRuleItem, AdviserQuantRecord.rule_item_id == AdviserQuantRuleItem.id)
        .where(AdviserQuantRuleItem.rule_version_id == rule_version_id)
        .limit(1)
    )
    if record_count:
        raise HTTPException(status_code=400, detail="该规则版本已有量化记录，不能原地修改规则项")

    version.items.clear()
    session.flush()
    for item in sorted(payload, key=lambda current: (current.sort_order, current.item_name)):
        version.items.append(
            AdviserQuantRuleItem(
                item_name=item.item_name.strip(),
                item_type=item.item_type.strip(),
                default_score=item.default_score,
                requires_attachment=item.requires_attachment,
                note=item.note,
                sort_order=item.sort_order,
                is_active=item.is_active,
            )
        )
    session.flush()
    write_audit_log(
        session,
        module="adviser_quant",
        action="save_rule_items",
        target_type="rule_version",
        target_id=str(rule_version_id),
        detail_json={"item_count": len(payload)},
    )
    session.refresh(version)
    return [_serialize_rule_item(item) for item in sorted(version.items, key=lambda current: (current.sort_order, current.id))]


def list_adviser_records(
    session: Session,
    *,
    semester_id: int | None = None,
    teacher_id: int | None = None,
) -> list[AdviserQuantRecordRead]:
    query = (
        select(AdviserQuantRecord)
        .options(
            joinedload(AdviserQuantRecord.teacher),
            joinedload(AdviserQuantRecord.school_class),
            joinedload(AdviserQuantRecord.semester).joinedload(Semester.academic_year),
            joinedload(AdviserQuantRecord.rule_item).joinedload(AdviserQuantRuleItem.rule_version).joinedload(AdviserQuantRuleVersion.semester),
            joinedload(AdviserQuantRecord.attachments).joinedload(AdviserQuantRecordAttachment.stored_file),
        )
        .where(AdviserQuantRecord.is_active.is_(True))
        .order_by(desc(AdviserQuantRecord.record_month), desc(AdviserQuantRecord.recorded_at), desc(AdviserQuantRecord.id))
    )
    if semester_id:
        query = query.where(AdviserQuantRecord.semester_id == semester_id)
    if teacher_id:
        query = query.where(AdviserQuantRecord.teacher_id == teacher_id)
    items = session.scalars(query).unique().all()
    return [_serialize_quant_record(item) for item in items]


def create_adviser_record(session: Session, payload: AdviserQuantRecordPayload) -> AdviserQuantRecordRead:
    record = AdviserQuantRecord()
    session.add(record)
    _apply_adviser_record_payload(session, record, payload)
    session.flush()
    write_audit_log(
        session,
        module="adviser_quant",
        action="create_record",
        target_type="adviser_quant_record",
        target_id=str(record.id),
    )
    session.refresh(record)
    return _serialize_quant_record(record)


def update_adviser_record(session: Session, record_id: int, payload: AdviserQuantRecordPayload) -> AdviserQuantRecordRead:
    record = session.scalar(
        select(AdviserQuantRecord)
        .options(joinedload(AdviserQuantRecord.attachments))
        .where(AdviserQuantRecord.id == record_id)
    )
    if not record:
        raise HTTPException(status_code=404, detail="量化记录不存在")
    _apply_adviser_record_payload(session, record, payload)
    session.flush()
    write_audit_log(
        session,
        module="adviser_quant",
        action="update_record",
        target_type="adviser_quant_record",
        target_id=str(record.id),
    )
    session.refresh(record)
    return _serialize_quant_record(record)


def _apply_adviser_record_payload(session: Session, record: AdviserQuantRecord, payload: AdviserQuantRecordPayload) -> None:
    teacher = session.get(Teacher, payload.teacher_id)
    semester = session.get(Semester, payload.semester_id)
    rule_item = session.scalar(
        select(AdviserQuantRuleItem)
        .options(joinedload(AdviserQuantRuleItem.rule_version).joinedload(AdviserQuantRuleVersion.semester).joinedload(Semester.academic_year))
        .where(AdviserQuantRuleItem.id == payload.rule_item_id)
    )
    school_class = session.get(SchoolClass, payload.class_id) if payload.class_id else None
    if not teacher:
        raise HTTPException(status_code=404, detail="教师不存在")
    if not semester:
        raise HTTPException(status_code=404, detail="学期不存在")
    if not rule_item:
        raise HTTPException(status_code=404, detail="量化规则项不存在")
    if payload.class_id and not school_class:
        raise HTTPException(status_code=404, detail="班级不存在")
    if len(payload.record_month) != 7 or payload.record_month[4] != "-":
        raise HTTPException(status_code=400, detail="记录月份格式应为 YYYY-MM")
    if rule_item.requires_attachment and not payload.attachment_file_ids:
        raise HTTPException(status_code=400, detail="该量化项必须上传附件")

    if school_class:
        assignment = session.scalar(
            select(ClassAdviserAssignment).where(
                ClassAdviserAssignment.teacher_id == teacher.id,
                ClassAdviserAssignment.class_id == school_class.id,
                ClassAdviserAssignment.is_active.is_(True),
            )
        )
        if assignment is None and school_class.head_teacher_id not in (None, teacher.id):
            raise HTTPException(status_code=400, detail="当前教师不是该班的班主任或班主任记录未维护")

    record.teacher_id = teacher.id
    record.class_id = school_class.id if school_class else None
    record.semester_id = semester.id
    record.rule_item_id = rule_item.id
    record.record_month = payload.record_month
    record.score = payload.score if payload.score is not None else rule_item.default_score
    record.description = payload.description
    record.snapshot_json = {
        "item_name": rule_item.item_name,
        "item_type": rule_item.item_type,
        "default_score": rule_item.default_score,
        "requires_attachment": rule_item.requires_attachment,
        "rule_version_id": rule_item.rule_version_id,
    }
    record.is_active = payload.is_active
    record.attachments.clear()
    session.flush()
    for file_id in payload.attachment_file_ids:
        stored_file = get_stored_file(session, file_id)
        if not stored_file or not stored_file.is_active:
            raise HTTPException(status_code=404, detail=f"附件不存在: {file_id}")
        record.attachments.append(AdviserQuantRecordAttachment(stored_file_id=file_id))
    session.flush()


def list_adviser_summary(
    session: Session,
    *,
    semester_id: int,
    rule_version_id: int | None = None,
    teacher_id: int | None = None,
) -> list[AdviserQuantSummaryRead]:
    semester = session.scalar(
        select(Semester)
        .options(joinedload(Semester.academic_year))
        .where(Semester.id == semester_id)
    )
    if not semester:
        raise HTTPException(status_code=404, detail="学期不存在")
    records = session.scalars(
        select(AdviserQuantRecord)
        .options(
            joinedload(AdviserQuantRecord.teacher),
            joinedload(AdviserQuantRecord.school_class),
            joinedload(AdviserQuantRecord.rule_item).joinedload(AdviserQuantRuleItem.rule_version).joinedload(AdviserQuantRuleVersion.semester),
        )
        .where(
            AdviserQuantRecord.semester_id == semester_id,
            AdviserQuantRecord.is_active.is_(True),
        )
        .order_by(AdviserQuantRecord.teacher_id, AdviserQuantRecord.id)
    ).unique().all()

    filtered: list[AdviserQuantRecord] = []
    for record in records:
        if teacher_id and record.teacher_id != teacher_id:
            continue
        if rule_version_id and record.rule_item and record.rule_item.rule_version_id != rule_version_id:
            continue
        filtered.append(record)

    grouped: dict[int, list[AdviserQuantRecord]] = defaultdict(list)
    for item in filtered:
        grouped[item.teacher_id].append(item)

    rows: list[AdviserQuantSummaryRead] = []
    for items in grouped.values():
        first = items[0]
        category_scores: dict[str, float] = defaultdict(float)
        class_names = sorted({item.school_class.name for item in items if item.school_class})
        positive_score = 0.0
        negative_score = 0.0
        for item in items:
            snapshot = item.snapshot_json or {}
            item_type = item.rule_item.item_type if item.rule_item else snapshot.get("item_type", "unknown")
            category_scores[item_type] += item.score
            if item.score >= 0:
                positive_score += item.score
            else:
                negative_score += item.score
        version = first.rule_item.rule_version if first.rule_item else None
        rows.append(
            AdviserQuantSummaryRead(
                teacher_id=first.teacher_id,
                teacher_name=first.teacher.name if first.teacher else str(first.teacher_id),
                semester_id=semester.id,
                semester_name=_semester_name(semester),
                rule_version_id=version.id if version else None,
                rule_version_name=version.name if version else None,
                total_score=round(sum(item.score for item in items), 2),
                positive_score=round(positive_score, 2),
                negative_score=round(negative_score, 2),
                record_count=len(items),
                class_names=class_names,
                category_scores_json={key: round(value, 2) for key, value in category_scores.items()},
            )
        )
    rows.sort(key=lambda item: item.total_score, reverse=True)
    return rows
