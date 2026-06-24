from __future__ import annotations

from datetime import date, datetime, timedelta

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models import (
    Student,
    StudentPathwayEvaluation,
    StudentPathwayProfile,
    StudentPlanningGoal,
    StudentPlanningNote,
    StudentPlanningTask,
    VolunteerDraft,
)
from app.repositories.system import write_audit_log
from app.schemas.planning import (
    DashboardPlanningSummary,
    PlanningBulkCreateFromPathwayPayload,
    PlanningBulkCreateResult,
    PlanningGoalPayload,
    PlanningGoalRead,
    PlanningGoalUpdatePayload,
    PlanningNotePayload,
    PlanningNoteRead,
    PlanningStudentRead,
    PlanningTaskPayload,
    PlanningTaskRead,
    PlanningTaskUpdatePayload,
    StudentPlanningResponse,
    StudentPlanningSummary,
)
from app.schemas.knowledge import KnowledgeTaskCandidate, KnowledgeTaskGenerateResponse, KnowledgeTaskPreviewResponse
from app.schemas.exam import StudentKnowledgePointAnalytics, StudentKnowledgeTrendAnalytics
from app.services import gaokao_pathways


GOAL_STATUS_LABELS = {
    "not_started": "未开始",
    "in_progress": "进行中",
    "review": "待复核",
    "completed": "已完成",
    "paused": "暂缓",
}

TASK_STATUS_LABELS = GOAL_STATUS_LABELS

PRIORITY_LABELS = {
    "high": "高",
    "medium": "中",
    "low": "低",
}

TASK_TYPE_LABELS = {
    "material": "材料补齐",
    "score_review": "成绩复核",
    "volunteer_draft": "志愿草稿",
    "chapter_review": "章程核对",
    "family_contact": "家校沟通",
    "stage_review": "阶段复盘",
    "risk_followup": "风险跟进",
    "knowledge_remediation": "知识点补弱",
    "other": "其他",
}

NOTE_TYPE_LABELS = {
    "review": "复盘",
    "communication": "沟通",
    "decision": "决策",
    "risk": "风险",
    "other": "其他",
}

ACTIVE_TASK_STATUSES = {"not_started", "in_progress", "review", "paused"}


def get_student_planning(
    session: Session,
    student_id: int,
    *,
    target_year: int | None = None,
    province: str = "山东",
) -> StudentPlanningResponse:
    student = _ensure_student(session, student_id)
    goals = _list_goals(session, student_id, target_year=target_year)
    tasks = _list_tasks(session, student_id)
    notes = _list_notes(session, student_id)
    pathway_profile = gaokao_pathways.get_student_pathway_profile(session, student_id, province=province)
    pathway_evaluations = _list_pathway_evaluations(session, student_id, target_year=target_year)
    suggested_tasks = _build_suggested_tasks(student, goals, tasks, pathway_evaluations)
    return StudentPlanningResponse(
        student=_serialize_student(student),
        goals=[_serialize_goal(item) for item in goals],
        tasks=[_serialize_task(item) for item in tasks],
        notes=[_serialize_note(item) for item in notes],
        pathway_profile=pathway_profile,
        pathway_evaluations=pathway_evaluations,
        suggested_tasks=suggested_tasks,
        summary=_build_student_summary(goals, tasks, pathway_profile is not None, bool(pathway_evaluations)),
    )


def create_goal(session: Session, payload: PlanningGoalPayload) -> PlanningGoalRead:
    _ensure_student(session, payload.student_id)
    _validate_goal_payload(payload)
    existing = session.scalar(
        select(StudentPlanningGoal).where(
            StudentPlanningGoal.student_id == payload.student_id,
            StudentPlanningGoal.target_year == payload.target_year,
            StudentPlanningGoal.pathway_code == payload.pathway_code.strip(),
            StudentPlanningGoal.is_active.is_(True),
        )
    )
    if existing:
        raise HTTPException(status_code=409, detail="该学生已有同年份同路径规划目标")
    item = StudentPlanningGoal()
    _apply_goal_payload(item, payload)
    session.add(item)
    session.flush()
    write_audit_log(
        session,
        module="planning",
        action="create_goal",
        target_type="student_planning_goal",
        target_id=str(item.id),
        detail_json={"student_id": item.student_id, "pathway_code": item.pathway_code},
    )
    session.refresh(item)
    return _serialize_goal(item)


def update_goal(session: Session, goal_id: int, payload: PlanningGoalUpdatePayload) -> PlanningGoalRead:
    item = session.get(StudentPlanningGoal, goal_id)
    if not item:
        raise HTTPException(status_code=404, detail="升学规划目标不存在")
    _apply_goal_update(item, payload)
    _validate_goal_item(item)
    session.flush()
    write_audit_log(
        session,
        module="planning",
        action="update_goal",
        target_type="student_planning_goal",
        target_id=str(item.id),
    )
    session.refresh(item)
    return _serialize_goal(item)


