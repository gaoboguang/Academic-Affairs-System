from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date, timedelta

from fastapi import HTTPException
from sqlalchemy import desc, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.analytics.score_contexts import effective_class_id, load_exam_context_map
from app.models import (
    AttendanceRecord,
    BehaviorRecord,
    ClassHonor,
    Exam,
    Grade,
    SchoolClass,
    ScoreTotalSnapshot,
    Semester,
    Student,
    Teacher,
    TeachingAssignment,
)
from app.repositories.system import write_audit_log
from app.schemas.class_profile import (
    ClassHonorPayload,
    ClassHonorRead,
    ClassOverviewItem,
    ClassProfileResponse,
    ClassRiskSummary,
    ClassScoreSummary,
    ClassTeacherSummary,
    ClassesOverviewResponse,
    GradeOverviewGroup,
    GradeProfileResponse,
)
from app.schemas.student import StudentRead
from app.schemas.teacher import TeachingAssignmentRead
from app.services.students import _serialize_student
from app.services.teachers import _serialize_assignment
from app.utils.parsers import clean_text


def get_classes_overview(
    session: Session,
    *,
    grade_id: int | None = None,
    semester_id: int | None = None,
    exam_id: int | None = None,
) -> ClassesOverviewResponse:
    grade = _get_grade_or_404(session, grade_id) if grade_id else None
    semester = _resolve_semester(session, semester_id)
    exam = _resolve_exam(session, exam_id, grade_id=grade_id)
    classes = _list_classes(session, grade_id=grade.id if grade else None)
    items = _build_class_overview_items(session, classes, semester=semester, exam=exam)
    groups = _group_by_grade(items)
    return ClassesOverviewResponse(
        semester_id=semester.id if semester else None,
        semester_name=_format_semester_name(semester),
        exam_id=exam.id if exam else None,
        exam_name=exam.name if exam else None,
        grades=groups,
        total_classes=len(items),
        total_students=sum(item.active_student_count for item in items),
        total_honors=sum(item.honor_count for item in items),
    )


def get_class_profile(
    session: Session,
    class_id: int,
    *,
    semester_id: int | None = None,
    exam_id: int | None = None,
) -> ClassProfileResponse:
    school_class = _get_class_or_404(session, class_id)
    semester = _resolve_semester(session, semester_id)
    exam = _resolve_exam(session, exam_id, grade_id=school_class.grade_id)
    overview = _build_class_overview_items(session, [school_class], semester=semester, exam=exam)[0]
    students = session.scalars(
        select(Student)
        .options(
            joinedload(Student.current_grade),
            joinedload(Student.current_class),
            joinedload(Student.guardians),
        )
        .where(Student.current_class_id == class_id, Student.is_active.is_(True))
        .order_by(Student.student_no.asc(), Student.id.asc())
    ).unique().all()
    assignments = _list_assignments(session, [class_id], semester.id if semester else None).get(class_id, [])
    return ClassProfileResponse(
        overview=overview,
        honors=list_class_honors(session, class_id),
        students=[_serialize_student(item) for item in students],
        assignments=[_serialize_assignment(item) for item in assignments],
    )


def get_grade_profile(
    session: Session,
    grade_id: int,
    *,
    semester_id: int | None = None,
    exam_id: int | None = None,
) -> GradeProfileResponse:
    grade = _get_grade_or_404(session, grade_id)
    semester = _resolve_semester(session, semester_id)
    exam = _resolve_exam(session, exam_id, grade_id=grade_id)
    classes = _list_classes(session, grade_id=grade.id)
    items = _build_class_overview_items(session, classes, semester=semester, exam=exam)
    group = _build_grade_group(grade.id, grade.name, items)
    return GradeProfileResponse(grade=group, classes=items)


