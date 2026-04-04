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
