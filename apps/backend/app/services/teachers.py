from __future__ import annotations

from datetime import date, datetime

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.analytics.scores import calculate_rate, safe_mean
from app.core.config import Settings
from app.exporters.teachers import export_teachers as export_teachers_workbook
from app.importers.teachers import TeacherImporter
from app.models import Exam, Grade, SchoolClass, Semester, Subject, Teacher, TeacherTitleHistory, TeachingAssignment
from app.repositories.exams import get_score_records_for_exam
from app.repositories.system import create_import_job, write_audit_log
from app.repositories.teachers import (
    get_teacher,
    get_teacher_by_no,
    list_teachers as repo_list_teachers,
    list_teaching_assignments as repo_list_teaching_assignments,
)
from app.schemas.teacher import (
    TeacherExamTrendItem,
    TeacherListResponse,
    TeacherPayload,
    TeacherPeerComparisonItem,
    TeacherProfileRead,
    TeacherRead,
    TeacherTitleHistoryPayload,
    TeacherTitleHistoryRead,
    TeachingAssignmentPayload,
    TeachingAssignmentRead,
)


def _serialize_teacher(item: Teacher) -> TeacherRead:
    return TeacherRead(
        id=item.id,
        teacher_no=item.teacher_no,
        name=item.name,
        gender=item.gender,
        subject_id=item.subject_id,
        subject_name=item.subject.name if item.subject else None,
        phone=item.phone,
        title_code=item.title_code,
        position_code=item.position_code,
        is_head_teacher=item.is_head_teacher,
        employment_status=item.employment_status,
        entry_date=item.entry_date,
        note=item.note,
        is_active=item.is_active,
    )


def _serialize_assignment(item: TeachingAssignment) -> TeachingAssignmentRead:
    semester_name = None
    if item.semester and item.semester.academic_year:
        semester_name = f"{item.semester.academic_year.name} {item.semester.name}"
    elif item.semester:
        semester_name = item.semester.name
    return TeachingAssignmentRead(
        id=item.id,
        teacher_id=item.teacher_id,
        teacher_name=item.teacher.name if item.teacher else None,
        semester_id=item.semester_id,
        semester_name=semester_name,
        grade_id=item.grade_id,
        grade_name=item.grade.name if item.grade else None,
        class_id=item.class_id,
        class_name=item.school_class.name if item.school_class else None,
        subject_id=item.subject_id,
        subject_name=item.subject.name if item.subject else None,
        course_type=item.course_type,
        weekly_periods_manual=item.weekly_periods_manual,
        is_active=item.is_active,
    )


def _serialize_title_history(item: TeacherTitleHistory) -> TeacherTitleHistoryRead:
    return TeacherTitleHistoryRead(
        id=item.id,
        teacher_id=item.teacher_id,
        title_code=item.title_code,
        start_date=item.start_date,
        end_date=item.end_date,
        note=item.note,
        is_active=item.is_active,
    )


