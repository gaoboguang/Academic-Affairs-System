from __future__ import annotations

from collections import defaultdict
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import delete, select
from sqlalchemy.orm import Session, joinedload

from app.analytics.workload import (
    build_rule_lookup,
)
from app.core.config import Settings
from app.exporters.workload import export_workload_results
from app.importers.timetable import TimetableImporter
from app.models import (
    DictItem,
    DictType,
    Grade,
    SchoolClass,
    Semester,
    Subject,
    Teacher,
    TeacherWorkloadExtra,
    TeacherWorkloadResult,
    TimetableBatch,
    TimetableEntry,
    WorkloadRuleItem,
    WorkloadRuleVersion,
)
from app.repositories.system import create_import_job, write_audit_log
from app.repositories.workload import (
    count_batch_entries,
    count_workload_results_by_rule_version,
    get_latest_effective_batch,
    get_rule_version,
    get_timetable_batch,
    get_workload_result,
    list_rule_items,
    list_rule_versions as repo_list_rule_versions,
    list_timetable_batches as repo_list_timetable_batches,
    list_timetable_entries as repo_list_timetable_entries,
    list_workload_extras as repo_list_workload_extras,
    list_workload_results as repo_list_workload_results,
)
from app.schemas.workload import (
    TeacherWorkloadExtraPayload,
    TeacherWorkloadExtraRead,
    TeacherWorkloadResultRead,
    TimetableBatchRead,
    TimetableEntryRead,
    TimetableEntryUpdatePayload,
    TimetableImportResponse,
    WorkloadCalculatePayload,
    WorkloadCalculateResponse,
    WorkloadRuleItemPayload,
    WorkloadRuleItemRead,
    WorkloadRuleVersionPayload,
    WorkloadRuleVersionRead,
)

from ._workload_calculation import build_teacher_workload_computation


DEFAULT_RULE_ITEMS = [
    ("subject", "chinese", 1.0, None, "语文学科系数"),
    ("subject", "math", 1.1, None, "数学学科系数"),
    ("grade", "高一", 1.0, None, "高一年级系数"),
    ("grade", "高二", 1.05, None, "高二年级系数"),
    ("grade", "高三", 1.1, None, "高三年级系数"),
    ("class_type", "normal", 1.0, None, "普通班系数"),
    ("class_type", "key", 1.1, None, "重点班系数"),
    ("class_type", "experiment", 1.15, None, "实验班系数"),
    ("class_type", "art", 1.05, None, "艺体班系数"),
    ("course_type", "regular", 1.0, None, "正课系数"),
    ("course_type", "morning_reading", 0.8, None, "早读系数"),
    ("course_type", "evening_study", 0.8, None, "晚修系数"),
    ("course_type", "self_study", 0.7, None, "自习系数"),
    ("course_type", "tutorial", 0.9, None, "辅导系数"),
    ("course_type", "club", 0.6, None, "社团系数"),
    ("class_size", "0-35", 0.9, None, "班额 0-35"),
    ("class_size", "36-45", 1.0, None, "班额 36-45"),
    ("class_size", "46+", 1.1, None, "班额 46+"),
    ("head_teacher", "true", None, 3.0, "班主任附加量"),
]


def _semester_name(item: Semester | None) -> str | None:
    if not item:
        return None
    if item.academic_year:
        return f"{item.academic_year.name} {item.name}"
    return item.name


def _serialize_batch(session: Session, item: TimetableBatch) -> TimetableBatchRead:
    total, unresolved = count_batch_entries(session, item.id)
    return TimetableBatchRead(
        id=item.id,
        semester_id=item.semester_id,
        semester_name=_semester_name(item.semester),
        source_filename=item.source_filename,
        import_time=item.import_time,
        status=item.status,
        remark=item.remark,
        entry_count=total,
        unresolved_count=unresolved,
        is_active=item.is_active,
    )


def _serialize_entry(item: TimetableEntry) -> TimetableEntryRead:
    return TimetableEntryRead(
        id=item.id,
        batch_id=item.batch_id,
        semester_id=item.semester_id,
        weekday=item.weekday,
        period_no=item.period_no,
        teacher_id=item.teacher_id,
        teacher_name=item.teacher.name if item.teacher else None,
        class_id=item.class_id,
        class_name=item.school_class.name if item.school_class else None,
        subject_id=item.subject_id,
        subject_name=item.subject.name if item.subject else None,
        course_type=item.course_type,
        week_rule=item.week_rule,
        week_list_json=item.week_list_json,
        note=item.note,
        mapping_status=item.mapping_status,
        raw_teacher_name=item.raw_teacher_name,
        raw_class_name=item.raw_class_name,
        raw_subject_name=item.raw_subject_name,
        raw_course_type=item.raw_course_type,
        is_active=item.is_active,
    )


