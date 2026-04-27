#!/usr/bin/env python3
from __future__ import annotations

import argparse
import concurrent.futures
import json
import socket
import sqlite3
import ssl
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = REPO_ROOT / "data" / "app.db"
DEFAULT_BACKUP_DIR = REPO_ROOT / "data" / "backups"
DEFAULT_REPORT_PATH = REPO_ROOT / "docs" / "round5-chapter-machine-preaudit.md"
USER_AGENT = "local-edu-tool-round5-chapter-preaudit/2026-04-27"

PENDING_REVIEW_STATUSES = {
    "pending_manual_review",
    "pending_manual_review_with_official_candidate",
}


@dataclass(frozen=True)
class ChapterCandidate:
    id: int
    college_name: str
    review_status: str
    fallback_url: str
    fallback_source_type: str | None
    fallback_note: str | None


@dataclass(frozen=True)
class UrlCheckResult:
    id: int
    status: str
    status_label: str
    http_status: int | None
    final_url: str | None
    error: str | None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a conservative machine preaudit for gaokao college chapter fallback URLs.")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH, help="SQLite app database path.")
    parser.add_argument("--backup-dir", type=Path, default=DEFAULT_BACKUP_DIR, help="Directory for DB backups.")
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT_PATH, help="Markdown audit report path.")
    parser.add_argument("--limit", type=int, default=80, help="Maximum records to preaudit.")
    parser.add_argument("--timeout", type=float, default=4.0, help="Per URL timeout seconds.")
    parser.add_argument("--workers", type=int, default=8, help="Concurrent URL checks.")
    parser.add_argument("--no-backup", action="store_true", help="Skip database backup.")
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
        candidates = _load_candidates(conn, limit=args.limit)
        results = _check_candidates(candidates, timeout=args.timeout, workers=args.workers)
        payload = _apply_results(conn, candidates, results)
        payload["backup_path"] = str(backup_path) if backup_path else None
        payload["report_path"] = str(args.report)

    _write_report(args.report, payload)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    print(f"章程候选链接机器预审完成：处理 {payload['checked']} 条，报告 {args.report}。")
    if backup_path:
        print(f"备份：{backup_path}")
    return 0


