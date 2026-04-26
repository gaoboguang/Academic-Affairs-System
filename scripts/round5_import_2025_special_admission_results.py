#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
import sys
import urllib.request
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = REPO_ROOT / "data" / "app.db"
DEFAULT_BACKUP_DIR = REPO_ROOT / "data" / "backups"
DEFAULT_IMPORT_DIR = REPO_ROOT / "data" / "imports" / "gaokao" / "official" / "2025"
IMPORTER_NAME = "round5_import_2025_special_admission_results"
DATA_VERSION_LABEL = "round5_special_admission_20260426"
USER_AGENT = "local-edu-tool-round5-special-admission/2026-04-26"


@dataclass(frozen=True)
class AttachmentSource:
    source_type: str
    title: str
    page_url: str
    file_url: str
    published_at: date
    candidate_type: str
    student_type: str
    batch_name: str
    art_track: str | None
    metric: str
    note: str


ATTACHMENTS: tuple[AttachmentSource, ...] = (
    AttachmentSource(
        "art_admission_min_score",
        "山东省2025年艺术类本科批美术与设计类第1次志愿录取情况表",
        "https://www.sdzk.cn/NewsInfo.aspx?NewsID=6989",
        "https://www.sdzk.cn/Floadup/file/20250719/6388854557531257877974041.xls",
        date(2025, 7, 19),
        "艺术类",
        "art",
        "艺术类本科批",
        "美术与设计类",
        "min_score",
        "第五轮官方附件；录取最低分为综合分。",
    ),
    AttachmentSource(
        "art_admission_min_score",
        "山东省2025年艺术类本科批书法类第1次志愿录取情况表",
        "https://www.sdzk.cn/NewsInfo.aspx?NewsID=6989",
        "https://www.sdzk.cn/Floadup/file/20250719/6388854558090382302998910.xls",
        date(2025, 7, 19),
        "艺术类",
        "art",
        "艺术类本科批",
        "书法类",
        "min_score",
        "第五轮官方附件；录取最低分为综合分。",
    ),
    AttachmentSource(
        "art_admission_min_score",
        "山东省2025年艺术类本科批舞蹈类第1次志愿录取情况表",
        "https://www.sdzk.cn/NewsInfo.aspx?NewsID=6989",
        "https://www.sdzk.cn/Floadup/file/20250719/6388854558624905031566821.xls",
        date(2025, 7, 19),
        "艺术类",
        "art",
        "艺术类本科批",
        "舞蹈类",
        "min_score",
        "第五轮官方附件；录取最低分为综合分。",
    ),
    AttachmentSource(
        "art_admission_min_score",
        "山东省2025年艺术类本科批音乐类第1次志愿录取情况表",
        "https://www.sdzk.cn/NewsInfo.aspx?NewsID=6989",
        "https://www.sdzk.cn/Floadup/file/20250719/6388854560378105457310468.xls",
        date(2025, 7, 19),
        "艺术类",
        "art",
        "艺术类本科批",
        "音乐类",
        "min_score",
        "第五轮官方附件；录取最低分为综合分。",
    ),
    AttachmentSource(
        "art_admission_min_score",
        "山东省2025年艺术类本科批播音与主持类第1次志愿录取情况表",
        "https://www.sdzk.cn/NewsInfo.aspx?NewsID=6989",
        "https://www.sdzk.cn/Floadup/file/20250719/6388854560926405457134275.xls",
        date(2025, 7, 19),
        "艺术类",
        "art",
        "艺术类本科批",
        "播音与主持类",
        "min_score",
        "第五轮官方附件；录取最低分为综合分。",
    ),
    AttachmentSource(
        "art_admission_min_score",
        "山东省2025年艺术类本科批表导演类第1次志愿录取情况表",
        "https://www.sdzk.cn/NewsInfo.aspx?NewsID=6989",
        "https://www.sdzk.cn/Floadup/file/20250719/6388854561478148244416573.xls",
        date(2025, 7, 19),
        "艺术类",
        "art",
        "艺术类本科批",
        "表导演类",
        "min_score",
        "第五轮官方附件；录取最低分为综合分。",
    ),
    AttachmentSource(
        "sports_admission_min_score",
        "山东省2025年体育类常规批第1次志愿录取情况表",
        "https://www.sdzk.cn/NewsInfo.aspx?NewsID=6987",
        "https://www.sdzk.cn/Floadup/file/20250719/6388854553462400418705216.xls",
        date(2025, 7, 19),
        "体育类",
        "sports",
        "体育类常规批",
        "sports",
        "min_score",
        "第五轮官方附件；录取最低分为综合分。",
    ),
    AttachmentSource(
        "spring_exam_admission_min_score",
        "山东省2025年春季高考本科批第1次志愿录取情况表",
        "https://www.sdzk.cn/NewsInfo.aspx?NewsID=6988",
        "https://www.sdzk.cn/Floadup/file/20250719/6388854551287224941949963.xls",
        date(2025, 7, 19),
        "春季高考",
        "spring_exam",
        "春季高考本科批",
        None,
        "min_rank",
        "第五轮官方附件；录取最低位次按春季高考专业类别口径解释。",
    ),
)