def _serialize_rule_version(item: WorkloadRuleVersion) -> WorkloadRuleVersionRead:
    return WorkloadRuleVersionRead(
        id=item.id,
        name=item.name,
        semester_id=item.semester_id,
        semester_name=_semester_name(item.semester),
        is_default=item.is_default,
        status=item.status,
        note=item.note,
        is_active=item.is_active,
    )


def _serialize_rule_item(item: WorkloadRuleItem) -> WorkloadRuleItemRead:
    return WorkloadRuleItemRead.model_validate(item)


def _serialize_extra(item: TeacherWorkloadExtra) -> TeacherWorkloadExtraRead:
    return TeacherWorkloadExtraRead(
        id=item.id,
        teacher_id=item.teacher_id,
        teacher_name=item.teacher.name if item.teacher else None,
        semester_id=item.semester_id,
        item_name=item.item_name,
        quantity=item.quantity,
        coefficient=item.coefficient,
        amount=item.amount,
        note=item.note,
        is_active=item.is_active,
    )


def _serialize_result(item: TeacherWorkloadResult) -> TeacherWorkloadResultRead:
    return TeacherWorkloadResultRead(
        id=item.id,
        teacher_id=item.teacher_id,
        teacher_name=item.teacher.name if item.teacher else None,
        semester_id=item.semester_id,
        semester_name=_semester_name(item.semester),
        rule_version_id=item.rule_version_id,
        rule_version_name=item.rule_version.name if item.rule_version else None,
        weekly_hours=item.weekly_hours,
        monthly_hours_json=item.monthly_hours_json,
        semester_hours=item.semester_hours,
        semester_workload=item.semester_workload,
        snapshot_json=item.snapshot_json,
        calculated_at=item.calculated_at,
        is_active=item.is_active,
    )


def ensure_default_rule_version(session: Session) -> WorkloadRuleVersion:
    existing_default = session.scalar(
        select(WorkloadRuleVersion).where(
            WorkloadRuleVersion.is_default.is_(True),
            WorkloadRuleVersion.is_active.is_(True),
        )
    )
    if existing_default:
        return existing_default
    version = WorkloadRuleVersion(
        name="默认工作量规则",
        semester_id=None,
        is_default=True,
        status="active",
        note="系统初始化生成",
    )
    session.add(version)
    session.flush()
    for dimension_type, match_key, coefficient, fixed_value, note in DEFAULT_RULE_ITEMS:
        session.add(
            WorkloadRuleItem(
                rule_version_id=version.id,
                dimension_type=dimension_type,
                match_key=match_key,
                coefficient=coefficient,
                fixed_value=fixed_value,
                note=note,
            )
        )
    session.flush()
    return version


def list_timetable_batches(session: Session, semester_id: int | None = None) -> list[TimetableBatchRead]:
    return [_serialize_batch(session, item) for item in repo_list_timetable_batches(session, semester_id)]


def list_timetable_entries(
    session: Session,
    *,
    batch_id: int,
    unresolved_only: bool = False,
) -> list[TimetableEntryRead]:
    if not get_timetable_batch(session, batch_id):
        raise HTTPException(status_code=404, detail="课表批次不存在")
    return [_serialize_entry(item) for item in repo_list_timetable_entries(session, batch_id=batch_id, unresolved_only=unresolved_only)]


def import_timetable(
    session: Session,
    settings: Settings,
    *,
    semester_id: int,
    filename: str | None,
    content: bytes,
    remark: str | None = None,
) -> TimetableImportResponse:
    semester = session.scalar(
        select(Semester)
        .options(joinedload(Semester.academic_year))
        .where(Semester.id == semester_id)
    )
    if not semester:
        raise HTTPException(status_code=404, detail="学期不存在")

    batch = TimetableBatch(
        semester_id=semester_id,
        source_filename=filename,
        import_time=datetime.now(),
        status="processing",
        remark=remark,
    )
    session.add(batch)
    session.flush()
    job = create_import_job(session, "timetable", filename)
    job.started_at = datetime.now()

    importer = TimetableImporter(session, settings, semester)
    result, unresolved_rows = importer.execute(filename=filename, content=content, batch=batch)

    batch.status = "completed_with_unresolved" if unresolved_rows else "completed"
    job.finished_at = datetime.now()
    job.status = batch.status
    job.result_json = {"batch_id": batch.id, "unresolved_rows": unresolved_rows, **result.model_dump()}
    write_audit_log(
        session,
        module="timetable",
        action="import",
        target_type="timetable_batch",
        target_id=str(batch.id),
        detail_json=job.result_json,
    )
    return TimetableImportResponse(batch_id=batch.id, unresolved_rows=unresolved_rows, **result.model_dump())


