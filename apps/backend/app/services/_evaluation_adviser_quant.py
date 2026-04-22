from __future__ import annotations

from collections import defaultdict

from fastapi import HTTPException
from sqlalchemy import desc, select
from sqlalchemy.orm import Session, joinedload

from app.models import (
    AdviserQuantRecord,
    AdviserQuantRecordAttachment,
    AdviserQuantRuleItem,
    AdviserQuantRuleVersion,
    ClassAdviserAssignment,
    SchoolClass,
    Semester,
    Teacher,
)
from app.repositories.system import get_stored_file, write_audit_log
from app.schemas.evaluation import (
    AdviserQuantRecordPayload,
    AdviserQuantRecordRead,
    AdviserQuantRuleItemPayload,
    AdviserQuantRuleItemRead,
    AdviserQuantRuleVersionPayload,
    AdviserQuantRuleVersionRead,
    AdviserQuantSummaryRead,
)

from ._evaluation_shared import (
    _semester_name,
    _serialize_quant_record,
    _serialize_rule_item,
    _serialize_rule_version,
    ensure_default_adviser_rule_version,
)


def list_adviser_rule_versions(session: Session) -> list[AdviserQuantRuleVersionRead]:
    ensure_default_adviser_rule_version(session)
    items = session.scalars(
        select(AdviserQuantRuleVersion)
        .options(joinedload(AdviserQuantRuleVersion.semester).joinedload(Semester.academic_year))
        .where(AdviserQuantRuleVersion.is_active.is_(True))
        .order_by(desc(AdviserQuantRuleVersion.id))
    ).unique().all()
    return [_serialize_rule_version(item) for item in items]


def create_adviser_rule_version(session: Session, payload: AdviserQuantRuleVersionPayload) -> AdviserQuantRuleVersionRead:
    if payload.semester_id and not session.get(Semester, payload.semester_id):
        raise HTTPException(status_code=404, detail="学期不存在")
    if payload.is_default:
        for item in session.scalars(select(AdviserQuantRuleVersion).where(AdviserQuantRuleVersion.is_default.is_(True))).all():
            item.is_default = False
    version = AdviserQuantRuleVersion(**payload.model_dump())
    session.add(version)
    session.flush()
    write_audit_log(
        session,
        module="adviser_quant",
        action="create_rule_version",
        target_type="rule_version",
        target_id=str(version.id),
    )
    session.refresh(version)
    return _serialize_rule_version(version)


def update_adviser_rule_version(
    session: Session,
    rule_version_id: int,
    payload: AdviserQuantRuleVersionPayload,
) -> AdviserQuantRuleVersionRead:
    version = session.scalar(
        select(AdviserQuantRuleVersion)
        .options(joinedload(AdviserQuantRuleVersion.semester).joinedload(Semester.academic_year))
        .where(AdviserQuantRuleVersion.id == rule_version_id)
    )
    if not version:
        raise HTTPException(status_code=404, detail="量化规则版本不存在")
    if payload.semester_id and not session.get(Semester, payload.semester_id):
        raise HTTPException(status_code=404, detail="学期不存在")
    if payload.is_default:
        for item in session.scalars(select(AdviserQuantRuleVersion).where(AdviserQuantRuleVersion.is_default.is_(True))).all():
            item.is_default = False
    for key, value in payload.model_dump().items():
        setattr(version, key, value)
    session.flush()
    write_audit_log(
        session,
        module="adviser_quant",
        action="update_rule_version",
        target_type="rule_version",
        target_id=str(version.id),
    )
    session.refresh(version)
    return _serialize_rule_version(version)


def list_adviser_rule_items(session: Session, rule_version_id: int) -> list[AdviserQuantRuleItemRead]:
    version = session.scalar(
        select(AdviserQuantRuleVersion)
        .options(joinedload(AdviserQuantRuleVersion.items))
        .where(AdviserQuantRuleVersion.id == rule_version_id)
    )
    if not version:
        raise HTTPException(status_code=404, detail="量化规则版本不存在")
    items = sorted((item for item in version.items if item.is_active), key=lambda item: (item.sort_order, item.id))
    return [_serialize_rule_item(item) for item in items]