@dataclass(frozen=True)
class ParsedSpecialAdmissionRow:
    row_number: int
    category: str | None
    college_code: str | None
    college_name: str
    major_code: str | None
    major_name: str
    min_score: Decimal | None
    min_rank: int | None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import 2025 Shandong art/sports/spring admission result attachments.")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH, help="SQLite app database path.")
    parser.add_argument("--download-dir", type=Path, default=DEFAULT_IMPORT_DIR, help="Official file download directory.")
    parser.add_argument("--backup-dir", type=Path, default=DEFAULT_BACKUP_DIR, help="Directory for DB backups.")
    parser.add_argument("--no-download", action="store_true", help="Use existing local files only.")
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

    download_dir = args.download_dir.resolve()
    download_dir.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(str(db_path)) as conn:
        conn.row_factory = sqlite3.Row
        payload = import_special_admission_results(conn, download_dir, download_missing=not args.no_download)

    payload["backup_path"] = str(backup_path) if backup_path else None
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    print(
        "2025 艺术/体育/春考录取情况已导入："
        f"raw {payload['raw_created']} 条，应用侧匹配 {payload['app_created']} 条，"
        f"应用侧未匹配 {payload['app_skipped']} 条。"
    )
    if backup_path:
        print(f"备份：{backup_path}")
    return 0


def import_special_admission_results(
    conn: sqlite3.Connection,
    download_dir: Path,
    *,
    download_missing: bool,
) -> dict[str, Any]:
    _require_tables(conn)
    items: list[dict[str, Any]] = []
    total_raw_created = 0
    total_app_created = 0
    total_app_skipped = 0
    for source in ATTACHMENTS:
        file_path = _resolve_or_download(download_dir, source, download_missing=download_missing)
        source_document_id = _upsert_source_document(conn, source, file_path)
        import_run_id, import_run_created = _ensure_import_run(conn, source_document_id)
        rows = _parse_attachment(file_path, source)
        raw_created = _replace_raw_rows(conn, source, source_document_id, import_run_id, file_path, rows)
        app_created, app_skipped = _replace_application_rows(conn, source, source_document_id, import_run_id, rows)
        _finish_import_run(
            conn,
            import_run_id,
            source_document_id,
            file_path,
            total_rows=len(rows),
            raw_created=raw_created,
            app_created=app_created,
            app_skipped=app_skipped,
        )
        total_raw_created += raw_created
        total_app_created += app_created
        total_app_skipped += app_skipped
        items.append(
            {
                "source_document_id": source_document_id,
                "import_run_id": import_run_id,
                "import_run_created": import_run_created,
                "title": source.title,
                "candidate_type": source.candidate_type,
                "art_track": source.art_track,
                "local_file_path": _relative_path(file_path),
                "file_sha256": _sha256_file(file_path),
                "parsed_rows": len(rows),
                "raw_created": raw_created,
                "app_created": app_created,
                "app_skipped": app_skipped,
            }
        )
    conn.commit()
    return {
        "items": items,
        "raw_created": total_raw_created,
        "app_created": total_app_created,
        "app_skipped": total_app_skipped,
        "source_document_total": _count_rows(conn, "gaokao_source_document"),
        "import_run_total": _count_rows(conn, "gaokao_import_run"),
    }