def create_task(session: Session, payload: PlanningTaskPayload) -> PlanningTaskRead:
    _ensure_student(session, payload.student_id)
    _validate_task_payload(payload)
    if payload.goal_id:
        _ensure_goal_for_student(session, payload.goal_id, payload.student_id)
    item = StudentPlanningTask()
    _apply_task_payload(item, payload)
    session.add(item)
    session.flush()
    write_audit_log(
        session,
        module="planning",
        action="create_task",
        target_type="student_planning_task",
        target_id=str(item.id),
        detail_json={"student_id": item.student_id, "source_type": item.source_type},
    )
    session.refresh(item)
    return _serialize_task(item)


def update_task(session: Session, task_id: int, payload: PlanningTaskUpdatePayload) -> PlanningTaskRead:
    item = session.get(StudentPlanningTask, task_id)
    if not item:
        raise HTTPException(status_code=404, detail="升学规划任务不存在")
    _apply_task_update(item, payload)
    _validate_task_item(item)
    if item.goal_id:
        _ensure_goal_for_student(session, item.goal_id, item.student_id)
    session.flush()
    write_audit_log(
        session,
        module="planning",
        action="update_task",
        target_type="student_planning_task",
        target_id=str(item.id),
        detail_json={"status": item.status},
    )
    session.refresh(item)
    return _serialize_task(item)


def create_note(session: Session, payload: PlanningNotePayload) -> PlanningNoteRead:
    _ensure_student(session, payload.student_id)
    if payload.goal_id:
        _ensure_goal_for_student(session, payload.goal_id, payload.student_id)
    if payload.task_id:
        _ensure_task_for_student(session, payload.task_id, payload.student_id)
    if not payload.content.strip():
        raise HTTPException(status_code=400, detail="复盘记录内容不能为空")
    item = StudentPlanningNote(
        student_id=payload.student_id,
        goal_id=payload.goal_id,
        task_id=payload.task_id,
        note_type=_normalize_choice(payload.note_type, NOTE_TYPE_LABELS, "other"),
        content=payload.content.strip(),
        is_active=payload.is_active,
    )
    session.add(item)
    session.flush()
    write_audit_log(
        session,
        module="planning",
        action="create_note",
        target_type="student_planning_note",
        target_id=str(item.id),
    )
    session.refresh(item)
    return _serialize_note(item)


def bulk_create_tasks_from_pathway(
    session: Session,
    payload: PlanningBulkCreateFromPathwayPayload,
) -> PlanningBulkCreateResult:
    student = _ensure_student(session, payload.student_id)
    evaluation_response = gaokao_pathways.preview_student_pathway_evaluations(
        session,
        payload.student_id,
        target_year=payload.target_year,
        province=payload.province,
    )
    evaluations = evaluation_response.evaluations
    if payload.pathway_ids:
        allowed = set(payload.pathway_ids)
        evaluations = [item for item in evaluations if item.pathway_id in allowed]

    created: list[StudentPlanningTask] = []
    skipped_count = 0
    notices: list[str] = []
    due_date = payload.due_date or date.today() + timedelta(days=14)

    for evaluation in evaluations:
        if payload.include_material_gaps:
            for gap in evaluation.missing_materials_json:
                candidate = _task_payload_from_material_gap(student.id, evaluation, gap, due_date)
                item = _create_task_if_missing(session, candidate)
                if item:
                    created.append(item)
                else:
                    skipped_count += 1

        if payload.include_review_tasks and _evaluation_needs_review(evaluation):
            candidate = PlanningTaskPayload(
                student_id=student.id,
                source_type="pathway_review",
                source_ref_id=f"{evaluation.pathway_id}:{payload.target_year}",
                task_type="chapter_review",
                title=f"复核{evaluation.pathway_name or '升学路径'}章程和报名边界",
                description=evaluation.summary or "正式报名前需核对官方公告、招生章程、报名时间和限制条件。",
                status="not_started",
                priority="high" if evaluation.status in {"manual_review", "insufficient_data"} else "medium",
                due_date=due_date,
                related_route=f"/gaokao-pathways?student_id={student.id}",
            )
            item = _create_task_if_missing(session, candidate)
            if item:
                created.append(item)
            else:
                skipped_count += 1

    draft_notices = _ensure_volunteer_draft_review_tasks(session, student.id, due_date)
    created.extend(draft_notices[0])
    skipped_count += draft_notices[1]
    if not created and skipped_count == 0:
        notices.append("当前路径评估没有识别到可生成的材料缺口或复核任务")

    session.flush()
    for item in created:
        session.refresh(item)
    if created:
        write_audit_log(
            session,
            module="planning",
            action="bulk_create_tasks_from_pathway",
            target_type="student",
            target_id=str(student.id),
            detail_json={"created_count": len(created), "skipped_count": skipped_count},
        )
    return PlanningBulkCreateResult(
        created_count=len(created),
        skipped_count=skipped_count,
        tasks=[_serialize_task(item) for item in created],
        notices=notices,
    )


