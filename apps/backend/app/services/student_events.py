from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from zipfile import BadZipFile

from fastapi import HTTPException
from openpyxl.utils.exceptions import InvalidFileException
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session, joinedload

from app.core.config import Settings
from app.importers.student_events import AttendanceImporter, BehaviorImporter
from app.models import (
    AttendanceRecord,
    BehaviorRecord,
    Exam,
    Grade,
    ScoreTotalSnapshot,
    SchoolClass,
    Student,
    StudentGrowthRecord,
)
from app.repositories.system import create_import_job, write_audit_log
from app.schemas.student_event import (
    AdviserActionItem,
    AdviserDashboardOverview,
    AdviserDashboardResponse,
    AdviserDashboardScoreSummary,
    AdviserRiskStudentItem,
    AttendanceRecordListResponse,
    AttendanceRecordRead,
    AttendanceRiskSummary,
    BehaviorRecordListResponse,
    BehaviorRecordRead,
    BehaviorRiskSummary,
    GrowthRiskSummary,
    ScoreRiskSummary,
    StudentRiskResponse,
)


RISK_LABELS = {
    "urgent": "紧急跟进",
    "follow_up": "需要跟进",
    "watch": "持续观察",
    "normal": "暂无明显风险",
}
RISK_PRIORITY = {"urgent": 0, "follow_up": 1, "watch": 2, "normal": 3}


def import_attendance_records(
    session: Session,
    settings: Settings,
    *,
    filename: str | None,
    content: bytes,
) -> dict:
    job = create_import_job(session, "attendance", filename)
    job.started_at = datetime.now()
    importer = AttendanceImporter(session, settings, source_batch_id=job.id)
    try:
        result = importer.execute(filename=filename, content=content)
    except (ValueError, InvalidFileException, BadZipFile) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    job.finished_at = datetime.now()
    job.status = result.status
    job.result_json = result.model_dump()
    write_audit_log(
        session,
        module="attendance",
        action="import",
        target_type="import_job",
        target_id=str(job.id),
        detail_json=result.model_dump(),
    )
    if result.updated_rows:
        write_audit_log(
            session,
            module="attendance",
            action="overwrite",
            target_type="import_job",
            target_id=str(job.id),
            detail_json={"updated_rows": result.updated_rows, "source_filename": filename},
        )
    return {"job_id": job.id, **result.model_dump()}


def import_behavior_records(
    session: Session,
    settings: Settings,
    *,
    filename: str | None,
    content: bytes,
) -> dict:
    job = create_import_job(session, "behavior", filename)
    job.started_at = datetime.now()
    importer = BehaviorImporter(session, settings, source_batch_id=job.id)
    try:
        result = importer.execute(filename=filename, content=content)
    except (ValueError, InvalidFileException, BadZipFile) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    job.finished_at = datetime.now()
    job.status = result.status
    job.result_json = result.model_dump()
    write_audit_log(
        session,
        module="behavior",
        action="import",
        target_type="import_job",
        target_id=str(job.id),
        detail_json=result.model_dump(),
    )
    return {"job_id": job.id, **result.model_dump()}


def list_attendance_records(
    session: Session,
    *,
    student_id: int | None = None,
    grade_id: int | None = None,
    class_id: int | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    limit: int = 1000,
) -> AttendanceRecordListResponse:
    stmt = (
        select(AttendanceRecord)
        .join(Student, AttendanceRecord.student_id == Student.id)
        .options(
            joinedload(AttendanceRecord.student).joinedload(Student.current_grade),
            joinedload(AttendanceRecord.student).joinedload(Student.current_class),
        )
        .where(AttendanceRecord.is_active.is_(True))
    )
    if student_id:
        stmt = stmt.where(AttendanceRecord.student_id == student_id)
    if grade_id:
        stmt = stmt.where(Student.current_grade_id == grade_id)
    if class_id:
        stmt = stmt.where(Student.current_class_id == class_id)
    if start_date:
        stmt = stmt.where(AttendanceRecord.record_date >= start_date)
    if end_date:
        stmt = stmt.where(AttendanceRecord.record_date <= end_date)
    rows = session.scalars(
        stmt.order_by(desc(AttendanceRecord.record_date), desc(AttendanceRecord.id)).limit(limit)
    ).all()
    return AttendanceRecordListResponse(total=len(rows), items=[_serialize_attendance_record(item) for item in rows])


