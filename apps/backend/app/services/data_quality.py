from __future__ import annotations

from datetime import date, datetime

from fastapi import HTTPException
from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.models import Exam, ExamSubject, SchoolClass, ScoreRecord, Student, StudentClassHistory, Subject, TimetableEntry
from app.repositories.system import write_audit_log
from app.schemas.system import DataQualityIssueRead, DataRepairActionRead, DataRepairScanRead

SEVERITY_ORDER = {"error": 0, "warning": 1, "info": 2}
REPAIR_ACTIONS = {
    "refresh_class_student_counts": {
        "title": "重算班级人数",
        "description": "按当前学生归属重新回填每个班级的在册人数。",
        "affected_issue_codes": ["class_student_count_mismatch"],
    },
    "sync_student_grade_from_class": {
        "title": "同步学生当前年级",
        "description": "将学生当前年级修正为其当前班级所属年级。",
        "affected_issue_codes": ["student_grade_class_mismatch"],
    },
    "repair_student_class_history": {
        "title": "补齐学籍历史",
        "description": "补建与当前年级班级一致的开放历史记录，并关闭冲突历史。",
        "affected_issue_codes": ["student_open_history_missing"],
    },
}
ISSUE_ACTION_MAP = {
    "class_student_count_mismatch": "refresh_class_student_counts",
    "student_grade_class_mismatch": "sync_student_grade_from_class",
    "student_open_history_missing": "repair_student_class_history",
}


def build_data_quality_issues(session: Session, limit: int | None = None) -> list[DataQualityIssueRead]:
    issues = [
        _scan_class_student_count_mismatch(session),
        _scan_student_grade_class_mismatch(session),
        _scan_student_history_gap(session),
        _scan_timetable_unmatched(session),
        _scan_score_anomalies(session),
    ]
    rows = [item for item in issues if item and item.count > 0]
    rows.sort(key=lambda item: (SEVERITY_ORDER.get(item.severity, 99), -item.count, item.title))
    if limit is not None:
        return rows[:limit]
    return rows


def build_data_repair_scan(session: Session) -> DataRepairScanRead:
    issues = build_data_quality_issues(session)
    active_issue_codes = {item.code for item in issues}
    actions = [
        DataRepairActionRead(
            code=code,
            title=meta["title"],
            description=meta["description"],
            enabled=bool(active_issue_codes.intersection(meta["affected_issue_codes"])),
            affected_issue_codes=list(meta["affected_issue_codes"]),
        )
        for code, meta in REPAIR_ACTIONS.items()
    ]
    return DataRepairScanRead(generated_at=datetime.now(), issues=issues, actions=actions)


def execute_repair_action(session: Session, action_code: str) -> tuple[int, str]:
    if action_code == "refresh_class_student_counts":
        repaired_count = _refresh_class_student_counts(session)
        message = f"已重算 {repaired_count} 个班级人数"
    elif action_code == "sync_student_grade_from_class":
        repaired_count = _sync_student_grade_from_class(session)
        message = f"已修正 {repaired_count} 名学生的当前年级"
    elif action_code == "repair_student_class_history":
        repaired_count = _repair_student_class_history(session)
        message = f"已补齐 {repaired_count} 名学生的学籍历史"
    else:
        raise HTTPException(status_code=404, detail="修复动作不存在")

    write_audit_log(
        session,
        module="system",
        action="data_repair",
        target_type="repair_action",
        target_id=action_code,
        detail_json={"action_code": action_code, "repaired_count": repaired_count},
    )
    return repaired_count, message