def preview_student_knowledge_tasks(
    session: Session,
    student_id: int,
    exam_id: int,
    *,
    due_date: date | None = None,
) -> KnowledgeTaskPreviewResponse:
    from app.services import analytics

    analytics_data = analytics.get_student_analytics(session, student_id, exam_id)
    target_due_date = due_date or date.today() + timedelta(days=14)
    candidates = _build_student_knowledge_task_candidates(
        session,
        exam_id=exam_id,
        student_id=student_id,
        student_name=analytics_data.student_name,
        class_name=None,
        knowledge_trends=analytics_data.knowledge_trends,
        knowledge_points=analytics_data.knowledge_points,
        due_date=target_due_date,
    )
    return KnowledgeTaskPreviewResponse(
        exam_id=exam_id,
        student_id=student_id,
        due_date=target_due_date,
        candidates=candidates,
        create_count=sum(1 for item in candidates if item.will_create),
        skip_count=sum(1 for item in candidates if not item.will_create),
        notices=[] if candidates else ["当前学生暂无可生成的知识点补弱任务。"],
    )


def generate_student_knowledge_tasks(
    session: Session,
    student_id: int,
    exam_id: int,
    *,
    due_date: date | None = None,
) -> KnowledgeTaskGenerateResponse:
    preview = preview_student_knowledge_tasks(session, student_id, exam_id, due_date=due_date)
    created = _create_knowledge_tasks_from_candidates(session, preview.candidates)
    session.flush()
    for item in created:
        session.refresh(item)
    return KnowledgeTaskGenerateResponse(
        created_count=len(created),
        skipped_count=len(preview.candidates) - len(created),
        tasks=[_serialize_task(item) for item in created],
        notices=preview.notices,
    )


def preview_class_knowledge_tasks(
    session: Session,
    class_id: int,
    exam_id: int,
    *,
    knowledge_point_ids: list[int] | None = None,
    due_date: date | None = None,
) -> KnowledgeTaskPreviewResponse:
    from app.services import analytics

    briefing = analytics.get_class_knowledge_briefing(session, class_id, exam_id)
    target_due_date = due_date or date.today() + timedelta(days=14)
    selected_ids = set(knowledge_point_ids or [])
    candidates: list[KnowledgeTaskCandidate] = []
    for item in briefing.items:
        if selected_ids and item.knowledge_point_id not in selected_ids:
            continue
        for weak_student in item.weak_students:
            candidates.append(
                _build_knowledge_task_candidate(
                    session,
                    exam_id=exam_id,
                    student_id=weak_student.student_id,
                    student_name=weak_student.student_name,
                    class_name=weak_student.class_name,
                    subject_id=item.subject_id,
                    subject_name=item.subject_name,
                    knowledge_point_id=item.knowledge_point_id,
                    knowledge_point_name=item.knowledge_point_name,
                    knowledge_path=item.knowledge_path,
                    due_date=target_due_date,
                    reason=f"班级讲评清单：{item.priority_label}优先级，得分率 {weak_student.score_rate if weak_student.score_rate is not None else '-'}",
                    description=item.suggestion,
                    priority="high" if item.priority_label == "高" else "medium",
                )
            )
    return KnowledgeTaskPreviewResponse(
        exam_id=exam_id,
        class_id=class_id,
        due_date=target_due_date,
        candidates=candidates,
        create_count=sum(1 for item in candidates if item.will_create),
        skip_count=sum(1 for item in candidates if not item.will_create),
        notices=[] if candidates else ["当前班级讲评清单暂无可生成的学生补弱任务。"],
    )


def generate_class_knowledge_tasks(
    session: Session,
    class_id: int,
    exam_id: int,
    *,
    knowledge_point_ids: list[int] | None = None,
    due_date: date | None = None,
) -> KnowledgeTaskGenerateResponse:
    preview = preview_class_knowledge_tasks(
        session,
        class_id,
        exam_id,
        knowledge_point_ids=knowledge_point_ids,
        due_date=due_date,
    )
    created = _create_knowledge_tasks_from_candidates(session, preview.candidates)
    session.flush()
    for item in created:
        session.refresh(item)
    skipped = len(preview.candidates) - len(created)
    return KnowledgeTaskGenerateResponse(
        created_count=len(created),
        skipped_count=skipped,
        tasks=[_serialize_task(item) for item in created],
        notices=preview.notices,
    )