def list_behavior_records(
    session: Session,
    *,
    student_id: int | None = None,
    grade_id: int | None = None,
    class_id: int | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    limit: int = 1000,
) -> BehaviorRecordListResponse:
    stmt = (
        select(BehaviorRecord)
        .join(Student, BehaviorRecord.student_id == Student.id)
        .options(
            joinedload(BehaviorRecord.student).joinedload(Student.current_grade),
            joinedload(BehaviorRecord.student).joinedload(Student.current_class),
        )
        .where(BehaviorRecord.is_active.is_(True))
    )
    if student_id:
        stmt = stmt.where(BehaviorRecord.student_id == student_id)
    if grade_id:
        stmt = stmt.where(Student.current_grade_id == grade_id)
    if class_id:
        stmt = stmt.where(Student.current_class_id == class_id)
    if start_date:
        stmt = stmt.where(BehaviorRecord.record_date >= start_date)
    if end_date:
        stmt = stmt.where(BehaviorRecord.record_date <= end_date)
    rows = session.scalars(
        stmt.order_by(desc(BehaviorRecord.record_date), desc(BehaviorRecord.id)).limit(limit)
    ).all()
    return BehaviorRecordListResponse(total=len(rows), items=[_serialize_behavior_record(item) for item in rows])


def get_adviser_dashboard(
    session: Session,
    *,
    grade_id: int | None = None,
    class_id: int | None = None,
    exam_id: int | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
) -> AdviserDashboardResponse:
    start_date, end_date = _normalize_date_range(start_date, end_date)
    if class_id:
        school_class = session.get(SchoolClass, class_id)
        if not school_class:
            raise HTTPException(status_code=404, detail="班级不存在")
        grade_id = grade_id or school_class.grade_id
    if grade_id and not session.get(Grade, grade_id):
        raise HTTPException(status_code=404, detail="年级不存在")

    students = _list_scope_students(session, grade_id=grade_id, class_id=class_id)
    student_ids = [item.id for item in students]
    exam = _resolve_dashboard_exam(session, exam_id=exam_id, grade_id=grade_id)

    score_by_student = _build_score_summary_map(session, students, exam)
    attendance_by_student, attendance_summary = _build_attendance_summary_map(
        session,
        student_ids,
        start_date=start_date,
        end_date=end_date,
    )
    behavior_by_student, behavior_summary = _build_behavior_summary_map(
        session,
        student_ids,
        start_date=start_date,
        end_date=end_date,
    )
    growth_by_student = _build_growth_summary_map(session, student_ids)

    risk_responses = [
        _build_student_risk_response(
            student,
            score_by_student.get(student.id, ScoreRiskSummary()),
            attendance_by_student.get(student.id, AttendanceRiskSummary()),
            behavior_by_student.get(student.id, BehaviorRiskSummary()),
            growth_by_student.get(student.id, GrowthRiskSummary()),
        )
        for student in students
    ]
    risk_students = [
        _to_risk_student_item(item)
        for item in sorted(
            risk_responses,
            key=lambda current: (RISK_PRIORITY[current.risk_level], current.class_name or "", current.student_name),
        )
        if item.risk_level != "normal"
    ]
    score_summary = _build_dashboard_score_summary(exam, score_by_student)
    data_flags = _build_dashboard_data_flags(score_summary, attendance_summary, behavior_summary)
    overview = AdviserDashboardOverview(
        student_count=len(students),
        score_sample_count=score_summary.sample_count,
        attendance_status="已导入" if attendance_summary.imported else "未导入",
        behavior_status="已导入" if behavior_summary.imported else "未导入",
        absence_risk_count=sum(1 for item in risk_responses if item.attendance_summary.truancy_count > 0),
        behavior_risk_count=sum(1 for item in risk_responses if item.behavior_summary.severe_count > 0),
        follow_up_count=sum(1 for item in risk_responses if item.risk_level in {"urgent", "follow_up"}),
    )

    return AdviserDashboardResponse(
        grade_id=grade_id,
        grade_name=students[0].current_grade.name if students and students[0].current_grade else None,
        class_id=class_id,
        class_name=students[0].current_class.name if class_id and students and students[0].current_class else None,
        exam_id=exam.id if exam else None,
        exam_name=exam.name if exam else None,
        start_date=start_date,
        end_date=end_date,
        overview=overview,
        score_summary=score_summary,
        attendance_summary=attendance_summary,
        behavior_summary=behavior_summary,
        risk_students=risk_students[:100],
        action_items=_build_adviser_actions(risk_responses, data_flags),
        data_flags=data_flags,
    )


