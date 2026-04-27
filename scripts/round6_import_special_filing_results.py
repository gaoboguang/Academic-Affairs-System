#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import shutil
import sqlite3
import sys
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = REPO_ROOT / "data" / "app.db"
DEFAULT_BACKUP_DIR = REPO_ROOT / "data" / "backups"
DEFAULT_REPORT_PATH = REPO_ROOT / "docs" / "round6-special-filing-import-result.md"
IMPORTER_NAME = "round6_import_special_filing_results"
DATA_VERSION_LABEL = "round6_special_filing_20260427"
USER_AGENT = "local-edu-tool-round6-special-filing/2026-04-27"
SOURCE_TYPES = ("art_filing_result", "sports_filing_result", "spring_exam_filing_result")


@dataclass(frozen=True)
class FilingPage:
    source_document_id: int
    year: int
    source_type: str
    title: str
    page_url: str
    published_at: str | None


@dataclass(frozen=True)
class Attachment:
    page: FilingPage
    title: str
    file_url: str
    file_path: Path
    source_document_id: int | None = None
    import_run_id: int | None = None


@dataclass(frozen=True)
class ParsedFilingRow:
    row_number: int
    category: str | None
    college_code: str | None
    college_name: str
    major_code: str | None
    major_name: str
    plan_count: int | None
    min_score: Decimal | None
    min_rank: int | None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download and import Shandong art/sports/spring filing result attachments for Round 6."
    )
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH, help="SQLite app database path.")
    parser.add_argument("--backup-dir", type=Path, default=DEFAULT_BACKUP_DIR, help="Database backup directory.")
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT_PATH, help="Markdown report path.")
    parser.add_argument("--year", type=int, action="append", help="Limit to one or more years.")
    parser.add_argument("--no-download", action="store_true", help="Only use existing local files.")
    parser.add_argument("--no-backup", action="store_true", help="Skip DB backup.")
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
        payload = import_special_filing_results(
            conn,
            years=tuple(args.year or (2023, 2024, 2025)),
            download_missing=not args.no_download,
        )

    payload["backup_path"] = _relative_path(backup_path) if backup_path else None
    payload["report_path"] = _relative_path(args.report.resolve())
    _write_report(args.report.resolve(), payload)

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(
            "第六轮特殊类型投档表处理完成："
            f"解析附件 {payload['imported_files']} 个，raw 新增 {payload['raw_created']} 条，"
            f"失败/待处理 {len(payload['failures'])} 项。"
        )
        print(f"报告：{payload['report_path']}")
    return 0


def import_special_filing_results(
    conn: sqlite3.Connection,
    *,
    years: tuple[int, ...],
    download_missing: bool,
) -> dict[str, Any]:
    _require_tables(conn)
    pages = _load_registered_pages(conn, years)
    imported_items: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    raw_created = 0

    for page in pages:
        page_attachments, page_failures = _resolve_page_attachments(page, download_missing=download_missing)
        failures.extend(page_failures)
        for attachment in page_attachments:
            try:
                source_document_id = _upsert_attachment_source_document(conn, attachment)
                import_run_id = _create_import_run(conn, source_document_id, attachment)
                imported_attachment = Attachment(
                    page=attachment.page,
                    title=attachment.title,
                    file_url=attachment.file_url,
                    file_path=attachment.file_path,
                    source_document_id=source_document_id,
                    import_run_id=import_run_id,
                )
                rows = _parse_filing_file(imported_attachment.file_path)
                created = _replace_raw_rows(conn, imported_attachment, rows)
                _finish_import_run(conn, import_run_id, source_document_id, imported_attachment, len(rows), created)
                raw_created += created
                imported_items.append(
                    {
                        "year": page.year,
                        "source_type": page.source_type,
                        "title": attachment.title,
                        "source_document_id": source_document_id,
                        "import_run_id": import_run_id,
                        "local_file_path": _relative_path(attachment.file_path),
                        "file_sha256": _sha256_file(attachment.file_path),
                        "parsed_rows": len(rows),
                        "raw_created": created,
                        "candidate_type": _candidate_type(page.source_type),
                        "batch_name": _batch_name(page.title),
                        "metric": _metric_label(rows),
                    }
                )
            except Exception as exc:  # noqa: BLE001 - report per attachment and keep other files moving.
                failures.append(
                    {
                        "year": page.year,
                        "source_type": page.source_type,
                        "title": attachment.title,
                        "url": attachment.file_url,
                        "reason": str(exc),
                    }
                )
    conn.commit()
    return {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "years": list(years),
        "registered_pages": len(pages),
        "imported_files": len(imported_items),
        "raw_created": raw_created,
        "application_created": 0,
        "items": imported_items,
        "failures": failures,
        "coverage": _build_coverage(conn),
    }


