from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from datetime import date, datetime
from zipfile import BadZipFile

from fastapi import HTTPException
from openpyxl.utils.exceptions import InvalidFileException
from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session, joinedload

from app.core.config import Settings
from app.exporters.students import export_students as export_students_workbook
from app.importers.students import StudentImporter
from app.models import (
    ConfigItem,
    Exam,
    ExamSubject,
    Grade,
    RecommendationResult,
    SchoolClass,
    ScoreRecord,
    ScoreSubjectSnapshot,
    ScoreTotalSnapshot,
    Student,
    StudentAttachment,
    StudentCareerPreference,
    StudentClassHistory,
    StudentClassTransferBatch,
    StudentClassTransferItem,
    StudentGaokaoScoreProjection,
    StudentGuardian,
    StudentGrowthRecord,
    StudentPathwayEvaluation,
    StudentPathwayProfile,
    StudentTeacherComment,
    Subject,
    TeachingAssignment,
    VolunteerDraft,
)
from app.repositories.archive import list_growth_records as repo_list_growth_records
from app.repositories.recommendations import get_employment_direction
from app.repositories.students import (
    get_student,
    get_student_by_no,
    get_student_career_preference as repo_get_student_career_preference,
    list_students as repo_list_students,
)
from app.repositories.system import create_import_job, get_stored_file, write_audit_log
from app.schemas.student import (
    StudentAttachmentPayload,
    StudentAttachmentSummary,
    StudentBulkDeleteAssociationSummary,
    StudentBulkDeleteExecuteItem,
    StudentBulkDeleteExecuteRequest,
    StudentBulkDeleteExecuteResponse,
    StudentBulkDeletePreviewItem,
    StudentBulkDeletePreviewRequest,
    StudentBulkDeletePreviewResponse,
    StudentCareerPreferencePayload,
    StudentCareerPreferenceRead,
    StudentClassHistoryRead,
    StudentClassTransferExecuteItem,
    StudentClassTransferExecuteRequest,
    StudentClassTransferExecuteResponse,
    StudentClassTransferHistoryItem,
    StudentClassTransferPreviewItem,
    StudentClassTransferPreviewRequest,
    StudentClassTransferPreviewResponse,
    StudentExamSubjectItem,
    StudentExamTrendItem,
    StudentGuardianPayload,
    StudentGuardianRead,
    StudentGrowthRecordSummary,
    StudentListResponse,
    StudentPayload,
    StudentPerformanceSummary,
    StudentProfileRead,
    StudentRecommendationSummary,
    StudentRead,
    StudentTeacherCommentListResponse,
    StudentTeacherCommentPayload,
    StudentTeacherCommentRead,
    StudentTeacherCommentSubjectOption,
)
from app.services.auth import AuthContext
from app.services import recommendations as recommendation_service


def _serialize_guardian(item: StudentGuardian) -> StudentGuardianRead:
    return StudentGuardianRead.model_validate(item)


def _serialize_student(item: Student) -> StudentRead:
    return StudentRead(
        id=item.id,
        student_no=item.student_no,
        name=item.name,
        gender=item.gender,
        birth_date=item.birth_date,
        id_number=item.id_number,
        admission_year=item.admission_year,
        current_grade_id=item.current_grade_id,
        current_grade_name=item.current_grade.name if item.current_grade else None,
        current_class_id=item.current_class_id,
        current_class_name=item.current_class.name if item.current_class else None,
        status=item.status,
        student_type=item.student_type,
        art_track=item.art_track,
        origin_province=item.origin_province,
        phone=item.phone,
        address=item.address,
        note=item.note,
        is_active=item.is_active,
        guardians=[_serialize_guardian(guardian) for guardian in item.guardians],
    )


def _serialize_student_career_preference(item: StudentCareerPreference) -> StudentCareerPreferenceRead:
    return StudentCareerPreferenceRead(
        id=item.id,
        student_id=item.student_id,
        primary_direction_id=item.primary_direction_id,
        primary_direction_name=item.primary_direction.name if item.primary_direction else None,
        secondary_direction_id=item.secondary_direction_id,
        secondary_direction_name=item.secondary_direction.name if item.secondary_direction else None,
        alternative_direction_id=item.alternative_direction_id,
        alternative_direction_name=item.alternative_direction.name if item.alternative_direction else None,
        priority_focuses_json=item.priority_focuses_json or [],
        preferred_industries_json=item.preferred_industries_json or [],
        preferred_job_types_json=item.preferred_job_types_json or [],
        target_employment_cities_json=item.target_employment_cities_json or [],
        accepts_postgraduate=item.accepts_postgraduate,
        accepts_public_service=item.accepts_public_service,
        accepts_certificate=item.accepts_certificate,
        accepts_long_training=item.accepts_long_training,
        created_at=item.created_at,
        updated_at=item.updated_at,
        is_active=item.is_active,
    )


def _ensure_grade_class(session: Session, grade_id: int | None, class_id: int | None) -> tuple[int | None, int | None]:
    grade = session.get(Grade, grade_id) if grade_id else None
    school_class = session.get(SchoolClass, class_id) if class_id else None
    if grade_id and not grade:
        raise HTTPException(status_code=404, detail="年级不存在")
    if class_id and not school_class:
        raise HTTPException(status_code=404, detail="班级不存在")
    if grade and school_class and school_class.grade_id != grade.id:
        raise HTTPException(status_code=400, detail="班级与年级不匹配")
    return (grade.id if grade else (school_class.grade_id if school_class else None), school_class.id if school_class else None)


def _sync_guardians(student: Student, guardians: list[StudentGuardianPayload]) -> None:
    student.guardians.clear()
    for guardian in guardians:
        student.guardians.append(StudentGuardian(**guardian.model_dump()))


def _update_class_history(session: Session, student: Student, new_grade_id: int | None, new_class_id: int | None) -> None:
    if not new_grade_id and not new_class_id:
        return
    current_open_history = next((item for item in student.class_histories if item.end_date is None), None)
    if current_open_history and current_open_history.grade_id == new_grade_id and current_open_history.class_id == new_class_id:
        return
    if current_open_history and current_open_history.end_date is None:
        current_open_history.end_date = date.today()
    student.class_histories.append(
        StudentClassHistory(
            grade_id=new_grade_id,
            class_id=new_class_id,
            start_date=date.today(),
            end_date=None,
            reason="系统维护",
        )
    )
    session.flush()


def _refresh_class_student_count(session: Session, class_id: int | None) -> None:
    if not class_id:
        return
    school_class = session.get(SchoolClass, class_id)
    if not school_class:
        return
    school_class.student_count = (
        session.scalar(
            select(func.count())
            .select_from(Student)
            .where(Student.current_class_id == class_id, Student.is_active.is_(True))
        )
        or 0
    )