def list_class_honors(session: Session, class_id: int) -> list[ClassHonorRead]:
    _get_class_or_404(session, class_id)
    rows = session.scalars(
        select(ClassHonor)
        .where(ClassHonor.class_id == class_id, ClassHonor.is_active.is_(True))
        .order_by(desc(ClassHonor.awarded_on), desc(ClassHonor.id))
    ).all()
    return [_serialize_honor(item) for item in rows]


def create_class_honor(session: Session, class_id: int, payload: ClassHonorPayload) -> ClassHonorRead:
    _get_class_or_404(session, class_id)
    item = ClassHonor(class_id=class_id, **_normalize_honor_payload(payload).model_dump())
    session.add(item)
    _flush_or_400(session)
    session.refresh(item)
    write_audit_log(
        session,
        module="classes",
        action="create_honor",
        target_type="class_honor",
        target_id=str(item.id),
        detail_json={"class_id": class_id, "title": item.title},
    )
    return _serialize_honor(item)


def update_class_honor(
    session: Session,
    class_id: int,
    honor_id: int,
    payload: ClassHonorPayload,
) -> ClassHonorRead:
    _get_class_or_404(session, class_id)
    item = _get_honor_or_404(session, class_id, honor_id)
    normalized = _normalize_honor_payload(payload)
    for key, value in normalized.model_dump().items():
        setattr(item, key, value)
    _flush_or_400(session)
    session.refresh(item)
    write_audit_log(
        session,
        module="classes",
        action="update_honor",
        target_type="class_honor",
        target_id=str(item.id),
        detail_json={"class_id": class_id, "title": item.title},
    )
    return _serialize_honor(item)


def delete_class_honor(session: Session, class_id: int, honor_id: int) -> dict[str, str]:
    _get_class_or_404(session, class_id)
    item = _get_honor_or_404(session, class_id, honor_id)
    item.is_active = False
    session.flush()
    write_audit_log(
        session,
        module="classes",
        action="delete_honor",
        target_type="class_honor",
        target_id=str(item.id),
        detail_json={"class_id": class_id, "title": item.title},
    )
    return {"status": "ok"}


def _build_class_overview_items(
    session: Session,
    classes: list[SchoolClass],
    *,
    semester: Semester | None,
    exam: Exam | None,
) -> list[ClassOverviewItem]:
    class_ids = [item.id for item in classes]
    student_counts = _count_active_students(session, class_ids)
    assignments_by_class = _list_assignments(session, class_ids, semester.id if semester else None)
    honors_by_class = _list_recent_honors(session, class_ids)
    score_by_class = _build_score_summary_by_class(session, class_ids, exam)
    risk_by_class = _build_risk_summary_by_class(session, class_ids)

    result: list[ClassOverviewItem] = []
    for school_class in classes:
        assignments = assignments_by_class.get(school_class.id, [])
        teacher_summary = _build_teacher_summary(assignments)
        honors = honors_by_class.get(school_class.id, [])
        result.append(
            ClassOverviewItem(
                class_id=school_class.id,
                class_name=school_class.name,
                grade_id=school_class.grade_id,
                grade_name=school_class.grade.name if school_class.grade else None,
                class_type=school_class.class_type,
                head_teacher_id=school_class.head_teacher_id,
                head_teacher_name=school_class.head_teacher.name if school_class.head_teacher else None,
                student_count=school_class.student_count,
                active_student_count=student_counts.get(school_class.id, 0),
                teacher_count=len({item.teacher_id for item in assignments if item.is_active}),
                teacher_summary=teacher_summary[:8],
                honor_count=len(honors),
                latest_honor=_serialize_honor(honors[0]) if honors else None,
                score_summary=score_by_class.get(school_class.id, ClassScoreSummary()),
                risk_summary=risk_by_class.get(school_class.id, ClassRiskSummary()),
                teaching_complete=bool(teacher_summary),
            )
        )
    result.sort(key=lambda item: (item.grade_id, item.class_name))
    return result