def build_dashboard_planning_summary(session: Session) -> DashboardPlanningSummary:
    today = date.today()
    soon = today + timedelta(days=7)
    open_task_count = session.scalar(
        select(func.count()).select_from(StudentPlanningTask).where(
            StudentPlanningTask.is_active.is_(True),
            StudentPlanningTask.status.in_(ACTIVE_TASK_STATUSES),
        )
    ) or 0
    overdue_task_count = session.scalar(
        select(func.count()).select_from(StudentPlanningTask).where(
            StudentPlanningTask.is_active.is_(True),
            StudentPlanningTask.status.in_(ACTIVE_TASK_STATUSES),
            StudentPlanningTask.due_date.is_not(None),
            StudentPlanningTask.due_date < today,
        )
    ) or 0
    due_soon_task_count = session.scalar(
        select(func.count()).select_from(StudentPlanningTask).where(
            StudentPlanningTask.is_active.is_(True),
            StudentPlanningTask.status.in_(ACTIVE_TASK_STATUSES),
            StudentPlanningTask.due_date.is_not(None),
            StudentPlanningTask.due_date >= today,
            StudentPlanningTask.due_date <= soon,
        )
    ) or 0
    students_with_goal_count = session.scalar(
        select(func.count(func.distinct(StudentPlanningGoal.student_id))).where(
            StudentPlanningGoal.is_active.is_(True)
        )
    ) or 0
    total_students = session.scalar(select(func.count()).select_from(Student).where(Student.is_active.is_(True))) or 0
    volunteer_draft_count = session.scalar(select(func.count()).select_from(VolunteerDraft).where(VolunteerDraft.is_active.is_(True))) or 0
    volunteer_review_task_count = session.scalar(
        select(func.count()).select_from(StudentPlanningTask).where(
            StudentPlanningTask.is_active.is_(True),
            StudentPlanningTask.source_type == "volunteer_draft",
            StudentPlanningTask.task_type == "chapter_review",
        )
    ) or 0
    material_gap_without_due_count = session.scalar(
        select(func.count()).select_from(StudentPlanningTask).where(
            StudentPlanningTask.is_active.is_(True),
            StudentPlanningTask.status.in_(ACTIVE_TASK_STATUSES),
            StudentPlanningTask.task_type == "material",
            StudentPlanningTask.due_date.is_(None),
        )
    ) or 0
    return DashboardPlanningSummary(
        open_task_count=open_task_count,
        overdue_task_count=overdue_task_count,
        due_soon_task_count=due_soon_task_count,
        students_with_goal_count=students_with_goal_count,
        students_without_goal_count=max(total_students - students_with_goal_count, 0),
        volunteer_draft_without_review_count=max(volunteer_draft_count - volunteer_review_task_count, 0),
        material_gap_without_due_count=material_gap_without_due_count,
    )


def build_planning_followup_export_payload(session: Session, student_id: int, *, exam_id: int | None = None) -> dict[str, object]:
    planning = get_student_planning(session, student_id)
    risk_payload: dict[str, object] | None = None
    try:
        from app.services import student_followup

        risk_payload = student_followup.get_student_risk(session, student_id, exam_id=exam_id).model_dump(mode="json")
    except HTTPException:
        risk_payload = None

    return {
        "student": planning.student.model_dump(mode="json"),
        "goals": [item.model_dump(mode="json") for item in planning.goals],
        "tasks": [item.model_dump(mode="json") for item in planning.tasks],
        "notes": [item.model_dump(mode="json") for item in planning.notes],
        "pathway_profile": planning.pathway_profile.model_dump(mode="json") if planning.pathway_profile else None,
        "pathway_evaluations": [item.model_dump(mode="json") for item in planning.pathway_evaluations],
        "suggested_tasks": [item.model_dump(mode="json") for item in planning.suggested_tasks],
        "summary": planning.summary.model_dump(mode="json"),
        "risk": risk_payload,
        "generated_at": datetime.now().isoformat(sep=" ", timespec="seconds"),
    }


def _task_payload_from_material_gap(student_id: int, evaluation, gap: dict[str, object], due_date: date) -> PlanningTaskPayload:
    material_key = str(gap.get("material_key") or gap.get("rule_code") or "material")
    material_label = str(gap.get("material_label") or material_key)
    pathway_name = evaluation.pathway_name or "升学路径"
    return PlanningTaskPayload(
        student_id=student_id,
        source_type="pathway_material",
        source_ref_id=f"{evaluation.pathway_id}:{evaluation.target_year}:{material_key}",
        task_type="material",
        title=f"补齐{pathway_name}材料：{material_label}",
        description=str(gap.get("next_action") or f"补充{material_label}后重新评估该路径。"),
        status="not_started",
        priority="high" if gap.get("gap_type") != "profile_field" else "medium",
        due_date=due_date,
        related_route=f"/students/{student_id}?tab=planning",
    )