def list_teachers(
    session: Session,
    *,
    page: int,
    page_size: int,
    teacher_no: str | None = None,
    name: str | None = None,
    subject_id: int | None = None,
    title_code: str | None = None,
    is_head_teacher: bool | None = None,
) -> TeacherListResponse:
    items, total = repo_list_teachers(
        session,
        page=page,
        page_size=page_size,
        teacher_no=teacher_no,
        name=name,
        subject_id=subject_id,
        title_code=title_code,
        is_head_teacher=is_head_teacher,
    )
    return TeacherListResponse(
        items=[_serialize_teacher(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


def get_teacher_detail(session: Session, teacher_id: int) -> TeacherRead:
    item = get_teacher(session, teacher_id)
    if not item:
        raise HTTPException(status_code=404, detail="教师不存在")
    return _serialize_teacher(item)


def get_teacher_profile(session: Session, teacher_id: int) -> TeacherProfileRead:
    teacher = session.scalar(
        select(Teacher)
        .options(
            joinedload(Teacher.subject),
            selectinload(Teacher.title_histories),
        )
        .where(Teacher.id == teacher_id)
    )
    if not teacher:
        raise HTTPException(status_code=404, detail="教师不存在")

    assignments = session.scalars(
        select(TeachingAssignment)
        .options(
            joinedload(TeachingAssignment.teacher),
            joinedload(TeachingAssignment.semester).joinedload(Semester.academic_year),
            joinedload(TeachingAssignment.grade),
            joinedload(TeachingAssignment.school_class),
            joinedload(TeachingAssignment.subject),
        )
        .where(TeachingAssignment.teacher_id == teacher_id)
        .order_by(TeachingAssignment.semester_id.desc(), TeachingAssignment.id.desc())
    ).all()
    recent_exam_trends = _build_teacher_exam_trends(session, teacher, assignments)
    latest_exam_id = recent_exam_trends[0].exam_id if recent_exam_trends else None
    peer_comparisons = _build_latest_peer_comparisons(session, teacher, latest_exam_id)
    return TeacherProfileRead(
        teacher=_serialize_teacher(teacher),
        title_histories=[
            _serialize_title_history(item)
            for item in sorted(
                teacher.title_histories,
                key=lambda current: (current.start_date or date.min, current.id),
                reverse=True,
            )
            if item.is_active
        ],
        assignments=[_serialize_assignment(item) for item in assignments if item.is_active],
        recent_exam_trends=recent_exam_trends,
        peer_comparisons=peer_comparisons,
    )


def create_teacher(session: Session, payload: TeacherPayload) -> TeacherRead:
    existing = get_teacher_by_no(session, payload.teacher_no)
    if existing:
        raise HTTPException(status_code=400, detail="工号已存在")
    _validate_teacher_payload(session, payload)
    item = Teacher(**payload.model_dump())
    session.add(item)
    session.flush()
    write_audit_log(
        session,
        module="teachers",
        action="create",
        target_type="teacher",
        target_id=str(item.id),
        detail_json={"teacher_no": item.teacher_no},
    )
    session.refresh(item)
    return _serialize_teacher(item)


def update_teacher(session: Session, teacher_id: int, payload: TeacherPayload) -> TeacherRead:
    item = get_teacher(session, teacher_id)
    if not item:
        raise HTTPException(status_code=404, detail="教师不存在")
    existing = get_teacher_by_no(session, payload.teacher_no)
    if existing and existing.id != teacher_id:
        raise HTTPException(status_code=400, detail="工号已存在")
    _validate_teacher_payload(session, payload)
    for key, value in payload.model_dump().items():
        setattr(item, key, value)
    session.flush()
    write_audit_log(
        session,
        module="teachers",
        action="update",
        target_type="teacher",
        target_id=str(item.id),
        detail_json={"teacher_no": item.teacher_no},
    )
    session.refresh(item)
    return _serialize_teacher(item)


def list_teacher_title_histories(session: Session, teacher_id: int) -> list[TeacherTitleHistoryRead]:
    teacher = session.scalar(
        select(Teacher).options(selectinload(Teacher.title_histories)).where(Teacher.id == teacher_id)
    )
    if not teacher:
        raise HTTPException(status_code=404, detail="教师不存在")
    return [
        _serialize_title_history(item)
        for item in sorted(
            teacher.title_histories,
            key=lambda current: (current.start_date or date.min, current.id),
            reverse=True,
        )
        if item.is_active
    ]


def save_teacher_title_histories(
    session: Session,
    teacher_id: int,
    payloads: list[TeacherTitleHistoryPayload],
) -> list[TeacherTitleHistoryRead]:
    teacher = session.scalar(
        select(Teacher).options(selectinload(Teacher.title_histories)).where(Teacher.id == teacher_id)
    )
    if not teacher:
        raise HTTPException(status_code=404, detail="教师不存在")
    for item in payloads:
        if item.start_date and item.end_date and item.start_date > item.end_date:
            raise HTTPException(status_code=400, detail="职称历史开始日期不能晚于结束日期")

    teacher.title_histories.clear()
    for payload in sorted(payloads, key=lambda current: (current.start_date or date.min, current.end_date or date.max)):
        teacher.title_histories.append(TeacherTitleHistory(**payload.model_dump()))
    teacher.title_code = _resolve_current_title_code(payloads, teacher.title_code)
    session.flush()
    write_audit_log(
        session,
        module="teachers",
        action="save_title_histories",
        target_type="teacher",
        target_id=str(teacher_id),
        detail_json={"history_count": len(payloads)},
    )
    session.refresh(teacher)
    return list_teacher_title_histories(session, teacher_id)


def _validate_teacher_payload(session: Session, payload: TeacherPayload) -> None:
    if payload.subject_id and not session.get(Subject, payload.subject_id):
        raise HTTPException(status_code=404, detail="学科不存在")


def import_teachers(
    session: Session,
    settings: Settings,
    *,
    filename: str | None,
    content: bytes,
    strategy: str,
) -> dict:
    job = create_import_job(session, "teachers", filename)
    job.started_at = datetime.now()
    importer = TeacherImporter(session, settings)
    result = importer.execute(filename=filename, content=content, strategy=strategy)
    job.finished_at = datetime.now()
    job.status = "success" if result.failed_rows == 0 else "partial_success"
    job.result_json = result.model_dump()
    write_audit_log(
        session,
        module="teachers",
        action="import",
        target_type="import_job",
        target_id=str(job.id),
        detail_json=result.model_dump(),
    )
    return {"job_id": job.id, **result.model_dump()}


def export_teachers(session: Session, settings: Settings) -> dict[str, str]:
    rows = [
        _serialize_teacher(item).model_dump(mode="json")
        for item in repo_list_teachers(session, page=1, page_size=10000)[0]
    ]
    file_path = export_teachers_workbook(settings, rows)
    return {"file_path": file_path}


def list_teaching_assignments(session: Session) -> list[TeachingAssignmentRead]:
    return [_serialize_assignment(item) for item in repo_list_teaching_assignments(session)]


def create_teaching_assignment(session: Session, payload: TeachingAssignmentPayload) -> TeachingAssignmentRead:
    teacher = session.get(Teacher, payload.teacher_id)
    semester = session.get(Semester, payload.semester_id)
    if not teacher:
        raise HTTPException(status_code=404, detail="教师不存在")
    if not semester:
        raise HTTPException(status_code=404, detail="学期不存在")
    grade = session.get(Grade, payload.grade_id) if payload.grade_id else None
    school_class = session.get(SchoolClass, payload.class_id) if payload.class_id else None
    subject = session.get(Subject, payload.subject_id) if payload.subject_id else None
    if payload.grade_id and not grade:
        raise HTTPException(status_code=404, detail="年级不存在")
    if payload.class_id and not school_class:
        raise HTTPException(status_code=404, detail="班级不存在")
    if payload.subject_id and not subject:
        raise HTTPException(status_code=404, detail="学科不存在")
    if grade and school_class and school_class.grade_id != grade.id:
        raise HTTPException(status_code=400, detail="班级与年级不匹配")

    existing_stmt = select(TeachingAssignment).where(
        TeachingAssignment.teacher_id == payload.teacher_id,
        TeachingAssignment.semester_id == payload.semester_id,
        TeachingAssignment.class_id == payload.class_id,
        TeachingAssignment.subject_id == payload.subject_id,
        TeachingAssignment.course_type == payload.course_type,
    )
    if session.scalar(existing_stmt):
        raise HTTPException(status_code=400, detail="任教关系已存在")

    item = TeachingAssignment(**payload.model_dump())
    if item.grade_id is None and school_class:
        item.grade_id = school_class.grade_id
    session.add(item)
    session.flush()
    session.refresh(item)
    write_audit_log(
        session,
        module="teachers",
        action="create_assignment",
        target_type="teaching_assignment",
        target_id=str(item.id),
        detail_json={"teacher_id": item.teacher_id},
    )
    return _serialize_assignment(item)


def _resolve_current_title_code(
    payloads: list[TeacherTitleHistoryPayload],
    fallback: str | None,
) -> str | None:
    if not payloads:
        return fallback
    active_items = [item for item in payloads if item.end_date is None]
    if active_items:
        active_items.sort(key=lambda current: current.start_date or date.min, reverse=True)
        return active_items[0].title_code
    ordered_items = sorted(payloads, key=lambda current: (current.end_date or date.min, current.start_date or date.min), reverse=True)
    return ordered_items[0].title_code if ordered_items else fallback


def _build_teacher_exam_trends(
    session: Session,
    teacher: Teacher,
    assignments: list[TeachingAssignment],
) -> list[TeacherExamTrendItem]:
    active_assignments = [item for item in assignments if item.is_active]
    semester_ids = {item.semester_id for item in active_assignments}
    if not semester_ids:
        return []
    exams = session.scalars(
        select(Exam)
        .options(joinedload(Exam.semester).joinedload(Semester.academic_year), selectinload(Exam.subjects))
        .where(Exam.semester_id.in_(semester_ids), Exam.is_active.is_(True))
        .order_by(Exam.exam_date.desc(), Exam.id.desc())
    ).unique().all()
    trends: list[TeacherExamTrendItem] = []
    for exam in exams:
        semester_assignments = [item for item in active_assignments if item.semester_id == exam.semester_id]
        summary = _build_teacher_exam_summary(session, teacher, exam, semester_assignments)
        if summary:
            trends.append(summary)
        if len(trends) >= 6:
            break
    return trends


def _build_teacher_exam_summary(
    session: Session,
    teacher: Teacher,
    exam: Exam,
    assignments: list[TeachingAssignment],
) -> TeacherExamTrendItem | None:
    score_records = [
        item
        for item in get_score_records_for_exam(session, exam.id)
        if item.score is not None and item.score_status == "normal"
    ]
    if not score_records:
        return None
    subject_meta_map = {item.subject_id: item for item in exam.subjects if item.is_active}
    matched_records = []
    matched_class_ids: set[int] = set()
    excellent_count = 0
    pass_count = 0

    for assignment in assignments:
        current_records = [
            record
            for record in score_records
            if record.student
            and record.student.current_class_id == assignment.class_id
            and record.subject_id == assignment.subject_id
        ]
        if not current_records:
            continue
        matched_records.extend(current_records)
        if assignment.class_id:
            matched_class_ids.add(assignment.class_id)
        meta = subject_meta_map.get(assignment.subject_id)
        for record in current_records:
            if meta and meta.excellent_line is not None and record.score is not None and record.score >= meta.excellent_line:
                excellent_count += 1
            if meta and meta.pass_line is not None and record.score is not None and record.score >= meta.pass_line:
                pass_count += 1

    if not matched_records:
        return None

    scores = [record.score for record in matched_records if record.score is not None]
    peer_rows = _build_subject_peer_rows(session, exam, teacher.subject_id)
    peer_average = safe_mean([item.overall_average for item in peer_rows if item.overall_average is not None])
    overall_average = safe_mean(scores) if scores else None
    return TeacherExamTrendItem(
        exam_id=exam.id,
        exam_name=exam.name,
        exam_date=exam.exam_date,
        semester_name=_serialize_semester_name(exam.semester),
        overall_average=overall_average,
        excellent_rate=calculate_rate(excellent_count, len(scores)) if scores else None,
        pass_rate=calculate_rate(pass_count, len(scores)) if scores else None,
        peer_average=peer_average,
        peer_gap=round((overall_average or 0) - peer_average, 2) if overall_average is not None and peer_average is not None else None,
        class_count=len(matched_class_ids),
    )


def _build_latest_peer_comparisons(
    session: Session,
    teacher: Teacher,
    exam_id: int | None,
) -> list[TeacherPeerComparisonItem]:
    if not exam_id:
        return []
    exam = session.scalar(
        select(Exam).options(selectinload(Exam.subjects)).where(Exam.id == exam_id)
    )
    if not exam:
        return []
    return _build_subject_peer_rows(session, exam, teacher.subject_id)


def _build_subject_peer_rows(
    session: Session,
    exam: Exam,
    subject_id: int | None,
) -> list[TeacherPeerComparisonItem]:
    if not subject_id:
        return []
    assignments = session.scalars(
        select(TeachingAssignment)
        .options(joinedload(TeachingAssignment.teacher), joinedload(TeachingAssignment.subject))
        .where(
            TeachingAssignment.semester_id == exam.semester_id,
            TeachingAssignment.subject_id == subject_id,
            TeachingAssignment.is_active.is_(True),
        )
        .order_by(TeachingAssignment.teacher_id, TeachingAssignment.id)
    ).all()
    if not assignments:
        return []
    meta = next((item for item in exam.subjects if item.subject_id == subject_id), None)
    score_records = [
        item
        for item in get_score_records_for_exam(session, exam.id)
        if item.score is not None and item.score_status == "normal" and item.subject_id == subject_id
    ]
    if not score_records:
        return []

    grouped_records: dict[int, list] = {}
    assignment_counts: dict[int, int] = {}
    teacher_names: dict[int, str] = {}
    subject_name = assignments[0].subject.name if assignments[0].subject else None

    for assignment in assignments:
        assignment_counts[assignment.teacher_id] = assignment_counts.get(assignment.teacher_id, 0) + 1
        teacher_names[assignment.teacher_id] = assignment.teacher.name if assignment.teacher else str(assignment.teacher_id)
        current_records = [
            record
            for record in score_records
            if record.student and record.student.current_class_id == assignment.class_id
        ]
        grouped_records.setdefault(assignment.teacher_id, []).extend(current_records)

    rows: list[TeacherPeerComparisonItem] = []
    for teacher_id, records in grouped_records.items():
        scores = [record.score for record in records if record.score is not None]
        if not scores:
            continue
        excellent_count = 0
        pass_count = 0
        for record in records:
            if meta and meta.excellent_line is not None and record.score is not None and record.score >= meta.excellent_line:
                excellent_count += 1
            if meta and meta.pass_line is not None and record.score is not None and record.score >= meta.pass_line:
                pass_count += 1
        rows.append(
            TeacherPeerComparisonItem(
                teacher_id=teacher_id,
                teacher_name=teacher_names.get(teacher_id, str(teacher_id)),
                subject_name=subject_name,
                overall_average=safe_mean(scores),
                excellent_rate=calculate_rate(excellent_count, len(scores)),
                pass_rate=calculate_rate(pass_count, len(scores)),
                assignment_count=assignment_counts.get(teacher_id, 0),
            )
        )
    rows.sort(
        key=lambda item: (
            -(item.overall_average or 0),
            item.teacher_name,
        )
    )
    for index, item in enumerate(rows, start=1):
        item.rank = index
    return rows


def _serialize_semester_name(semester: Semester | None) -> str | None:
    if not semester:
        return None
    if semester.academic_year:
        return f"{semester.academic_year.name} {semester.name}"
    return semester.name
