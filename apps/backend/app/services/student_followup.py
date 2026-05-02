from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta

from fastapi import HTTPException
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session, joinedload

from app.models import (
    Exam,
    Grade,
    ScoreTotalSnapshot,
    SchoolClass,
    Student,
    StudentGrowthRecord,
    StudentPlanningGoal,
    StudentPlanningTask,
)
from app.schemas.student_followup import (
    AdviserActionItem,
    AdviserDashboardGrowthSummary,
    AdviserDashboardOverview,
    AdviserDashboardPlanningSummary,
    AdviserDashboardResponse,
    AdviserDashboardScoreSummary,
    AdviserRiskStudentItem,
    GrowthFollowupSummary,
    PlanningFollowupSummary,
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
ACTIVE_TASK_STATUSES = {"not_started", "in_progress", "review", "paused"}


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
    growth_by_student, growth_summary = _build_growth_summary_map(session, student_ids)
    planning_by_student, planning_summary = _build_planning_summary_map(
        session,
        student_ids,
        start_date=start_date,
        end_date=end_date,
    )

    risk_responses = [
        _build_student_risk_response(
            student,
            score_by_student.get(student.id, ScoreRiskSummary()),
            growth_by_student.get(student.id, GrowthFollowupSummary()),
            planning_by_student.get(student.id, PlanningFollowupSummary()),
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
    data_flags = _build_dashboard_data_flags(score_summary, growth_summary)
    overview = AdviserDashboardOverview(
        student_count=len(students),
        score_sample_count=score_summary.sample_count,
        growth_record_count=growth_summary.total_records,
        open_task_count=planning_summary.open_task_count,
        overdue_task_count=planning_summary.overdue_task_count,
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
        growth_summary=growth_summary,
        planning_summary=planning_summary,
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
    growth_summary = _build_growth_summary_map(session, [student.id])[0].get(student.id, GrowthFollowupSummary())
    planning_summary = _build_planning_summary_map(
        session,
        [student.id],
        start_date=start_date,
        end_date=end_date,
    )[0].get(student.id, PlanningFollowupSummary())
    return _build_student_risk_response(student, score_summary, growth_summary, planning_summary)


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


def _build_growth_summary_map(
    session: Session,
    student_ids: list[int],
) -> tuple[dict[int, GrowthFollowupSummary], AdviserDashboardGrowthSummary]:
    result = {student_id: GrowthFollowupSummary() for student_id in student_ids}
    if not student_ids:
        return result, AdviserDashboardGrowthSummary()
    rows = session.execute(
        select(
            StudentGrowthRecord.student_id,
            func.count(StudentGrowthRecord.id),
            func.max(StudentGrowthRecord.occurred_on),
        )
        .where(StudentGrowthRecord.is_active.is_(True), StudentGrowthRecord.student_id.in_(student_ids))
        .group_by(StudentGrowthRecord.student_id)
    ).all()
    total_records = 0
    latest_record_date: date | None = None
    for student_id, record_count, latest_date in rows:
        count_value = int(record_count or 0)
        result[student_id] = GrowthFollowupSummary(record_count=count_value, latest_record_date=latest_date)
        total_records += count_value
        if latest_date and (latest_record_date is None or latest_date > latest_record_date):
            latest_record_date = latest_date
    return result, AdviserDashboardGrowthSummary(
        total_records=total_records,
        students_with_records_count=len(rows),
        latest_record_date=latest_record_date,
    )


def _build_planning_summary_map(
    session: Session,
    student_ids: list[int],
    *,
    start_date: date,
    end_date: date,
) -> tuple[dict[int, PlanningFollowupSummary], AdviserDashboardPlanningSummary]:
    result = {student_id: PlanningFollowupSummary() for student_id in student_ids}
    if not student_ids:
        return result, AdviserDashboardPlanningSummary()

    today = date.today()
    due_soon_end = today + timedelta(days=7)
    task_rows = session.scalars(
        select(StudentPlanningTask).where(
            StudentPlanningTask.is_active.is_(True),
            StudentPlanningTask.student_id.in_(student_ids),
            StudentPlanningTask.status.in_(ACTIVE_TASK_STATUSES),
        )
    ).all()
    goals_by_student = set(
        session.scalars(
            select(StudentPlanningGoal.student_id).where(
                StudentPlanningGoal.is_active.is_(True),
                StudentPlanningGoal.student_id.in_(student_ids),
            )
        ).all()
    )
    tasks_by_student: dict[int, list[StudentPlanningTask]] = defaultdict(list)
    for task in task_rows:
        tasks_by_student[task.student_id].append(task)

    dashboard = AdviserDashboardPlanningSummary()
    for student_id in student_ids:
        tasks = tasks_by_student.get(student_id, [])
        due_dates = [item.due_date for item in tasks if item.due_date is not None]
        summary = PlanningFollowupSummary(
            open_task_count=len(tasks),
            overdue_task_count=sum(1 for item in tasks if item.due_date is not None and item.due_date < today),
            due_soon_task_count=sum(
                1
                for item in tasks
                if item.due_date is not None and today <= item.due_date <= due_soon_end
            ),
            high_priority_open_count=sum(1 for item in tasks if item.priority == "high"),
            no_goal=student_id not in goals_by_student,
            next_due_date=min(due_dates) if due_dates else None,
        )
        result[student_id] = summary
        dashboard.open_task_count += summary.open_task_count
        dashboard.overdue_task_count += summary.overdue_task_count
        dashboard.due_soon_task_count += summary.due_soon_task_count
        dashboard.high_priority_open_count += summary.high_priority_open_count
        if summary.no_goal:
            dashboard.students_without_goal_count += 1
    return result, dashboard


def _build_student_risk_response(
    student: Student,
    score_summary: ScoreRiskSummary,
    growth_summary: GrowthFollowupSummary,
    planning_summary: PlanningFollowupSummary,
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

    if growth_summary.record_count <= 0:
        data_flags.append("成长档案暂无记录")
    elif growth_summary.latest_record_date and growth_summary.latest_record_date < date.today() - timedelta(days=90):
        reasons.append("成长档案超过 90 天未更新")
        actions.append("补充阶段复盘")

    if planning_summary.overdue_task_count > 0:
        signal_count += 2
        reasons.append(f"升学规划逾期任务 {planning_summary.overdue_task_count} 项")
        actions.append("处理逾期规划任务")
    elif planning_summary.high_priority_open_count > 0:
        signal_count += 1
        reasons.append(f"高优先级规划任务 {planning_summary.high_priority_open_count} 项")
        actions.append("优先推进规划任务")
    elif planning_summary.due_soon_task_count > 0:
        signal_count += 1
        reasons.append(f"7 天内到期规划任务 {planning_summary.due_soon_task_count} 项")
        actions.append("检查近期到期任务")
    if planning_summary.no_goal:
        data_flags.append("尚未建立升学规划目标")

    risk_level = "normal"
    if score_summary.total_score_delta is not None and score_summary.total_score_delta <= -30:
        risk_level = "urgent"
    elif planning_summary.overdue_task_count > 0:
        risk_level = "urgent"
    elif signal_count >= 3:
        risk_level = "urgent"
    elif signal_count >= 1:
        risk_level = "follow_up"
    elif reasons or data_flags:
        risk_level = "watch"

    if not actions and data_flags:
        actions.append("补齐学生跟进基础数据")
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
        growth_summary=growth_summary,
        planning_summary=planning_summary,
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
    growth_summary: AdviserDashboardGrowthSummary,
) -> list[str]:
    flags: list[str] = []
    if not score_summary.imported:
        flags.append("成绩数据未导入或当前范围无成绩样本")
    if growth_summary.total_records <= 0:
        flags.append("当前范围暂无成长档案记录")
    return flags


def _build_adviser_actions(
    risk_responses: list[StudentRiskResponse],
    data_flags: list[str],
) -> list[AdviserActionItem]:
    urgent_ids = [item.student_id for item in risk_responses if item.risk_level == "urgent"]
    follow_up_ids = [item.student_id for item in risk_responses if item.risk_level == "follow_up"]
    score_ids = [item.student_id for item in risk_responses if item.score_summary.decline_risk or item.score_summary.low_score]
    planning_ids = [
        item.student_id
        for item in risk_responses
        if item.planning_summary.overdue_task_count
        or item.planning_summary.due_soon_task_count
        or item.planning_summary.high_priority_open_count
    ]
    growth_ids = [item.student_id for item in risk_responses if item.growth_summary.record_count <= 0]
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
    if planning_ids:
        actions.append(
            AdviserActionItem(
                action_type="planning_followup",
                title="推进规划任务",
                count=len(planning_ids),
                student_ids=planning_ids,
                target_route="/planning",
            )
        )
    if growth_ids:
        actions.append(
            AdviserActionItem(
                action_type="growth_archive",
                title="补充成长档案",
                count=len(growth_ids),
                student_ids=growth_ids,
                target_route="/growth-archive",
            )
        )
    if data_flags:
        actions.append(
            AdviserActionItem(
                action_type="data_backfill",
                title="补齐跟进数据",
                count=len(data_flags),
                target_route="/import-center",
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