def _build_student_knowledge_task_candidates(
    session: Session,
    *,
    exam_id: int,
    student_id: int,
    student_name: str,
    class_name: str | None,
    knowledge_trends: list[StudentKnowledgeTrendAnalytics],
    knowledge_points: list[StudentKnowledgePointAnalytics],
    due_date: date,
) -> list[KnowledgeTaskCandidate]:
    candidates: list[KnowledgeTaskCandidate] = []
    trend_items = [
        item
        for item in knowledge_trends
        if item.trend_label in {"持续薄弱", "波动反复"} and item.priority_score > 0
    ][:3]
    for item in trend_items:
        candidates.append(
            _build_knowledge_task_candidate(
                session,
                exam_id=exam_id,
                student_id=student_id,
                student_name=student_name,
                class_name=class_name,
                subject_id=item.subject_id,
                subject_name=item.subject_name,
                knowledge_point_id=item.knowledge_point_id,
                knowledge_point_name=item.knowledge_point_name,
                knowledge_path=item.knowledge_path,
                due_date=due_date,
                reason=f"连续趋势：{item.trend_label}",
                description=item.suggestion or "根据连续题分趋势生成补弱任务。",
                priority="high" if item.trend_label == "持续薄弱" else "medium",
            )
        )
    existing_point_ids = {item.knowledge_point_id for item in candidates}
    if len(candidates) < 3:
        fallback_items = [
            item
            for item in knowledge_points
            if item.knowledge_point_id not in existing_point_ids
            and item.diagnosis_label in {"优先补弱", "需要巩固", "低于年级"}
            and item.priority_score > 0
        ][:2]
        for item in fallback_items:
            candidates.append(
                _build_knowledge_task_candidate(
                    session,
                    exam_id=exam_id,
                    student_id=student_id,
                    student_name=student_name,
                    class_name=class_name,
                    subject_id=item.subject_id,
                    subject_name=item.subject_name,
                    knowledge_point_id=item.knowledge_point_id,
                    knowledge_point_name=item.knowledge_point_name,
                    knowledge_path=item.knowledge_path,
                    due_date=due_date,
                    reason=f"本次诊断：{item.diagnosis_label}",
                    description=item.suggestion or "根据本次题分诊断生成补弱任务。",
                    priority="high" if item.diagnosis_label == "优先补弱" else "medium",
                )
            )
    return candidates


def _build_knowledge_task_candidate(
    session: Session,
    *,
    exam_id: int,
    student_id: int,
    student_name: str,
    class_name: str | None,
    subject_id: int,
    subject_name: str,
    knowledge_point_id: int,
    knowledge_point_name: str,
    knowledge_path: str | None,
    due_date: date,
    reason: str,
    description: str,
    priority: str,
) -> KnowledgeTaskCandidate:
    source_ref_id = f"{exam_id}:{student_id}:{knowledge_point_id}"
    title = f"补弱：{subject_name}-{knowledge_point_name}"
    existing = session.scalar(
        select(StudentPlanningTask).where(
            StudentPlanningTask.student_id == student_id,
            StudentPlanningTask.source_type == "knowledge_remediation",
            StudentPlanningTask.source_ref_id == source_ref_id,
            StudentPlanningTask.task_type == "knowledge_remediation",
            StudentPlanningTask.is_active.is_(True),
            StudentPlanningTask.status.in_(ACTIVE_TASK_STATUSES),
        )
    )
    return KnowledgeTaskCandidate(
        student_id=student_id,
        student_name=student_name,
        class_name=class_name,
        subject_id=subject_id,
        subject_name=subject_name,
        knowledge_point_id=knowledge_point_id,
        knowledge_point_name=knowledge_point_name,
        knowledge_path=knowledge_path,
        source_ref_id=source_ref_id,
        title=title,
        description=f"{reason}。{description}",
        priority=priority,
        due_date=due_date,
        reason=reason,
        existing_task_id=existing.id if existing else None,
        will_create=existing is None,
    )


def _create_knowledge_tasks_from_candidates(
    session: Session,
    candidates: list[KnowledgeTaskCandidate],
) -> list[StudentPlanningTask]:
    created: list[StudentPlanningTask] = []
    for candidate in candidates:
        if not candidate.will_create:
            continue
        payload = PlanningTaskPayload(
            student_id=candidate.student_id,
            source_type="knowledge_remediation",
            source_ref_id=candidate.source_ref_id,
            task_type="knowledge_remediation",
            title=candidate.title,
            description=candidate.description,
            status="not_started",
            priority=candidate.priority,
            due_date=candidate.due_date,
            related_route=f"/students/{candidate.student_id}?tab=planning",
        )
        item = _create_task_if_missing(session, payload)
        if item:
            created.append(item)
    if created:
        write_audit_log(
            session,
            module="planning",
            action="create_knowledge_remediation_tasks",
            target_type="student_planning_task",
            detail_json={"created_count": len(created)},
        )
    return created