def _group_by_grade(items: list[ClassOverviewItem]) -> list[GradeOverviewGroup]:
    grouped: dict[int, list[ClassOverviewItem]] = defaultdict(list)
    grade_names: dict[int, str] = {}
    for item in items:
        grouped[item.grade_id].append(item)
        grade_names[item.grade_id] = item.grade_name or str(item.grade_id)
    return [
        _build_grade_group(grade_id, grade_names[grade_id], grouped[grade_id])
        for grade_id in sorted(grouped)
    ]


def _build_grade_group(grade_id: int, grade_name: str, items: list[ClassOverviewItem]) -> GradeOverviewGroup:
    class_count = len(items)
    complete_count = sum(1 for item in items if item.teaching_complete)
    head_teacher_count = sum(1 for item in items if item.head_teacher_id)
    latest_exam_sample_count = sum(item.score_summary.sample_count for item in items)
    return GradeOverviewGroup(
        grade_id=grade_id,
        grade_name=grade_name,
        class_count=class_count,
        student_count=sum(item.student_count for item in items),
        active_student_count=sum(item.active_student_count for item in items),
        head_teacher_coverage=round(head_teacher_count / class_count, 4) if class_count else 0.0,
        teaching_complete_rate=round(complete_count / class_count, 4) if class_count else 0.0,
        latest_exam_sample_count=latest_exam_sample_count,
        honor_count=sum(item.honor_count for item in items),
        classes=sorted(items, key=lambda item: item.class_name),
    )


def _count_active_students(session: Session, class_ids: list[int]) -> dict[int, int]:
    if not class_ids:
        return {}
    rows = session.execute(
        select(Student.current_class_id, func.count(Student.id))
        .where(Student.current_class_id.in_(class_ids), Student.is_active.is_(True))
        .group_by(Student.current_class_id)
    ).all()
    return {int(class_id): int(count) for class_id, count in rows if class_id is not None}


def _list_assignments(
    session: Session,
    class_ids: list[int],
    semester_id: int | None,
) -> dict[int, list[TeachingAssignment]]:
    if not class_ids:
        return {}
    stmt = (
        select(TeachingAssignment)
        .options(
            joinedload(TeachingAssignment.teacher),
            joinedload(TeachingAssignment.semester).joinedload(Semester.academic_year),
            joinedload(TeachingAssignment.grade),
            joinedload(TeachingAssignment.school_class),
            joinedload(TeachingAssignment.subject),
        )
        .where(TeachingAssignment.class_id.in_(class_ids), TeachingAssignment.is_active.is_(True))
        .order_by(TeachingAssignment.subject_id.asc(), TeachingAssignment.teacher_id.asc(), TeachingAssignment.id.asc())
    )
    if semester_id:
        stmt = stmt.where(TeachingAssignment.semester_id == semester_id)
    result: dict[int, list[TeachingAssignment]] = defaultdict(list)
    for item in session.scalars(stmt).unique().all():
        if item.class_id is not None:
            result[item.class_id].append(item)
    return result


def _build_teacher_summary(assignments: list[TeachingAssignment]) -> list[ClassTeacherSummary]:
    seen: set[tuple[int, int | None, str | None]] = set()
    result: list[ClassTeacherSummary] = []
    for item in assignments:
        if not item.teacher:
            continue
        key = (item.teacher_id, item.subject_id, item.course_type)
        if key in seen:
            continue
        seen.add(key)
        result.append(
            ClassTeacherSummary(
                teacher_id=item.teacher_id,
                teacher_name=item.teacher.name,
                subject_id=item.subject_id,
                subject_name=item.subject.name if item.subject else None,
                course_type=item.course_type,
                weekly_periods_manual=item.weekly_periods_manual,
            )
        )
    return result


