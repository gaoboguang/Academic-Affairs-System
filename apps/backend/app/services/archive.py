from __future__ import annotations

from datetime import date

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.exporters.archive import export_growth_summary
from app.models import Student, StudentGrowthAttachment, StudentGrowthRecord
from app.repositories.archive import get_growth_record, list_growth_records as repo_list_growth_records
from app.repositories.system import get_stored_file, write_audit_log
from app.schemas.archive import (
    StoredFileRead,
    StudentGrowthAttachmentRead,
    StudentGrowthRecordPayload,
    StudentGrowthRecordRead,
    StudentGrowthTimelineResponse,
)


def _serialize_file(item) -> StoredFileRead:
    return StoredFileRead(
        id=item.id,
        original_filename=item.original_filename,
        file_path=item.file_path,
        content_type=item.content_type,
        file_size=item.file_size,
        category=item.category,
        created_at=item.created_at,
        download_url=f"/api/files/{item.id}",
    )


def _serialize_attachment(item: StudentGrowthAttachment) -> StudentGrowthAttachmentRead:
    return StudentGrowthAttachmentRead(
        id=item.id,
        stored_file_id=item.stored_file_id,
        note=item.note,
        file=_serialize_file(item.stored_file),
    )


def _serialize_record(item: StudentGrowthRecord) -> StudentGrowthRecordRead:
    return StudentGrowthRecordRead(
        id=item.id,
        student_id=item.student_id,
        student_name=item.student.name if item.student else None,
        occurred_on=item.occurred_on,
        record_type=item.record_type,
        title=item.title,
        content=item.content,
        owner_name=item.owner_name,
        note=item.note,
        is_active=item.is_active,
        attachments=[_serialize_attachment(attachment) for attachment in item.attachments if attachment.is_active],
    )


def list_growth_records(
    session: Session,
    student_id: int,
    *,
    record_type: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
) -> StudentGrowthTimelineResponse:
    student = session.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="学生不存在")
    items, total = repo_list_growth_records(
        session,
        student_id,
        record_type=record_type,
        start_date=start_date,
        end_date=end_date,
    )
    return StudentGrowthTimelineResponse(
        items=[_serialize_record(item) for item in items],
        total=total,
    )


def create_growth_record(
    session: Session,
    student_id: int,
    payload: StudentGrowthRecordPayload,
) -> StudentGrowthRecordRead:
    student = session.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="学生不存在")
    record = StudentGrowthRecord(student_id=student_id)
    session.add(record)
    _apply_growth_payload(session, record, payload)
    write_audit_log(
        session,
        module="growth_archive",
        action="create_record",
        target_type="student_growth_record",
        target_id=str(record.id),
        detail_json={"student_id": student_id, "record_type": record.record_type},
    )
    session.refresh(record)
    return _serialize_record(record)


def update_growth_record(
    session: Session,
    record_id: int,
    payload: StudentGrowthRecordPayload,
) -> StudentGrowthRecordRead:
    record = get_growth_record(session, record_id)
    if not record or not record.is_active:
        raise HTTPException(status_code=404, detail="成长记录不存在")
    _apply_growth_payload(session, record, payload)
    write_audit_log(
        session,
        module="growth_archive",
        action="update_record",
        target_type="student_growth_record",
        target_id=str(record.id),
        detail_json={"record_type": record.record_type},
    )
    session.refresh(record)
    return _serialize_record(record)


def delete_growth_record(session: Session, record_id: int) -> dict[str, str]:
    record = get_growth_record(session, record_id)
    if not record or not record.is_active:
        raise HTTPException(status_code=404, detail="成长记录不存在")
    record.is_active = False
    for item in record.attachments:
        item.is_active = False
    session.flush()
    write_audit_log(
        session,
        module="growth_archive",
        action="delete_record",
        target_type="student_growth_record",
        target_id=str(record.id),
    )
    return {"message": "成长记录已删除"}


def export_student_growth_summary(session: Session, settings, student_id: int) -> dict[str, str]:
    student = session.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="学生不存在")
    items, total = repo_list_growth_records(session, student_id)
    if total == 0:
        raise HTTPException(status_code=404, detail="该学生暂无成长记录")
    file_path = export_growth_summary(
        settings,
        {
            "student_no": student.student_no,
            "student_name": student.name,
            "grade_name": student.current_grade.name if student.current_grade else None,
            "class_name": student.current_class.name if student.current_class else None,
        },
        [
            {
                "occurred_on": item.occurred_on.isoformat(),
                "record_type": item.record_type,
                "title": item.title,
                "content": item.content,
                "owner_name": item.owner_name,
                "note": item.note,
                "attachments": [_serialize_attachment(attachment).model_dump() for attachment in item.attachments if attachment.is_active],
            }
            for item in items
        ],
    )
    write_audit_log(
        session,
        module="growth_archive",
        action="export_summary",
        target_type="student",
        target_id=str(student_id),
        detail_json={"file_path": file_path},
    )
    return {"file_path": file_path}


def _apply_growth_payload(session: Session, record: StudentGrowthRecord, payload: StudentGrowthRecordPayload) -> None:
    record.occurred_on = payload.occurred_on
    record.record_type = payload.record_type.strip()
    record.title = payload.title.strip()
    record.content = payload.content
    record.owner_name = payload.owner_name
    record.note = payload.note
    record.is_active = payload.is_active
    record.attachments.clear()
    session.flush()
    for file_id in payload.attachment_file_ids:
        stored_file = get_stored_file(session, file_id)
        if not stored_file or not stored_file.is_active:
            raise HTTPException(status_code=404, detail=f"附件不存在: {file_id}")
        record.attachments.append(StudentGrowthAttachment(stored_file_id=file_id))
    session.flush()
