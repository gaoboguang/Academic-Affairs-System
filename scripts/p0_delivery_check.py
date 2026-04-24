#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZIP_DEFLATED, ZipFile


ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / "apps" / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from fastapi.testclient import TestClient  # noqa: E402

from app.core.bootstrap import ensure_runtime_directories  # noqa: E402
from app.core.config import Settings  # noqa: E402
from app.main import create_app  # noqa: E402
from app.utils.data_health import build_data_health_report, format_data_health_report  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="执行 P0 本地交付验收：健康检查、备份、临时恢复和二次启动。")
    parser.add_argument(
        "--db",
        type=Path,
        default=ROOT_DIR / "data" / "app.db",
        help="要验收的主库路径。",
    )
    parser.add_argument(
        "--backup-dir",
        type=Path,
        default=ROOT_DIR / "data" / "backups",
        help="P0 验收备份包输出目录。",
    )
    parser.add_argument(
        "--keep-restore-dir",
        action="store_true",
        help="保留临时恢复目录，便于人工排查。",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="输出 JSON 结果。",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = run_p0_delivery_check(
        args.db,
        backup_dir=args.backup_dir,
        keep_restore_dir=args.keep_restore_dir,
    )
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(format_p0_delivery_result(result))
    return 0 if result["ok"] else 1


def run_p0_delivery_check(
    db_path: Path,
    *,
    backup_dir: Path,
    keep_restore_dir: bool = False,
) -> dict[str, object]:
    db_path = db_path.resolve()
    backup_dir = backup_dir.resolve()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    checks: list[dict[str, object]] = []

    source_health = build_data_health_report(db_path)
    checks.append(_check("data_health", bool(source_health["exists"]), source_health["summary"]))
    if not source_health["exists"]:
        return _result(False, db_path, None, None, source_health, None, checks)

    integrity = check_sqlite_integrity(db_path)
    checks.append(_check("source_integrity", integrity == "ok", integrity))

    backup_dir.mkdir(parents=True, exist_ok=True)
    backup_path = backup_dir / f"p0_delivery_backup_{timestamp}.zip"
    create_backup_zip(db_path, backup_path)
    checks.append(_check("backup_created", backup_path.exists(), str(backup_path)))

    backup_valid, backup_message = validate_backup_zip(backup_path)
    checks.append(_check("backup_structure", backup_valid, backup_message))

    if keep_restore_dir:
        restore_root = backup_dir / f"p0_restore_check_{timestamp}"
        restore_root.mkdir(parents=True, exist_ok=True)
        restored_db, restore_integrity, restore_health, startup_message = restore_and_check(backup_path, restore_root)
        restore_dir = restore_root
    else:
        with TemporaryDirectory(prefix=f"p0_restore_check_{timestamp}_", dir=str(backup_dir)) as tmp_dir:
            restored_db, restore_integrity, restore_health, startup_message = restore_and_check(backup_path, Path(tmp_dir))
            restore_dir = None

    checks.append(_check("restore_integrity", restore_integrity == "ok", f"{restore_integrity}: {restored_db}"))
    checks.append(_check("restore_data_health", bool(restore_health["exists"]), restore_health["summary"]))
    checks.append(_check("restore_startup", startup_message == "ok", startup_message))

    return _result(
        all(bool(item["ok"]) for item in checks),
        db_path,
        backup_path,
        restore_dir,
        source_health,
        restore_health,
        checks,
    )


def create_backup_zip(db_path: Path, backup_path: Path) -> None:
    with TemporaryDirectory() as tmp_dir:
        tmp_root = Path(tmp_dir)
        snapshot_db = tmp_root / "app.db"
        backup_sqlite_database(db_path, snapshot_db)
        manifest = {
            "app_name": "本地教务工具",
            "check": "p0_delivery",
            "database_file": "db/app.db",
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "source_db": str(db_path),
        }
        with ZipFile(backup_path, "w", compression=ZIP_DEFLATED) as archive:
            archive.write(snapshot_db, arcname="db/app.db")
            _add_directory_to_zip(archive, ROOT_DIR / "data" / "uploads", "uploads")
            _add_directory_to_zip(archive, ROOT_DIR / "data" / "templates", "templates")
            env_path = ROOT_DIR / ".env"
            if env_path.exists():
                archive.write(env_path, arcname="config/.env")
            archive.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))