def _load_registered_pages(conn: sqlite3.Connection, years: tuple[int, ...]) -> list[FilingPage]:
    placeholders = ",".join("?" for _ in years)
    rows = conn.execute(
        f"""
        SELECT id, year, source_type, title, url, published_at
        FROM gaokao_source_document
        WHERE province = '山东'
          AND year IN ({placeholders})
          AND source_type IN ({",".join("?" for _ in SOURCE_TYPES)})
          AND is_active = 1
        ORDER BY year, source_type, id
        """,
        (*years, *SOURCE_TYPES),
    ).fetchall()
    return [
        FilingPage(
            source_document_id=int(row["id"]),
            year=int(row["year"]),
            source_type=str(row["source_type"]),
            title=str(row["title"]),
            page_url=str(row["url"]),
            published_at=str(row["published_at"]) if row["published_at"] else None,
        )
        for row in rows
    ]


def _resolve_page_attachments(page: FilingPage, *, download_missing: bool) -> tuple[list[Attachment], list[dict[str, Any]]]:
    local_matches = _find_existing_local_files(page)
    if local_matches:
        return [
            Attachment(page=page, title=_title_from_path(path), file_url=page.page_url, file_path=path)
            for path in local_matches
        ], []
    if not download_missing:
        return [], [_failure(page, page.page_url, "本地未找到已下载附件，且本次使用 --no-download。")]

    try:
        html_text = _fetch_text(page.page_url)
    except Exception as exc:  # noqa: BLE001
        return [], [_failure(page, page.page_url, f"官方页面下载失败：{exc}")]

    links = _extract_official_file_links(html_text, page.page_url)
    if not links:
        return [], [_failure(page, page.page_url, "官方页面未发现 xls/xlsx 附件链接。")]

    attachments: list[Attachment] = []
    failures: list[dict[str, Any]] = []
    for title, file_url in links:
        target = _target_file_path(page.year, title, file_url)
        if not target.exists():
            try:
                _download_file(file_url, target)
            except Exception as exc:  # noqa: BLE001
                failures.append(_failure(page, file_url, f"附件下载失败：{exc}", title=title))
                continue
        attachments.append(Attachment(page=page, title=title, file_url=file_url, file_path=target))
    return attachments, failures


def _find_existing_local_files(page: FilingPage) -> list[Path]:
    year_dir = REPO_ROOT / "data" / "imports" / "gaokao" / "official" / str(page.year)
    if not year_dir.exists():
        return []
    title_keywords = [keyword for keyword in _title_keywords(page.title) if keyword]
    candidates: list[Path] = []
    for path in sorted(list(year_dir.glob("*.xls")) + list(year_dir.glob("*.xlsx"))):
        name = path.name
        if all(keyword in name for keyword in title_keywords):
            candidates.append(path)
    return candidates


def _title_keywords(title: str) -> list[str]:
    if "艺术" in title:
        return ["投档情况表", "艺术"]
    if "体育" in title:
        return ["投档情况表", "体育"]
    if "春季高考" in title:
        return ["投档情况表", "春季高考", "本科" if "本科" in title else "专科"]
    return ["投档情况表"]


