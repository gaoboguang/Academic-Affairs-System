from __future__ import annotations

import json
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4
from zipfile import ZIP_DEFLATED, ZipFile

from fastapi import HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.bootstrap import ensure_runtime_directories
from app.db.session import DatabaseManager
from app.models import AuditLog, BackupRecord, ConfigItem, ReportExportRecord, StoredFile
from app.repositories.system import (
    get_backup_record,
    get_stored_file,
    list_audit_logs as repo_list_audit_logs,
    list_backups as repo_list_backups,
    write_audit_log,
)
from app.schemas.archive import StoredFileRead
from app.schemas.system import (
    AuditLogRead,
    BackupCreateResponse,
    BackupRecordRead,
    BackupRestorePayload,
    DataRepairExecutePayload,
    DataRepairExecuteResponse,
    DataRepairScanRead,
    SystemConfigGroupRead,
    SystemConfigItemRead,
    SystemConfigItemUpdatePayload,
    SystemTemplateRead,
)
from app.services.data_quality import build_data_repair_scan, execute_repair_action
from app.utils.parsers import make_timestamped_filename, relative_to_project

CONFIG_GROUP_TITLES = {
    "analytics": "成绩分析参数",
    "recommendation": "推荐策略参数",
    "system": "系统运行参数",
}


def _serialize_stored_file(item: StoredFile) -> StoredFileRead:
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


def _serialize_backup(item: BackupRecord) -> BackupRecordRead:
    return BackupRecordRead(
        id=item.id,
        backup_name=item.backup_name,
        file_path=item.file_path,
        file_size=item.file_size,
        created_at=item.created_at,
        status=item.status,
        download_url=f"/api/system/backups/{item.id}/download",
    )


def list_backups(session: Session) -> list[BackupRecordRead]:
    return [_serialize_backup(item) for item in repo_list_backups(session)]


def list_audit_logs(session: Session, limit: int = 100) -> list[AuditLogRead]:
    return [AuditLogRead.model_validate(item) for item in repo_list_audit_logs(session, limit=limit)]


def list_config_groups(session: Session) -> list[SystemConfigGroupRead]:
    rows = session.scalars(
        select(ConfigItem)
        .where(ConfigItem.is_active.is_(True))
        .order_by(ConfigItem.config_group, ConfigItem.config_key)
    ).all()
    grouped: dict[str, list[SystemConfigItemRead]] = {}
    for row in rows:
        grouped.setdefault(row.config_group, []).append(_serialize_config_item(row))
    return [
        SystemConfigGroupRead(
            config_group=config_group,
            title=CONFIG_GROUP_TITLES.get(config_group, config_group.replace("_", " ").title()),
            items=items,
        )
        for config_group, items in grouped.items()
    ]


def update_config_items(
    session: Session,
    payloads: list[SystemConfigItemUpdatePayload],
) -> list[SystemConfigGroupRead]:
    existing = {
        (row.config_group, row.config_key): row
        for row in session.scalars(select(ConfigItem)).all()
    }
    for payload in payloads:
        key = (payload.config_group, payload.config_key)
        config_value = _stringify_config_value(payload.config_value, payload.value_type)
        row = existing.get(key)
        if row:
            row.config_value = config_value
            row.value_type = payload.value_type
            if payload.description is not None:
                row.description = payload.description
            row.is_active = True
            continue
        session.add(
            ConfigItem(
                config_group=payload.config_group,
                config_key=payload.config_key,
                config_value=config_value,
                value_type=payload.value_type,
                description=payload.description,
            )
        )
    session.flush()
    write_audit_log(
        session,
        module="system",
        action="update_config",
        target_type="config_group",
        detail_json={"item_count": len(payloads)},
    )
    return list_config_groups(session)


def list_templates(settings) -> list[SystemTemplateRead]:
    if not settings.templates_dir.exists():
        return []
    rows: list[SystemTemplateRead] = []
    for path in sorted(settings.templates_dir.iterdir(), key=lambda item: item.stat().st_mtime, reverse=True):
        if not path.is_file():
            continue
        stat = path.stat()
        rows.append(
            SystemTemplateRead(
                name=path.stem.replace("_", " "),
                file_name=path.name,
                file_size=stat.st_size,
                updated_at=datetime.fromtimestamp(stat.st_mtime),
                download_url=f"/api/system/templates/{path.name}/download",
            )
        )
    return rows