def _resolve_or_download(download_dir: Path, source: AttachmentSource, *, download_missing: bool) -> Path:
    target = download_dir / f"2025_{_safe_filename(source.title)}.xls"
    if target.exists():
        return target
    if not download_missing:
        raise FileNotFoundError(f"missing local official file: {target}")
    request = urllib.request.Request(source.file_url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=60) as response:
        target.write_bytes(response.read())
    return target


def _upsert_source_document(conn: sqlite3.Connection, source: AttachmentSource, file_path: Path) -> int:
    now = _now_text()
    existing = conn.execute(
        """
        SELECT id FROM gaokao_source_document
        WHERE province = '山东'
          AND year = 2025
          AND source_type = ?
          AND url = ?
        LIMIT 1
        """,
        (source.source_type, source.file_url),
    ).fetchone()
    payload = {
        "province": "山东",
        "year": 2025,
        "source_type": source.source_type,
        "title": source.title,
        "url": source.file_url,
        "official_org": "山东省教育招生考试院",
        "source_registry_code": "sdzk",
        "published_at": source.published_at.isoformat(),
        "fetched_at": now,
        "local_file_path": _relative_path(file_path),
        "file_sha256": _sha256_file(file_path),
        "parser_name": IMPORTER_NAME,
        "parser_version": "2026-04-26",
        "status": "file_ready",
        "note": f"{source.note} 来源页面：{source.page_url}",
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


def _ensure_import_run(conn: sqlite3.Connection, source_document_id: int) -> tuple[int, bool]:
    existing = conn.execute(
        """
        SELECT id FROM gaokao_import_run
        WHERE source_document_id = ?
          AND importer_name = ?
          AND status = 'success'
        ORDER BY id
        LIMIT 1
        """,
        (source_document_id, IMPORTER_NAME),
    ).fetchone()
    if existing:
        return int(existing["id"]), False
    now = _now_text()
    conn.execute(
        """
        INSERT INTO gaokao_import_run (
            source_document_id, importer_name, started_at, finished_at, status,
            total_rows, success_rows, failed_rows, skipped_rows, created_rows,
            updated_rows, raw_snapshot_path, note, created_at, updated_at, is_active
        ) VALUES (?, ?, ?, ?, 'pending', 0, 0, 0, 0, 0, 0, NULL, NULL, ?, ?, 1)
        """,
        (source_document_id, IMPORTER_NAME, now, now, now, now),
    )
    return int(conn.execute("SELECT last_insert_rowid()").fetchone()[0]), True


def _parse_attachment(file_path: Path, source: AttachmentSource) -> list[ParsedSpecialAdmissionRow]:
    df = pd.read_excel(file_path, header=None, dtype=str).fillna("")
    rows: list[ParsedSpecialAdmissionRow] = []
    for index, record in df.iloc[2:].iterrows():
        values = [str(value).strip() for value in record.tolist()]
        if source.metric == "min_score":
            if len(values) < 4 or not values[1] or not values[2] or not values[3]:
                continue
            major_code, major_name = _split_code_name(values[1], code_length=2)
            college_code, college_name = _split_code_name(values[2], code_length=4)
            min_score = _parse_decimal(values[3])
            if min_score is None:
                continue
            rows.append(
                ParsedSpecialAdmissionRow(
                    row_number=int(index) + 1,
                    category=source.art_track,
                    college_code=college_code,
                    college_name=college_name,
                    major_code=major_code,
                    major_name=major_name,
                    min_score=min_score,
                    min_rank=None,
                )
            )
        else:
            if len(values) < 5 or not values[1] or not values[2] or not values[3] or not values[4]:
                continue
            major_code, major_name = _split_code_name(values[2], code_length=2)
            college_code, college_name = _split_code_name(values[3], code_length=4)
            min_rank = _parse_int(values[4])
            if min_rank is None:
                continue
            rows.append(
                ParsedSpecialAdmissionRow(
                    row_number=int(index) + 1,
                    category=values[1],
                    college_code=college_code,
                    college_name=college_name,
                    major_code=major_code,
                    major_name=major_name,
                    min_score=None,
                    min_rank=min_rank,
                )
            )
    if not rows:
        raise ValueError(f"no rows parsed from {file_path}")
    return rows


def _replace_raw_rows(
    conn: sqlite3.Connection,
    source: AttachmentSource,
    source_document_id: int,
    import_run_id: int,
    file_path: Path,
    rows: list[ParsedSpecialAdmissionRow],
) -> int:
    conn.execute(
        "DELETE FROM gaokao_admission_result WHERE source_document_id = ? AND parser_script_name = ?",
        (source_document_id, IMPORTER_NAME),
    )
    now = _now_text()
    payload_rows = []
    for row in rows:
        remark = _row_remark(source, row)
        payload_rows.append(
            (
                "sd",
                2025,
                source.candidate_type,
                source.batch_name,
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
                None,
                None,
                str(row.min_rank) if row.min_rank is not None else None,
                remark,
                now,
                now,
                "official",
                source.title,
                source.page_url,
                _relative_path(file_path),
                IMPORTER_NAME,
                source.published_at.isoformat(),
                "confirmed_official_public",
                _hash_text(f"{source.file_url}|{row.college_code}|{row.major_code}|{row.major_name}|{row.min_score}|{row.min_rank}|{row.category}"),
                DATA_VERSION_LABEL,
                None,
                source_document_id,
                import_run_id,
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


def _replace_application_rows(
    conn: sqlite3.Connection,
    source: AttachmentSource,
    source_document_id: int,
    import_run_id: int,
    rows: list[ParsedSpecialAdmissionRow],
) -> tuple[int, int]:
    conn.execute("DELETE FROM admission_record WHERE source_document_id = ? AND import_run_id = ?", (source_document_id, import_run_id))
    now = _now_text()
    created = 0
    skipped = 0
    seen_keys: set[tuple[int, int, str | None]] = set()
    for row in rows:
        college_id = _find_college_id(conn, row.college_name)
        if college_id is None:
            skipped += 1
            continue
        major_id = _find_major_id(conn, row.major_name)
        if major_id is None:
            skipped += 1
            continue
        key = (college_id, major_id, row.category or source.art_track)
        if key in seen_keys:
            skipped += 1
            continue
        seen_keys.add(key)
        try:
            conn.execute(
                """
                INSERT INTO admission_record (
                    year, province, batch, college_id, major_id, student_type,
                    art_track, subject_requirement, min_score, min_rank, avg_score,
                    max_score, plan_count, source_note, created_at, updated_at,
                    is_active, source_document_id, import_run_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, NULL, ?, ?, NULL, NULL, NULL, ?, ?, ?, 1, ?, ?)
                """,
                (
                    2025,
                    "山东",
                    source.batch_name,
                    college_id,
                    major_id,
                    source.student_type,
                    row.category or source.art_track,
                    _decimal_to_float(row.min_score),
                    row.min_rank,
                    _row_remark(source, row),
                    now,
                    now,
                    source_document_id,
                    import_run_id,
                ),
            )
        except sqlite3.IntegrityError:
            skipped += 1
            continue
        created += 1
    return created, skipped


def _finish_import_run(
    conn: sqlite3.Connection,
    import_run_id: int,
    source_document_id: int,
    file_path: Path,
    *,
    total_rows: int,
    raw_created: int,
    app_created: int,
    app_skipped: int,
) -> None:
    now = _now_text()
    conn.execute(
        """
        UPDATE gaokao_import_run
        SET finished_at = ?,
            status = 'success',
            total_rows = ?,
            success_rows = ?,
            failed_rows = 0,
            skipped_rows = ?,
            created_rows = ?,
            updated_rows = 0,
            raw_snapshot_path = ?,
            note = ?,
            updated_at = ?
        WHERE id = ?
        """,
        (
            now,
            total_rows,
            raw_created,
            app_skipped,
            raw_created + app_created,
            _relative_path(file_path),
            f"第五轮专项导入：raw 专门录取结果 {raw_created} 条；应用侧可靠匹配 {app_created} 条，未匹配 {app_skipped} 条。",
            now,
            import_run_id,
        ),
    )
    conn.execute(
        "UPDATE gaokao_source_document SET status = 'imported', updated_at = ? WHERE id = ?",
        (now, source_document_id),
    )


def _row_remark(source: AttachmentSource, row: ParsedSpecialAdmissionRow) -> str:
    details = []
    if row.category:
        details.append(f"类别：{row.category}")
    details.append("录取最低分为综合分" if source.metric == "min_score" else "录取最低位次按专业类别口径")
    return "；".join(details)


def _find_college_id(conn: sqlite3.Connection, college_name: str) -> int | None:
    row = conn.execute("SELECT id FROM college WHERE name = ? AND is_active = 1 LIMIT 1", (college_name,)).fetchone()
    return int(row["id"]) if row else None


def _find_major_id(conn: sqlite3.Connection, major_name: str) -> int | None:
    candidates = [major_name]
    stripped = re.sub(r"[（(].*[）)]$", "", major_name).strip()
    if stripped and stripped not in candidates:
        candidates.append(stripped)
    for candidate in candidates:
        row = conn.execute("SELECT id FROM major WHERE name = ? AND is_active = 1 LIMIT 1", (candidate,)).fetchone()
        if row:
            return int(row["id"])
    return None


def _split_code_name(value: str, *, code_length: int) -> tuple[str | None, str]:
    text = value.strip()
    if len(text) <= code_length:
        return None, text
    code = text[:code_length].strip()
    name = text[code_length:].strip()
    if not re.fullmatch(r"[A-Za-z0-9]+", code) or not name:
        match = re.match(r"^([A-Za-z0-9]+)(.+)$", text)
        if not match:
            return None, text
        return match.group(1), match.group(2).strip()
    return code, name


def _parse_decimal(value: str) -> Decimal | None:
    text = str(value).strip()
    if not text:
        return None
    try:
        return Decimal(text)
    except InvalidOperation:
        return None


def _parse_int(value: str) -> int | None:
    text = str(value).strip()
    if not text:
        return None
    try:
        return int(Decimal(text))
    except (InvalidOperation, ValueError):
        return None


def _decimal_to_float(value: Decimal | None) -> float | None:
    return float(value) if value is not None else None


def _require_tables(conn: sqlite3.Connection) -> None:
    required = {"gaokao_source_document", "gaokao_import_run", "gaokao_admission_result", "admission_record", "college", "major"}
    existing = {
        row["name"]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
    }
    missing = required - existing
    if missing:
        raise RuntimeError(f"missing required tables: {', '.join(sorted(missing))}")


def _safe_filename(value: str) -> str:
    text = re.sub(r"[^\w\u4e00-\u9fff.-]+", "_", value.strip(), flags=re.U)
    return text.strip("._")[:150] or "gaokao_source"


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file_obj:
        for chunk in iter(lambda: file_obj.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _hash_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


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
    backup_path = backup_dir / f"{source_path.stem}_before_round5_special_admission_import_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    with sqlite3.connect(str(source_path)) as source_conn, sqlite3.connect(str(backup_path)) as backup_conn:
        source_conn.backup(backup_conn)
    return backup_path


if __name__ == "__main__":
    raise SystemExit(main())