def _extract_official_file_links(html_text: str, base_url: str) -> list[tuple[str, str]]:
    pattern = re.compile(r"<a\s+[^>]*href=[\"'](?P<href>[^\"']+)[\"'][^>]*>(?P<label>.*?)</a>", re.I | re.S)
    links: list[tuple[str, str]] = []
    seen: set[str] = set()
    for match in pattern.finditer(html_text):
        href = html.unescape(match.group("href")).strip()
        label = re.sub(r"<[^>]+>", "", match.group("label"))
        label = html.unescape(label).strip()
        if not re.search(r"\.xls[x]?(?:$|\?)", href, re.I):
            continue
        file_url = urllib.parse.urljoin(base_url, href)
        if file_url in seen:
            continue
        seen.add(file_url)
        links.append((label or Path(urllib.parse.urlparse(file_url).path).name, file_url))
    return links


def _fetch_text(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=40) as response:
        raw = response.read()
    for encoding in ("utf-8", "gb18030"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def _download_file(url: str, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=90) as response:
        target.write_bytes(response.read())


def _target_file_path(year: int, title: str, file_url: str) -> Path:
    suffix = Path(urllib.parse.urlparse(file_url).path).suffix or ".xls"
    name = f"{year}_{_safe_filename(title)}{suffix}"
    return REPO_ROOT / "data" / "imports" / "gaokao" / "official" / str(year) / name


def _parse_filing_file(file_path: Path) -> list[ParsedFilingRow]:
    frame = pd.read_excel(file_path, header=None, dtype=str)
    header_index, columns = _detect_columns(frame)
    rows: list[ParsedFilingRow] = []
    for index in range(header_index + 1, len(frame.index)):
        values = [_cell_text(frame.iat[index, col]) for col in range(len(frame.columns))]
        major_text = values[columns["major"]]
        college_text = values[columns["college"]]
        if not major_text or not college_text:
            continue
        major_code, major_name = _split_code_name(major_text, code_length=2)
        college_code, college_name = _split_code_name(college_text, code_length=4)
        if not major_name or not college_name:
            continue
        category = values[columns["category"]] if "category" in columns else None
        plan_count = _parse_int(values[columns["plan"]]) if "plan" in columns else None
        min_score = _parse_decimal(values[columns["min_score"]]) if "min_score" in columns else None
        min_rank = _parse_int(values[columns["min_rank"]]) if "min_rank" in columns else None
        if min_score is None and min_rank is None:
            continue
        rows.append(
            ParsedFilingRow(
                row_number=index + 1,
                category=category,
                college_code=college_code,
                college_name=college_name,
                major_code=major_code,
                major_name=major_name,
                plan_count=plan_count,
                min_score=min_score,
                min_rank=min_rank,
            )
        )
    if not rows:
        raise ValueError(f"no filing rows parsed from {file_path}")
    return rows


def _detect_columns(frame: pd.DataFrame) -> tuple[int, dict[str, int]]:
    for index in range(min(len(frame.index), 20)):
        values = [_cell_text(frame.iat[index, col]) for col in range(len(frame.columns))]
        joined = "|".join(values)
        if "专业" not in joined or "院校" not in joined:
            continue
        columns: dict[str, int] = {}
        for col, value in enumerate(values):
            if "专业类别" in value:
                columns["category"] = col
            elif "专业" in value and "代号" in value:
                columns["major"] = col
            elif "院校" in value and "代号" in value:
                columns["college"] = col
            elif "计划" in value:
                columns["plan"] = col
            elif "最低位次" in value:
                columns["min_rank"] = col
            elif "最低分" in value or "投档最低分" in value or "最低综合分" in value:
                columns["min_score"] = col
        if {"major", "college"} <= columns.keys() and ({"min_score", "min_rank"} & columns.keys()):
            return index, columns
    raise ValueError("cannot detect filing table header")


def _upsert_attachment_source_document(conn: sqlite3.Connection, attachment: Attachment) -> int:
    now = _now_text()
    existing = conn.execute(
        """
        SELECT id FROM gaokao_source_document
        WHERE province = '山东'
          AND year = ?
          AND source_type = ?
          AND url = ?
        LIMIT 1
        """,
        (attachment.page.year, attachment.page.source_type, attachment.file_url),
    ).fetchone()
    payload = (
        attachment.page.year,
        attachment.page.source_type,
        attachment.title,
        attachment.file_url,
        "山东省教育招生考试院",
        "sdzk",
        attachment.page.published_at,
        now,
        _relative_path(attachment.file_path),
        _sha256_file(attachment.file_path),
        IMPORTER_NAME,
        "2026-04-27",
        "file_ready",
        f"第六轮官方投档附件；来源页面：{attachment.page.page_url}。投档情况表只写 raw，不写应用侧录取结论。",
        now,
    )
    if existing:
        conn.execute(
            """
            UPDATE gaokao_source_document
            SET title = ?, official_org = ?, source_registry_code = ?,
                published_at = ?, fetched_at = ?, local_file_path = ?,
                file_sha256 = ?, parser_name = ?, parser_version = ?,
                status = ?, note = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                attachment.title,
                "山东省教育招生考试院",
                "sdzk",
                attachment.page.published_at,
                now,
                _relative_path(attachment.file_path),
                _sha256_file(attachment.file_path),
                IMPORTER_NAME,
                "2026-04-27",
                "file_ready",
                f"第六轮官方投档附件；来源页面：{attachment.page.page_url}。投档情况表只写 raw，不写应用侧录取结论。",
                now,
                int(existing["id"]),
            ),
        )
        return int(existing["id"])
    cursor = conn.execute(
        """
        INSERT INTO gaokao_source_document (
            province, year, source_type, title, url, official_org,
            source_registry_code, published_at, fetched_at, local_file_path,
            file_sha256, parser_name, parser_version, status, note, updated_at
        ) VALUES ('山东', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        payload,
    )
    return int(cursor.lastrowid)


def _create_import_run(conn: sqlite3.Connection, source_document_id: int, attachment: Attachment) -> int:
    now = _now_text()
    cursor = conn.execute(
        """
        INSERT INTO gaokao_import_run (
            source_document_id, importer_name, started_at, status, raw_snapshot_path, note, updated_at
        ) VALUES (?, ?, ?, 'running', ?, ?, ?)
        """,
        (
            source_document_id,
            IMPORTER_NAME,
            now,
            _relative_path(attachment.file_path),
            "第六轮特殊类型投档表 raw 导入。",
            now,
        ),
    )
    return int(cursor.lastrowid)


def _replace_raw_rows(conn: sqlite3.Connection, attachment: Attachment, rows: list[ParsedFilingRow]) -> int:
    assert attachment.source_document_id is not None
    assert attachment.import_run_id is not None
    conn.execute(
        "DELETE FROM gaokao_admission_result WHERE source_document_id = ? AND parser_script_name = ?",
        (attachment.source_document_id, IMPORTER_NAME),
    )
    now = _now_text()
    page = attachment.page
    candidate_type = _candidate_type(page.source_type)
    batch_name = _batch_name(page.title)
    payload_rows = []
    for row in rows:
        remark = _row_remark(page, row)
        source_hash = _hash_text(
            f"{attachment.file_url}|{row.category}|{row.college_code}|{row.major_code}|"
            f"{row.major_name}|{row.plan_count}|{row.min_score}|{row.min_rank}"
        )
        payload_rows.append(
            (
                "sd",
                page.year,
                candidate_type,
                batch_name,
                "1",
                None,
                row.college_code,
                row.college_name,
                None,
                row.major_code,
                row.major_name,
                _decimal_to_float(row.min_score),
                row.min_rank,
                None,
                None,
                None,
                row.plan_count,
                row.plan_count,
                str(row.min_rank) if row.min_rank is not None else None,
                remark,
                now,
                now,
                "official",
                attachment.title,
                page.page_url,
                _relative_path(attachment.file_path),
                IMPORTER_NAME,
                page.published_at,
                "confirmed_official_public",
                source_hash,
                DATA_VERSION_LABEL,
                None,
                attachment.source_document_id,
                attachment.import_run_id,
            )
        )
    conn.executemany(
        """
        INSERT INTO gaokao_admission_result (
            province, year, candidate_type, batch_name, round_no,
            college_id, college_code_snapshot, college_name_snapshot,
            major_id, major_code_snapshot, major_name_snapshot,
            min_score, min_rank, avg_score, max_score, control_line,
            plan_count, actual_filed_count, original_min_rank_text, remark,
            created_at, updated_at, source_level, source_title, source_url,
            local_source_path, parser_script_name, published_at, review_status,
            source_record_hash, data_version_label, import_batch_id,
            source_document_id, import_run_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        payload_rows,
    )
    return len(payload_rows)


def _finish_import_run(
    conn: sqlite3.Connection,
    import_run_id: int,
    source_document_id: int,
    attachment: Attachment,
    total_rows: int,
    raw_created: int,
) -> None:
    now = _now_text()
    conn.execute(
        """
        UPDATE gaokao_import_run
        SET finished_at = ?, status = 'success', total_rows = ?,
            success_rows = ?, failed_rows = 0, skipped_rows = 0,
            created_rows = ?, updated_rows = 0, raw_snapshot_path = ?,
            note = ?, updated_at = ?
        WHERE id = ?
        """,
        (
            now,
            total_rows,
            raw_created,
            raw_created,
            _relative_path(attachment.file_path),
            f"第六轮专项导入：特殊类型投档 raw {raw_created} 条；未写应用侧 admission_record。",
            now,
            import_run_id,
        ),
    )
    conn.execute(
        "UPDATE gaokao_source_document SET status = 'imported', updated_at = ? WHERE id = ?",
        (now, source_document_id),
    )


def _build_coverage(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT year, candidate_type, batch_name, COUNT(*) AS total
        FROM gaokao_admission_result
        WHERE year BETWEEN 2023 AND 2025
        GROUP BY year, candidate_type, batch_name
        ORDER BY year, candidate_type, batch_name
        """
    ).fetchall()
    return [dict(row) for row in rows]


def _write_report(report_path: Path, payload: dict[str, Any]) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# 第六轮特殊类型投档表导入结果",
        "",
        f"- 生成时间：{payload['generated_at']}",
        "- 数据范围：山东省 2023-2025 年艺术类、体育类、春季高考投档情况表官方附件。",
        "- 写库边界：投档情况表只写 `gaokao_admission_result` raw 表和导入审计，不写 `admission_record`，避免把投档最低分包装成最终录取结果。",
        "",
        "## 1. 执行摘要",
        "",
        f"- 已登记投档来源页面：{payload['registered_pages']} 个",
        f"- 成功解析附件：{payload['imported_files']} 个",
        f"- raw 新增记录：{payload['raw_created']} 条",
        f"- 应用侧录取结果新增：{payload['application_created']} 条",
        f"- 失败或待人工处理：{len(payload['failures'])} 项",
        "",
    ]
    if payload.get("backup_path"):
        lines.append(f"- 写库前备份：`{payload['backup_path']}`")
        lines.append("")

    lines.extend(["## 2. 已导入附件", "", "| 年份 | 类型 | 附件 | raw 行数 | 口径 | 本地文件 |", "| --- | --- | --- | ---: | --- | --- |"])
    if payload["items"]:
        for item in payload["items"]:
            lines.append(
                f"| {item['year']} | {item['candidate_type']} | {item['title']} | "
                f"{item['raw_created']} | {item['metric']} | `{item['local_file_path']}` |"
            )
    else:
        lines.append("| - | - | 本次没有成功导入附件 | 0 | - | - |")

    lines.extend(["", "## 3. 失败或待处理清单", "", "| 年份 | 类型 | 来源/附件 | URL | 原因 |", "| --- | --- | --- | --- | --- |"])
    if payload["failures"]:
        for failure in payload["failures"]:
            lines.append(
                f"| {failure.get('year', '-')} | {failure.get('source_type', '-')} | "
                f"{failure.get('title', '-')} | {failure.get('url', '-')} | {failure.get('reason', '-')} |"
            )
    else:
        lines.append("| - | - | 无 | - | - |")

    lines.extend(["", "## 4. 当前 raw 覆盖", "", "| 年份 | 类型 | 批次 | raw 行数 |", "| --- | --- | --- | ---: |"])
    for row in payload["coverage"]:
        lines.append(f"| {row['year']} | {row['candidate_type']} | {row['batch_name']} | {row['total']} |")

    lines.extend(
        [
            "",
            "## 5. 后续边界",
            "",
            "1. 若本机无法访问 `sdzk.cn/Floadup`，需在网络恢复后复跑本脚本，或把官方附件放入 `data/imports/gaokao/official/{year}/` 后加 `--no-download` 复跑。",
            "2. 2023/2024 艺术、体育、春考若仍只找到投档表而未找到录取情况表，不能关闭“专门录取结果缺口”。",
            "3. 单独招生、综合评价招生缺专门录取结果的风险边界不因本脚本改变。",
        ]
    )
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _candidate_type(source_type: str) -> str:
    if source_type.startswith("art"):
        return "艺术类"
    if source_type.startswith("sports"):
        return "体育类"
    if source_type.startswith("spring_exam"):
        return "春季高考"
    return source_type


def _batch_name(title: str) -> str:
    if "春季高考本科" in title:
        return "春季高考本科批"
    if "春季高考专科" in title:
        return "春季高考专科批"
    if "体育" in title:
        return "体育类常规批"
    if "艺术" in title and "专科" in title:
        return "艺术类专科批"
    if "艺术" in title:
        return "艺术类本科批"
    return "特殊类型批"


def _row_remark(page: FilingPage, row: ParsedFilingRow) -> str:
    details = ["投档情况表"]
    if row.category:
        details.append(f"类别：{row.category}")
    if row.plan_count is not None:
        details.append(f"投档计划数：{row.plan_count}")
    if row.min_score is not None:
        details.append("最低分按官方投档综合分口径")
    if row.min_rank is not None:
        details.append("最低位次按官方专业类别口径")
    details.append("非最终录取情况")
    return "；".join(details)


def _metric_label(rows: list[ParsedFilingRow]) -> str:
    has_score = any(row.min_score is not None for row in rows)
    has_rank = any(row.min_rank is not None for row in rows)
    if has_score and has_rank:
        return "最低分/最低位次"
    if has_score:
        return "投档最低分/综合分"
    if has_rank:
        return "最低位次"
    return "未知"


def _cell_text(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if text.lower() == "nan":
        return ""
    return re.sub(r"\s+", "", text)


def _split_code_name(value: str, *, code_length: int) -> tuple[str | None, str]:
    text = value.strip()
    if len(text) > code_length:
        code = text[:code_length].strip()
        name = text[code_length:].strip()
        if re.fullmatch(r"[A-Za-z0-9]+", code) and name:
            return code, name
    match = re.match(r"^([A-Za-z0-9]+)(.+)$", text)
    if match:
        return match.group(1), match.group(2).strip()
    return None, text


def _parse_decimal(value: str) -> Decimal | None:
    text = value.strip()
    if not text:
        return None
    try:
        return Decimal(text)
    except InvalidOperation:
        return None


def _parse_int(value: str) -> int | None:
    number = _parse_decimal(value)
    return int(number) if number is not None else None


def _decimal_to_float(value: Decimal | None) -> float | None:
    return float(value) if value is not None else None


def _require_tables(conn: sqlite3.Connection) -> None:
    required = {"gaokao_source_document", "gaokao_import_run", "gaokao_admission_result"}
    existing = {
        row["name"]
        for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
    }
    missing = required - existing
    if missing:
        raise RuntimeError(f"missing required tables: {', '.join(sorted(missing))}")


def _safe_filename(value: str) -> str:
    text = re.sub(r"[^\w\u4e00-\u9fff().-]+", "_", value.strip(), flags=re.U)
    return text.strip("._")[:150] or "gaokao_source"


def _title_from_path(path: Path) -> str:
    name = path.stem
    return re.sub(r"^\d{4}_", "", name)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file_obj:
        for chunk in iter(lambda: file_obj.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _hash_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _relative_path(path: Path | None) -> str | None:
    if path is None:
        return None
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def _now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _backup_database(source_path: Path, backup_dir: Path) -> Path:
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup_path = backup_dir / f"{source_path.stem}_before_round6_special_filing_import_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    shutil.copy2(source_path, backup_path)
    return backup_path


def _failure(page: FilingPage, url: str, reason: str, *, title: str | None = None) -> dict[str, Any]:
    return {
        "year": page.year,
        "source_type": page.source_type,
        "title": title or page.title,
        "url": url,
        "reason": reason,
    }


if __name__ == "__main__":
    raise SystemExit(main())
