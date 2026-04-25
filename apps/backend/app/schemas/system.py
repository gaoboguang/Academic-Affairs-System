from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class BackupCreateResponse(BaseModel):
    message: str
    backup_id: int


class BackupRestorePayload(BaseModel):
    backup_id: int
    auto_backup_current: bool = True


class BackupRecordRead(ORMModel):
    id: int
    backup_name: str
    file_path: str
    file_size: int
    created_at: datetime
    status: str
    download_url: str | None = None


class AuditLogRead(ORMModel):
    id: int
    module: str
    action: str
    target_type: str | None = None
    target_id: str | None = None
    detail_json: dict | None = None
    created_at: datetime


class SystemConfigItemRead(ORMModel):
    id: int
    config_group: str
    config_key: str
    config_value: str
    parsed_value: Any | None = None
    value_type: str
    description: str | None = None


class SystemConfigItemUpdatePayload(BaseModel):
    config_group: str
    config_key: str
    config_value: Any
    value_type: str = "string"
    description: str | None = None


class SystemConfigGroupRead(BaseModel):
    config_group: str
    title: str
    items: list[SystemConfigItemRead] = Field(default_factory=list)


class SystemTemplateRead(BaseModel):
    name: str
    file_name: str
    file_size: int
    updated_at: datetime
    download_url: str


class ImportCenterTemplateRead(BaseModel):
    job_type: str
    job_type_label: str
    template_name: str
    file_name: str
    download_url: str
    business_path: str
    guidance: str


class ImportCenterSummaryRead(BaseModel):
    total_batches: int = 0
    failed_batches: int = 0
    partial_batches: int = 0
    error_report_count: int = 0


class ImportCenterBatchRead(BaseModel):
    id: str
    numeric_id: int
    source_type: str
    source_type_label: str
    job_type: str
    job_type_label: str
    source_filename: str | None = None
    status: str
    started_at: datetime | None = None
    finished_at: datetime | None = None
    total_rows: int | None = None
    success_rows: int | None = None
    failed_rows: int | None = None
    skipped_rows: int = 0
    created_rows: int = 0
    updated_rows: int = 0
    error_report_path: str | None = None
    business_path: str
    template_download_url: str | None = None
    rollback_supported: bool = False
    rollback_hint: str
    detail_summary: str


class ImportCenterBatchDetailRead(BaseModel):
    batch: ImportCenterBatchRead
    result_json: dict | None = None
    audit_logs: list[AuditLogRead] = Field(default_factory=list)
    error_preview: list[str] = Field(default_factory=list)
    notice_preview: list[str] = Field(default_factory=list)
    rollback_steps: list[str] = Field(default_factory=list)


class ImportCenterResponse(BaseModel):
    generated_at: datetime
    summary: ImportCenterSummaryRead
    templates: list[ImportCenterTemplateRead] = Field(default_factory=list)
    batches: list[ImportCenterBatchRead] = Field(default_factory=list)


class DataQualityIssueRead(BaseModel):
    code: str
    title: str
    severity: str
    count: int
    summary: str
    repairable: bool = False
    action_code: str | None = None
    samples: list[str] = Field(default_factory=list)


class DataRepairActionRead(BaseModel):
    code: str
    title: str
    description: str
    enabled: bool
    affected_issue_codes: list[str] = Field(default_factory=list)


class DataRepairScanRead(BaseModel):
    generated_at: datetime
    issues: list[DataQualityIssueRead] = Field(default_factory=list)
    actions: list[DataRepairActionRead] = Field(default_factory=list)


class DataRepairExecutePayload(BaseModel):
    action_code: str


class DataRepairExecuteResponse(BaseModel):
    action_code: str
    repaired_count: int
    message: str
    scan: DataRepairScanRead
