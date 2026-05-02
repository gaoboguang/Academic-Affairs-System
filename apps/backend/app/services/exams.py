from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.analytics.score_contexts import ensure_exam_student_contexts, upsert_score_class_mapping
from app.analytics.scores import rebuild_exam_snapshots
from app.core.config import Settings
from app.importers.score_layouts import ScoreImportMapping, ScoreLayoutAdapter
from app.importers.scores import ScoreImporter
from app.models import (
    ConfigItem,
    Exam,
    ExamSubject,
    Grade,
    SchoolClass,
    ScoreClassMapping,
    ScoreExamStudentContext,
    ScoreImportBatch,
    ScoreImportProfile,
    ScoreTargetLine,
    ScoreTotalSnapshot,
    Semester,
    Subject,
)
from app.repositories.exams import get_exam, list_exam_subjects as repo_list_exam_subjects, list_exams as repo_list_exams, list_score_batches
from app.repositories.system import create_import_job, write_audit_log
from app.schemas.exam import (
    ExamListResponse,
    ExamPayload,
    ExamRead,
    ExamSubjectPayload,
    ExamSubjectRead,
    ScoreClassMappingPayload,
    ScoreClassMappingRead,
    ScoreImportPreviewResponse,
    ScoreImportProfileRead,
    ScoreImportResponse,
    ScoreRankAuditResponse,
    ScoreRankDiffItem,
    ScoreRebuildResponse,
    ScoreTargetLinePayload,
    ScoreTargetLineRead,
)
def _serialize_exam_with_grade_map(item: Exam, grade_map: dict[int, str]) -> ExamRead:
    semester_name = None
    if item.semester and item.semester.academic_year:
        semester_name = f"{item.semester.academic_year.name} {item.semester.name}"
    elif item.semester:
        semester_name = item.semester.name
    grade_scope_names = [grade_map.get(grade_id, str(grade_id)) for grade_id in (item.grade_scope_json or [])]
    return ExamRead(
        id=item.id,
        name=item.name,
        exam_type=item.exam_type,
        exam_date=item.exam_date,
        semester_id=item.semester_id,
        semester_name=semester_name,
        grade_scope_json=item.grade_scope_json,
        grade_scope_names=grade_scope_names,
        is_trend_enabled=item.is_trend_enabled,
        status=item.status,
        note=item.note,
        is_active=item.is_active,
        subject_count=len([subject for subject in item.subjects if subject.is_active]),
    )


def _serialize_exam_subject(item: ExamSubject) -> ExamSubjectRead:
    return ExamSubjectRead(
        id=item.id,
        exam_id=item.exam_id,
        subject_id=item.subject_id,
        subject_name=item.subject.name if item.subject else None,
        full_score=item.full_score,
        is_in_total=item.is_in_total,
        excellent_line=item.excellent_line,
        pass_line=item.pass_line,
        sort_order=item.sort_order,
        is_active=item.is_active,
    )


def _get_rank_mode(session: Session) -> str:
    config = session.scalar(
        select(ConfigItem).where(
            ConfigItem.config_group == "analytics",
            ConfigItem.config_key == "ranking_mode",
        )
    )
    return config.config_value if config else "competition"