def _scan_class_student_count_mismatch(session: Session) -> DataQualityIssueRead | None:
    actual_counts = dict(
        session.execute(
            select(Student.current_class_id, func.count())
            .where(Student.is_active.is_(True), Student.current_class_id.is_not(None))
            .group_by(Student.current_class_id)
        ).all()
    )
    samples: list[str] = []
    mismatch_count = 0
    classes = session.scalars(
        select(SchoolClass).where(SchoolClass.is_active.is_(True)).order_by(SchoolClass.grade_id, SchoolClass.id)
    ).all()
    for school_class in classes:
        actual = int(actual_counts.get(school_class.id, 0) or 0)
        if school_class.student_count != actual:
            mismatch_count += 1
            if len(samples) < 3:
                samples.append(f"{school_class.name}: 账面 {school_class.student_count} / 实际 {actual}")
    if mismatch_count == 0:
        return None
    return DataQualityIssueRead(
        code="class_student_count_mismatch",
        title="班级人数与实际归属不一致",
        severity="warning",
        count=mismatch_count,
        summary="当前班级在册人数与学生当前班级归属不一致。",
        repairable=True,
        action_code=ISSUE_ACTION_MAP["class_student_count_mismatch"],
        samples=samples,
    )


def _scan_student_grade_class_mismatch(session: Session) -> DataQualityIssueRead | None:
    students = session.scalars(
        select(Student)
        .options(joinedload(Student.current_class), joinedload(Student.current_grade))
        .where(Student.is_active.is_(True), Student.current_class_id.is_not(None))
        .order_by(Student.student_no)
    ).all()
    samples: list[str] = []
    mismatch_count = 0
    for item in students:
        if not item.current_class:
            continue
        if item.current_grade_id != item.current_class.grade_id:
            mismatch_count += 1
            if len(samples) < 3:
                samples.append(
                    f"{item.name}: 当前年级 {item.current_grade.name if item.current_grade else '-'} / 班级归属 {item.current_class.name}"
                )
    if mismatch_count == 0:
        return None
    return DataQualityIssueRead(
        code="student_grade_class_mismatch",
        title="学生当前年级与班级归属不一致",
        severity="error",
        count=mismatch_count,
        summary="部分学生的当前年级与当前班级所属年级不一致，会影响分析与推荐。",
        repairable=True,
        action_code=ISSUE_ACTION_MAP["student_grade_class_mismatch"],
        samples=samples,
    )


def _scan_student_history_gap(session: Session) -> DataQualityIssueRead | None:
    students = session.scalars(
        select(Student)
        .options(
            joinedload(Student.current_class),
            joinedload(Student.current_grade),
            selectinload(Student.class_histories),
        )
        .where(Student.is_active.is_(True))
        .order_by(Student.student_no)
    ).all()
    samples: list[str] = []
    mismatch_count = 0
    for item in students:
        if not item.current_class_id and not item.current_grade_id:
            continue
        open_history = next(
            (history for history in item.class_histories if history.is_active and history.end_date is None),
            None,
        )
        if open_history and open_history.class_id == item.current_class_id and open_history.grade_id == item.current_grade_id:
            continue
        mismatch_count += 1
        if len(samples) < 3:
            samples.append(
                f"{item.name}: 当前 {item.current_class.name if item.current_class else '-'} 缺少对应开放历史"
            )
    if mismatch_count == 0:
        return None
    return DataQualityIssueRead(
        code="student_open_history_missing",
        title="学生学籍开放历史缺失",
        severity="warning",
        count=mismatch_count,
        summary="部分学生缺少与当前年级班级一致的开放历史记录。",
        repairable=True,
        action_code=ISSUE_ACTION_MAP["student_open_history_missing"],
        samples=samples,
    )


def _scan_timetable_unmatched(session: Session) -> DataQualityIssueRead | None:
    base_stmt = select(TimetableEntry).where(
        TimetableEntry.is_active.is_(True),
        TimetableEntry.mapping_status != "matched",
    )
    mismatch_count = session.scalar(select(func.count()).select_from(base_stmt.subquery())) or 0
    if mismatch_count == 0:
        return None
    entries = session.scalars(base_stmt.order_by(TimetableEntry.id.desc()).limit(3)).all()
    samples = [
        " / ".join(
            filter(
                None,
                [
                    item.raw_teacher_name or "未识别教师",
                    item.raw_class_name or "未识别班级",
                    item.raw_subject_name or "未识别学科",
                ],
            )
        )
        for item in entries
    ]
    return DataQualityIssueRead(
        code="timetable_unmatched_entries",
        title="课表仍有待修正映射项",
        severity="warning",
        count=int(mismatch_count),
        summary="存在尚未修正的课表映射记录，这些课时不会进入统计与工作量计算。",
        repairable=False,
        samples=samples,
    )