def get_template_path(settings, template_name: str) -> Path:
    safe_name = Path(template_name).name
    path = settings.templates_dir / safe_name
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail="模板文件不存在")
    return path


def get_data_repair_scan(session: Session) -> DataRepairScanRead:
    return build_data_repair_scan(session)


def execute_data_repair(
    session: Session,
    payload: DataRepairExecutePayload,
) -> DataRepairExecuteResponse:
    repaired_count, message = execute_repair_action(session, payload.action_code)
    return DataRepairExecuteResponse(
        action_code=payload.action_code,
        repaired_count=repaired_count,
        message=message,
        scan=build_data_repair_scan(session),
    )


def upload_file(
    session: Session,
    settings,
    *,
    filename: str | None,
    content: bytes,
    content_type: str | None,
    category: str = "general",
) -> StoredFileRead:
    if not filename:
        raise HTTPException(status_code=400, detail="文件名不能为空")
    safe_name = Path(filename).name
    suffix = Path(safe_name).suffix
    stored_name = f"{uuid4().hex}{suffix}"
    target_dir = settings.uploads_dir / category
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / stored_name
    target_path.write_bytes(content)
    record = StoredFile(
        original_filename=safe_name,
        file_path=relative_to_project(target_path, settings.project_root),
        content_type=content_type,
        file_size=len(content),
        category=category,
    )
    session.add(record)
    session.flush()
    write_audit_log(
        session,
        module="files",
        action="upload",
        target_type="stored_file",
        target_id=str(record.id),
        detail_json={"category": category, "original_filename": safe_name},
    )
    return _serialize_stored_file(record)


def get_file_path(session: Session, settings, file_id: int) -> Path:
    item = get_stored_file(session, file_id)
    if not item or not item.is_active:
        raise HTTPException(status_code=404, detail="文件不存在")
    path = settings.project_root / item.file_path
    if not path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")
    return path


def create_backup(request: Request) -> BackupCreateResponse:
    settings = request.app.state.settings
    ensure_runtime_directories(settings)
    with TemporaryDirectory() as tmp_dir:
        tmp_root = Path(tmp_dir)
        snapshot_db = tmp_root / "app.db"
        _snapshot_sqlite_db(settings.db_path, snapshot_db)
        manifest = {
            "app_name": settings.app_name,
            "version": "0.1.0",
            "database_file": "db/app.db",
            "created_from": str(settings.project_root),
        }
        backup_name = make_timestamped_filename("local_edu_backup", ".zip")
        backup_path = settings.backups_dir / backup_name
        with ZipFile(backup_path, "w", compression=ZIP_DEFLATED) as archive:
            archive.write(snapshot_db, arcname="db/app.db")
            _add_directory_to_zip(archive, settings.uploads_dir, "uploads")
            _add_directory_to_zip(archive, settings.templates_dir, "templates")
            env_path = settings.project_root / ".env"
            if env_path.exists():
                archive.write(env_path, arcname="config/.env")
            archive.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))

    file_size = backup_path.stat().st_size if backup_path.exists() else 0
    with request.app.state.db.session_scope() as session:
        record = BackupRecord(
            backup_name=backup_name,
            file_path=relative_to_project(backup_path, settings.project_root),
            file_size=file_size,
            status="success",
        )
        session.add(record)
        session.flush()
        write_audit_log(
            session,
            module="system",
            action="backup",
            target_type="backup_record",
            target_id=str(record.id),
            detail_json={"backup_name": backup_name},
        )
        backup_id = record.id
    return BackupCreateResponse(message="备份完成", backup_id=backup_id)