def list_exams(
    session: Session,
    *,
    page: int,
    page_size: int,
    name: str | None = None,
    semester_id: int | None = None,
) -> ExamListResponse:
    items, total = repo_list_exams(session, page=page, page_size=page_size, name=name, semester_id=semester_id)
    grade_map = {grade.id: grade.name for grade in session.scalars(select(Grade)).all()}
    return ExamListResponse(
        items=[_serialize_exam_with_grade_map(item, grade_map) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


def get_exam_detail(session: Session, exam_id: int) -> ExamRead:
    item = get_exam(session, exam_id)
    if not item:
        raise HTTPException(status_code=404, detail="考试不存在")
    grade_map = {grade.id: grade.name for grade in session.scalars(select(Grade)).all()}
    return _serialize_exam_with_grade_map(item, grade_map)


def create_exam(session: Session, payload: ExamPayload) -> ExamRead:
    _validate_exam_payload(session, payload)
    item = Exam(**payload.model_dump())
    session.add(item)
    session.flush()
    write_audit_log(session, module="exams", action="create", target_type="exam", target_id=str(item.id))
    item = get_exam(session, item.id) or item
    grade_map = {grade.id: grade.name for grade in session.scalars(select(Grade)).all()}
    return _serialize_exam_with_grade_map(item, grade_map)


def update_exam(session: Session, exam_id: int, payload: ExamPayload) -> ExamRead:
    item = get_exam(session, exam_id)
    if not item:
        raise HTTPException(status_code=404, detail="考试不存在")
    _validate_exam_payload(session, payload)
    for key, value in payload.model_dump().items():
        setattr(item, key, value)
    session.flush()
    write_audit_log(session, module="exams", action="update", target_type="exam", target_id=str(item.id))
    session.refresh(item)
    grade_map = {grade.id: grade.name for grade in session.scalars(select(Grade)).all()}
    return _serialize_exam_with_grade_map(item, grade_map)


def _validate_exam_payload(session: Session, payload: ExamPayload) -> None:
    semester = session.get(Semester, payload.semester_id)
    if not semester:
        raise HTTPException(status_code=404, detail="学期不存在")
    if payload.grade_scope_json:
        valid_ids = {grade.id for grade in session.scalars(select(Grade)).all()}
        invalid = [grade_id for grade_id in payload.grade_scope_json if grade_id not in valid_ids]
        if invalid:
            raise HTTPException(status_code=400, detail=f"年级范围无效: {invalid}")


def list_exam_subjects(session: Session, exam_id: int) -> list[ExamSubjectRead]:
    if not get_exam(session, exam_id):
        raise HTTPException(status_code=404, detail="考试不存在")
    return [_serialize_exam_subject(item) for item in repo_list_exam_subjects(session, exam_id)]


def list_score_import_profiles(session: Session) -> list[ScoreImportProfileRead]:
    items = session.scalars(
        select(ScoreImportProfile)
        .where(ScoreImportProfile.is_active.is_(True))
        .order_by(ScoreImportProfile.updated_at.desc(), ScoreImportProfile.id.desc())
    ).all()
    return [ScoreImportProfileRead.model_validate(item) for item in items]


def replace_exam_subjects(
    session: Session,
    exam_id: int,
    payload: list[ExamSubjectPayload],
) -> list[ExamSubjectRead]:
    exam = get_exam(session, exam_id)
    if not exam:
        raise HTTPException(status_code=404, detail="考试不存在")
    subject_ids = [item.subject_id for item in payload]
    if len(subject_ids) != len(set(subject_ids)):
        raise HTTPException(status_code=400, detail="考试科目重复")
    for item in payload:
        if not session.get(Subject, item.subject_id):
            raise HTTPException(status_code=404, detail=f"学科不存在: {item.subject_id}")

    existing = list(repo_list_exam_subjects(session, exam_id))
    existing_map = {item.subject_id: item for item in existing}
    keep_ids = set(subject_ids)
    for subject_id, current in existing_map.items():
        if subject_id not in keep_ids:
            current.is_active = False
    for item in payload:
        current = existing_map.get(item.subject_id)
        if current:
            for key, value in item.model_dump().items():
                setattr(current, key, value)
            current.is_active = True
        else:
            session.add(ExamSubject(exam_id=exam_id, **item.model_dump()))
    session.flush()
    write_audit_log(session, module="exams", action="replace_subjects", target_type="exam", target_id=str(exam_id))
    return [_serialize_exam_subject(item) for item in repo_list_exam_subjects(session, exam_id)]


def rebuild_exam(session: Session, exam_id: int) -> dict[str, str]:
    exam = get_exam(session, exam_id)
    if not exam:
        raise HTTPException(status_code=404, detail="考试不存在")
    rank_mode = _get_rank_mode(session)
    rebuild_exam_snapshots(session, exam, rank_mode)
    write_audit_log(session, module="exams", action="rebuild", target_type="exam", target_id=str(exam.id))
    return {"message": "统计快照已重建"}


def rebuild_exam_score_snapshots(session: Session, exam_id: int) -> ScoreRebuildResponse:
    exam = get_exam(session, exam_id)
    if not exam:
        raise HTTPException(status_code=404, detail="考试不存在")
    rank_mode = _get_rank_mode(session)
    rebuild_exam_snapshots(session, exam, rank_mode)
    write_audit_log(session, module="exams", action="rebuild_score_snapshots", target_type="exam", target_id=str(exam.id))
    return ScoreRebuildResponse(message="已按考试时点班级重建成绩快照", audit=get_score_rank_audit(session, exam_id))


def import_scores(
    session: Session,
    settings: Settings,
    *,
    exam_id: int,
    filename: str | None,
    content: bytes,
    strategy: str,
    rebuild: bool = True,
    mapping_json: str | None = None,
    profile_id: int | None = None,
    save_profile_name: str | None = None,
) -> ScoreImportResponse:
    exam = get_exam(session, exam_id)
    if not exam:
        raise HTTPException(status_code=404, detail="考试不存在")
    if not repo_list_exam_subjects(session, exam_id):
        raise HTTPException(status_code=400, detail="请先配置考试科目")

    mapping, profile = _resolve_score_import_mapping(session, mapping_json=mapping_json, profile_id=profile_id)
    if save_profile_name and mapping is None:
        raise HTTPException(status_code=400, detail="保存平台模板前，请先完成成绩单识别映射。")
    if save_profile_name and mapping is not None:
        profile = _save_score_import_profile(session, save_profile_name, mapping)

    batch = ScoreImportBatch(
        exam_id=exam_id,
        profile_id=profile.id if profile else None,
        source_filename=filename,
        import_time=datetime.now(),
    )
    session.add(batch)
    session.flush()
    job = create_import_job(session, "scores", filename)
    job.started_at = datetime.now()

    importer = ScoreImporter(session, settings, exam)
    try:
        result = importer.execute(filename=filename, content=content, strategy=strategy, batch=batch, mapping=mapping)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    batch.total_rows = result.total_rows
    batch.success_rows = result.success_rows
    batch.failed_rows = result.failed_rows
    batch.status = result.status
    batch.error_report_path = result.error_report_path
    batch.detection_summary_json = importer.last_detection_summary

    if rebuild:
        rebuild_exam_snapshots(session, exam, _get_rank_mode(session))

    job.finished_at = datetime.now()
    job.status = result.status
    job.result_json = {"exam_id": exam_id, "batch_id": batch.id, **result.model_dump()}
    write_audit_log(
        session,
        module="exams",
        action="import_scores",
        target_type="score_import_batch",
        target_id=str(batch.id),
        detail_json=job.result_json,
    )
    return ScoreImportResponse(
        batch_id=batch.id,
        profile_id=batch.profile_id,
        detection_summary=batch.detection_summary_json,
        **result.model_dump(),
    )


def preview_score_import(
    session: Session,
    *,
    exam_id: int,
    filename: str | None,
    content: bytes,
    mapping_json: str | None = None,
    profile_id: int | None = None,
) -> ScoreImportPreviewResponse:
    exam = get_exam(session, exam_id)
    if not exam:
        raise HTTPException(status_code=404, detail="考试不存在")
    if not repo_list_exam_subjects(session, exam_id):
        raise HTTPException(status_code=400, detail="请先配置考试科目")

    mapping, _profile = _resolve_score_import_mapping(session, mapping_json=mapping_json, profile_id=profile_id)
    try:
        preview = ScoreLayoutAdapter(session, exam).preview(filename=filename, content=content, mapping=mapping)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ScoreImportPreviewResponse.model_validate(preview.to_dict())


def get_score_import_batches(session: Session, exam_id: int) -> list[dict]:
    if not get_exam(session, exam_id):
        raise HTTPException(status_code=404, detail="考试不存在")
    return [
        {
            "id": item.id,
            "source_filename": item.source_filename,
            "import_time": item.import_time.isoformat(sep=" ", timespec="seconds"),
            "total_rows": item.total_rows,
            "success_rows": item.success_rows,
            "failed_rows": item.failed_rows,
            "status": item.status,
            "error_report_path": item.error_report_path,
            "profile_id": item.profile_id,
            "detection_summary": item.detection_summary_json,
        }
        for item in list_score_batches(session, exam_id)
    ]


def list_score_target_lines(session: Session, exam_id: int) -> list[ScoreTargetLineRead]:
    if not get_exam(session, exam_id):
        raise HTTPException(status_code=404, detail="考试不存在")
    items = session.scalars(
        select(ScoreTargetLine)
        .where(ScoreTargetLine.exam_id == exam_id, ScoreTargetLine.is_active.is_(True))
        .order_by(ScoreTargetLine.sort_order.asc(), ScoreTargetLine.id.asc())
    ).all()
    return [_serialize_target_line(item) for item in items]


def replace_score_target_lines(
    session: Session,
    exam_id: int,
    payload: list[ScoreTargetLinePayload],
) -> list[ScoreTargetLineRead]:
    exam = get_exam(session, exam_id)
    if not exam:
        raise HTTPException(status_code=404, detail="考试不存在")
    seen_names: set[str] = set()
    existing = {
        item.name: item
        for item in session.scalars(select(ScoreTargetLine).where(ScoreTargetLine.exam_id == exam_id)).all()
    }
    keep_names: set[str] = set()
    for item_payload in payload:
        _validate_target_line_payload(item_payload)
        name = item_payload.name.strip()
        if name in seen_names:
            raise HTTPException(status_code=400, detail=f"目标线名称重复: {name}")
        seen_names.add(name)
        item = existing.get(name)
        if item is None:
            item = ScoreTargetLine(exam_id=exam_id, name=name, line_type=item_payload.line_type)
            session.add(item)
        for key, value in item_payload.model_dump().items():
            setattr(item, key, value.strip() if isinstance(value, str) else value)
        item.name = name
        keep_names.add(name)
    for name, item in existing.items():
        if name not in keep_names:
            item.is_active = False
    session.flush()
    write_audit_log(session, module="exams", action="replace_score_target_lines", target_type="exam", target_id=str(exam.id))
    return list_score_target_lines(session, exam_id)


def save_score_class_mappings(
    session: Session,
    exam_id: int,
    payload: list[ScoreClassMappingPayload],
) -> ScoreRankAuditResponse:
    exam = get_exam(session, exam_id)
    if not exam:
        raise HTTPException(status_code=404, detail="考试不存在")
    ensure_exam_student_contexts(session, exam)
    for item in payload:
        source_class_name = item.source_class_name.strip()
        if not source_class_name:
            raise HTTPException(status_code=400, detail="源班级不能为空")
        if item.mapped_class_id is not None and not session.get(SchoolClass, item.mapped_class_id):
            raise HTTPException(status_code=404, detail=f"班级不存在: {item.mapped_class_id}")
        mapping_status = item.mapping_status.strip() or ("mapped" if item.mapped_class_id else "unmapped")
        upsert_score_class_mapping(
            session,
            exam,
            source_class_name,
            item.mapped_class_id,
            mapping_status,
            note=item.note,
        )
        contexts = session.scalars(
            select(ScoreExamStudentContext).where(
                ScoreExamStudentContext.exam_id == exam_id,
                ScoreExamStudentContext.source_class_name == source_class_name,
            )
        ).all()
        for context in contexts:
            context.mapped_class_id = item.mapped_class_id
            context.mapping_status = mapping_status
    session.flush()
    write_audit_log(session, module="exams", action="save_score_class_mappings", target_type="exam", target_id=str(exam.id))
    return get_score_rank_audit(session, exam_id)


def get_score_rank_audit(session: Session, exam_id: int, *, diff_limit: int = 50) -> ScoreRankAuditResponse:
    exam = get_exam(session, exam_id)
    if not exam:
        raise HTTPException(status_code=404, detail="考试不存在")
    context_map = ensure_exam_student_contexts(session, exam)
    snapshots = session.scalars(
        select(ScoreTotalSnapshot)
        .where(ScoreTotalSnapshot.exam_id == exam_id, ScoreTotalSnapshot.is_active.is_(True))
    ).all()
    snapshot_map = {item.student_id: item for item in snapshots}
    mappings = _list_score_class_mappings(session, exam_id)

    context_count = len(context_map)
    mapped_context_count = sum(1 for item in context_map.values() if item.mapped_class_id is not None)
    unmapped_context_count = context_count - mapped_context_count
    mapping_rate = round(mapped_context_count / context_count, 4) if context_count else 0.0
    source_rank_count = sum(
        1
        for item in context_map.values()
        if item.source_class_rank is not None or item.source_school_rank is not None or item.source_grade_rank is not None
    )

    diff_items: list[ScoreRankDiffItem] = []
    class_delta_values: list[int] = []
    school_delta_values: list[int] = []
    for context in context_map.values():
        snapshot = snapshot_map.get(context.student_id)
        if snapshot is None:
            continue
        source_school_rank = context.source_school_rank or context.source_grade_rank
        class_delta = (
            snapshot.class_rank - context.source_class_rank
            if snapshot.class_rank is not None and context.source_class_rank is not None
            else None
        )
        school_delta = (
            snapshot.grade_rank - source_school_rank
            if snapshot.grade_rank is not None and source_school_rank is not None
            else None
        )
        if class_delta is None and school_delta is None:
            continue
        if class_delta is not None:
            class_delta_values.append(abs(class_delta))
        if school_delta is not None:
            school_delta_values.append(abs(school_delta))
        if class_delta == 0 and school_delta == 0:
            continue
        student = context.student
        diff_items.append(
            ScoreRankDiffItem(
                student_id=context.student_id,
                student_name=student.name if student else str(context.student_id),
                source_class_name=context.source_class_name,
                mapped_class_name=context.mapped_class.name if context.mapped_class else None,
                total_score=snapshot.total_score,
                system_class_rank=snapshot.class_rank,
                source_class_rank=context.source_class_rank,
                class_rank_delta=class_delta,
                system_school_rank=snapshot.grade_rank,
                source_school_rank=source_school_rank,
                school_rank_delta=school_delta,
            )
        )
    diff_items.sort(
        key=lambda item: (
            max(abs(item.class_rank_delta or 0), abs(item.school_rank_delta or 0)),
            item.total_score or 0,
        ),
        reverse=True,
    )

    warnings: list[str] = []
    if unmapped_context_count:
        warnings.append(f"有 {unmapped_context_count} 名学生缺少考试时点班级映射，班级名次可能回退或缺失。")
    if len(snapshots) != context_count:
        warnings.append("考试导入样本与总分快照样本不完全一致，请重建快照后再核对名次。")
    if diff_items:
        warnings.append(f"发现 {len(diff_items)} 名学生的平台原始名次与系统重算名次存在差异。")
        warnings.append("差异通常来自未导入学生、平台完整排名范围或平台总分取整规则；系统名次仅代表本次有效导入样本。")
    if not snapshots:
        warnings.append("当前考试暂无总分快照，请先导入成绩或重建快照。")

    return ScoreRankAuditResponse(
        exam_id=exam.id,
        exam_name=exam.name,
        total_students=len(snapshots),
        context_count=context_count,
        mapped_context_count=mapped_context_count,
        unmapped_context_count=unmapped_context_count,
        mapping_rate=mapping_rate,
        source_class_count=len({item.source_class_name for item in context_map.values() if item.source_class_name}),
        mapped_class_count=len({item.mapped_class_id for item in context_map.values() if item.mapped_class_id is not None}),
        source_rank_count=source_rank_count,
        rank_diff_count=len(diff_items),
        max_abs_class_rank_delta=max(class_delta_values) if class_delta_values else None,
        max_abs_school_rank_delta=max(school_delta_values) if school_delta_values else None,
        warnings=warnings,
        class_mappings=mappings,
        rank_diffs=diff_items[:diff_limit],
    )


def _list_score_class_mappings(session: Session, exam_id: int) -> list[ScoreClassMappingRead]:
    context_counts: dict[str, int] = defaultdict(int)
    for source_class_name, in session.execute(
        select(ScoreExamStudentContext.source_class_name).where(
            ScoreExamStudentContext.exam_id == exam_id,
            ScoreExamStudentContext.is_active.is_(True),
        )
    ):
        if source_class_name:
            context_counts[source_class_name] += 1
    items = session.scalars(
        select(ScoreClassMapping)
        .where(ScoreClassMapping.exam_id == exam_id, ScoreClassMapping.is_active.is_(True))
        .order_by(ScoreClassMapping.source_class_name.asc())
    ).all()
    return [
        ScoreClassMappingRead(
            id=item.id,
            exam_id=item.exam_id,
            source_class_name=item.source_class_name,
            mapped_class_id=item.mapped_class_id,
            mapped_class_name=item.mapped_class.name if item.mapped_class else None,
            mapping_status=item.mapping_status,
            note=item.note,
            student_count=context_counts.get(item.source_class_name, 0),
        )
        for item in items
    ]


def _serialize_target_line(item: ScoreTargetLine) -> ScoreTargetLineRead:
    return ScoreTargetLineRead.model_validate(item)


def _validate_target_line_payload(payload: ScoreTargetLinePayload) -> None:
    line_type = payload.line_type.strip()
    if line_type not in {"score", "rank"}:
        raise HTTPException(status_code=400, detail="目标线类型只能是 score 或 rank")
    if not payload.name.strip():
        raise HTTPException(status_code=400, detail="目标线名称不能为空")
    if line_type == "score" and payload.score_value is None:
        raise HTTPException(status_code=400, detail="分数线必须填写分数阈值")
    if line_type == "rank" and payload.rank_value is None:
        raise HTTPException(status_code=400, detail="名次线必须填写名次阈值")
    if payload.rank_value is not None and payload.rank_value <= 0:
        raise HTTPException(status_code=400, detail="名次阈值必须大于 0")
    if payload.near_margin_rank is not None and payload.near_margin_rank < 0:
        raise HTTPException(status_code=400, detail="临界名次范围不能为负数")
    if payload.near_margin_score is not None and payload.near_margin_score < 0:
        raise HTTPException(status_code=400, detail="临界分数范围不能为负数")


def _resolve_score_import_mapping(
    session: Session,
    *,
    mapping_json: str | None,
    profile_id: int | None,
) -> tuple[ScoreImportMapping | None, ScoreImportProfile | None]:
    profile: ScoreImportProfile | None = None
    if profile_id is not None:
        profile = session.get(ScoreImportProfile, profile_id)
        if profile is None or not profile.is_active:
            raise HTTPException(status_code=404, detail="成绩导入平台模板不存在")
    if mapping_json:
        try:
            return ScoreImportMapping.from_dict(json.loads(mapping_json)), profile
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            raise HTTPException(status_code=400, detail="成绩单映射 JSON 无法解析") from exc
    if profile is not None:
        mapping = ScoreImportMapping(
            layout_type=profile.layout_type,
            sheet_name=profile.sheet_name,
            header_row=profile.header_row,
            field_mapping=profile.field_mapping_json or {},
            subject_mapping=profile.subject_mapping_json or {},
            subject_score_types=profile.subject_score_type_json or {},
            ignored_columns=profile.ignored_columns_json or [],
            metadata_mapping=profile.metadata_mapping_json or {},
        )
        return mapping, profile
    return None, None


def _save_score_import_profile(session: Session, name: str, mapping: ScoreImportMapping) -> ScoreImportProfile:
    clean_name = name.strip()
    if not clean_name:
        raise HTTPException(status_code=400, detail="平台模板名称不能为空")
    existing = session.scalar(select(ScoreImportProfile).where(ScoreImportProfile.name == clean_name))
    if existing:
        existing.layout_type = mapping.layout_type
        existing.sheet_name = mapping.sheet_name
        existing.header_row = mapping.header_row
        existing.field_mapping_json = mapping.field_mapping
        existing.subject_mapping_json = mapping.subject_mapping
        existing.subject_score_type_json = mapping.subject_score_types
        existing.ignored_columns_json = mapping.ignored_columns
        existing.metadata_mapping_json = mapping.metadata_mapping
        existing.is_active = True
        session.flush()
        return existing
    profile = ScoreImportProfile(
        name=clean_name,
        layout_type=mapping.layout_type,
        sheet_name=mapping.sheet_name,
        header_row=mapping.header_row,
        field_mapping_json=mapping.field_mapping,
        subject_mapping_json=mapping.subject_mapping,
        subject_score_type_json=mapping.subject_score_types,
        ignored_columns_json=mapping.ignored_columns,
        metadata_mapping_json=mapping.metadata_mapping,
    )
    session.add(profile)
    session.flush()
    return profile