def _list_recent_honors(session: Session, class_ids: list[int]) -> dict[int, list[ClassHonor]]:
    if not class_ids:
        return {}
    rows = session.scalars(
        select(ClassHonor)
        .where(ClassHonor.class_id.in_(class_ids), ClassHonor.is_active.is_(True))
        .order_by(ClassHonor.class_id.asc(), desc(ClassHonor.awarded_on), desc(ClassHonor.id))
    ).all()
    result: dict[int, list[ClassHonor]] = defaultdict(list)
    for item in rows:
        result[item.class_id].append(item)
    return result


def _build_score_summary_by_class(
    session: Session,
    class_ids: list[int],
    exam: Exam | None,
) -> dict[int, ClassScoreSummary]:
    if not class_ids or not exam:
        return {}
    context_map = load_exam_context_map(session, exam.id)
    grouped: dict[int, list[ScoreTotalSnapshot]] = defaultdict(list)
    rows = session.scalars(
        select(ScoreTotalSnapshot)
        .options(joinedload(ScoreTotalSnapshot.student))
        .where(ScoreTotalSnapshot.exam_id == exam.id, ScoreTotalSnapshot.is_active.is_(True))
    ).all()
    class_id_set = set(class_ids)
    for snapshot in rows:
        resolved_class_id = effective_class_id(snapshot.student, context_map.get(snapshot.student_id))
        if resolved_class_id in class_id_set:
            grouped[resolved_class_id].append(snapshot)

    result: dict[int, ClassScoreSummary] = {}
    for class_id, items in grouped.items():
        scores = [item.total_score for item in items if item.total_score is not None]
        result[class_id] = ClassScoreSummary(
            exam_id=exam.id,
            exam_name=exam.name,
            sample_count=len(scores),
            average_score=round(sum(scores) / len(scores), 2) if scores else None,
            max_score=max(scores) if scores else None,
            min_score=min(scores) if scores else None,
        )
    return result


def _build_risk_summary_by_class(session: Session, class_ids: list[int]) -> dict[int, ClassRiskSummary]:
    if not class_ids:
        return {}
    since = date.today() - timedelta(days=30)
    class_id_set = set(class_ids)
    attendance_rows = session.execute(
        select(Student.current_class_id, AttendanceRecord.status, func.count(AttendanceRecord.id))
        .join(Student, AttendanceRecord.student_id == Student.id)
        .where(
            Student.current_class_id.in_(class_ids),
            Student.is_active.is_(True),
            AttendanceRecord.is_active.is_(True),
            AttendanceRecord.record_date >= since,
        )
        .group_by(Student.current_class_id, AttendanceRecord.status)
    ).all()
    behavior_rows = session.execute(
        select(Student.current_class_id, BehaviorRecord.severity, func.count(BehaviorRecord.id))
        .join(Student, BehaviorRecord.student_id == Student.id)
        .where(
            Student.current_class_id.in_(class_ids),
            Student.is_active.is_(True),
            BehaviorRecord.is_active.is_(True),
            BehaviorRecord.record_date >= since,
        )
        .group_by(Student.current_class_id, BehaviorRecord.severity)
    ).all()
    result = {class_id: ClassRiskSummary() for class_id in class_id_set}
    attendance_by_class: dict[int, Counter[str]] = defaultdict(Counter)
    behavior_by_class: dict[int, Counter[str]] = defaultdict(Counter)
    for class_id, status, count in attendance_rows:
        if class_id is not None:
            attendance_by_class[int(class_id)][status] += int(count)
    for class_id, severity, count in behavior_rows:
        if class_id is not None:
            behavior_by_class[int(class_id)][severity] += int(count)
    for class_id in class_id_set:
        attendance = attendance_by_class.get(class_id, Counter())
        behavior = behavior_by_class.get(class_id, Counter())
        attendance_risk = attendance.get("truancy", 0) + attendance.get("late", 0) + attendance.get("early_leave", 0)
        behavior_risk = behavior.get("severe", 0) + behavior.get("high", 0)
        result[class_id] = ClassRiskSummary(
            follow_up_count=attendance_risk + behavior_risk,
            urgent_count=attendance.get("truancy", 0) + behavior.get("severe", 0),
            attendance_risk_count=attendance_risk,
            behavior_risk_count=behavior_risk,
        )
    return result