def restore_backup(request: Request, payload: BackupRestorePayload) -> dict[str, str]:
    settings = request.app.state.settings
    if payload.auto_backup_current:
        create_backup(request)

    with request.app.state.db.session_scope() as session:
        record = get_backup_record(session, payload.backup_id)
        if not record:
            raise HTTPException(status_code=404, detail="备份记录不存在")
        backup_path = settings.project_root / record.file_path

    if not backup_path.exists():
        raise HTTPException(status_code=404, detail="备份文件不存在")

    with TemporaryDirectory() as tmp_dir:
        tmp_root = Path(tmp_dir)
        with ZipFile(backup_path, "r") as archive:
            if "manifest.json" not in archive.namelist() or "db/app.db" not in archive.namelist():
                raise HTTPException(status_code=400, detail="备份包结构无效")
            archive.extractall(tmp_root)
        restored_db = tmp_root / "db" / "app.db"
        if not restored_db.exists():
            raise HTTPException(status_code=400, detail="备份包缺少数据库文件")

        request.app.state.db.dispose()
        _replace_file(restored_db, settings.db_path)
        _replace_directory(tmp_root / "uploads", settings.uploads_dir)
        _replace_directory(tmp_root / "templates", settings.templates_dir)
        env_path = tmp_root / "config" / ".env"
        if env_path.exists():
            _replace_file(env_path, settings.project_root / ".env")

    request.app.state.db = DatabaseManager(settings.database_url, settings.debug)
    request.app.state.db.initialize()
    ensure_runtime_directories(settings)
    with request.app.state.db.session_scope() as session:
        write_audit_log(
            session,
            module="system",
            action="restore",
            target_type="backup_record",
            target_id=str(payload.backup_id),
            detail_json={"backup_id": payload.backup_id},
        )
    return {"message": "恢复完成"}


def get_backup_path(session: Session, settings, backup_id: int) -> Path:
    record = get_backup_record(session, backup_id)
    if not record:
        raise HTTPException(status_code=404, detail="备份记录不存在")
    path = settings.project_root / record.file_path
    if not path.exists():
        raise HTTPException(status_code=404, detail="备份文件不存在")
    return path


def _serialize_config_item(item: ConfigItem) -> SystemConfigItemRead:
    return SystemConfigItemRead(
        id=item.id,
        config_group=item.config_group,
        config_key=item.config_key,
        config_value=item.config_value,
        parsed_value=_parse_config_value(item.config_value, item.value_type),
        value_type=item.value_type,
        description=item.description,
    )


def _parse_config_value(value: str, value_type: str):
    if value_type == "bool":
        return str(value).strip().lower() in {"1", "true", "yes", "on"}
    if value_type == "int":
        try:
            return int(str(value).strip())
        except (TypeError, ValueError):
            return value
    if value_type == "float":
        try:
            return float(str(value).strip())
        except (TypeError, ValueError):
            return value
    if value_type == "json":
        try:
            return json.loads(value)
        except (TypeError, json.JSONDecodeError):
            return value
    return value


def _stringify_config_value(value, value_type: str) -> str:
    if value_type == "bool":
        if isinstance(value, str):
            normalized = value.strip().lower() in {"1", "true", "yes", "on"}
        else:
            normalized = bool(value)
        return "true" if normalized else "false"
    if value_type == "json":
        if isinstance(value, str):
            json.loads(value)
            return value
        return json.dumps(value, ensure_ascii=False)
    return "" if value is None else str(value)


def _snapshot_sqlite_db(source_path: Path, target_path: Path) -> None:
    source = sqlite3.connect(source_path)
    target = sqlite3.connect(target_path)
    try:
        source.backup(target)
    finally:
        target.close()
        source.close()


def _add_directory_to_zip(archive: ZipFile, directory: Path, prefix: str) -> None:
    if not directory.exists():
        return
    for path in directory.rglob("*"):
        if path.is_file():
            archive.write(path, arcname=f"{prefix}/{path.relative_to(directory).as_posix()}")


def _replace_directory(source: Path, target: Path) -> None:
    if target.exists():
        shutil.rmtree(target)
    if source.exists():
        shutil.copytree(source, target)
    else:
        target.mkdir(parents=True, exist_ok=True)


def _replace_file(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    wal_path = target.with_suffix(target.suffix + "-wal")
    shm_path = target.with_suffix(target.suffix + "-shm")
    if wal_path.exists():
        wal_path.unlink()
    if shm_path.exists():
        shm_path.unlink()