def _load_candidates(conn: sqlite3.Connection, *, limit: int) -> list[ChapterCandidate]:
    rows = conn.execute(
        """
        SELECT
            id,
            COALESCE(college_name_snapshot, '') AS college_name,
            COALESCE(review_status, '') AS review_status,
            COALESCE(chapter_fallback_url, '') AS fallback_url,
            chapter_fallback_source_type,
            chapter_fallback_note
        FROM gaokao_college_chapter_rule
        WHERE review_status IN ('pending_manual_review', 'pending_manual_review_with_official_candidate')
          AND COALESCE(chapter_fallback_url, '') <> ''
          AND COALESCE(chapter_fallback_verification_status, '') NOT LIKE 'round5_machine_%'
        ORDER BY
            CASE
                WHEN chapter_fallback_source_type LIKE '%recruit%' THEN 0
                WHEN chapter_fallback_source_type LIKE '%official%' THEN 1
                ELSE 2
            END,
            id
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    return [
        ChapterCandidate(
            id=int(row["id"]),
            college_name=str(row["college_name"]),
            review_status=str(row["review_status"]),
            fallback_url=str(row["fallback_url"]),
            fallback_source_type=row["chapter_fallback_source_type"],
            fallback_note=row["chapter_fallback_note"],
        )
        for row in rows
    ]


def _check_candidates(candidates: list[ChapterCandidate], *, timeout: float, workers: int) -> list[UrlCheckResult]:
    if not candidates:
        return []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, workers)) as executor:
        futures = [executor.submit(_check_url, candidate, timeout) for candidate in candidates]
        return [future.result() for future in concurrent.futures.as_completed(futures)]


def _check_url(candidate: ChapterCandidate, timeout: float) -> UrlCheckResult:
    url = candidate.fallback_url.strip()
    if not url.startswith(("http://", "https://")):
        return UrlCheckResult(candidate.id, "round5_machine_invalid_url", "URL 格式无效", None, None, "invalid url")
    try:
        return _request_url(candidate.id, url, timeout=timeout, method="HEAD")
    except urllib.error.HTTPError as exc:
        if exc.code in {403, 405}:
            try:
                return _request_url(candidate.id, url, timeout=timeout, method="GET")
            except Exception as fallback_exc:  # noqa: BLE001 - report-only network probe
                return _result_from_exception(candidate.id, fallback_exc)
        return _result_from_http_error(candidate.id, exc)
    except Exception as exc:  # noqa: BLE001 - report-only network probe
        return _result_from_exception(candidate.id, exc)


def _request_url(id_: int, url: str, *, timeout: float, method: str) -> UrlCheckResult:
    request = urllib.request.Request(url, method=method, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        status = int(response.status)
        return _result_from_status(id_, status, response.geturl())


def _result_from_status(id_: int, status: int, final_url: str | None) -> UrlCheckResult:
    if 200 <= status < 400:
        return UrlCheckResult(id_, "round5_machine_reachable", "可访问", status, final_url, None)
    if status in {401, 403}:
        return UrlCheckResult(id_, "round5_machine_restricted", "访问受限但站点存在", status, final_url, None)
    if status == 404:
        return UrlCheckResult(id_, "round5_machine_not_found", "页面不存在", status, final_url, None)
    return UrlCheckResult(id_, f"round5_machine_http_{status}", f"HTTP {status}", status, final_url, None)


def _result_from_http_error(id_: int, exc: urllib.error.HTTPError) -> UrlCheckResult:
    return _result_from_status(id_, int(exc.code), exc.url)


def _result_from_exception(id_: int, exc: Exception) -> UrlCheckResult:
    if isinstance(exc, TimeoutError) or isinstance(exc, socket.timeout):
        return UrlCheckResult(id_, "round5_machine_timeout", "访问超时", None, None, str(exc))
    if isinstance(exc, urllib.error.URLError) and isinstance(exc.reason, TimeoutError | socket.timeout):
        return UrlCheckResult(id_, "round5_machine_timeout", "访问超时", None, None, str(exc))
    if isinstance(exc, ssl.SSLError):
        return UrlCheckResult(id_, "round5_machine_ssl_error", "SSL 错误", None, None, str(exc))
    return UrlCheckResult(id_, "round5_machine_error", "访问异常", None, None, str(exc))


def _apply_results(
    conn: sqlite3.Connection,
    candidates: list[ChapterCandidate],
    results: list[UrlCheckResult],
) -> dict[str, Any]:
    result_by_id = {result.id: result for result in results}
    now = _now_text()
    items: list[dict[str, Any]] = []
    status_counts: dict[str, int] = {}
    for candidate in candidates:
        result = result_by_id.get(candidate.id)
        if result is None:
            continue
        status_counts[result.status] = status_counts.get(result.status, 0) + 1
        note = _append_machine_note(candidate.fallback_note, result)
        conn.execute(
            """
            UPDATE gaokao_college_chapter_rule
            SET chapter_fallback_verification_status = ?,
                chapter_fallback_note = ?,
                updated_at = ?
            WHERE id = ?
            """,
            (result.status, note, now, candidate.id),
        )
        items.append(
            {
                "id": candidate.id,
                "college_name": candidate.college_name,
                "review_status": candidate.review_status,
                "fallback_url": candidate.fallback_url,
                "fallback_source_type": candidate.fallback_source_type,
                "machine_status": result.status,
                "machine_status_label": result.status_label,
                "http_status": result.http_status,
                "final_url": result.final_url,
                "error": result.error,
            }
        )
    conn.commit()
    return {
        "generated_at": now,
        "checked": len(items),
        "status_counts": status_counts,
        "items": sorted(items, key=lambda item: item["id"]),
        "boundary": "机器预审只记录候选链接连通性，不把待人工复核项改为人工已确认。",
    }


def _append_machine_note(existing_note: str | None, result: UrlCheckResult) -> str:
    machine_note = (
        f"Round5 machine preaudit {datetime.now().strftime('%Y-%m-%d')}: "
        f"{result.status_label}"
    )
    if result.http_status is not None:
        machine_note += f", HTTP {result.http_status}"
    if result.final_url and result.final_url != "":
        machine_note += f", final_url={result.final_url}"
    if result.error:
        machine_note += f", error={result.error[:180]}"
    existing = (existing_note or "").strip()
    if not existing:
        return machine_note
    return f"{existing}\n{machine_note}"


def _write_report(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# 第五轮章程限制链机器预审",
        "",
        f"- 生成时间：{payload['generated_at']}",
        "- 主库：`data/app.db`",
        "- 边界：机器预审只记录候选链接连通性，不把待人工复核项改为人工已确认。",
        "",
        "## 1. 汇总",
        "",
        f"- 本批处理：{payload['checked']} 条",
    ]
    for status, count in sorted(payload["status_counts"].items()):
        lines.append(f"- `{status}`：{count} 条")
    lines.extend(
        [
            "",
            "## 2. 明细",
            "",
            "| ID | 院校 | 原状态 | 候选来源 | 机器状态 | HTTP | 候选链接 |",
            "| ---: | --- | --- | --- | --- | ---: | --- |",
        ]
    )
    for item in payload["items"]:
        http_status = item["http_status"] if item["http_status"] is not None else ""
        url = str(item["fallback_url"]).replace("|", "%7C")
        lines.append(
            f"| {item['id']} | {item['college_name']} | `{item['review_status']}` | "
            f"`{item['fallback_source_type'] or ''}` | `{item['machine_status']}` | "
            f"{http_status} | {url} |"
        )
    lines.extend(
        [
            "",
            "## 3. 后续建议",
            "",
            "1. 对 `round5_machine_reachable` 的记录，下一步仍需人工打开页面并确认是否为招生章程或招生官网入口。",
            "2. 对超时、SSL 错误或访问异常的记录，不应改为已确认；可在网络环境更稳定时复跑本脚本。",
            "3. 只有找到明确招生章程页面、PDF 或高校招生网对应章程栏目后，才能进入人工确认状态。",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def _backup_database(source_path: Path, backup_dir: Path) -> Path:
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup_path = backup_dir / f"{source_path.stem}_before_round5_chapter_machine_preaudit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    with sqlite3.connect(str(source_path)) as source_conn, sqlite3.connect(str(backup_path)) as backup_conn:
        source_conn.backup(backup_conn)
    return backup_path


def _now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


if __name__ == "__main__":
    raise SystemExit(main())
