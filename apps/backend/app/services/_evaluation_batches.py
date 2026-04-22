from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from statistics import mean

from fastapi import HTTPException
from sqlalchemy import delete, desc, select
from sqlalchemy.orm import Session, joinedload

from app.core.config import Settings
from app.importers.base import RowError, save_error_report
from app.importers.evaluation import EXPECTED_HEADERS, read_evaluation_rows
from app.models import (
    EvaluationBatch,
    EvaluationResponse,
    EvaluationSummary,
    EvaluationTemplate,
    SchoolClass,
    Semester,
    Teacher,
)
from app.repositories.system import create_import_job, write_audit_log
from app.schemas.evaluation import (
    EvaluationBatchCompareRead,
    EvaluationBatchCompareTeacherRead,
    EvaluationBatchOverviewRead,
    EvaluationBatchRead,
    EvaluationClassStatRead,
    EvaluationDimensionSummaryRead,
    EvaluationImportResponse,
    EvaluationQuestionStatRead,
    EvaluationTeacherDetailRead,
    EvaluationTeacherSummaryRead,
    EvaluationTeacherTrendPointRead,
    EvaluationTeacherTrendRead,
)
from app.utils.parsers import clean_text

from ._evaluation_shared import (
    _batch_display_name,
    _load_batch,
    _semester_name,
    _serialize_batch,
)
from ._evaluation_batch_stats import (
    _build_dimension_rows,
    _build_teacher_summary_rows,
    _overall_average,
)


def list_evaluation_batches(session: Session, semester_id: int | None = None) -> list[EvaluationBatchRead]:
    query = (
        select(EvaluationBatch)
        .options(
            joinedload(EvaluationBatch.template),
            joinedload(EvaluationBatch.semester).joinedload(Semester.academic_year),
        )
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

    question_map = {question.question_text: question for question in template.questions if question.is_active}
    teacher_map = {item.name: item for item in session.scalars(select(Teacher).where(Teacher.is_active.is_(True))).all()}
    class_map = {item.name: item for item in session.scalars(select(SchoolClass).where(SchoolClass.is_active.is_(True))).all()}

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