def update_timetable_entry(
    session: Session,
    entry_id: int,
    payload: TimetableEntryUpdatePayload,
) -> TimetableEntryRead:
    entry = session.scalar(
        select(TimetableEntry)
        .options(
            joinedload(TimetableEntry.teacher),
            joinedload(TimetableEntry.school_class),
            joinedload(TimetableEntry.subject),
        )
        .where(TimetableEntry.id == entry_id)
    )
    if not entry:
        raise HTTPException(status_code=404, detail="课表条目不存在")
    if payload.teacher_id and not session.get(Teacher, payload.teacher_id):
        raise HTTPException(status_code=404, detail="教师不存在")
    if payload.class_id and not session.get(SchoolClass, payload.class_id):
        raise HTTPException(status_code=404, detail="班级不存在")
    if payload.subject_id and not session.get(Subject, payload.subject_id):
        raise HTTPException(status_code=404, detail="学科不存在")
    if payload.course_type:
        valid_course_types = {
            item.code
            for item in session.scalars(
                select(DictItem)
                .join(DictType, DictItem.dict_type_id == DictType.id)
                .where(DictType.code == "course_type", DictItem.is_active.is_(True))
            ).all()
        }
        if payload.course_type not in valid_course_types:
            raise HTTPException(status_code=400, detail="课程类型无效")

    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(entry, key, value)
    entry.mapping_status = (
        "matched"
        if entry.teacher_id and entry.class_id and entry.subject_id and entry.course_type
        else "unresolved"
    )
    session.flush()
    session.refresh(entry)
    write_audit_log(
        session,
        module="timetable",
        action="update_entry",
        target_type="timetable_entry",
        target_id=str(entry.id),
        detail_json={"mapping_status": entry.mapping_status},
    )
    return _serialize_entry(entry)


def list_rule_versions(session: Session) -> list[WorkloadRuleVersionRead]:
    ensure_default_rule_version(session)
    return [_serialize_rule_version(item) for item in repo_list_rule_versions(session)]


def create_rule_version(session: Session, payload: WorkloadRuleVersionPayload) -> WorkloadRuleVersionRead:
    if payload.semester_id and not session.get(Semester, payload.semester_id):
        raise HTTPException(status_code=404, detail="学期不存在")
    if payload.is_default:
        for item in session.scalars(select(WorkloadRuleVersion).where(WorkloadRuleVersion.is_default.is_(True))).all():
            item.is_default = False
    version = WorkloadRuleVersion(**payload.model_dump())
    session.add(version)
    session.flush()
    write_audit_log(session, module="workload", action="create_rule_version", target_type="rule_version", target_id=str(version.id))
    session.refresh(version)
    return _serialize_rule_version(version)


def list_rule_items_read(session: Session, rule_version_id: int) -> list[WorkloadRuleItemRead]:
    version = get_rule_version(session, rule_version_id)
    if not version:
        raise HTTPException(status_code=404, detail="规则版本不存在")
    return [_serialize_rule_item(item) for item in list_rule_items(session, rule_version_id)]


def replace_rule_items(
    session: Session,
    rule_version_id: int,
    payload: list[WorkloadRuleItemPayload],
) -> list[WorkloadRuleItemRead]:
    version = get_rule_version(session, rule_version_id)
    if not version:
        raise HTTPException(status_code=404, detail="规则版本不存在")
    if count_workload_results_by_rule_version(session, rule_version_id) > 0:
        raise HTTPException(status_code=400, detail="规则版本已有计算结果，请新建版本后再调整规则")
    session.execute(delete(WorkloadRuleItem).where(WorkloadRuleItem.rule_version_id == rule_version_id))
    session.flush()
    for item in payload:
        session.add(WorkloadRuleItem(rule_version_id=rule_version_id, **item.model_dump()))
    session.flush()
    write_audit_log(session, module="workload", action="replace_rule_items", target_type="rule_version", target_id=str(rule_version_id))
    return [_serialize_rule_item(item) for item in list_rule_items(session, rule_version_id)]


def list_workload_extras(session: Session, semester_id: int | None = None) -> list[TeacherWorkloadExtraRead]:
    return [_serialize_extra(item) for item in repo_list_workload_extras(session, semester_id)]