def get_student_risk(
    session: Session,
    student_id: int,
    *,
    exam_id: int | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
) -> StudentRiskResponse:
    start_date, end_date = _normalize_date_range(start_date, end_date)
    student = session.scalar(
        select(Student)
        .options(joinedload(Student.current_grade), joinedload(Student.current_class))
        .where(Student.id == student_id)
    )
    if not student:
        raise HTTPException(status_code=404, detail="学生不存在")
    exam = _resolve_dashboard_exam(session, exam_id=exam_id, grade_id=student.current_grade_id)
    score_summary = _build_score_summary_map(session, [student], exam).get(student.id, ScoreRiskSummary())
    attendance_by_student, _attendance_summary = _build_attendance_summary_map(
        session,
        [student.id],
        start_date=start_date,
        end_date=end_date,
    )
    behavior_by_student, _behavior_summary = _build_behavior_summary_map(
        session,
        [student.id],
        start_date=start_date,
        end_date=end_date,
    )
    growth_summary = _build_growth_summary_map(session, [student.id]).get(student.id, GrowthRiskSummary())
    return _build_student_risk_response(
        student,
        score_summary,
        attendance_by_student.get(student.id, AttendanceRiskSummary()),
        behavior_by_student.get(student.id, BehaviorRiskSummary()),
        growth_summary,
    )