def _ensure_volunteer_draft_review_tasks(
    session: Session,
    student_id: int,
    due_date: date,
) -> tuple[list[StudentPlanningTask], int]:
    drafts = session.scalars(
        select(VolunteerDraft).where(
            VolunteerDraft.student_id == student_id,
            VolunteerDraft.is_active.is_(True),
        )
    ).all()
    created: list[StudentPlanningTask] = []
    skipped = 0
    for draft in drafts:
        candidate = PlanningTaskPayload(
            student_id=student_id,
            source_type="volunteer_draft",
            source_ref_id=str(draft.id),
            task_type="chapter_review",
            title=f"复核志愿草稿：{draft.name}",
            description="从志愿草稿生成章程、选科、学费、学制和专业限制复核任务。",
            status="not_started",
            priority="high",
            due_date=due_date,
            related_route="/reports",
        )
        item = _create_task_if_missing(session, candidate)
        if item:
            created.append(item)
        else:
            skipped += 1
    return created, skipped


def _create_task_if_missing(session: Session, payload: PlanningTaskPayload) -> StudentPlanningTask | None:
    existing = session.scalar(
        select(StudentPlanningTask).where(
            StudentPlanningTask.student_id == payload.student_id,
            StudentPlanningTask.source_type == payload.source_type,
            StudentPlanningTask.source_ref_id == payload.source_ref_id,
            StudentPlanningTask.task_type == payload.task_type,
            StudentPlanningTask.title == payload.title.strip(),
            StudentPlanningTask.is_active.is_(True),
        )
    )
    if existing:
        return None
    item = StudentPlanningTask()
    _apply_task_payload(item, payload)
    session.add(item)
    return item


def _evaluation_needs_review(evaluation) -> bool:
    if evaluation.status in {"manual_review", "insufficient_data", "possible"}:
        return True
    warning_rules = evaluation.warning_rules_json or []
    return any(item.get("manual_review_required") for item in warning_rules if isinstance(item, dict))


def _list_goals(session: Session, student_id: int, *, target_year: int | None = None) -> list[StudentPlanningGoal]:
    stmt = select(StudentPlanningGoal).where(
        StudentPlanningGoal.student_id == student_id,
        StudentPlanningGoal.is_active.is_(True),
    )
    if target_year:
        stmt = stmt.where(StudentPlanningGoal.target_year == target_year)
    return list(session.scalars(stmt.order_by(StudentPlanningGoal.target_year.desc(), StudentPlanningGoal.id.desc())))


def _list_tasks(session: Session, student_id: int) -> list[StudentPlanningTask]:
    return list(
        session.scalars(
            select(StudentPlanningTask)
            .where(StudentPlanningTask.student_id == student_id, StudentPlanningTask.is_active.is_(True))
            .order_by(
                StudentPlanningTask.status == "completed",
                StudentPlanningTask.due_date.is_(None),
                StudentPlanningTask.due_date,
                StudentPlanningTask.id.desc(),
            )
        )
    )


def _list_notes(session: Session, student_id: int) -> list[StudentPlanningNote]:
    return list(
        session.scalars(
            select(StudentPlanningNote)
            .where(StudentPlanningNote.student_id == student_id, StudentPlanningNote.is_active.is_(True))
            .order_by(StudentPlanningNote.created_at.desc(), StudentPlanningNote.id.desc())
            .limit(30)
        )
    )


def _list_pathway_evaluations(session: Session, student_id: int, *, target_year: int | None = None):
    stmt = (
        select(StudentPathwayEvaluation)
        .options(selectinload(StudentPathwayEvaluation.pathway))
        .where(StudentPathwayEvaluation.student_id == student_id, StudentPathwayEvaluation.is_active.is_(True))
    )
    if target_year:
        stmt = stmt.where(StudentPathwayEvaluation.target_year == target_year)
    rows = session.scalars(stmt.order_by(StudentPathwayEvaluation.target_year.desc(), StudentPathwayEvaluation.score.desc())).all()
    return [gaokao_pathways._serialize_evaluation(item) for item in rows]


def _build_student_summary(
    goals: list[StudentPlanningGoal],
    tasks: list[StudentPlanningTask],
    has_pathway_profile: bool,
    has_pathway_evaluations: bool,
) -> StudentPlanningSummary:
    today = date.today()
    soon = today + timedelta(days=7)
    active_tasks = [item for item in tasks if item.status in ACTIVE_TASK_STATUSES]
    return StudentPlanningSummary(
        open_task_count=len(active_tasks),
        completed_task_count=sum(1 for item in tasks if item.status == "completed"),
        overdue_task_count=sum(1 for item in active_tasks if item.due_date and item.due_date < today),
        due_soon_task_count=sum(1 for item in active_tasks if item.due_date and today <= item.due_date <= soon),
        material_gap_task_count=sum(1 for item in active_tasks if item.task_type == "material"),
        no_goal=not goals,
        has_pathway_profile=has_pathway_profile,
        has_pathway_evaluations=has_pathway_evaluations,
    )