def save_adviser_rule_items(
    session: Session,
    rule_version_id: int,
    payload: list[AdviserQuantRuleItemPayload],
) -> list[AdviserQuantRuleItemRead]:
    version = session.scalar(
        select(AdviserQuantRuleVersion)
        .options(joinedload(AdviserQuantRuleVersion.items))
        .where(AdviserQuantRuleVersion.id == rule_version_id)
    )
    if not version:
        raise HTTPException(status_code=404, detail="量化规则版本不存在")
    record_count = session.scalar(
        select(AdviserQuantRecord.id)
        .join(AdviserQuantRuleItem, AdviserQuantRecord.rule_item_id == AdviserQuantRuleItem.id)
        .where(AdviserQuantRuleItem.rule_version_id == rule_version_id)
        .limit(1)
    )
    if record_count:
        raise HTTPException(status_code=400, detail="该规则版本已有量化记录，不能原地修改规则项")

    version.items.clear()
    session.flush()
    for item in sorted(payload, key=lambda current: (current.sort_order, current.item_name)):
        version.items.append(
            AdviserQuantRuleItem(
                item_name=item.item_name.strip(),
                item_type=item.item_type.strip(),
                default_score=item.default_score,
                requires_attachment=item.requires_attachment,
                note=item.note,
                sort_order=item.sort_order,
                is_active=item.is_active,
            )
        )
    session.flush()
    write_audit_log(
        session,
        module="adviser_quant",
        action="save_rule_items",
        target_type="rule_version",
        target_id=str(rule_version_id),
        detail_json={"item_count": len(payload)},
    )
    session.refresh(version)
    return [_serialize_rule_item(item) for item in sorted(version.items, key=lambda current: (current.sort_order, current.id))]


def list_adviser_records(
    session: Session,
    *,
    semester_id: int | None = None,
    teacher_id: int | None = None,
) -> list[AdviserQuantRecordRead]:
    query = (
        select(AdviserQuantRecord)
        .options(
            joinedload(AdviserQuantRecord.teacher),
            joinedload(AdviserQuantRecord.school_class),
            joinedload(AdviserQuantRecord.semester).joinedload(Semester.academic_year),
            joinedload(AdviserQuantRecord.rule_item)
            .joinedload(AdviserQuantRuleItem.rule_version)
            .joinedload(AdviserQuantRuleVersion.semester),
            joinedload(AdviserQuantRecord.attachments).joinedload(AdviserQuantRecordAttachment.stored_file),
        )
        .where(AdviserQuantRecord.is_active.is_(True))
        .order_by(desc(AdviserQuantRecord.record_month), desc(AdviserQuantRecord.recorded_at), desc(AdviserQuantRecord.id))
    )
    if semester_id:
        query = query.where(AdviserQuantRecord.semester_id == semester_id)
    if teacher_id:
        query = query.where(AdviserQuantRecord.teacher_id == teacher_id)
    items = session.scalars(query).unique().all()
    return [_serialize_quant_record(item) for item in items]


def create_adviser_record(session: Session, payload: AdviserQuantRecordPayload) -> AdviserQuantRecordRead:
    record = AdviserQuantRecord()
    session.add(record)
    _apply_adviser_record_payload(session, record, payload)
    session.flush()
    write_audit_log(
        session,
        module="adviser_quant",
        action="create_record",
        target_type="adviser_quant_record",
        target_id=str(record.id),
    )
    session.refresh(record)
    return _serialize_quant_record(record)


def update_adviser_record(session: Session, record_id: int, payload: AdviserQuantRecordPayload) -> AdviserQuantRecordRead:
    record = session.scalar(
        select(AdviserQuantRecord)
        .options(joinedload(AdviserQuantRecord.attachments))
        .where(AdviserQuantRecord.id == record_id)
    )
    if not record:
        raise HTTPException(status_code=404, detail="量化记录不存在")
    _apply_adviser_record_payload(session, record, payload)
    session.flush()
    write_audit_log(
        session,
        module="adviser_quant",
        action="update_record",
        target_type="adviser_quant_record",
        target_id=str(record.id),
    )
    session.refresh(record)
    return _serialize_quant_record(record)