def restore_and_check(backup_path: Path, restore_root: Path) -> tuple[Path, str, dict[str, object], str]:
    restore_root.mkdir(parents=True, exist_ok=True)
    with ZipFile(backup_path, "r") as archive:
        archive.extractall(restore_root)
    restored_db = restore_root / "db" / "app.db"
    restored_data_dir = restore_root / "data"
    restored_data_dir.mkdir(parents=True, exist_ok=True)
    restored_app_db = restored_data_dir / "app.db"
    shutil.copy2(restored_db, restored_app_db)

    uploads_dir = restore_root / "uploads"
    templates_dir = restore_root / "templates"
    if uploads_dir.exists():
        shutil.copytree(uploads_dir, restored_data_dir / "uploads", dirs_exist_ok=True)
    if templates_dir.exists():
        shutil.copytree(templates_dir, restored_data_dir / "templates", dirs_exist_ok=True)

    restore_integrity = check_sqlite_integrity(restored_app_db)
    restore_health = build_data_health_report(restored_app_db)
    startup_message = check_restored_app_startup(restored_data_dir, restored_app_db)
    return restored_app_db, restore_integrity, restore_health, startup_message


def check_restored_app_startup(data_dir: Path, db_path: Path) -> str:
    settings = Settings(
        data_dir=data_dir,
        db_path=db_path,
        gaokao_db_path=data_dir / "local_edu_tool" / "local_edu.sqlite3",
        allowed_origins=["http://127.0.0.1:5173"],
        debug=False,
    )
    app = create_app(settings)
    ensure_runtime_directories(settings)
    try:
        with TestClient(app) as client:
            health_response = client.get("/api/system/health")
            if health_response.status_code != 200:
                return f"system health failed: {health_response.status_code}"
            data_health_response = client.get("/api/gaokao/data-health")
            if data_health_response.status_code != 200:
                return f"data health failed: {data_health_response.status_code}"
        return "ok"
    finally:
        app.state.db.dispose()
        if getattr(app.state, "gaokao_db", None) is not None:
            app.state.gaokao_db.dispose()


def validate_backup_zip(backup_path: Path) -> tuple[bool, str]:
    if not backup_path.exists():
        return False, "备份包不存在"
    with ZipFile(backup_path, "r") as archive:
        names = set(archive.namelist())
    missing = {"manifest.json", "db/app.db"} - names
    if missing:
        return False, f"备份包缺少: {', '.join(sorted(missing))}"
    return True, "ok"


def check_sqlite_integrity(db_path: Path) -> str:
    if not db_path.exists():
        return f"database not found: {db_path}"
    with sqlite3.connect(str(db_path)) as conn:
        row = conn.execute("PRAGMA integrity_check").fetchone()
    return str(row[0]) if row and row[0] else "unknown"


def backup_sqlite_database(source_path: Path, backup_path: Path) -> None:
    with sqlite3.connect(str(source_path)) as source_conn, sqlite3.connect(str(backup_path)) as backup_conn:
        source_conn.backup(backup_conn)


def format_p0_delivery_result(result: dict[str, object]) -> str:
    lines = [
        "P0 交付验收",
        f"- ok: {result['ok']}",
        f"- db: {result['db_path']}",
        f"- backup: {result.get('backup_path') or '未生成'}",
        f"- restore_dir: {result.get('restore_dir') or '临时目录已清理'}",
        "",
        "检查项:",
    ]
    for item in result["checks"]:
        status = "PASS" if item["ok"] else "FAIL"
        lines.append(f"- {status} {item['key']}: {item['message']}")

    lines.append("")
    lines.append("源库健康摘要:")
    lines.append(format_data_health_report(result["source_health"]))

    if result.get("restore_health"):
        lines.append("")
        lines.append("恢复库健康摘要:")
        lines.append(format_data_health_report(result["restore_health"]))
    return "\n".join(lines)


def _add_directory_to_zip(archive: ZipFile, source_dir: Path, arc_prefix: str) -> None:
    if not source_dir.exists():
        return
    for path in source_dir.rglob("*"):
        if path.is_file():
            archive.write(path, arcname=str(Path(arc_prefix) / path.relative_to(source_dir)))


def _check(key: str, ok: bool, message: str) -> dict[str, object]:
    return {"key": key, "ok": ok, "message": message}


def _result(
    ok: bool,
    db_path: Path,
    backup_path: Path | None,
    restore_dir: Path | None,
    source_health: dict[str, object],
    restore_health: dict[str, object] | None,
    checks: list[dict[str, object]],
) -> dict[str, object]:
    return {
        "ok": ok,
        "db_path": str(db_path),
        "backup_path": str(backup_path) if backup_path else None,
        "restore_dir": str(restore_dir) if restore_dir else None,
        "source_health": source_health,
        "restore_health": restore_health,
        "checks": checks,
    }


if __name__ == "__main__":
    raise SystemExit(main())
