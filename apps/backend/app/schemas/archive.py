from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class StoredFileRead(ORMModel):
    id: int
    original_filename: str
    file_path: str
    content_type: str | None = None
    file_size: int
    category: str
    created_at: datetime
    download_url: str | None = None


class StudentGrowthAttachmentRead(ORMModel):
    id: int
    stored_file_id: int
    note: str | None = None
    file: StoredFileRead


class StudentGrowthRecordPayload(BaseModel):
    occurred_on: date
    record_type: str
    title: str
    content: str | None = None
    owner_name: str | None = None
    note: str | None = None
    attachment_file_ids: list[int] = Field(default_factory=list)
    is_active: bool = True


class StudentGrowthRecordRead(ORMModel):
    id: int
    student_id: int
    student_name: str | None = None
    occurred_on: date
    record_type: str
    title: str
    content: str | None = None
    owner_name: str | None = None
    note: str | None = None
    is_active: bool
    attachments: list[StudentGrowthAttachmentRead] = Field(default_factory=list)


class StudentGrowthTimelineResponse(BaseModel):
    items: list[StudentGrowthRecordRead]
    total: int