def _build_suggested_tasks(
    student: Student,
    goals: list[StudentPlanningGoal],
    tasks: list[StudentPlanningTask],
    pathway_evaluations,
) -> list[PlanningTaskRead]:
    existing_titles = {item.title for item in tasks if item.is_active}
    suggestions: list[PlanningTaskRead] = []
    if not goals:
        suggestions.append(
            _serialize_task_payload(
                PlanningTaskPayload(
                    student_id=student.id,
                    source_type="suggestion",
                    task_type="stage_review",
                    title="建立学生升学目标",
                    description="先确定目标路径、目标院校或专业方向，再把材料和复核任务拆成可跟进清单。",
                    priority="high",
                    related_route=f"/students/{student.id}?tab=planning",
                )
            )
        )

    for evaluation in pathway_evaluations[:5]:
        for gap in evaluation.missing_materials_json[:3]:
            material_label = str(gap.get("material_label") or "材料")
            title = f"补齐{evaluation.pathway_name or '升学路径'}材料：{material_label}"
            if title in existing_titles:
                continue
            suggestions.append(
                _serialize_task_payload(
                    PlanningTaskPayload(
                        student_id=student.id,
                        source_type="suggestion",
                        task_type="material",
                        title=title,
                        description=str(gap.get("next_action") or ""),
                        priority="medium",
                        related_route=f"/gaokao-pathways?student_id={student.id}",
                    )
                )
            )
            if len(suggestions) >= 5:
                return suggestions
    return suggestions


def _serialize_task_payload(payload: PlanningTaskPayload) -> PlanningTaskRead:
    today = date.today()
    return PlanningTaskRead(
        id=None,
        student_id=payload.student_id,
        goal_id=payload.goal_id,
        source_type=payload.source_type,
        source_ref_id=payload.source_ref_id,
        task_type=payload.task_type,
        task_type_label=TASK_TYPE_LABELS.get(payload.task_type, payload.task_type),
        title=payload.title,
        description=payload.description,
        status=payload.status,
        status_label=TASK_STATUS_LABELS.get(payload.status, payload.status),
        priority=payload.priority,
        priority_label=PRIORITY_LABELS.get(payload.priority, payload.priority),
        due_date=payload.due_date,
        completed_at=None,
        related_route=payload.related_route,
        is_overdue=bool(payload.due_date and payload.due_date < today),
        is_active=payload.is_active,
    )


def _ensure_student(session: Session, student_id: int) -> Student:
    item = session.scalar(
        select(Student)
        .options(selectinload(Student.current_grade), selectinload(Student.current_class))
        .where(Student.id == student_id, Student.is_active.is_(True))
    )
    if not item:
        raise HTTPException(status_code=404, detail="学生不存在")
    return item


def _ensure_goal_for_student(session: Session, goal_id: int, student_id: int) -> StudentPlanningGoal:
    item = session.get(StudentPlanningGoal, goal_id)
    if not item or not item.is_active or item.student_id != student_id:
        raise HTTPException(status_code=404, detail="升学规划目标不存在或不属于该学生")
    return item


def _ensure_task_for_student(session: Session, task_id: int, student_id: int) -> StudentPlanningTask:
    item = session.get(StudentPlanningTask, task_id)
    if not item or not item.is_active or item.student_id != student_id:
        raise HTTPException(status_code=404, detail="升学规划任务不存在或不属于该学生")
    return item


def _validate_goal_payload(payload: PlanningGoalPayload) -> None:
    if not payload.pathway_code.strip():
        raise HTTPException(status_code=400, detail="目标路径不能为空")
    if not payload.pathway_name.strip():
        raise HTTPException(status_code=400, detail="目标路径名称不能为空")
    _validate_status(payload.status, GOAL_STATUS_LABELS)
    _validate_priority(payload.priority)


def _validate_goal_item(item: StudentPlanningGoal) -> None:
    if not item.pathway_code.strip() or not item.pathway_name.strip():
        raise HTTPException(status_code=400, detail="目标路径不能为空")
    _validate_status(item.status, GOAL_STATUS_LABELS)
    _validate_priority(item.priority)


def _validate_task_payload(payload: PlanningTaskPayload) -> None:
    if not payload.title.strip():
        raise HTTPException(status_code=400, detail="任务标题不能为空")
    _validate_status(payload.status, TASK_STATUS_LABELS)
    _validate_priority(payload.priority)


def _validate_task_item(item: StudentPlanningTask) -> None:
    if not item.title.strip():
        raise HTTPException(status_code=400, detail="任务标题不能为空")
    _validate_status(item.status, TASK_STATUS_LABELS)
    _validate_priority(item.priority)


def _validate_status(value: str, labels: dict[str, str]) -> None:
    if value not in labels:
        raise HTTPException(status_code=400, detail=f"不支持的状态：{value}")


def _validate_priority(value: str) -> None:
    if value not in PRIORITY_LABELS:
        raise HTTPException(status_code=400, detail=f"不支持的优先级：{value}")


def _normalize_choice(value: str, labels: dict[str, str], fallback: str) -> str:
    current = (value or "").strip()
    return current if current in labels else fallback