def _scan_score_anomalies(session: Session) -> DataQualityIssueRead | None:
    base_stmt = (
        select(
            ScoreRecord.id,
            ScoreRecord.score,
            Exam.name,
            Student.name,
            Subject.name,
            ExamSubject.full_score,
        )
        .join(Exam, Exam.id == ScoreRecord.exam_id)
        .join(Student, Student.id == ScoreRecord.student_id)
        .join(Subject, Subject.id == ScoreRecord.subject_id)
        .join(
            ExamSubject,
            and_(
                ExamSubject.exam_id == ScoreRecord.exam_id,
                ExamSubject.subject_id == ScoreRecord.subject_id,
            ),
        )
        .where(
            ScoreRecord.is_active.is_(True),
            ScoreRecord.score_status == "normal",
            ScoreRecord.score.is_not(None),
            or_(ScoreRecord.score < 0, ScoreRecord.score > ExamSubject.full_score),
        )
    )
    mismatch_count = session.scalar(select(func.count()).select_from(base_stmt.subquery())) or 0
    if mismatch_count == 0:
        return None
    rows = session.execute(base_stmt.order_by(ScoreRecord.id.desc()).limit(3)).all()
    samples = [f"{exam_name} / {student_name} / {subject_name}: {score}/{full_score}" for _, score, exam_name, student_name, subject_name, full_score in rows]
    return DataQualityIssueRead(
        code="score_anomaly_records",
        title="成绩存在异常值",
        severity="error",
        count=int(mismatch_count),
        summary="存在小于 0 或超过满分的正常成绩记录，建议先核对原始导入数据。",
        repairable=False,
        samples=samples,
    )


def _refresh_class_student_counts(session: Session) -> int:
    actual_counts = dict(
        session.execute(
            select(Student.current_class_id, func.count())
            .where(Student.is_active.is_(True), Student.current_class_id.is_not(None))
            .group_by(Student.current_class_id)
        ).all()
    )
    repaired_count = 0
    classes = session.scalars(select(SchoolClass)).all()
    for school_class in classes:
        actual = int(actual_counts.get(school_class.id, 0) or 0)
        if school_class.student_count != actual:
            school_class.student_count = actual
            repaired_count += 1
    session.flush()
    return repaired_count


def _sync_student_grade_from_class(session: Session) -> int:
    repaired_count = 0
    students = session.scalars(
        select(Student).options(joinedload(Student.current_class)).where(Student.is_active.is_(True))
    ).all()
    for item in students:
        if not item.current_class:
            continue
        if item.current_grade_id != item.current_class.grade_id:
            item.current_grade_id = item.current_class.grade_id
            repaired_count += 1
    session.flush()
    return repaired_count


def _repair_student_class_history(session: Session) -> int:
    repaired_count = 0
    students = session.scalars(
        select(Student)
        .options(selectinload(Student.class_histories))
        .where(Student.is_active.is_(True))
        .order_by(Student.student_no)
    ).all()
    today = date.today()
    for item in students:
        if not item.current_class_id and not item.current_grade_id:
            continue
        open_history = next(
            (history for history in item.class_histories if history.is_active and history.end_date is None),
            None,
        )
        if open_history and open_history.class_id == item.current_class_id and open_history.grade_id == item.current_grade_id:
            continue
        if open_history and open_history.end_date is None:
            open_history.end_date = today
        item.class_histories.append(
            StudentClassHistory(
                grade_id=item.current_grade_id,
                class_id=item.current_class_id,
                start_date=today,
                end_date=None,
                reason="系统修复",
            )
        )
        repaired_count += 1
    session.flush()
    return repaired_count
