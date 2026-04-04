from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class PageMeta(BaseModel):
    total: int
    page: int
    page_size: int


class ImportResult(BaseModel):
    total_rows: int
    success_rows: int
    failed_rows: int
    skipped_rows: int = 0
    error_report_path: str | None = None
    message: str