def _apply_goal_payload(item: StudentPlanningGoal, payload: PlanningGoalPayload) -> None:
    item.student_id = payload.student_id
    item.target_year = payload.target_year
    item.pathway_code = payload.pathway_code.strip()
    item.pathway_name = payload.pathway_name.strip()
    item.target_college = _clean_text(payload.target_college)
    item.target_major = _clean_text(payload.target_major)
    item.target_score = payload.target_score
    item.target_rank = payload.target_rank
    item.backup_pathways = _clean_text(payload.backup_pathways)
    item.status = payload.status
    item.priority = payload.priority
    item.note = _clean_text(payload.note)
    item.is_active = payload.is_active


def _apply_goal_update(item: StudentPlanningGoal, payload: PlanningGoalUpdatePayload) -> None:
    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        if field in {"pathway_code", "pathway_name", "target_college", "target_major", "backup_pathways", "note"}:
            setattr(item, field, _clean_text(value) or "" if field in {"pathway_code", "pathway_name"} else _clean_text(value))
        else:
            setattr(item, field, value)


def _apply_task_payload(item: StudentPlanningTask, payload: PlanningTaskPayload) -> None:
    item.student_id = payload.student_id
    item.goal_id = payload.goal_id
    item.source_type = payload.source_type.strip() or "manual"
    item.source_ref_id = _clean_text(payload.source_ref_id)
    item.task_type = payload.task_type.strip() or "other"
    item.title = payload.title.strip()
    item.description = _clean_text(payload.description)
    item.status = payload.status
    item.priority = payload.priority
    item.due_date = payload.due_date
    item.completed_at = datetime.now() if payload.status == "completed" else None
    item.related_route = _clean_text(payload.related_route)
    item.is_active = payload.is_active


def _apply_task_update(item: StudentPlanningTask, payload: PlanningTaskUpdatePayload) -> None:
    updates = payload.model_dump(exclude_unset=True)
    original_status = item.status
    for field, value in updates.items():
        if field in {"source_type", "source_ref_id", "task_type", "title", "description", "related_route"}:
            if field == "title":
                setattr(item, field, _clean_text(value) or "")
            else:
                setattr(item, field, _clean_text(value))
        else:
            setattr(item, field, value)
    if item.status == "completed" and original_status != "completed":
        item.completed_at = datetime.now()
    if item.status != "completed":
        item.completed_at = None


def _clean_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _serialize_student(item: Student) -> PlanningStudentRead:
    return PlanningStudentRead(
        id=item.id,
        student_no=item.student_no,
        name=item.name,
        grade_name=item.current_grade.name if item.current_grade else None,
        class_name=item.current_class.name if item.current_class else None,
    )


def _serialize_goal(item: StudentPlanningGoal) -> PlanningGoalRead:
    return PlanningGoalRead(
        id=item.id,
        student_id=item.student_id,
        target_year=item.target_year,
        pathway_code=item.pathway_code,
        pathway_name=item.pathway_name,
        target_college=item.target_college,
        target_major=item.target_major,
        target_score=item.target_score,
        target_rank=item.target_rank,
        backup_pathways=item.backup_pathways,
        status=item.status,
        status_label=GOAL_STATUS_LABELS.get(item.status, item.status),
        priority=item.priority,
        priority_label=PRIORITY_LABELS.get(item.priority, item.priority),
        note=item.note,
        created_at=item.created_at,
        updated_at=item.updated_at,
        is_active=item.is_active,
    )


def _serialize_task(item: StudentPlanningTask) -> PlanningTaskRead:
    today = date.today()
    return PlanningTaskRead(
        id=item.id,
        student_id=item.student_id,
        goal_id=item.goal_id,
        source_type=item.source_type,
        source_ref_id=item.source_ref_id,
        task_type=item.task_type,
        task_type_label=TASK_TYPE_LABELS.get(item.task_type, item.task_type),
        title=item.title,
        description=item.description,
        status=item.status,
        status_label=TASK_STATUS_LABELS.get(item.status, item.status),
        priority=item.priority,
        priority_label=PRIORITY_LABELS.get(item.priority, item.priority),
        due_date=item.due_date,
        completed_at=item.completed_at,
        related_route=item.related_route,
        is_overdue=bool(item.due_date and item.status in ACTIVE_TASK_STATUSES and item.due_date < today),
        created_at=item.created_at,
        updated_at=item.updated_at,
        is_active=item.is_active,
    )


def _serialize_note(item: StudentPlanningNote) -> PlanningNoteRead:
    return PlanningNoteRead(
        id=item.id,
        student_id=item.student_id,
        goal_id=item.goal_id,
        task_id=item.task_id,
        note_type=item.note_type,
        note_type_label=NOTE_TYPE_LABELS.get(item.note_type, item.note_type),
        content=item.content,
        created_at=item.created_at,
        updated_at=item.updated_at,
        is_active=item.is_active,
    )
