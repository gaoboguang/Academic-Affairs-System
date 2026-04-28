from __future__ import annotations

from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.importers.admissions import AdmissionImporter
from app.models import College, CollegeAlias, Major
from app.repositories.recommendations import (
    get_college,
    get_college_by_name,
    get_major,
    get_major_by_name,
    list_admission_records as repo_list_admission_records,
    list_admission_records_page as repo_list_admission_records_page,
    list_colleges as repo_list_colleges,
    list_majors as repo_list_majors,
    list_majors_page as repo_list_majors_page,
)
from app.repositories.system import create_import_job, write_audit_log
from app.schemas.recommendation import (
    AdmissionImportResponse,
    AdmissionRecordPageRead,
    AdmissionRecordRead,
    CollegePayload,
    CollegeRead,
    MajorPageRead,
    MajorPayload,
    MajorRead,
)

from ._recommendations_shared import _serialize_admission_record, _serialize_college, _serialize_major


def list_colleges(
    session: Session,
    *,
    keyword: str | None = None,
    province: str | None = None,
    supports_art: bool | None = None,
) -> list[CollegeRead]:
    return [
        _serialize_college(item)
        for item in repo_list_colleges(session, keyword=keyword, province=province, supports_art=supports_art)
    ]


def create_college(session: Session, payload: CollegePayload) -> CollegeRead:
    existing = get_college_by_name(session, payload.name)
    if existing:
        raise HTTPException(status_code=400, detail="院校名称已存在")
    item = College(name=payload.name.strip())
    session.add(item)
    session.flush()
    _apply_college_payload(item, payload)
    write_audit_log(session, module="recommendations", action="create_college", target_type="college", target_id=str(item.id))
    session.refresh(item)
    return _serialize_college(item)


def update_college(session: Session, college_id: int, payload: CollegePayload) -> CollegeRead:
    item = get_college(session, college_id)
    if not item:
        raise HTTPException(status_code=404, detail="院校不存在")
    existing = get_college_by_name(session, payload.name)
    if existing and existing.id != college_id:
        raise HTTPException(status_code=400, detail="院校名称已存在")
    _apply_college_payload(item, payload)
    write_audit_log(session, module="recommendations", action="update_college", target_type="college", target_id=str(item.id))
    session.refresh(item)
    return _serialize_college(item)


def _apply_college_payload(item: College, payload: CollegePayload) -> None:
    item.name = payload.name.strip()
    item.college_code = payload.college_code
    item.province = payload.province
    item.city = payload.city
    item.school_type = payload.school_type
    item.school_level_tags_json = payload.school_level_tags_json or None
    item.intro = payload.intro
    item.website = payload.website
    item.supports_art = payload.supports_art
    item.note = payload.note
    item.is_active = payload.is_active
    item.aliases.clear()
    for alias_name in payload.alias_names:
        cleaned = alias_name.strip()
        if cleaned:
            item.aliases.append(CollegeAlias(alias_name=cleaned))


def list_majors(session: Session, *, keyword: str | None = None, is_art_related: bool | None = None) -> list[MajorRead]:
    return [_serialize_major(item) for item in repo_list_majors(session, keyword=keyword, is_art_related=is_art_related)]


def list_majors_page(
    session: Session,
    *,
    keyword: str | None = None,
    is_art_related: bool | None = None,
    page: int = 1,
    page_size: int = 50,
) -> MajorPageRead:
    items, total = repo_list_majors_page(
        session,
        keyword=keyword,
        is_art_related=is_art_related,
        page=page,
        page_size=page_size,
    )
    return MajorPageRead(
        items=[_serialize_major(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


def create_major(session: Session, payload: MajorPayload) -> MajorRead:
    existing = get_major_by_name(session, payload.name)
    if existing:
        raise HTTPException(status_code=400, detail="专业名称已存在")
    item = Major(**payload.model_dump())
    session.add(item)
    session.flush()
    write_audit_log(session, module="recommendations", action="create_major", target_type="major", target_id=str(item.id))
    session.refresh(item)
    return _serialize_major(item)


def update_major(session: Session, major_id: int, payload: MajorPayload) -> MajorRead:
    item = get_major(session, major_id)
    if not item:
        raise HTTPException(status_code=404, detail="专业不存在")
    existing = get_major_by_name(session, payload.name)
    if existing and existing.id != major_id:
        raise HTTPException(status_code=400, detail="专业名称已存在")
    for key, value in payload.model_dump().items():
        setattr(item, key, value)
    session.flush()
    write_audit_log(session, module="recommendations", action="update_major", target_type="major", target_id=str(item.id))
    session.refresh(item)
    return _serialize_major(item)


def list_admission_records(
    session: Session,
    *,
    year: int | None = None,
    province: str | None = None,
    college_id: int | None = None,
    student_type: str | None = None,
) -> list[AdmissionRecordRead]:
    return [
        _serialize_admission_record(item)
        for item in repo_list_admission_records(
            session,
            year=year,
            province=province,
            college_id=college_id,
            student_type=student_type,
        )
    ]


def list_admission_records_page(
    session: Session,
    *,
    year: int | None = None,
    province: str | None = None,
    college_id: int | None = None,
    student_type: str | None = None,
    page: int = 1,
    page_size: int = 50,
) -> AdmissionRecordPageRead:
    items, total = repo_list_admission_records_page(
        session,
        year=year,
        province=province,
        college_id=college_id,
        student_type=student_type,
        page=page,
        page_size=page_size,
    )
    return AdmissionRecordPageRead(
        items=[_serialize_admission_record(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


def import_admissions(
    session: Session,
    settings: Settings,
    *,
    filename: str | None,
    content: bytes,
) -> AdmissionImportResponse:
    job = create_import_job(session, "admissions", filename)
    job.started_at = datetime.now()
    importer = AdmissionImporter(session, settings)
    result, created_colleges, created_majors = importer.execute(filename=filename, content=content)
    job.finished_at = datetime.now()
    job.status = result.status
    job.result_json = {
        **result.model_dump(),
        "created_college_count": created_colleges,
        "created_major_count": created_majors,
    }
    write_audit_log(
        session,
        module="recommendations",
        action="import_admissions",
        target_type="import_job",
        target_id=str(job.id),
        detail_json=job.result_json,
    )
    return AdmissionImportResponse(
        created_college_count=created_colleges,
        created_major_count=created_majors,
        **result.model_dump(),
    )