def _serialize_attendance_record(item: AttendanceRecord) -> AttendanceRecordRead:
    student = item.student
    return AttendanceRecordRead(
        id=item.id,
        student_id=item.student_id,
        student_no=student.student_no if student else None,
        student_name=student.name if student else None,
        grade_id=student.current_grade_id if student else None,
        grade_name=student.current_grade.name if student and student.current_grade else None,
        class_id=student.current_class_id if student else None,
        class_name=student.current_class.name if student and student.current_class else None,
        record_date=item.record_date,
        scope=item.scope,
        period_index=item.period_index,
        status=item.status,
        reason=item.reason,
        note=item.note,
        source_batch_id=item.source_batch_id,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


def _serialize_behavior_record(item: BehaviorRecord) -> BehaviorRecordRead:
    student = item.student
    return BehaviorRecordRead(
        id=item.id,
        student_id=item.student_id,
        student_no=student.student_no if student else None,
        student_name=student.name if student else None,
        grade_id=student.current_grade_id if student else None,
        grade_name=student.current_grade.name if student and student.current_grade else None,
        class_id=student.current_class_id if student else None,
        class_name=student.current_class.name if student and student.current_class else None,
        record_date=item.record_date,
        category=item.category,
        severity=item.severity,
        title=item.title,
        description=item.description,
        handler_name=item.handler_name,
        points_delta=item.points_delta,
        attachment_path=item.attachment_path,
        source_batch_id=item.source_batch_id,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


def _normalize_date_range(start_date: date | None, end_date: date | None) -> tuple[date, date]:
    current_end = end_date or date.today()
    current_start = start_date or (current_end - timedelta(days=29))
    if current_start > current_end:
        raise HTTPException(status_code=400, detail="开始日期不能晚于结束日期")
    return current_start, current_end


def _list_scope_students(session: Session, *, grade_id: int | None, class_id: int | None) -> list[Student]:
    stmt = (
        select(Student)
        .options(joinedload(Student.current_grade), joinedload(Student.current_class))
        .where(Student.is_active.is_(True))
    )
    if grade_id:
        stmt = stmt.where(Student.current_grade_id == grade_id)
    if class_id:
        stmt = stmt.where(Student.current_class_id == class_id)
    return session.scalars(stmt.order_by(Student.current_class_id, Student.student_no)).all()


def _resolve_dashboard_exam(session: Session, *, exam_id: int | None, grade_id: int | None) -> Exam | None:
    if exam_id:
        exam = session.get(Exam, exam_id)
        if not exam:
            raise HTTPException(status_code=404, detail="考试不存在")
        return exam
    rows = session.scalars(
        select(Exam)
        .where(Exam.is_active.is_(True), Exam.status != "draft")
        .order_by(desc(Exam.exam_date), desc(Exam.id))
        .limit(20)
    ).all()
    if grade_id:
        return next((item for item in rows if not item.grade_scope_json or grade_id in item.grade_scope_json), None)
    return rows[0] if rows else None


def _build_score_summary_map(
    session: Session,
    students: list[Student],
    exam: Exam | None,
) -> dict[int, ScoreRiskSummary]:
    if not students:
        return {}
    if not exam:
        return {student.id: ScoreRiskSummary() for student in students}
    student_ids = [item.id for item in students]
    current_rows = session.scalars(
        select(ScoreTotalSnapshot).where(
            ScoreTotalSnapshot.exam_id == exam.id,
            ScoreTotalSnapshot.student_id.in_(student_ids),
        )
    ).all()
    previous_exam = session.scalar(
        select(Exam)
        .where(Exam.exam_date < exam.exam_date, Exam.is_active.is_(True), Exam.status != "draft")
        .order_by(desc(Exam.exam_date), desc(Exam.id))
        .limit(1)
    )
    previous_by_student: dict[int, ScoreTotalSnapshot] = {}
    if previous_exam:
        previous_by_student = {
            item.student_id: item
            for item in session.scalars(
                select(ScoreTotalSnapshot).where(
                    ScoreTotalSnapshot.exam_id == previous_exam.id,
                    ScoreTotalSnapshot.student_id.in_(student_ids),
                )
            ).all()
        }

    result = {student.id: ScoreRiskSummary(exam_id=exam.id, exam_name=exam.name) for student in students}
    for row in current_rows:
        previous = previous_by_student.get(row.student_id)
        delta = row.total_score - previous.total_score if previous else None
        percentile = row.grade_percentile if row.grade_percentile is not None else row.class_percentile
        result[row.student_id] = ScoreRiskSummary(
            imported=True,
            exam_id=exam.id,
            exam_name=exam.name,
            sample_count=1,
            total_score=row.total_score,
            class_rank=row.class_rank,
            grade_rank=row.grade_rank,
            previous_total_score=previous.total_score if previous else None,
            total_score_delta=delta,
            low_score=bool(percentile is not None and percentile <= 0.25),
            decline_risk=bool(delta is not None and delta <= -10),
        )
    return result


def _build_attendance_summary_map(
    session: Session,
    student_ids: list[int],
    *,
    start_date: date,
    end_date: date,
) -> tuple[dict[int, AttendanceRiskSummary], AttendanceRiskSummary]:
    result = {student_id: AttendanceRiskSummary() for student_id in student_ids}
    if not student_ids:
        return result, AttendanceRiskSummary()
    rows = session.scalars(
        select(AttendanceRecord).where(
            AttendanceRecord.is_active.is_(True),
            AttendanceRecord.student_id.in_(student_ids),
            AttendanceRecord.record_date >= start_date,
            AttendanceRecord.record_date <= end_date,
        )
    ).all()
    grouped: dict[int, list[AttendanceRecord]] = defaultdict(list)
    for row in rows:
        grouped[row.student_id].append(row)
    for student_id, items in grouped.items():
        result[student_id] = _summarize_attendance(items)
    return result, _summarize_attendance(rows)


def _build_behavior_summary_map(
    session: Session,
    student_ids: list[int],
    *,
    start_date: date,
    end_date: date,
) -> tuple[dict[int, BehaviorRiskSummary], BehaviorRiskSummary]:
    result = {student_id: BehaviorRiskSummary() for student_id in student_ids}
    if not student_ids:
        return result, BehaviorRiskSummary()
    rows = session.scalars(
        select(BehaviorRecord).where(
            BehaviorRecord.is_active.is_(True),
            BehaviorRecord.student_id.in_(student_ids),
            BehaviorRecord.record_date >= start_date,
            BehaviorRecord.record_date <= end_date,
        )
    ).all()
    grouped: dict[int, list[BehaviorRecord]] = defaultdict(list)
    for row in rows:
        grouped[row.student_id].append(row)
    for student_id, items in grouped.items():
        result[student_id] = _summarize_behavior(items)
    return result, _summarize_behavior(rows)


def _build_growth_summary_map(session: Session, student_ids: list[int]) -> dict[int, GrowthRiskSummary]:
    result = {student_id: GrowthRiskSummary() for student_id in student_ids}
    if not student_ids:
        return result
    rows = session.execute(
        select(
            StudentGrowthRecord.student_id,
            func.count(StudentGrowthRecord.id),
            func.max(StudentGrowthRecord.occurred_on),
        )
        .where(StudentGrowthRecord.is_active.is_(True), StudentGrowthRecord.student_id.in_(student_ids))
        .group_by(StudentGrowthRecord.student_id)
    ).all()
    for student_id, record_count, latest_date in rows:
        result[student_id] = GrowthRiskSummary(record_count=record_count, latest_record_date=latest_date)
    return result


def _summarize_attendance(rows: list[AttendanceRecord]) -> AttendanceRiskSummary:
    counter = Counter(row.status for row in rows)
    return AttendanceRiskSummary(
        imported=bool(rows),
        total_records=len(rows),
        normal_count=counter.get("正常", 0),
        late_count=counter.get("迟到", 0),
        early_leave_count=counter.get("早退", 0),
        sick_leave_count=counter.get("病假", 0),
        personal_leave_count=counter.get("事假", 0),
        truancy_count=counter.get("旷课", 0),
        other_count=counter.get("其他", 0),
        status_counts=dict(counter),
    )


def _summarize_behavior(rows: list[BehaviorRecord]) -> BehaviorRiskSummary:
    category_counter = Counter(row.category for row in rows)
    severity_counter = Counter(row.severity for row in rows)
    severe_count = sum(
        1
        for row in rows
        if row.category in {"安全事件", "心理关注"} or row.severity in {"高", "严重"}
    )
    return BehaviorRiskSummary(
        imported=bool(rows),
        total_records=len(rows),
        positive_count=category_counter.get("表扬", 0),
        discipline_count=category_counter.get("违纪", 0) + category_counter.get("奖惩", 0),
        severe_count=severe_count,
        category_counts=dict(category_counter),
        severity_counts=dict(severity_counter),
    )


def _build_student_risk_response(
    student: Student,
    score_summary: ScoreRiskSummary,
    attendance_summary: AttendanceRiskSummary,
    behavior_summary: BehaviorRiskSummary,
    growth_summary: GrowthRiskSummary,
) -> StudentRiskResponse:
    reasons: list[str] = []
    actions: list[str] = []
    data_flags: list[str] = []
    signal_count = 0

    if not score_summary.imported:
        data_flags.append("成绩未导入或当前考试无该生样本")
        reasons.append("成绩样本不完整")
    elif score_summary.total_score_delta is not None and score_summary.total_score_delta <= -30:
        signal_count += 2
        reasons.append(f"总分较上次下降 {abs(score_summary.total_score_delta):.1f} 分")
        actions.append("复核成绩并安排学科跟进")
    elif score_summary.decline_risk:
        signal_count += 1
        reasons.append("成绩较上次明显下滑")
        actions.append("复核成绩")
    elif score_summary.low_score:
        signal_count += 1
        reasons.append("成绩处于低位区间")
        actions.append("安排学习支持")

    attendance_risk_points = (
        attendance_summary.late_count
        + attendance_summary.early_leave_count
        + attendance_summary.sick_leave_count
        + attendance_summary.personal_leave_count
    )
    if not attendance_summary.imported:
        data_flags.append("考勤未导入")
    if attendance_summary.truancy_count > 0:
        signal_count += 2
        reasons.append(f"存在旷课 {attendance_summary.truancy_count} 次")
        actions.append("当日核实考勤并联系家长")
    elif attendance_risk_points >= 3:
        signal_count += 1
        reasons.append(f"迟到/早退/请假累计 {attendance_risk_points} 次")
        actions.append("与学生谈话并关注出勤")
    elif attendance_risk_points > 0:
        reasons.append("近期出勤有轻微波动")

    if not behavior_summary.imported:
        data_flags.append("行为记录未导入")
    if behavior_summary.severe_count > 0:
        signal_count += 2
        reasons.append(f"存在高关注行为 {behavior_summary.severe_count} 条")
        actions.append("查看成长档案并形成跟进记录")
    elif behavior_summary.discipline_count > 0:
        signal_count += 1
        reasons.append(f"违纪/奖惩记录 {behavior_summary.discipline_count} 条")
        actions.append("核对行为记录")
    elif behavior_summary.total_records > 0:
        reasons.append("近期有行为记录需持续观察")

    risk_level = "normal"
    if attendance_summary.truancy_count > 0 or behavior_summary.severe_count > 0:
        risk_level = "urgent"
    elif score_summary.total_score_delta is not None and score_summary.total_score_delta <= -30:
        risk_level = "urgent"
    elif signal_count >= 3:
        risk_level = "urgent"
    elif signal_count >= 1:
        risk_level = "follow_up"
    elif reasons or data_flags:
        risk_level = "watch"

    if not actions and data_flags:
        actions.append("补录或复核缺失数据")
    if not actions and risk_level == "normal":
        actions.append("保持常规观察")

    return StudentRiskResponse(
        student_id=student.id,
        student_no=student.student_no,
        student_name=student.name,
        grade_id=student.current_grade_id,
        grade_name=student.current_grade.name if student.current_grade else None,
        class_id=student.current_class_id,
        class_name=student.current_class.name if student.current_class else None,
        risk_level=risk_level,
        risk_label=RISK_LABELS[risk_level],
        reasons=reasons or ["暂无明显风险"],
        suggested_actions=_unique_keep_order(actions),
        data_flags=data_flags,
        score_summary=score_summary,
        attendance_summary=attendance_summary,
        behavior_summary=behavior_summary,
        growth_summary=growth_summary,
    )


def _to_risk_student_item(item: StudentRiskResponse) -> AdviserRiskStudentItem:
    return AdviserRiskStudentItem(
        student_id=item.student_id,
        student_no=item.student_no,
        student_name=item.student_name,
        class_id=item.class_id,
        class_name=item.class_name,
        risk_level=item.risk_level,
        risk_label=item.risk_label,
        primary_reason=item.reasons[0] if item.reasons else "需复核",
        reasons=item.reasons,
        suggested_action=item.suggested_actions[0] if item.suggested_actions else "查看学生详情",
    )


def _build_dashboard_score_summary(
    exam: Exam | None,
    score_by_student: dict[int, ScoreRiskSummary],
) -> AdviserDashboardScoreSummary:
    imported = [item for item in score_by_student.values() if item.imported and item.total_score is not None]
    average_total_score = (
        round(sum(float(item.total_score or 0) for item in imported) / len(imported), 2)
        if imported
        else None
    )
    return AdviserDashboardScoreSummary(
        imported=bool(imported),
        exam_id=exam.id if exam else None,
        exam_name=exam.name if exam else None,
        sample_count=len(imported),
        average_total_score=average_total_score,
        low_score_count=sum(1 for item in imported if item.low_score),
        decline_count=sum(1 for item in imported if item.decline_risk),
    )


def _build_dashboard_data_flags(
    score_summary: AdviserDashboardScoreSummary,
    attendance_summary: AttendanceRiskSummary,
    behavior_summary: BehaviorRiskSummary,
) -> list[str]:
    flags: list[str] = []
    if not score_summary.imported:
        flags.append("成绩数据未导入或当前范围无成绩样本")
    if not attendance_summary.imported:
        flags.append("考勤数据未导入")
    if not behavior_summary.imported:
        flags.append("行为数据未导入")
    return flags


def _build_adviser_actions(
    risk_responses: list[StudentRiskResponse],
    data_flags: list[str],
) -> list[AdviserActionItem]:
    urgent_ids = [item.student_id for item in risk_responses if item.risk_level == "urgent"]
    follow_up_ids = [item.student_id for item in risk_responses if item.risk_level == "follow_up"]
    score_ids = [item.student_id for item in risk_responses if item.score_summary.decline_risk or item.score_summary.low_score]
    growth_ids = [item.student_id for item in risk_responses if item.risk_level in {"urgent", "follow_up"}]
    actions: list[AdviserActionItem] = []
    if urgent_ids or follow_up_ids:
        actions.append(
            AdviserActionItem(
                action_type="conversation",
                title="安排学生谈话",
                count=len(urgent_ids) + len(follow_up_ids),
                student_ids=[*urgent_ids, *follow_up_ids],
                target_route="/students",
            )
        )
    if urgent_ids:
        actions.append(
            AdviserActionItem(
                action_type="family_contact",
                title="联系家长核实",
                count=len(urgent_ids),
                student_ids=urgent_ids,
                target_route="/students",
            )
        )
    if data_flags:
        actions.append(
            AdviserActionItem(
                action_type="data_backfill",
                title="补录缺失数据",
                count=len(data_flags),
                target_route="/import-center",
            )
        )
    if score_ids:
        actions.append(
            AdviserActionItem(
                action_type="score_review",
                title="复核成绩波动",
                count=len(score_ids),
                student_ids=score_ids,
                target_route="/analytics",
            )
        )
    if growth_ids:
        actions.append(
            AdviserActionItem(
                action_type="growth_archive",
                title="查看成长档案",
                count=len(growth_ids),
                student_ids=growth_ids,
                target_route="/archives",
            )
        )
    actions.append(
        AdviserActionItem(
            action_type="report_export",
            title="生成班主任周报",
            count=1,
            target_route="/reports",
        )
    )
    return actions


def _unique_keep_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result
