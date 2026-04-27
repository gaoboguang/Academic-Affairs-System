#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
import sys
import urllib.error
import urllib.request
import zipfile
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any
from xml.etree import ElementTree


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = REPO_ROOT / "data" / "app.db"
DEFAULT_BACKUP_DIR = REPO_ROOT / "data" / "backups"
DEFAULT_REPORT_PATH = REPO_ROOT / "docs" / "round5-plan-supplement-audit.md"
IMPORTER_NAME = "round5_register_plan_supplement_documents"
USER_AGENT = "local-edu-tool-round5-plan-supplement/2026-04-27"


@dataclass(frozen=True)
class PlanSupplementSource:
    year: int
    title: str
    page_url: str
    file_url: str
    published_at: date
    note: str


PLAN_SUPPLEMENT_SOURCES: tuple[PlanSupplementSource, ...] = (
    PlanSupplementSource(
        2023,
        "山东省2023年普通高等学校分专业招生计划补充信息",
        "https://www.sdzk.cn/NewsInfo.aspx?NewsID=6222",
        "https://www.sdzk.cn/Floadup/file/20230627/6382348029376827184337893.docx",
        date(2023, 6, 27),
        "本科/普通高等学校分专业招生计划补充信息；不能替代完整填报志愿指南。",
    ),
    PlanSupplementSource(
        2024,
        "山东省2024年普通高等学校分专业招生计划补充信息",
        "https://www.sdzk.cn/NewsInfo.aspx?NewsID=6611",
        "https://www.sdzk.cn/Floadup/file/20240627/6385516213636230688036970.docx",
        date(2024, 6, 27),
        "本科/普通高等学校分专业招生计划补充信息；不能替代完整填报志愿指南。",
    ),
    PlanSupplementSource(
        2024,
        "山东省2024年普通高等学校专科层次分专业招生计划补充信息",
        "https://www.sdzk.cn/NewsInfo.aspx?NewsID=6661",
        "https://www.sdzk.cn/Floadup/file/20240722/6385726159356393297171291.docx",
        date(2024, 7, 22),
        "专科层次分专业招生计划补充信息；不能替代完整填报志愿指南。",
    ),
    PlanSupplementSource(
        2025,
        "山东省2025年普通高等学校分专业招生计划补充信息",
        "https://www.sdzk.cn/NewsInfo.aspx?NewsID=6955",
        "https://www.sdzk.cn/Floadup/file/20250627/6388661855703111824442516.docx",
        date(2025, 6, 27),
        "本科/普通高等学校分专业招生计划补充信息；不能替代完整填报志愿指南。",
    ),
    PlanSupplementSource(
        2025,
        "山东省2025年普通高等学校专科层次分专业招生计划补充信息",
        "https://www.sdzk.cn/NewsInfo.aspx?NewsID=6990",
        "https://www.sdzk.cn/Floadup/file/20250719/6388854771364040035069196.docx",
        date(2025, 7, 19),
        "专科层次分专业招生计划补充信息；不能替代完整填报志愿指南。",
    ),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download and register Round 5 Shandong admission plan supplement documents.")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH, help="SQLite app database path.")
    parser.add_argument("--backup-dir", type=Path, default=DEFAULT_BACKUP_DIR, help="Directory for DB backups.")
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT_PATH, help="Markdown audit report path.")
    parser.add_argument("--no-backup", action="store_true", help="Skip database backup.")
    parser.add_argument("--no-download", action="store_true", help="Use existing local files only.")
    parser.add_argument("--json", action="store_true", help="Output JSON.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    db_path = args.db.resolve()
    if not db_path.exists():
        print(f"database not found: {db_path}", file=sys.stderr)
        return 2

    backup_path = None
    if not args.no_backup:
        backup_path = _backup_database(db_path, args.backup_dir.resolve())

    with sqlite3.connect(str(db_path)) as conn:
        conn.row_factory = sqlite3.Row
        payload = register_plan_supplements(conn, download_missing=not args.no_download)

    payload["backup_path"] = str(backup_path) if backup_path else None
    payload["report_path"] = str(args.report)
    _write_report(args.report, payload)

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    print(f"第五轮招生计划补充信息已登记：{len(payload['items'])} 份官方 docx，报告 {args.report}。")
    if backup_path:
        print(f"备份：{backup_path}")
    return 0


def register_plan_supplements(conn: sqlite3.Connection, *, download_missing: bool) -> dict[str, Any]:
    _require_tables(conn)
    items: list[dict[str, Any]] = []
    failed_items: list[dict[str, Any]] = []
    for source in PLAN_SUPPLEMENT_SOURCES:
        try:
            file_path = _resolve_or_download(source, download_missing=download_missing)
        except (OSError, TimeoutError, urllib.error.URLError) as exc:
            failed_items.append(
                {
                    "year": source.year,
                    "title": source.title,
                    "page_url": source.page_url,
                    "file_url": source.file_url,
                    "error": str(exc),
                    "conclusion": "官方附件暂未下载成功，需人工下载后复跑本脚本。",
                }
            )
            continue
        source_document_id = _update_source_document(conn, source, file_path)
        stats = _extract_docx_stats(file_path)
        items.append(
            {
                "source_document_id": source_document_id,
                "year": source.year,
                "title": source.title,
                "page_url": source.page_url,
                "file_url": source.file_url,
                "local_file_path": _relative_path(file_path),
                "file_sha256": _sha256_file(file_path),
                "paragraph_count": stats["paragraph_count"],
                "table_count": stats["table_count"],
                "table_row_count": stats["table_row_count"],
                "text_snippet": stats["text_snippet"],
                "conclusion": "补充信息已下载登记；不得作为完整招生计划直接写入 gaokao_admission_plan。",
            }
        )
    conn.commit()
    return {
        "generated_at": _now_text(),
        "items": items,
        "failed_items": failed_items,
        "source_document_total": _count_rows(conn, "gaokao_source_document"),
        "plan_supplement_ready": len(items),
        "business_rows_imported": 0,
        "boundary": "本脚本只登记官方补充信息附件，不导入招生计划业务行。",
    }


def _resolve_or_download(source: PlanSupplementSource, *, download_missing: bool) -> Path:
    target_dir = REPO_ROOT / "data" / "imports" / "gaokao" / "official" / str(source.year)
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f"{source.year}_plan_supplement_{_safe_filename(source.title)}.docx"
    if target.exists():
        return target
    if not download_missing:
        raise FileNotFoundError(f"missing local official file: {target}")
    request = urllib.request.Request(source.file_url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=12) as response:
        target.write_bytes(response.read())
    return target


def _update_source_document(conn: sqlite3.Connection, source: PlanSupplementSource, file_path: Path) -> int:
    now = _now_text()
    existing = conn.execute(
        """
        SELECT id FROM gaokao_source_document
        WHERE province IN ('山东', 'sd')
          AND year = ?
          AND source_type = 'admission_plan_supplement'
          AND url = ?
        LIMIT 1
        """,
        (source.year, source.page_url),
    ).fetchone()
    payload = {
        "province": "山东",
        "year": source.year,
        "source_type": "admission_plan_supplement",
        "title": source.title,
        "url": source.page_url,
        "official_org": "山东省教育招生考试院",
        "source_registry_code": "sdzk",
        "published_at": source.published_at.isoformat(),
        "fetched_at": now,
        "local_file_path": _relative_path(file_path),
        "file_sha256": _sha256_file(file_path),
        "parser_name": IMPORTER_NAME,
        "parser_version": "2026-04-27",
        "status": "file_ready",
        "note": f"{source.note} 官方附件：{source.file_url}",
        "updated_at": now,
    }
    if existing:
        conn.execute(
            """
            UPDATE gaokao_source_document
            SET title = :title,
                official_org = :official_org,
                source_registry_code = :source_registry_code,
                published_at = :published_at,
                fetched_at = :fetched_at,
                local_file_path = :local_file_path,
                file_sha256 = :file_sha256,
                parser_name = :parser_name,
                parser_version = :parser_version,
                status = :status,
                note = :note,
                updated_at = :updated_at
            WHERE id = :id
            """,
            {**payload, "id": existing["id"]},
        )
        return int(existing["id"])
    conn.execute(
        """
        INSERT INTO gaokao_source_document (
            province, year, source_type, title, url, official_org, source_registry_code,
            published_at, fetched_at, local_file_path, file_sha256, parser_name,
            parser_version, status, note, created_at, updated_at, is_active
        ) VALUES (
            :province, :year, :source_type, :title, :url, :official_org, :source_registry_code,
            :published_at, :fetched_at, :local_file_path, :file_sha256, :parser_name,
            :parser_version, :status, :note, :created_at, :updated_at, 1
        )
        """,
        {**payload, "created_at": now},
    )
    return int(conn.execute("SELECT last_insert_rowid()").fetchone()[0])


def _extract_docx_stats(file_path: Path) -> dict[str, Any]:
    with zipfile.ZipFile(file_path) as archive:
        xml_bytes = archive.read("word/document.xml")
    root = ElementTree.fromstring(xml_bytes)
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    paragraphs = []
    for paragraph in root.findall(".//w:p", ns):
        text = "".join(node.text or "" for node in paragraph.findall(".//w:t", ns)).strip()
        if text:
            paragraphs.append(text)
    table_count = len(root.findall(".//w:tbl", ns))
    table_row_count = len(root.findall(".//w:tr", ns))
    snippet = "；".join(paragraphs[:5])
    return {
        "paragraph_count": len(paragraphs),
        "table_count": table_count,
        "table_row_count": table_row_count,
        "text_snippet": snippet[:300],
    }


def _write_report(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# 第五轮招生计划补充信息附件审计",
        "",
        f"- 生成时间：{payload['generated_at']}",
        "- 主库：`data/app.db`",
        "- 边界：本报告记录山东省教育招生考试院补充信息附件的下载、登记和读取结果；补充信息不是完整《填报志愿指南》，本轮不据此关闭招生计划完整性缺口。",
        "",
        "## 1. 附件登记结果",
        "",
        "| 年份 | source_document_id | 附件 | 表格数 | 表格行数 | SHA256 |",
        "| --- | ---: | --- | ---: | ---: | --- |",
    ]
    for item in payload["items"]:
        lines.append(
            f"| {item['year']} | {item['source_document_id']} | "
            f"[{item['title']}]({item['page_url']}) | {item['table_count']} | "
            f"{item['table_row_count']} | `{item['file_sha256']}` |"
        )
    lines.extend(
        [
            "",
            "## 2. 下载失败或待人工处理",
            "",
        ]
    )
    if payload.get("failed_items"):
        lines.extend(
            [
                "| 年份 | 附件 | 失败原因 | 下一步 |",
                "| --- | --- | --- | --- |",
            ]
        )
        for item in payload["failed_items"]:
            error = str(item["error"]).replace("|", "/")
            lines.append(
                f"| {item['year']} | [{item['title']}]({item['page_url']}) | {error} | "
                f"人工下载 `{item['file_url']}` 后复跑脚本 |"
            )
    else:
        lines.append("- 无。")
    lines.extend(
        [
            "",
            "## 3. 机器读取摘要",
            "",
        ]
    )
    for item in payload["items"]:
        lines.extend(
            [
                f"### {item['year']} {item['title']}",
                "",
                f"- 本地文件：`{item['local_file_path']}`",
                f"- 官方附件：{item['file_url']}",
                f"- 文本/表格：段落 {item['paragraph_count']}，表格 {item['table_count']}，表格行 {item['table_row_count']}",
                f"- 摘要：{item['text_snippet'] or '未提取到正文摘要'}",
                "- 处理结论：只作为计划补充证据，不直接写入 `gaokao_admission_plan`。",
                "",
            ]
        )
    lines.extend(
        [
            "## 4. 后续建议",
            "",
            "1. 继续寻找或由用户提供 2023-2025 完整《山东省普通高校招生填报志愿指南》或志愿填报辅助系统官方导出。",
            "2. 若后续要把补充信息合并到计划表，应先和完整计划做差异合并，保留原始计划、补充项、变更原因和来源附件。",
            "3. 当前 `2024 山东招生计划数量偏少` 告警不能因补充信息已登记而关闭。",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def _require_tables(conn: sqlite3.Connection) -> None:
    tables = {
        row["name"]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'gaokao_source_document'"
        ).fetchall()
    }
    if "gaokao_source_document" not in tables:
        raise RuntimeError("missing required table: gaokao_source_document")


def _safe_filename(value: str) -> str:
    text = re.sub(r"[^\w\u4e00-\u9fff.-]+", "_", value.strip(), flags=re.U)
    return text.strip("._")[:150] or "gaokao_source"


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file_obj:
        for chunk in iter(lambda: file_obj.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _relative_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def _now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _count_rows(conn: sqlite3.Connection, table: str) -> int:
    return int(conn.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0])


def _backup_database(source_path: Path, backup_dir: Path) -> Path:
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup_path = backup_dir / f"{source_path.stem}_before_round5_plan_supplement_register_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    with sqlite3.connect(str(source_path)) as source_conn, sqlite3.connect(str(backup_path)) as backup_conn:
        source_conn.backup(backup_conn)
    return backup_path


if __name__ == "__main__":
    raise SystemExit(main())