def list_adviser_summary(
    session: Session,
    *,
    semester_id: int,
    rule_version_id: int | None = None,
    teacher_id: int | None = None,
) -> list[AdviserQuantSummaryRead]:
    semester = session.scalar(
        select(Semester)
        .options(joinedload(Semester.academic_year))
        .where(Semester.id == semester_id)
    )
    if not semester:
        raise HTTPException(status_code=404, detail="学期不存在")
    records = session.scalars(
        select(AdviserQuantRecord)
        .options(
            joinedload(AdviserQuantRecord.teacher),
            joinedload(AdviserQuantRecord.school_class),
            joinedload(AdviserQuantRecord.rule_item)
            .joinedload(AdviserQuantRuleItem.rule_version)
            .joinedload(AdviserQuantRuleVersion.semester),
        )
        .where(
            AdviserQuantRecord.semester_id == semester_id,
            AdviserQuantRecord.is_active.is_(True),
        )
        .order_by(AdviserQuantRecord.teacher_id, AdviserQuantRecord.id)
    ).unique().all()

    filtered: list[AdviserQuantRecord] = []
    for record in records:
        if teacher_id and record.teacher_id != teacher_id:
            continue
        if rule_version_id and record.rule_item and record.rule_item.rule_version_id != rule_version_id:
            continue
        filtered.append(record)

    grouped: dict[int, list[AdviserQuantRecord]] = defaultdict(list)
    for item in filtered:
        grouped[item.teacher_id].append(item)

    rows: list[AdviserQuantSummaryRead] = []
    for items in grouped.values():
        first = items[0]
        category_scores: dict[str, float] = defaultdict(float)
        class_names = sorted({item.school_class.name for item in items if item.school_class})
        positive_score = 0.0
        negative_score = 0.0
        for item in items:
            snapshot = item.snapshot_json or {}
            item_type = item.rule_item.item_type if item.rule_item else snapshot.get("item_type", "unknown")
            category_scores[item_type] += item.score
            if item.score >= 0:
                positive_score += item.score
            else:
                negative_score += item.score
        version = first.rule_item.rule_version if first.rule_item else None
        rows.append(
            AdviserQuantSummaryRead(
                teacher_id=first.teacher_id,
                teacher_name=first.teacher.name if first.teacher else str(first.teacher_id),
                semester_id=semester.id,
                semester_name=_semester_name(semester),
                rule_version_id=version.id if version else None,
                rule_version_name=version.name if version else None,
                total_score=round(sum(item.score for item in items), 2),
                positive_score=round(positive_score, 2),
                negative_score=round(negative_score, 2),
                record_count=len(items),
                class_names=class_names,
                category_scores_json={key: round(value, 2) for key, value in category_scores.items()},
            )
        )
    rows.sort(key=lambda item: item.total_score, reverse=True)
    return rows


def _apply_adviser_record_payload(session: Session, record: AdviserQuantRecord, payload: AdviserQuantRecordPayload) -> None:
    teacher = session.get(Teacher, payload.teacher_id)
    semester = session.get(Semester, payload.semester_id)
    rule_item = session.scalar(
        select(AdviserQuantRuleItem)
        .options(
            joinedload(AdviserQuantRuleItem.rule_version)
            .joinedload(AdviserQuantRuleVersion.semester)
            .joinedload(Semester.academic_year)
        )
        .where(AdviserQuantRuleItem.id == payload.rule_item_id)
    )
    school_class = session.get(SchoolClass, payload.class_id) if payload.class_id else None
    if not teacher:
        raise HTTPException(status_code=404, detail="教师不存在")
    if not semester:
        raise HTTPException(status_code=404, detail="学期不存在")
    if not rule_item:
        raise HTTPException(status_code=404, detail="量化规则项不存在")
    if payload.class_id and not school_class:
        raise HTTPException(status_code=404, detail="班级不存在")
    if len(payload.record_month) != 7 or payload.record_month[4] != "-":
        raise HTTPException(status_code=400, detail="记录月份格式应为 YYYY-MM")
    if rule_item.requires_attachment and not payload.attachment_file_ids:
        raise HTTPException(status_code=400, detail="该量化项必须上传附件")

    if school_class:
        assignment = session.scalar(
            select(ClassAdviserAssignment).where(
                ClassAdviserAssignment.teacher_id == teacher.id,
                ClassAdviserAssignment.class_id == school_class.id,
                ClassAdviserAssignment.is_active.is_(True),
            )
        )
        if assignment is None and school_class.head_teacher_id not in (None, teacher.id):
            raise HTTPException(status_code=400, detail="当前教师不是该班的班主任或班主任记录未维护")

    record.teacher_id = teacher.id
    record.class_id = school_class.id if school_class else None
    record.semester_id = semester.id
    record.rule_item_id = rule_item.id
    record.record_month = payload.record_month
    record.score = payload.score if payload.score is not None else rule_item.default_score
    record.description = payload.description
    record.snapshot_json = {
        "item_name": rule_item.item_name,
        "item_type": rule_item.item_type,
        "default_score": rule_item.default_score,
        "requires_attachment": rule_item.requires_attachment,
        "rule_version_id": rule_item.rule_version_id,
    }
    record.is_active = payload.is_active
    record.attachments.clear()
    session.flush()
    for file_id in payload.attachment_file_ids:
        stored_file = get_stored_file(session, file_id)
        if not stored_file or not stored_file.is_active:
            raise HTTPException(status_code=404, detail=f"附件不存在: {file_id}")
        record.attachments.append(AdviserQuantRecordAttachment(stored_file_id=file_id))
    session.flush()