def list_students(
    session: Session,
    *,
    page: int,
    page_size: int,
    student_no: str | None = None,
    name: str | None = None,
    grade_id: int | None = None,
    class_id: int | None = None,
    status: str | None = None,
    student_type: str | None = None,
    art_track: str | None = None,
    include_inactive: bool = False,
    scope_class_ids: set[int] | None = None,
) -> StudentListResponse:
    items, total = repo_list_students(
        session,
        page=page,
        page_size=page_size,
        student_no=student_no,
        name=name,
        grade_id=grade_id,
        class_id=class_id,
        status=status,
        student_type=student_type,
        art_track=art_track,
        include_inactive=include_inactive,
        scope_class_ids=scope_class_ids,
    )
    return StudentListResponse(
        items=[_serialize_student(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


def _ensure_student_scope_access(
    item: Student,
    scope_class_ids: set[int] | None,
    *,
    detail: str = "无权访问该学生",
) -> None:
    if scope_class_ids is None:
        return
    if item.current_class_id not in scope_class_ids:
        raise HTTPException(status_code=403, detail=detail)


def get_student_detail(
    session: Session,
    student_id: int,
    *,
    scope_class_ids: set[int] | None = None,
) -> StudentRead:
    item = get_student(session, student_id)
    if not item:
        raise HTTPException(status_code=404, detail="学生不存在")
    _ensure_student_scope_access(item, scope_class_ids)
    return _serialize_student(item)


def _student_comment_class_ids(student: Student) -> set[int]:
    class_ids = {student.current_class_id} if student.current_class_id else set()
    class_ids.update(
        history.class_id
        for history in student.class_histories
        if history.is_active and history.class_id is not None
    )
    return class_ids


def _assignment_can_comment_now(assignment: TeachingAssignment) -> bool:
    if not assignment.is_active or assignment.subject_id is None:
        return False
    semester = assignment.semester
    if not semester or not semester.is_active:
        return False
    if semester.is_current:
        return True
    today = date.today()
    return semester.start_date <= today <= semester.end_date


def _load_teacher_comment_assignments(
    session: Session,
    student: Student,
    *,
    teacher_id: int | None,
) -> list[TeachingAssignment]:
    if teacher_id is None:
        return []
    class_ids = _student_comment_class_ids(student)
    if not class_ids:
        return []
    assignments = session.scalars(
        select(TeachingAssignment)
        .options(
            joinedload(TeachingAssignment.teacher),
            joinedload(TeachingAssignment.subject),
            joinedload(TeachingAssignment.school_class),
            joinedload(TeachingAssignment.semester),
        )
        .where(
            TeachingAssignment.teacher_id == teacher_id,
            TeachingAssignment.class_id.in_(class_ids),
            TeachingAssignment.is_active.is_(True),
        )
        .order_by(TeachingAssignment.semester_id.desc(), TeachingAssignment.subject_id)
    ).all()
    deduped: list[TeachingAssignment] = []
    seen_subject_ids: set[int] = set()
    for assignment in assignments:
        if not _assignment_can_comment_now(assignment):
            continue
        if assignment.subject_id is None or assignment.subject_id in seen_subject_ids:
            continue
        seen_subject_ids.add(assignment.subject_id)
        deduped.append(assignment)
    return deduped


def _serialize_teacher_comment_subject_option(
    assignment: TeachingAssignment,
) -> StudentTeacherCommentSubjectOption:
    return StudentTeacherCommentSubjectOption(
        subject_id=assignment.subject_id or 0,
        subject_name=assignment.subject.name if assignment.subject else "未维护科目",
        teacher_id=assignment.teacher_id,
        teacher_name=assignment.teacher.name if assignment.teacher else "未维护教师",
        class_id=assignment.class_id,
        class_name=assignment.school_class.name if assignment.school_class else None,
        semester_id=assignment.semester_id,
        semester_name=assignment.semester.name if assignment.semester else None,
    )


def _serialize_student_teacher_comment(item: StudentTeacherComment) -> StudentTeacherCommentRead:
    return StudentTeacherCommentRead(
        id=item.id,
        student_id=item.student_id,
        teacher_id=item.teacher_id,
        teacher_name=item.teacher.name if item.teacher else "未维护教师",
        subject_id=item.subject_id,
        subject_name=item.subject.name if item.subject else None,
        class_id=item.class_id,
        class_name=item.school_class.name if item.school_class else None,
        semester_id=item.semester_id,
        semester_name=item.semester.name if item.semester else None,
        content=item.content,
        commented_at=item.commented_at,
        created_at=item.created_at,
        updated_at=item.updated_at,
        is_active=item.is_active,
    )


def list_student_teacher_comments(
    session: Session,
    student_id: int,
    *,
    actor: AuthContext,
    scope_class_ids: set[int] | None = None,
) -> StudentTeacherCommentListResponse:
    student = get_student(session, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="学生不存在")
    _ensure_student_scope_access(student, scope_class_ids)

    comments = session.scalars(
        select(StudentTeacherComment)
        .options(
            joinedload(StudentTeacherComment.teacher),
            joinedload(StudentTeacherComment.subject),
            joinedload(StudentTeacherComment.school_class),
            joinedload(StudentTeacherComment.semester),
        )
        .where(
            StudentTeacherComment.student_id == student_id,
            StudentTeacherComment.is_active.is_(True),
        )
        .order_by(StudentTeacherComment.commented_at.desc(), StudentTeacherComment.id.desc())
    ).all()
    assignments = _load_teacher_comment_assignments(
        session,
        student,
        teacher_id=actor.teacher_id,
    )
    return StudentTeacherCommentListResponse(
        items=[_serialize_student_teacher_comment(item) for item in comments],
        can_comment=bool(assignments),
        available_subjects=[
            _serialize_teacher_comment_subject_option(assignment)
            for assignment in assignments
            if assignment.subject_id is not None
        ],
    )


def create_student_teacher_comment(
    session: Session,
    student_id: int,
    payload: StudentTeacherCommentPayload,
    *,
    actor: AuthContext,
    scope_class_ids: set[int] | None = None,
) -> StudentTeacherCommentRead:
    student = get_student(session, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="学生不存在")
    _ensure_student_scope_access(student, scope_class_ids)
    if actor.teacher_id is None:
        raise HTTPException(status_code=403, detail="当前账号未关联教师档案，无法发布教师评语")

    assignments = _load_teacher_comment_assignments(
        session,
        student,
        teacher_id=actor.teacher_id,
    )
    if not assignments:
        raise HTTPException(status_code=403, detail="当前账号不是该生任课教师，无法发布评语")

    selected_assignment: TeachingAssignment | None = None
    if payload.subject_id is None:
        subject_ids = {assignment.subject_id for assignment in assignments}
        if len(subject_ids) == 1:
            selected_assignment = assignments[0]
        else:
            raise HTTPException(status_code=400, detail="请选择评价科目")
    else:
        selected_assignment = next(
            (assignment for assignment in assignments if assignment.subject_id == payload.subject_id),
            None,
        )
        if selected_assignment is None:
            raise HTTPException(status_code=403, detail="当前账号不是该生该科任课教师，无法发布评语")

    comment = StudentTeacherComment(
        student_id=student_id,
        teacher_id=actor.teacher_id,
        subject_id=selected_assignment.subject_id,
        class_id=selected_assignment.class_id,
        semester_id=selected_assignment.semester_id,
        commented_at=datetime.now(),
        content=payload.content,
    )
    session.add(comment)
    session.flush()
    session.refresh(comment)
    write_audit_log(
        session,
        module="students",
        action="create_teacher_comment",
        target_type="student_teacher_comment",
        target_id=str(comment.id),
        actor_user_id=actor.user_id,
        actor_username=actor.username,
        client_ip=actor.client_ip,
        detail_json={
            "student_id": student_id,
            "teacher_id": actor.teacher_id,
            "subject_id": comment.subject_id,
            "class_id": comment.class_id,
            "semester_id": comment.semester_id,
        },
    )
    return _serialize_student_teacher_comment(comment)


def preview_student_bulk_delete(
    session: Session,
    payload: StudentBulkDeletePreviewRequest,
) -> StudentBulkDeletePreviewResponse:
    return _build_bulk_delete_preview(session, payload)


def execute_student_bulk_delete(
    session: Session,
    payload: StudentBulkDeleteExecuteRequest,
) -> StudentBulkDeleteExecuteResponse:
    preview = _build_bulk_delete_preview(session, payload)
    if payload.confirm_token != preview.confirm_token:
        raise HTTPException(status_code=400, detail="删除确认已过期，请重新预检后再执行")
    if payload.confirm_text != preview.required_confirm_text:
        raise HTTPException(status_code=400, detail=f"确认文字不正确，请输入：{preview.required_confirm_text}")

    execute_items: list[StudentBulkDeleteExecuteItem] = []
    refreshed_classes: set[int] = set()
    for preview_item in preview.items:
        if preview_item.status == "blocked":
            execute_items.append(
                StudentBulkDeleteExecuteItem(
                    student_id=preview_item.student_id,
                    student_no=preview_item.student_no,
                    student_name=preview_item.student_name,
                    status="blocked",
                    message=preview_item.message,
                    error_message=preview_item.reason,
                    association_counts=preview_item.association_counts,
                )
            )
            continue

        student = get_student(session, preview_item.student_id)
        if not student or not student.is_active:
            execute_items.append(
                StudentBulkDeleteExecuteItem(
                    student_id=preview_item.student_id,
                    student_no=preview_item.student_no,
                    student_name=preview_item.student_name,
                    status="failed",
                    message="执行时学生状态已变化，未停用",
                    error_message="学生不存在或已停用",
                    association_counts=preview_item.association_counts,
                )
            )
            continue

        before_snapshot = _snapshot_student_for_bulk_delete(student)
        student.is_active = False
        session.flush()
        if student.current_class_id:
            refreshed_classes.add(student.current_class_id)
        after_snapshot = _snapshot_student_for_bulk_delete(student)
        execute_items.append(
            StudentBulkDeleteExecuteItem(
                student_id=student.id,
                student_no=student.student_no,
                student_name=student.name,
                status="success",
                message="已停用学生主档，成绩、成长档案、教师评语、附件、推荐记录和升学画像均保留",
                before_snapshot_json=before_snapshot,
                after_snapshot_json=after_snapshot,
                association_counts=preview_item.association_counts,
            )
        )

    for class_id in refreshed_classes:
        _refresh_class_student_count(session, class_id)

    success_items = [item for item in execute_items if item.status == "success"]
    failed_items = [item for item in execute_items if item.status != "success"]
    blocked_items = [item for item in execute_items if item.status == "blocked"]
    if success_items and failed_items:
        operation_status = "partially_failed"
    elif success_items:
        operation_status = "success"
    else:
        operation_status = "failed"

    audit_log = write_audit_log(
        session,
        module="students",
        action="bulk_delete",
        target_type="student_bulk_operation",
        target_id=preview.confirm_token[:16],
        detail_json={
            "operation_type": "bulk_delete",
            "mode": payload.mode,
            "reason": payload.reason,
            "operator_name": payload.operator_name,
            "requested_student_ids": payload.student_ids,
            "required_confirm_text": preview.required_confirm_text,
            "status": operation_status,
            "success_count": len(success_items),
            "failed_count": len(failed_items),
            "blocked_count": len(blocked_items),
            "items": [item.model_dump(mode="json") for item in execute_items],
        },
    )
    message = (
        f"已停用 {len(success_items)} 名学生主档；"
        f"{len(failed_items)} 名未处理。历史成绩、成长档案、教师评语、附件、推荐记录和升学画像均未删除。"
    )
    return StudentBulkDeleteExecuteResponse(
        total=preview.total,
        success_count=len(success_items),
        failed_count=len(failed_items),
        blocked_count=len(blocked_items),
        status=operation_status,
        mode=payload.mode,
        message=message,
        audit_log_id=audit_log.id,
        items=execute_items,
        success_items=success_items,
        failed_items=failed_items,
        blocked=blocked_items,
    )


_BULK_DELETE_TOKEN_VERSION = "student-bulk-delete-v1"
_ASSOCIATION_LABELS = [
    ("score_count", "成绩记录"),
    ("score_snapshot_count", "成绩分析快照"),
    ("growth_record_count", "成长档案"),
    ("teacher_comment_count", "教师评语"),
    ("attachment_count", "附件"),
    ("class_history_count", "班级历史"),
    ("recommendation_count", "推荐记录"),
    ("volunteer_draft_count", "志愿草稿"),
    ("gaokao_score_projection_count", "高考分数预估"),
    ("pathway_profile_count", "升学画像"),
    ("pathway_evaluation_count", "路径评估"),
]


def _build_bulk_delete_preview(
    session: Session,
    payload: StudentBulkDeletePreviewRequest,
) -> StudentBulkDeletePreviewResponse:
    requested_ids = payload.student_ids
    students = _load_students_for_bulk_operation(session, requested_ids)
    association_map = _load_bulk_delete_association_counts(session, requested_ids)
    items: list[StudentBulkDeletePreviewItem] = []

    for student_id in requested_ids:
        student = students.get(student_id)
        counts = association_map.get(student_id, StudentBulkDeleteAssociationSummary())
        if not student or not student.is_active:
            items.append(
                StudentBulkDeletePreviewItem(
                    student_id=student_id,
                    student_no=student.student_no if student else None,
                    student_name=student.name if student else None,
                    status="blocked",
                    reason="学生不存在或已停用",
                    message="学生不存在或已停用，已阻断删除",
                    association_counts=counts,
                )
            )
            continue

        items.append(
            StudentBulkDeletePreviewItem(
                student_id=student.id,
                student_no=student.student_no,
                student_name=student.name,
                current_class_id=student.current_class_id,
                current_class_name=student.current_class.name if student.current_class else None,
                status="deletable",
                message=_build_bulk_delete_preview_message(counts),
                association_counts=counts,
            )
        )

    deletable = [item for item in items if item.status == "deletable"]
    blocked = [item for item in items if item.status == "blocked"]
    required_confirm_text = f"确认删除 {len(deletable)} 名学生"
    response = StudentBulkDeletePreviewResponse(
        total=len(requested_ids),
        deletable_count=len(deletable),
        blocked_count=len(blocked),
        mode=payload.mode,
        required_confirm_text=required_confirm_text,
        confirm_token="pending",
        items=items,
        warnings=[item for item in deletable if _association_total(item.association_counts) > 0],
        blocked=blocked,
    )
    response.confirm_token = _build_bulk_delete_confirm_token(payload, response)
    return response


def _load_students_for_bulk_operation(session: Session, student_ids: list[int]) -> dict[int, Student]:
    if not student_ids:
        return {}
    rows = session.scalars(
        select(Student)
        .where(Student.id.in_(student_ids))
        .options(
            joinedload(Student.current_grade),
            joinedload(Student.current_class),
        )
    ).all()
    return {item.id: item for item in rows}


def _load_bulk_delete_association_counts(
    session: Session,
    student_ids: list[int],
) -> dict[int, StudentBulkDeleteAssociationSummary]:
    score_counts = _count_active_by_student(session, ScoreRecord, student_ids)
    score_snapshot_counts = _merge_count_maps(
        _count_active_by_student(session, ScoreTotalSnapshot, student_ids),
        _count_active_by_student(session, ScoreSubjectSnapshot, student_ids),
    )
    growth_counts = _count_active_by_student(session, StudentGrowthRecord, student_ids)
    teacher_comment_counts = _count_active_by_student(session, StudentTeacherComment, student_ids)
    attachment_counts = _count_active_by_student(session, StudentAttachment, student_ids)
    class_history_counts = _count_active_by_student(session, StudentClassHistory, student_ids)
    recommendation_counts = _count_active_by_student(session, RecommendationResult, student_ids)
    volunteer_draft_counts = _count_active_by_student(session, VolunteerDraft, student_ids)
    score_projection_counts = _count_active_by_student(session, StudentGaokaoScoreProjection, student_ids)
    pathway_profile_counts = _count_active_by_student(session, StudentPathwayProfile, student_ids)
    pathway_evaluation_counts = _count_active_by_student(session, StudentPathwayEvaluation, student_ids)
    return {
        student_id: StudentBulkDeleteAssociationSummary(
            score_count=score_counts.get(student_id, 0),
            score_snapshot_count=score_snapshot_counts.get(student_id, 0),
            growth_record_count=growth_counts.get(student_id, 0),
            teacher_comment_count=teacher_comment_counts.get(student_id, 0),
            attachment_count=attachment_counts.get(student_id, 0),
            class_history_count=class_history_counts.get(student_id, 0),
            recommendation_count=recommendation_counts.get(student_id, 0),
            volunteer_draft_count=volunteer_draft_counts.get(student_id, 0),
            gaokao_score_projection_count=score_projection_counts.get(student_id, 0),
            pathway_profile_count=pathway_profile_counts.get(student_id, 0),
            pathway_evaluation_count=pathway_evaluation_counts.get(student_id, 0),
        )
        for student_id in student_ids
    }


def _count_active_by_student(session: Session, model, student_ids: list[int]) -> dict[int, int]:  # type: ignore[no-untyped-def]
    if not student_ids:
        return {}
    rows = session.execute(
        select(model.student_id, func.count())
        .where(model.student_id.in_(student_ids), model.is_active.is_(True))
        .group_by(model.student_id)
    ).all()
    return {int(student_id): int(count) for student_id, count in rows}


def _merge_count_maps(*maps: dict[int, int]) -> dict[int, int]:
    merged: dict[int, int] = {}
    for current in maps:
        for key, value in current.items():
            merged[key] = merged.get(key, 0) + value
    return merged


def _association_total(counts: StudentBulkDeleteAssociationSummary) -> int:
    return sum(int(value) for value in counts.model_dump().values())


def _build_bulk_delete_preview_message(counts: StudentBulkDeleteAssociationSummary) -> str:
    labels = [
        label
        for field_name, label in _ASSOCIATION_LABELS
        if int(getattr(counts, field_name)) > 0
    ]
    if not labels:
        return "可停用学生主档；未检测到主要关联数据。"
    return f"该学生有关联{'、'.join(labels)}，删除后仅停用学生主档，不清除历史数据。"


def _build_bulk_delete_confirm_token(
    payload: StudentBulkDeletePreviewRequest,
    preview: StudentBulkDeletePreviewResponse,
) -> str:
    token_payload = {
        "version": _BULK_DELETE_TOKEN_VERSION,
        "student_ids": payload.student_ids,
        "mode": payload.mode,
        "reason": payload.reason,
        "operator_name": payload.operator_name,
        "deletable_ids": [item.student_id for item in preview.items if item.status == "deletable"],
        "blocked_ids": [item.student_id for item in preview.items if item.status == "blocked"],
        "required_confirm_text": preview.required_confirm_text,
    }
    raw_value = json.dumps(token_payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw_value.encode("utf-8")).hexdigest()


def _snapshot_student_for_bulk_delete(student: Student) -> dict:
    return {
        "id": student.id,
        "student_no": student.student_no,
        "name": student.name,
        "status": student.status,
        "current_grade_id": student.current_grade_id,
        "current_grade_name": student.current_grade.name if student.current_grade else None,
        "current_class_id": student.current_class_id,
        "current_class_name": student.current_class.name if student.current_class else None,
        "student_type": student.student_type,
        "art_track": student.art_track,
        "origin_province": student.origin_province,
        "is_active": student.is_active,
    }


_CLASS_TRANSFER_TOKEN_VERSION = "student-class-transfer-v1"


def preview_student_class_transfer(
    session: Session,
    payload: StudentClassTransferPreviewRequest,
) -> StudentClassTransferPreviewResponse:
    return _build_class_transfer_preview(session, payload)


def execute_student_class_transfer(
    session: Session,
    payload: StudentClassTransferExecuteRequest,
) -> StudentClassTransferExecuteResponse:
    preview = _build_class_transfer_preview(session, payload)
    if payload.confirm_token != preview.confirm_token:
        raise HTTPException(status_code=400, detail="调班确认已过期，请重新预检后再执行")
    if payload.confirm_text != preview.required_confirm_text:
        raise HTTPException(status_code=400, detail=f"确认文字不正确，请输入：{preview.required_confirm_text}")

    target_class = _get_transfer_target_class(session, payload.target_class_id)
    target_grade_id = target_class.grade_id
    target_grade_name = target_class.grade.name if target_class.grade else None
    source_class_ids = {
        item.from_class_id for item in preview.items if item.status == "transferable" and item.from_class_id
    }
    batch = StudentClassTransferBatch(
        source_class_id=next(iter(source_class_ids)) if len(source_class_ids) == 1 else None,
        target_class_id=target_class.id,
        target_grade_id=target_grade_id,
        effective_on=payload.effective_on,
        reason=payload.reason,
        note=payload.note,
        operator_name=payload.operator_name,
        status="pending",
        requested_count=preview.total,
        confirm_text=preview.required_confirm_text,
    )
    session.add(batch)
    session.flush()

    execute_items: list[StudentClassTransferExecuteItem] = []
    refreshed_classes: set[int] = {target_class.id}
    for preview_item in preview.items:
        if preview_item.status == "blocked":
            transfer_item = StudentClassTransferItem(
                batch_id=batch.id,
                requested_student_id=preview_item.student_id,
                student_id=preview_item.student_id if preview_item.student_no else None,
                student_no_snapshot=preview_item.student_no,
                student_name_snapshot=preview_item.student_name,
                from_grade_id=preview_item.from_grade_id,
                from_grade_name_snapshot=preview_item.from_grade_name,
                from_class_id=preview_item.from_class_id,
                from_class_name_snapshot=preview_item.from_class_name,
                to_grade_id=preview_item.to_grade_id,
                to_grade_name_snapshot=preview_item.to_grade_name,
                to_class_id=preview_item.to_class_id,
                to_class_name_snapshot=preview_item.to_class_name,
                status="blocked",
                error_message=preview_item.reason,
            )
            session.add(transfer_item)
            session.flush()
            execute_items.append(
                StudentClassTransferExecuteItem(
                    student_id=preview_item.student_id,
                    batch_item_id=transfer_item.id,
                    student_no=preview_item.student_no,
                    student_name=preview_item.student_name,
                    from_grade_id=preview_item.from_grade_id,
                    from_grade_name=preview_item.from_grade_name,
                    from_class_id=preview_item.from_class_id,
                    from_class_name=preview_item.from_class_name,
                    to_grade_id=preview_item.to_grade_id,
                    to_grade_name=preview_item.to_grade_name,
                    to_class_id=preview_item.to_class_id,
                    to_class_name=preview_item.to_class_name,
                    status="blocked",
                    message=preview_item.message,
                    error_message=preview_item.reason,
                )
            )
            continue

        student = get_student(session, preview_item.student_id)
        if not student or not student.is_active:
            transfer_item = StudentClassTransferItem(
                batch_id=batch.id,
                requested_student_id=preview_item.student_id,
                student_id=student.id if student else None,
                student_no_snapshot=student.student_no if student else preview_item.student_no,
                student_name_snapshot=student.name if student else preview_item.student_name,
                from_grade_id=preview_item.from_grade_id,
                from_grade_name_snapshot=preview_item.from_grade_name,
                from_class_id=preview_item.from_class_id,
                from_class_name_snapshot=preview_item.from_class_name,
                to_grade_id=preview_item.to_grade_id,
                to_grade_name_snapshot=preview_item.to_grade_name,
                to_class_id=preview_item.to_class_id,
                to_class_name_snapshot=preview_item.to_class_name,
                status="failed",
                error_message="执行时学生状态已变化，未调班",
            )
            session.add(transfer_item)
            session.flush()
            execute_items.append(
                StudentClassTransferExecuteItem(
                    student_id=preview_item.student_id,
                    batch_item_id=transfer_item.id,
                    student_no=preview_item.student_no,
                    student_name=preview_item.student_name,
                    from_grade_id=preview_item.from_grade_id,
                    from_grade_name=preview_item.from_grade_name,
                    from_class_id=preview_item.from_class_id,
                    from_class_name=preview_item.from_class_name,
                    to_grade_id=preview_item.to_grade_id,
                    to_grade_name=preview_item.to_grade_name,
                    to_class_id=preview_item.to_class_id,
                    to_class_name=preview_item.to_class_name,
                    status="failed",
                    message="执行时学生状态已变化，未调班",
                    error_message="学生不存在或已停用",
                )
            )
            continue

        before_snapshot = _snapshot_student_for_class_transfer(student)
        old_class_id = student.current_class_id
        if old_class_id:
            refreshed_classes.add(old_class_id)
        student.current_grade_id = target_grade_id
        student.current_class_id = target_class.id
        student.current_grade = target_class.grade
        student.current_class = target_class
        _record_class_transfer_history(
            session,
            student,
            target_grade_id=target_grade_id,
            target_class_id=target_class.id,
            effective_on=payload.effective_on,
            reason=f"调班：{payload.reason}",
        )
        session.flush()
        after_snapshot = _snapshot_student_for_class_transfer(student)
        transfer_item = StudentClassTransferItem(
            batch_id=batch.id,
            requested_student_id=student.id,
            student_id=student.id,
            student_no_snapshot=student.student_no,
            student_name_snapshot=student.name,
            from_grade_id=before_snapshot["current_grade_id"],
            from_grade_name_snapshot=before_snapshot["current_grade_name"],
            from_class_id=before_snapshot["current_class_id"],
            from_class_name_snapshot=before_snapshot["current_class_name"],
            to_grade_id=target_grade_id,
            to_grade_name_snapshot=target_grade_name,
            to_class_id=target_class.id,
            to_class_name_snapshot=target_class.name,
            before_snapshot_json=before_snapshot,
            after_snapshot_json=after_snapshot,
            status="success",
        )
        session.add(transfer_item)
        session.flush()
        execute_items.append(
            StudentClassTransferExecuteItem(
                student_id=student.id,
                batch_item_id=transfer_item.id,
                student_no=student.student_no,
                student_name=student.name,
                from_grade_id=before_snapshot["current_grade_id"],
                from_grade_name=before_snapshot["current_grade_name"],
                from_class_id=before_snapshot["current_class_id"],
                from_class_name=before_snapshot["current_class_name"],
                to_grade_id=target_grade_id,
                to_grade_name=target_grade_name,
                to_class_id=target_class.id,
                to_class_name=target_class.name,
                status="success",
                message=_build_class_transfer_success_message(before_snapshot, target_grade_name, target_class.name),
                before_snapshot_json=before_snapshot,
                after_snapshot_json=after_snapshot,
            )
        )

    for class_id in refreshed_classes:
        _refresh_class_student_count(session, class_id)

    success_items = [item for item in execute_items if item.status == "success"]
    failed_items = [item for item in execute_items if item.status != "success"]
    blocked_items = [item for item in execute_items if item.status == "blocked"]
    if success_items and failed_items:
        operation_status = "partially_failed"
    elif success_items:
        operation_status = "success"
    else:
        operation_status = "failed"
    batch.status = operation_status
    batch.success_count = len(success_items)
    batch.failed_count = len(failed_items)
    batch.blocked_count = len(blocked_items)
    batch.finished_at = datetime.now()
    session.flush()

    audit_log = write_audit_log(
        session,
        module="students",
        action="class_transfer",
        target_type="student_class_transfer_batch",
        target_id=str(batch.id),
        detail_json={
            "operation_type": "class_transfer",
            "batch_id": batch.id,
            "target_class_id": payload.target_class_id,
            "target_class_name": target_class.name,
            "target_grade_id": target_grade_id,
            "target_grade_name": target_grade_name,
            "effective_on": payload.effective_on.isoformat(),
            "reason": payload.reason,
            "note": payload.note,
            "operator_name": payload.operator_name,
            "requested_student_ids": payload.student_ids,
            "required_confirm_text": preview.required_confirm_text,
            "status": operation_status,
            "success_count": len(success_items),
            "failed_count": len(failed_items),
            "blocked_count": len(blocked_items),
            "items": [item.model_dump(mode="json") for item in execute_items],
        },
    )
    message = f"已完成 {len(success_items)} 名学生调班；{len(failed_items)} 名未调班。"
    return StudentClassTransferExecuteResponse(
        total=preview.total,
        success_count=len(success_items),
        failed_count=len(failed_items),
        blocked_count=len(blocked_items),
        status=operation_status,
        message=message,
        batch_id=batch.id,
        audit_log_id=audit_log.id,
        items=execute_items,
        success_items=success_items,
        failed_items=failed_items,
        blocked=blocked_items,
    )


def list_student_class_transfer_history(
    session: Session,
    student_id: int,
) -> list[StudentClassTransferHistoryItem]:
    _ensure_student_exists(session, student_id)
    rows = session.execute(
        select(StudentClassTransferItem, StudentClassTransferBatch)
        .join(StudentClassTransferBatch, StudentClassTransferBatch.id == StudentClassTransferItem.batch_id)
        .where(
            StudentClassTransferItem.student_id == student_id,
            StudentClassTransferItem.status == "success",
            StudentClassTransferItem.is_active.is_(True),
            StudentClassTransferBatch.is_active.is_(True),
        )
        .order_by(
            StudentClassTransferBatch.effective_on.desc(),
            StudentClassTransferItem.id.desc(),
        )
    ).all()
    return [
        _serialize_class_transfer_history_item(item, batch)
        for item, batch in rows
    ]


def _build_class_transfer_preview(
    session: Session,
    payload: StudentClassTransferPreviewRequest,
) -> StudentClassTransferPreviewResponse:
    target_class = _get_transfer_target_class(session, payload.target_class_id)
    students = _load_students_for_bulk_operation(session, payload.student_ids)
    items = [
        _build_class_transfer_preview_item(
            student_id,
            students.get(student_id),
            target_class,
            payload,
        )
        for student_id in payload.student_ids
    ]
    transferable = [item for item in items if item.status == "transferable"]
    blocked = [item for item in items if item.status == "blocked"]
    target_grade_name = target_class.grade.name if target_class.grade else None
    required_confirm_text = f"确认调班 {len(transferable)} 名学生"
    response = StudentClassTransferPreviewResponse(
        total=len(payload.student_ids),
        transferable_count=len(transferable),
        blocked_count=len(blocked),
        target_class_id=target_class.id,
        target_class_name=target_class.name,
        target_grade_id=target_class.grade_id,
        target_grade_name=target_grade_name,
        effective_on=payload.effective_on,
        required_confirm_text=required_confirm_text,
        confirm_token="pending",
        items=items,
        warnings=[item for item in transferable if item.warnings],
        blocked=blocked,
    )
    response.confirm_token = _build_class_transfer_confirm_token(payload, response)
    return response


def _get_transfer_target_class(session: Session, target_class_id: int) -> SchoolClass:
    target_class = session.scalar(
        select(SchoolClass)
        .where(SchoolClass.id == target_class_id)
        .options(joinedload(SchoolClass.grade))
    )
    if not target_class:
        raise HTTPException(status_code=404, detail="目标班级不存在")
    if not target_class.is_active:
        raise HTTPException(status_code=400, detail="目标班级已停用")
    return target_class


def _build_class_transfer_preview_item(
    student_id: int,
    student: Student | None,
    target_class: SchoolClass,
    payload: StudentClassTransferPreviewRequest,
) -> StudentClassTransferPreviewItem:
    target_grade_name = target_class.grade.name if target_class.grade else None
    if not student or not student.is_active:
        return StudentClassTransferPreviewItem(
            student_id=student_id,
            student_no=student.student_no if student else None,
            student_name=student.name if student else None,
            to_grade_id=target_class.grade_id,
            to_grade_name=target_grade_name,
            to_class_id=target_class.id,
            to_class_name=target_class.name,
            status="blocked",
            reason="学生不存在或已停用",
            message="学生不存在或已停用，已阻断调班",
        )

    from_grade_name = student.current_grade.name if student.current_grade else None
    from_class_name = student.current_class.name if student.current_class else None
    if student.current_class_id == target_class.id:
        return StudentClassTransferPreviewItem(
            student_id=student.id,
            student_no=student.student_no,
            student_name=student.name,
            from_grade_id=student.current_grade_id,
            from_grade_name=from_grade_name,
            from_class_id=student.current_class_id,
            from_class_name=from_class_name,
            to_grade_id=target_class.grade_id,
            to_grade_name=target_grade_name,
            to_class_id=target_class.id,
            to_class_name=target_class.name,
            status="blocked",
            reason="学生已在目标班级",
            message="该学生已经在目标班级，无需调班",
        )

    if (
        student.current_grade_id
        and target_class.grade_id
        and student.current_grade_id != target_class.grade_id
        and not payload.allow_cross_grade
    ):
        return StudentClassTransferPreviewItem(
            student_id=student.id,
            student_no=student.student_no,
            student_name=student.name,
            from_grade_id=student.current_grade_id,
            from_grade_name=from_grade_name,
            from_class_id=student.current_class_id,
            from_class_name=from_class_name,
            to_grade_id=target_class.grade_id,
            to_grade_name=target_grade_name,
            to_class_id=target_class.id,
            to_class_name=target_class.name,
            status="blocked",
            reason="跨年级调班未确认",
            message="学生当前年级与目标班级年级不同，请确认跨年级调班后再执行",
        )

    warnings: list[str] = []
    if not student.current_class_id:
        warnings.append("学生当前没有班级，将直接转入目标班级")
    elif not student.current_class:
        warnings.append("学生当前班级记录缺失，将按学生档案中的班级 ID 留痕")
    if (
        student.current_grade_id
        and target_class.grade_id
        and student.current_grade_id != target_class.grade_id
        and payload.allow_cross_grade
    ):
        warnings.append("这是跨年级调班，已按请求确认执行")

    return StudentClassTransferPreviewItem(
        student_id=student.id,
        student_no=student.student_no,
        student_name=student.name,
        from_grade_id=student.current_grade_id,
        from_grade_name=from_grade_name,
        from_class_id=student.current_class_id,
        from_class_name=from_class_name,
        to_grade_id=target_class.grade_id,
        to_grade_name=target_grade_name,
        to_class_id=target_class.id,
        to_class_name=target_class.name,
        status="transferable",
        message=(
            f"可从 {_combine_grade_class_name(from_grade_name, from_class_name)} "
            f"调入 {_combine_grade_class_name(target_grade_name, target_class.name)}"
        ),
        warnings=warnings,
    )


def _build_class_transfer_confirm_token(
    payload: StudentClassTransferPreviewRequest,
    preview: StudentClassTransferPreviewResponse,
) -> str:
    token_payload = {
        "version": _CLASS_TRANSFER_TOKEN_VERSION,
        "student_ids": payload.student_ids,
        "target_class_id": payload.target_class_id,
        "effective_on": payload.effective_on.isoformat(),
        "reason": payload.reason,
        "note": payload.note,
        "operator_name": payload.operator_name,
        "allow_cross_grade": payload.allow_cross_grade,
        "required_confirm_text": preview.required_confirm_text,
        "items": [
            {
                "student_id": item.student_id,
                "status": item.status,
                "from_grade_id": item.from_grade_id,
                "from_class_id": item.from_class_id,
                "to_grade_id": item.to_grade_id,
                "to_class_id": item.to_class_id,
            }
            for item in preview.items
        ],
    }
    raw_value = json.dumps(token_payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw_value.encode("utf-8")).hexdigest()


def _snapshot_student_for_class_transfer(student: Student) -> dict:
    return {
        "id": student.id,
        "student_no": student.student_no,
        "name": student.name,
        "status": student.status,
        "current_grade_id": student.current_grade_id,
        "current_grade_name": student.current_grade.name if student.current_grade else None,
        "current_class_id": student.current_class_id,
        "current_class_name": student.current_class.name if student.current_class else None,
        "is_active": student.is_active,
    }


def _record_class_transfer_history(
    session: Session,
    student: Student,
    *,
    target_grade_id: int | None,
    target_class_id: int,
    effective_on: date,
    reason: str,
) -> None:
    current_open_history = next(
        (
            item
            for item in student.class_histories
            if item.is_active and item.end_date is None
        ),
        None,
    )
    if (
        current_open_history
        and current_open_history.grade_id == target_grade_id
        and current_open_history.class_id == target_class_id
    ):
        current_open_history.reason = reason
        current_open_history.start_date = effective_on
        session.flush()
        return
    if current_open_history:
        current_open_history.end_date = effective_on

    existing_target_history = next(
        (
            item
            for item in student.class_histories
            if item.is_active
            and item.grade_id == target_grade_id
            and item.class_id == target_class_id
            and item.start_date == effective_on
        ),
        None,
    )
    if existing_target_history:
        existing_target_history.end_date = None
        existing_target_history.reason = reason
    else:
        student.class_histories.append(
            StudentClassHistory(
                grade_id=target_grade_id,
                class_id=target_class_id,
                start_date=effective_on,
                end_date=None,
                reason=reason,
            )
        )
    session.flush()


def _build_class_transfer_success_message(
    before_snapshot: dict,
    target_grade_name: str | None,
    target_class_name: str,
) -> str:
    from_name = _combine_grade_class_name(
        before_snapshot.get("current_grade_name"),
        before_snapshot.get("current_class_name"),
    )
    to_name = _combine_grade_class_name(target_grade_name, target_class_name)
    return f"已调班：{from_name} -> {to_name}"


def _serialize_class_transfer_history_item(
    item: StudentClassTransferItem,
    batch: StudentClassTransferBatch,
) -> StudentClassTransferHistoryItem:
    from_name = _combine_grade_class_name(item.from_grade_name_snapshot, item.from_class_name_snapshot)
    to_name = _combine_grade_class_name(item.to_grade_name_snapshot, item.to_class_name_snapshot)
    summary = f"{batch.effective_on.isoformat()} 班级调整：{from_name} -> {to_name}，原因：{batch.reason}"
    if batch.note:
        summary = f"{summary}。备注：{batch.note}"
    return StudentClassTransferHistoryItem(
        title="班级调整",
        summary=summary,
        batch_id=batch.id,
        item_id=item.id,
        student_id=item.student_id or item.requested_student_id,
        student_no=item.student_no_snapshot,
        student_name=item.student_name_snapshot,
        from_grade_id=item.from_grade_id,
        from_grade_name=item.from_grade_name_snapshot,
        from_class_id=item.from_class_id,
        from_class_name=item.from_class_name_snapshot,
        to_grade_id=item.to_grade_id,
        to_grade_name=item.to_grade_name_snapshot,
        to_class_id=item.to_class_id,
        to_class_name=item.to_class_name_snapshot,
        effective_on=batch.effective_on,
        reason=batch.reason,
        note=batch.note,
        operator_name=batch.operator_name,
        status=item.status,
        error_message=item.error_message,
        created_at=item.created_at,
    )


def _combine_grade_class_name(grade_name: str | None, class_name: str | None) -> str:
    if grade_name and class_name:
        return f"{grade_name} {class_name}"
    return class_name or grade_name or "未分班"


def get_student_profile(session: Session, student_id: int) -> StudentProfileRead:
    item = get_student(session, student_id)
    if not item:
        raise HTTPException(status_code=404, detail="学生不存在")

    exam_limit = _get_int_config(session, "system", "student_profile_exam_limit", 6)
    class_histories = _serialize_class_histories(session, item.class_histories)
    exam_trends = _load_student_exam_trends(session, student_id, limit=exam_limit)
    performance_summary = _build_performance_summary(session, student_id, exam_trends)
    growth_records, _ = repo_list_growth_records(session, student_id)
    recommendation_history = [
        StudentRecommendationSummary(
            scheme_id=row.scheme_id,
            scheme_name=row.scheme_name,
            exam_id=row.exam_id,
            generated_at=row.generated_at.isoformat(),
            result_count=row.result_count,
            challenge_count=row.challenge_count,
            steady_count=row.steady_count,
            safe_count=row.safe_count,
            watch_count=row.watch_count,
        )
        for row in recommendation_service.list_recommendation_history(session, student_id=student_id)[:8]
    ]
    attachments = _collect_student_attachments(item.attachments, growth_records)
    recent_growth_records = [
        StudentGrowthRecordSummary(
            id=row.id,
            occurred_on=row.occurred_on,
            record_type=row.record_type,
            title=row.title,
            owner_name=row.owner_name,
            attachment_count=sum(1 for attachment in row.attachments if attachment.is_active),
        )
        for row in growth_records[:6]
    ]
    return StudentProfileRead(
        student=_serialize_student(item),
        class_histories=class_histories,
        performance_summary=performance_summary,
        exam_trends=exam_trends,
        recent_growth_records=recent_growth_records,
        recommendation_history=recommendation_history,
        attachments=attachments,
    )


def get_student_career_preference(session: Session, student_id: int) -> StudentCareerPreferenceRead | None:
    _ensure_student_exists(session, student_id)
    item = repo_get_student_career_preference(session, student_id)
    return _serialize_student_career_preference(item) if item and item.is_active else None


def create_student_career_preference(
    session: Session,
    student_id: int,
    payload: StudentCareerPreferencePayload,
) -> StudentCareerPreferenceRead:
    _ensure_student_exists(session, student_id)
    existing = repo_get_student_career_preference(session, student_id)
    if existing and existing.is_active:
        raise HTTPException(status_code=400, detail="该学生已存在职业意向")
    item = existing or StudentCareerPreference(student_id=student_id)
    if not existing:
        session.add(item)
    item.is_active = True
    _apply_student_career_preference_payload(session, item, payload)
    session.flush()
    session.refresh(item)
    write_audit_log(
        session,
        module="students",
        action="create_career_preference",
        target_type="student_career_preference",
        target_id=str(item.id),
        detail_json={"student_id": student_id},
    )
    return _serialize_student_career_preference(item)


def update_student_career_preference(
    session: Session,
    student_id: int,
    payload: StudentCareerPreferencePayload,
) -> StudentCareerPreferenceRead:
    _ensure_student_exists(session, student_id)
    item = repo_get_student_career_preference(session, student_id)
    if not item or not item.is_active:
        raise HTTPException(status_code=404, detail="学生职业意向不存在")
    _apply_student_career_preference_payload(session, item, payload)
    session.flush()
    session.refresh(item)
    write_audit_log(
        session,
        module="students",
        action="update_career_preference",
        target_type="student_career_preference",
        target_id=str(item.id),
        detail_json={"student_id": student_id},
    )
    return _serialize_student_career_preference(item)


def list_student_attachments(session: Session, student_id: int) -> list[StudentAttachmentSummary]:
    item = get_student(session, student_id)
    if not item:
        raise HTTPException(status_code=404, detail="学生不存在")
    return _serialize_direct_attachments(item.attachments)


def create_student_attachment(
    session: Session,
    student_id: int,
    payload: StudentAttachmentPayload,
) -> StudentAttachmentSummary:
    item = get_student(session, student_id)
    if not item:
        raise HTTPException(status_code=404, detail="学生不存在")
    stored_file = get_stored_file(session, payload.stored_file_id)
    if not stored_file or not stored_file.is_active:
        raise HTTPException(status_code=404, detail="附件文件不存在")
    duplicate = next(
        (
            attachment
            for attachment in item.attachments
            if attachment.is_active and attachment.stored_file_id == payload.stored_file_id
        ),
        None,
    )
    if duplicate:
        raise HTTPException(status_code=400, detail="该文件已挂接到当前学生")
    attachment = StudentAttachment(**payload.model_dump())
    attachment.student_id = student_id
    session.add(attachment)
    session.flush()
    write_audit_log(
        session,
        module="students",
        action="create_attachment",
        target_type="student_attachment",
        target_id=str(attachment.id),
        detail_json={"student_id": student_id, "stored_file_id": payload.stored_file_id},
    )
    session.refresh(attachment)
    return _serialize_direct_attachment(attachment)


def delete_student_attachment(session: Session, student_id: int, attachment_id: int) -> dict[str, str]:
    item = get_student(session, student_id)
    if not item:
        raise HTTPException(status_code=404, detail="学生不存在")
    attachment = next(
        (
            current
            for current in item.attachments
            if current.id == attachment_id and current.is_active
        ),
        None,
    )
    if not attachment:
        raise HTTPException(status_code=404, detail="学生附件不存在")
    attachment.is_active = False
    session.flush()
    write_audit_log(
        session,
        module="students",
        action="delete_attachment",
        target_type="student_attachment",
        target_id=str(attachment_id),
        detail_json={"student_id": student_id},
    )
    return {"message": "学生附件已删除"}


def create_student(
    session: Session,
    payload: StudentPayload,
    *,
    scope_class_ids: set[int] | None = None,
    actor: AuthContext | None = None,
) -> StudentRead:
    existing = get_student_by_no(session, payload.student_no)
    if existing:
        raise HTTPException(status_code=400, detail="学号已存在")

    grade_id, class_id = _ensure_grade_class(session, payload.current_grade_id, payload.current_class_id)
    if scope_class_ids is not None and class_id not in scope_class_ids:
        raise HTTPException(status_code=403, detail="无权在该班级创建学生")
    item = Student(student_no=payload.student_no, name=payload.name)
    session.add(item)
    session.flush()
    _apply_student_payload(session, item, payload, grade_id=grade_id, class_id=class_id)
    write_audit_log(
        session,
        module="students",
        action="create",
        target_type="student",
        target_id=str(item.id),
        actor_user_id=actor.user_id if actor else None,
        actor_username=actor.username if actor else None,
        client_ip=actor.client_ip if actor else None,
        detail_json={"student_no": item.student_no},
    )
    return _serialize_student(item)


def update_student(
    session: Session,
    student_id: int,
    payload: StudentPayload,
    *,
    scope_class_ids: set[int] | None = None,
    actor: AuthContext | None = None,
) -> StudentRead:
    item = get_student(session, student_id)
    if not item:
        raise HTTPException(status_code=404, detail="学生不存在")
    existing = get_student_by_no(session, payload.student_no)
    if existing and existing.id != student_id:
        raise HTTPException(status_code=400, detail="学号已存在")

    grade_id, class_id = _ensure_grade_class(session, payload.current_grade_id, payload.current_class_id)
    _ensure_student_scope_access(item, scope_class_ids)
    if scope_class_ids is not None and class_id not in scope_class_ids:
        raise HTTPException(status_code=403, detail="无权把学生调整到该班级")
    _apply_student_payload(session, item, payload, grade_id=grade_id, class_id=class_id)
    write_audit_log(
        session,
        module="students",
        action="update",
        target_type="student",
        target_id=str(item.id),
        actor_user_id=actor.user_id if actor else None,
        actor_username=actor.username if actor else None,
        client_ip=actor.client_ip if actor else None,
        detail_json={"student_no": item.student_no},
    )
    return _serialize_student(item)


def _ensure_student_exists(session: Session, student_id: int) -> Student:
    item = get_student(session, student_id)
    if not item:
        raise HTTPException(status_code=404, detail="学生不存在")
    return item


def _apply_student_career_preference_payload(
    session: Session,
    item: StudentCareerPreference,
    payload: StudentCareerPreferencePayload,
) -> None:
    selected_direction_ids = [
        direction_id
        for direction_id in [
            payload.primary_direction_id,
            payload.secondary_direction_id,
            payload.alternative_direction_id,
        ]
        if direction_id is not None
    ]
    if len(selected_direction_ids) != len(set(selected_direction_ids)):
        raise HTTPException(status_code=400, detail="首选、次选和替代就业方向不能重复")

    for direction_id in selected_direction_ids:
        direction = get_employment_direction(session, direction_id)
        if not direction or not direction.is_active:
            raise HTTPException(status_code=404, detail="就业方向不存在")

    invalid_focuses = sorted(set(payload.priority_focuses_json) - {"stability", "salary", "interest", "long_term"})
    if invalid_focuses:
        raise HTTPException(status_code=400, detail=f"职业意向重点无效：{'、'.join(invalid_focuses)}")

    item.primary_direction_id = payload.primary_direction_id
    item.secondary_direction_id = payload.secondary_direction_id
    item.alternative_direction_id = payload.alternative_direction_id
    item.priority_focuses_json = _dedupe_strings(payload.priority_focuses_json)
    item.preferred_industries_json = _dedupe_strings(payload.preferred_industries_json)
    item.preferred_job_types_json = _dedupe_strings(payload.preferred_job_types_json)
    item.target_employment_cities_json = _dedupe_strings(payload.target_employment_cities_json)
    item.accepts_postgraduate = payload.accepts_postgraduate
    item.accepts_public_service = payload.accepts_public_service
    item.accepts_certificate = payload.accepts_certificate
    item.accepts_long_training = payload.accepts_long_training


def _apply_student_payload(
    session: Session,
    item: Student,
    payload: StudentPayload,
    *,
    grade_id: int | None,
    class_id: int | None,
) -> None:
    old_class_id = item.current_class_id
    item.student_no = payload.student_no
    item.name = payload.name
    item.gender = payload.gender
    item.birth_date = payload.birth_date
    item.id_number = payload.id_number
    item.admission_year = payload.admission_year
    item.current_grade_id = grade_id
    item.current_class_id = class_id
    item.status = payload.status
    item.student_type = payload.student_type
    item.art_track = payload.art_track
    item.origin_province = payload.origin_province
    item.phone = payload.phone
    item.address = payload.address
    item.note = payload.note
    item.is_active = payload.is_active
    _sync_guardians(item, payload.guardians)
    session.flush()
    _update_class_history(session, item, grade_id, class_id)
    _refresh_class_student_count(session, old_class_id)
    _refresh_class_student_count(session, class_id)
    session.refresh(item)


def import_students(
    session: Session,
    settings: Settings,
    *,
    filename: str | None,
    content: bytes,
    strategy: str,
) -> dict:
    job = create_import_job(session, "students", filename)
    job.started_at = datetime.now()
    importer = StudentImporter(session, settings)
    try:
        result = importer.execute(filename=filename, content=content, strategy=strategy)
    except (ValueError, InvalidFileException, BadZipFile) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    job.finished_at = datetime.now()
    job.status = result.status
    job.result_json = result.model_dump()
    write_audit_log(
        session,
        module="students",
        action="import",
        target_type="import_job",
        target_id=str(job.id),
        detail_json=result.model_dump(),
    )
    return {"job_id": job.id, **result.model_dump()}


def export_students(session: Session, settings: Settings) -> dict[str, str]:
    rows = [
        _serialize_student(item).model_dump(mode="json")
        for item in repo_list_students(session, page=1, page_size=10000)[0]
    ]
    file_path = export_students_workbook(settings, rows)
    return {"file_path": file_path}


def _serialize_class_histories(
    session: Session,
    histories: list[StudentClassHistory],
) -> list[StudentClassHistoryRead]:
    if not histories:
        return []
    grade_ids = {item.grade_id for item in histories if item.grade_id}
    class_ids = {item.class_id for item in histories if item.class_id}
    grade_map = {
        item.id: item.name
        for item in session.scalars(select(Grade).where(Grade.id.in_(grade_ids))).all()
    } if grade_ids else {}
    class_map = {
        item.id: item.name
        for item in session.scalars(select(SchoolClass).where(SchoolClass.id.in_(class_ids))).all()
    } if class_ids else {}
    return [
        StudentClassHistoryRead(
            id=item.id,
            grade_id=item.grade_id,
            grade_name=grade_map.get(item.grade_id),
            class_id=item.class_id,
            class_name=class_map.get(item.class_id),
            start_date=item.start_date,
            end_date=item.end_date,
            reason=item.reason,
        )
        for item in sorted(
            histories,
            key=lambda current: (current.start_date or date.min, current.id),
            reverse=True,
        )
    ]


def _score_value_label(score_value_type: str | None) -> str:
    return "赋分" if score_value_type == "converted" else "原始分"


def _load_student_exam_trends(session: Session, student_id: int, *, limit: int) -> list[StudentExamTrendItem]:
    rows = session.execute(
        select(ScoreTotalSnapshot, Exam)
        .join(Exam, Exam.id == ScoreTotalSnapshot.exam_id)
        .where(ScoreTotalSnapshot.student_id == student_id)
        .order_by(Exam.exam_date.desc(), Exam.id.desc())
        .limit(limit)
    ).all()
    exam_ids = [exam.id for _, exam in rows]
    subject_rows = session.execute(
        select(ScoreSubjectSnapshot, Subject)
        .join(Subject, Subject.id == ScoreSubjectSnapshot.subject_id)
        .where(
            ScoreSubjectSnapshot.student_id == student_id,
            ScoreSubjectSnapshot.exam_id.in_(exam_ids),
        )
        .order_by(ScoreSubjectSnapshot.exam_id, ScoreSubjectSnapshot.subject_id)
    ).all() if exam_ids else []
    subjects_by_exam: dict[int, list[StudentExamSubjectItem]] = defaultdict(list)
    for snapshot, subject in subject_rows:
        subjects_by_exam[snapshot.exam_id].append(
            StudentExamSubjectItem(
                subject_id=snapshot.subject_id,
                subject_name=subject.name if subject else str(snapshot.subject_id),
                score=snapshot.score,
                score_value_type=snapshot.score_value_type,
                score_value_label=_score_value_label(snapshot.score_value_type),
                class_rank=snapshot.class_rank,
                grade_rank=snapshot.grade_rank,
            )
        )
    return [
        StudentExamTrendItem(
            exam_id=exam.id,
            exam_name=exam.name,
            exam_date=exam.exam_date,
            total_score=snapshot.total_score,
            score_value_type=snapshot.score_value_type,
            score_value_label=_score_value_label(snapshot.score_value_type),
            class_rank=snapshot.class_rank,
            grade_rank=snapshot.grade_rank,
            class_percentile=snapshot.class_percentile,
            grade_percentile=snapshot.grade_percentile,
            subjects=subjects_by_exam.get(exam.id, []),
        )
        for snapshot, exam in rows
    ]


def _build_performance_summary(
    session: Session,
    student_id: int,
    exam_trends: list[StudentExamTrendItem],
) -> StudentPerformanceSummary:
    latest = exam_trends[0] if exam_trends else None
    strength_subjects, weakness_subjects = _identify_subject_strengths(
        session,
        student_id,
        latest.exam_id if latest else None,
    )
    exam_count = session.scalar(
        select(func.count()).select_from(ScoreTotalSnapshot).where(ScoreTotalSnapshot.student_id == student_id)
    ) or 0
    return StudentPerformanceSummary(
        latest_exam_id=latest.exam_id if latest else None,
        latest_exam_name=latest.exam_name if latest else None,
        latest_exam_date=latest.exam_date if latest else None,
        latest_total_score=latest.total_score if latest else None,
        latest_score_value_type=latest.score_value_type if latest else None,
        latest_score_value_label=latest.score_value_label if latest else None,
        latest_class_rank=latest.class_rank if latest else None,
        latest_grade_rank=latest.grade_rank if latest else None,
        exam_count=exam_count,
        strength_subjects=strength_subjects,
        weakness_subjects=weakness_subjects,
    )


def _identify_subject_strengths(
    session: Session,
    student_id: int,
    exam_id: int | None,
) -> tuple[list[str], list[str]]:
    if not exam_id:
        return [], []
    gap = _get_float_config(session, "analytics", "subject_advantage_gap", 0.10)
    rows = session.execute(
        select(Subject.name, ScoreSubjectSnapshot.score, ExamSubject.full_score)
        .join(Subject, Subject.id == ScoreSubjectSnapshot.subject_id)
        .join(
            ExamSubject,
            and_(
                ExamSubject.exam_id == ScoreSubjectSnapshot.exam_id,
                ExamSubject.subject_id == ScoreSubjectSnapshot.subject_id,
            ),
        )
        .where(
            ScoreSubjectSnapshot.student_id == student_id,
            ScoreSubjectSnapshot.exam_id == exam_id,
            ScoreSubjectSnapshot.score.is_not(None),
        )
        .order_by(ScoreSubjectSnapshot.subject_id)
    ).all()
    subject_ratios: list[tuple[str, float]] = []
    for subject_name, score, full_score in rows:
        if full_score and full_score > 0 and score is not None:
            subject_ratios.append((subject_name, round(score / full_score, 4)))
    if not subject_ratios:
        return [], []
    average_ratio = sum(value for _, value in subject_ratios) / len(subject_ratios)
    strengths = sorted(
        ((name, ratio - average_ratio) for name, ratio in subject_ratios if ratio - average_ratio >= gap),
        key=lambda item: item[1],
        reverse=True,
    )
    weaknesses = sorted(
        ((name, average_ratio - ratio) for name, ratio in subject_ratios if average_ratio - ratio >= gap),
        key=lambda item: item[1],
        reverse=True,
    )
    if not strengths and len(subject_ratios) >= 2:
        strengths = sorted(((name, ratio) for name, ratio in subject_ratios), key=lambda item: item[1], reverse=True)[:2]
    if not weaknesses and len(subject_ratios) >= 2:
        weaknesses = sorted(((name, ratio) for name, ratio in subject_ratios), key=lambda item: item[1])[:2]
    return [name for name, _ in strengths[:3]], [name for name, _ in weaknesses[:3]]


def _serialize_direct_attachment(item: StudentAttachment) -> StudentAttachmentSummary:
    return StudentAttachmentSummary(
        id=item.id,
        stored_file_id=item.stored_file_id,
        file_id=item.stored_file_id,
        original_filename=item.stored_file.original_filename if item.stored_file else "",
        category=item.stored_file.category if item.stored_file else "student_attachment",
        attachment_type=item.attachment_type,
        title=item.title,
        note=item.note,
        source_title=item.title,
        source_type="student_attachment",
        created_at=(item.stored_file.created_at.isoformat() if item.stored_file else item.created_at.isoformat()),
        download_url=f"/api/files/{item.stored_file_id}",
    )


def _serialize_direct_attachments(attachments: list[StudentAttachment]) -> list[StudentAttachmentSummary]:
    return [
        _serialize_direct_attachment(item)
        for item in sorted(attachments, key=lambda current: (current.created_at, current.id), reverse=True)
        if item.is_active and item.stored_file and item.stored_file.is_active
    ]


def _collect_student_attachments(direct_attachments, growth_records) -> list[StudentAttachmentSummary]:
    seen_file_ids: set[int] = set()
    attachments = []
    for item in _serialize_direct_attachments(direct_attachments):
        seen_file_ids.add(item.file_id)
        attachments.append(item)
    for record in growth_records:
        for item in record.attachments:
            if not item.is_active or not item.stored_file or item.stored_file_id in seen_file_ids:
                continue
            seen_file_ids.add(item.stored_file_id)
            attachments.append(
                StudentAttachmentSummary(
                    id=None,
                    stored_file_id=item.stored_file_id,
                    file_id=item.stored_file_id,
                    original_filename=item.stored_file.original_filename,
                    category=item.stored_file.category,
                    attachment_type=None,
                    title=record.title,
                    note=item.note,
                    source_title=record.title,
                    source_type=f"growth:{record.record_type}",
                    created_at=item.stored_file.created_at.isoformat(),
                    download_url=f"/api/files/{item.stored_file_id}",
                )
            )
    return attachments


def _dedupe_strings(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        normalized = value.strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        result.append(normalized)
    return result


def _get_config_value(
    session: Session,
    config_group: str,
    config_key: str,
) -> str | None:
    row = session.scalar(
        select(ConfigItem).where(
            ConfigItem.config_group == config_group,
            ConfigItem.config_key == config_key,
            ConfigItem.is_active.is_(True),
        )
    )
    return row.config_value if row else None


def _get_int_config(session: Session, config_group: str, config_key: str, default: int) -> int:
    raw_value = _get_config_value(session, config_group, config_key)
    try:
        return int(str(raw_value)) if raw_value is not None else default
    except (TypeError, ValueError):
        return default


def _get_float_config(session: Session, config_group: str, config_key: str, default: float) -> float:
    raw_value = _get_config_value(session, config_group, config_key)
    try:
        return float(str(raw_value)) if raw_value is not None else default
    except (TypeError, ValueError):
        return default