def create_workload_extra(session: Session, payload: TeacherWorkloadExtraPayload) -> TeacherWorkloadExtraRead:
    if not session.get(Teacher, payload.teacher_id):
        raise HTTPException(status_code=404, detail="教师不存在")
    if not session.get(Semester, payload.semester_id):
        raise HTTPException(status_code=404, detail="学期不存在")
    extra = TeacherWorkloadExtra(**payload.model_dump())
    session.add(extra)
    session.flush()
    write_audit_log(session, module="workload", action="create_extra", target_type="teacher_workload_extra", target_id=str(extra.id))
    session.refresh(extra)
    return _serialize_extra(extra)


def calculate_workload(session: Session, payload: WorkloadCalculatePayload) -> WorkloadCalculateResponse:
    semester = session.scalar(
        select(Semester)
        .options(joinedload(Semester.academic_year))
        .where(Semester.id == payload.semester_id)
    )
    if not semester:
        raise HTTPException(status_code=404, detail="学期不存在")
    rule_version = get_rule_version(session, payload.rule_version_id)
    if not rule_version:
        raise HTTPException(status_code=404, detail="规则版本不存在")
    batch = get_timetable_batch(session, payload.batch_id) if payload.batch_id else get_latest_effective_batch(session, payload.semester_id)
    if not batch:
        raise HTTPException(status_code=404, detail="当前学期暂无可计算的课表批次")
    if batch.semester_id != payload.semester_id:
        raise HTTPException(status_code=400, detail="所选课表批次与学期不匹配")
    if semester.week_count <= 0:
        raise HTTPException(status_code=400, detail="学期周数必须大于 0")

    entries = session.scalars(
        select(TimetableEntry)
        .options(
            joinedload(TimetableEntry.teacher),
            joinedload(TimetableEntry.school_class).joinedload(SchoolClass.grade),
            joinedload(TimetableEntry.subject),
        )
        .where(
            TimetableEntry.batch_id == batch.id,
            TimetableEntry.mapping_status == "matched",
            TimetableEntry.is_active.is_(True),
        )
    ).all()
    if not entries:
        raise HTTPException(status_code=400, detail="当前批次没有可计算的已匹配课表条目")

    items = list_rule_items(session, payload.rule_version_id)
    lookup = build_rule_lookup(list(items))
    extras = [item for item in repo_list_workload_extras(session, payload.semester_id) if item.is_active]
    extras_by_teacher: dict[int, list[TeacherWorkloadExtra]] = defaultdict(list)
    for item in extras:
        extras_by_teacher[item.teacher_id].append(item)

    teachers = {
        entry.teacher_id: entry.teacher
        for entry in entries
        if entry.teacher_id is not None and entry.teacher is not None
    }

    results_count = 0
    for teacher_id, teacher in teachers.items():
        teacher_entries = [entry for entry in entries if entry.teacher_id == teacher_id]
        computation = build_teacher_workload_computation(
            teacher=teacher,
            teacher_entries=teacher_entries,
            extras=extras_by_teacher.get(teacher_id, []),
            lookup=lookup,
            semester=semester,
            batch=batch,
        )

        result = get_workload_result(
            session,
            teacher_id=teacher_id,
            semester_id=payload.semester_id,
            rule_version_id=payload.rule_version_id,
        )
        if result is None:
            result = TeacherWorkloadResult(
                teacher_id=teacher_id,
                semester_id=payload.semester_id,
                rule_version_id=payload.rule_version_id,
            )
            session.add(result)
        result.weekly_hours = computation.weekly_hours
        result.monthly_hours_json = computation.monthly_hours_json
        result.semester_hours = computation.semester_hours
        result.semester_workload = computation.semester_workload
        result.snapshot_json = computation.snapshot_json
        result.calculated_at = datetime.now()
        results_count += 1

    session.flush()
    write_audit_log(
        session,
        module="workload",
        action="calculate",
        target_type="rule_version",
        target_id=str(payload.rule_version_id),
        detail_json={"semester_id": payload.semester_id, "batch_id": batch.id, "result_count": results_count},
    )
    return WorkloadCalculateResponse(message="教师工作量计算完成", result_count=results_count)


def list_workload_results(
    session: Session,
    *,
    semester_id: int | None = None,
    rule_version_id: int | None = None,
) -> list[TeacherWorkloadResultRead]:
    return [_serialize_result(item) for item in repo_list_workload_results(session, semester_id=semester_id, rule_version_id=rule_version_id)]


def export_workload(
    session: Session,
    settings: Settings,
    *,
    semester_id: int | None = None,
    rule_version_id: int | None = None,
) -> dict[str, str]:
    rows = [
        _serialize_result(item).model_dump(mode="json")
        for item in repo_list_workload_results(session, semester_id=semester_id, rule_version_id=rule_version_id)
    ]
    if not rows:
        raise HTTPException(status_code=404, detail="暂无可导出的工作量结果")
    file_path = export_workload_results(settings, rows)
    return {"file_path": file_path}