def _resolve_semester(session: Session, semester_id: int | None) -> Semester | None:
    if semester_id:
        item = session.get(Semester, semester_id)
        if not item:
            raise HTTPException(status_code=404, detail="学期不存在")
        return item
    return session.scalar(
        select(Semester)
        .options(joinedload(Semester.academic_year))
        .where(Semester.is_current.is_(True), Semester.is_active.is_(True))
        .order_by(desc(Semester.start_date), desc(Semester.id))
    )


def _resolve_exam(session: Session, exam_id: int | None, *, grade_id: int | None) -> Exam | None:
    if exam_id:
        item = session.get(Exam, exam_id)
        if not item:
            raise HTTPException(status_code=404, detail="考试不存在")
        return item
    stmt = select(Exam).where(Exam.is_active.is_(True)).order_by(desc(Exam.exam_date), desc(Exam.id))
    rows = session.scalars(stmt).all()
    for exam in rows:
        scope = exam.grade_scope_json or []
        if grade_id is None or not scope or grade_id in scope:
            return exam
    return None


def _list_classes(session: Session, grade_id: int | None = None) -> list[SchoolClass]:
    stmt = (
        select(SchoolClass)
        .options(joinedload(SchoolClass.grade), joinedload(SchoolClass.head_teacher))
        .where(SchoolClass.is_active.is_(True))
        .order_by(SchoolClass.grade_id.asc(), SchoolClass.name.asc())
    )
    if grade_id:
        stmt = stmt.where(SchoolClass.grade_id == grade_id)
    return list(session.scalars(stmt).unique().all())


def _get_class_or_404(session: Session, class_id: int) -> SchoolClass:
    item = session.scalar(
        select(SchoolClass)
        .options(joinedload(SchoolClass.grade), joinedload(SchoolClass.head_teacher))
        .where(SchoolClass.id == class_id, SchoolClass.is_active.is_(True))
    )
    if not item:
        raise HTTPException(status_code=404, detail="班级不存在")
    return item


def _get_grade_or_404(session: Session, grade_id: int | None) -> Grade:
    item = session.get(Grade, grade_id) if grade_id else None
    if not item or not item.is_active:
        raise HTTPException(status_code=404, detail="年级不存在")
    return item


def _get_honor_or_404(session: Session, class_id: int, honor_id: int) -> ClassHonor:
    item = session.scalar(
        select(ClassHonor).where(
            ClassHonor.id == honor_id,
            ClassHonor.class_id == class_id,
            ClassHonor.is_active.is_(True),
        )
    )
    if not item:
        raise HTTPException(status_code=404, detail="班级荣誉不存在")
    return item


def _normalize_honor_payload(payload: ClassHonorPayload) -> ClassHonorPayload:
    title = clean_text(payload.title)
    if not title:
        raise HTTPException(status_code=400, detail="荣誉标题不能为空")
    return ClassHonorPayload(
        title=title,
        honor_level=clean_text(payload.honor_level),
        awarded_on=payload.awarded_on,
        source=clean_text(payload.source),
        note=clean_text(payload.note),
        is_active=payload.is_active,
    )


def _serialize_honor(item: ClassHonor) -> ClassHonorRead:
    return ClassHonorRead.model_validate(item)


def _format_semester_name(semester: Semester | None) -> str | None:
    if not semester:
        return None
    if semester.academic_year:
        return f"{semester.academic_year.name} {semester.name}"
    return semester.name


def _flush_or_400(session: Session) -> None:
    try:
        session.flush()
    except IntegrityError as exc:
        raise HTTPException(status_code=400, detail="班级荣誉已存在或数据约束冲突。") from exc
