#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sqlite3
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "apps" / "backend"))

from app.utils.gaokao_materialize import materialize_gaokao_structured_tables  # noqa: E402


DEFAULT_SOURCE_DIR = Path("/Users/gao/Desktop/高考志愿")
DEFAULT_DB_PATH = REPO_ROOT / "data" / "app.db"
DEFAULT_BACKUP_DIR = REPO_ROOT / "data" / "backups"
DEFAULT_REPORT_PATH = REPO_ROOT / "docs" / "user-gaokao-local-import-20260428.md"
IMPORTER_NAME = "import_user_gaokao_local_folder"
DATA_VERSION_LABEL = "user_gaokao_local_20260428"
SOURCE_LEVEL = "user_provided"
REVIEW_STATUS = "pending_local_review"
USER_ORG = "用户提供资料包"


@dataclass(frozen=True)
class LocalSource:
    year: int
    source_type: str
    title: str
    path: Path
    import_kind: str
    parser_note: str


@dataclass
class ParsedBundle:
    source: LocalSource
    rows: list[dict[str, Any]]
    warnings: list[str] = field(default_factory=list)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import usable Shandong gaokao data from a user-provided local folder.")
    parser.add_argument("--source-dir", type=Path, default=DEFAULT_SOURCE_DIR, help="User-provided gaokao material folder.")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH, help="Target SQLite database.")
    parser.add_argument("--years", type=int, nargs="+", default=[2023, 2024, 2025], help="Years to import.")
    parser.add_argument("--backup-dir", type=Path, default=DEFAULT_BACKUP_DIR, help="Backup directory before writing DB.")
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT_PATH, help="Markdown report path.")
    parser.add_argument("--dry-run", action="store_true", help="Parse and summarize only; do not write files or DB.")
    parser.add_argument("--no-backup", action="store_true", help="Skip DB backup for write mode.")
    parser.add_argument("--json", action="store_true", help="Output JSON summary.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source_dir = args.source_dir.resolve()
    db_path = args.db.resolve()
    years = tuple(sorted(set(args.years)))
    if not source_dir.exists():
        print(f"source directory not found: {source_dir}", file=sys.stderr)
        return 2
    if not args.dry_run and not db_path.exists():
        print(f"database not found: {db_path}", file=sys.stderr)
        return 2

    sources = discover_sources(source_dir, years)
    bundles: list[ParsedBundle] = []
    failures: list[dict[str, Any]] = []
    for source in sources:
        try:
            if source.import_kind == "plan":
                bundles.append(parse_plan_file(source))
            elif source.import_kind == "filing_result":
                bundles.append(parse_filing_result_file(source))
        except Exception as exc:  # noqa: BLE001 - keep other files moving and report exact file.
            failures.append({"file": str(source.path), "year": source.year, "source_type": source.source_type, "reason": str(exc)})

    skipped = build_skipped_notes(source_dir, years)
    payload = build_payload(
        db_path=db_path,
        source_dir=source_dir,
        years=years,
        bundles=bundles,
        failures=failures,
        skipped=skipped,
        dry_run=args.dry_run,
    )

    if not args.dry_run:
        backup_path = None
        if not args.no_backup:
            backup_path = backup_database(db_path, args.backup_dir.resolve())
        write_result = write_bundles(db_path, bundles)
        materialize_result = materialize_gaokao_structured_tables(db_path, backup_dir=None)
        payload["backup_path"] = relative_path(backup_path) if backup_path else None
        payload["write_result"] = write_result
        payload["materialize_result"] = materialize_result
        payload["after_counts"] = collect_counts(db_path)
        write_report(args.report.resolve(), payload)
        payload["report_path"] = relative_path(args.report.resolve())

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print_summary(payload)
    return 0


def discover_sources(source_dir: Path, years: tuple[int, ...]) -> list[LocalSource]:
    files = [path for path in source_dir.rglob("*") if path.is_file() and path.suffix.lower() in {".xls", ".xlsx"}]
    sources: list[LocalSource] = []

    def find_one(year: int, needle: str, *, source_type: str, title: str, import_kind: str, parser_note: str) -> None:
        if year not in years:
            return
        matches = [path for path in files if needle in path.name]
        if matches:
            sources.append(LocalSource(year, source_type, title, sorted(matches, key=lambda item: len(str(item)))[0], import_kind, parser_note))

    find_one(
        2023,
        "山东-2023-招生计划622",
        source_type="admission_plan_user",
        title="用户提供：山东2023招生计划完整表",
        import_kind="plan",
        parser_note="2023 招生计划表，字段含省份/年份/批次/科类/院校/专业/计划。",
    )
    find_one(
        2024,
        "山东-招生计划-2024-（本科）",
        source_type="admission_plan_user",
        title="用户提供：山东2024本科招生计划",
        import_kind="plan",
        parser_note="2024 本科招生计划表，字段含类型/批次/专业/计划/选科。",
    )
    find_one(
        2024,
        "山东2024年招生计划（专科）",
        source_type="admission_plan_user",
        title="用户提供：山东2024专科招生计划",
        import_kind="plan",
        parser_note="2024 专科招生计划表，字段含招生类型/院校/专业/24人/选科。",
    )
    find_one(
        2023,
        "山东省2023年春季高考本科批第1次志愿投档情况表",
        source_type="spring_exam_filing_result_user",
        title="用户提供：山东2023春季高考本科批投档情况",
        import_kind="filing_result",
        parser_note="春季高考投档表，只写 raw 投档事实。",
    )
    find_one(
        2023,
        "山东省2023年春季高考专科批第1次志愿投档情况表",
        source_type="spring_exam_filing_result_user",
        title="用户提供：山东2023春季高考专科批投档情况",
        import_kind="filing_result",
        parser_note="春季高考投档表，只写 raw 投档事实。",
    )

    if 2024 in years:
        for path in sorted(files):
            name = path.name
            if "山东省2024年体育类常规批" in name and "投档情况表" in name:
                sources.append(
                    LocalSource(2024, "sports_filing_result_user", f"用户提供：{path.stem}", path, "filing_result", "体育类投档表，只写 raw 投档事实。")
                )
            if "山东省2024年艺术类" in name and "投档情况表" in name:
                sources.append(
                    LocalSource(2024, "art_filing_result_user", f"用户提供：{path.stem}", path, "filing_result", "艺术类投档表，只写 raw 投档事实。")
                )

    return _dedupe_sources(sources)


def _dedupe_sources(sources: list[LocalSource]) -> list[LocalSource]:
    seen: set[tuple[int, str, str]] = set()
    result: list[LocalSource] = []
    for source in sources:
        key = (source.year, source.source_type, str(source.path))
        if key not in seen:
            result.append(source)
            seen.add(key)
    return result


def parse_plan_file(source: LocalSource) -> ParsedBundle:
    rows: list[dict[str, Any]] = []
    warnings: list[str] = []
    for sheet_name, table in read_excel_tables(source.path):
        header_index = find_header_index(table, (("院校",), ("专业",), ("计划", "24人")))
        if header_index is None:
            warnings.append(f"{sheet_name}: 未找到招生计划表头")
            continue
        headers = [_cell_text(cell) for cell in table[header_index]]
        for row_number, row in enumerate(table[header_index + 1 :], start=header_index + 2):
            parsed = parse_plan_row(source, headers, row, row_number)
            if parsed:
                rows.append(parsed)
    return ParsedBundle(source=source, rows=rows, warnings=warnings)


def parse_plan_row(source: LocalSource, headers: list[str], row: list[Any], row_number: int) -> dict[str, Any] | None:
    year = parse_int(value_by_header(headers, row, ("年份",))) or source.year
    province = value_by_header(headers, row, ("省份",)) or "山东"
    college_name = value_by_any_header(headers, row, ("招生院校", "院校名称"))
    college_code = value_by_header(headers, row, ("院校代码",))
    major_name = value_by_header(headers, row, ("专业名称",))
    major_code = value_by_header(headers, row, ("专业代码",))
    plan_count = parse_int(value_by_any_header(headers, row, ("计划人数", "计划", "24人")))
    if not college_name or not major_name or not plan_count:
        return None
    batch = value_by_header(headers, row, ("批次",)) or infer_plan_batch(source, headers, row)
    subject_requirement = value_by_any_header(headers, row, ("选科要求", "24选科"))
    tuition = value_by_header(headers, row, ("学费",))
    duration = value_by_header(headers, row, ("学制",))
    candidate_type = normalize_candidate_type(
        value_by_any_header(headers, row, ("类型", "科类", "招生类型")) or batch or "普通类",
        default="普通类",
    )
    special_plan_tag = build_special_plan_tag(source, headers, row)
    original_text = " | ".join(_cell_text(cell) for cell in row if _cell_text(cell))
    return {
        "province": "山东",
        "year": year,
        "candidate_type": candidate_type,
        "batch_name": normalize_batch(batch, candidate_type),
        "round_no": None,
        "pathway_code": None,
        "enrollment_type": value_by_header(headers, row, ("招生类型",)),
        "education_level": infer_education_level(batch, major_name),
        "college_code_snapshot": college_code,
        "college_name_snapshot": clean_college_name(college_name),
        "major_code_snapshot": major_code,
        "major_name_snapshot": major_name,
        "major_group_code": None,
        "plan_count": plan_count,
        "duration_years": duration,
        "tuition": tuition,
        "campus": None,
        "subject_requirement_text": subject_requirement,
        "subject_requirement_code": None,
        "special_plan_tag": special_plan_tag,
        "major_note": value_by_any_header(headers, row, ("注意事项", "专业类")),
        "authority_scope": "山东",
        "plan_scope": "local_user_file",
        "update_type": "user_provided_import",
        "merge_status": "unverified_user_provided",
        "parse_confidence": "medium",
        "original_major_text": original_text,
        "original_update_text": f"{source.path.name}:{row_number}",
        "source_record_hash": hash_text(f"plan|{year}|{college_code}|{college_name}|{major_code}|{major_name}|{batch}|{plan_count}|{original_text}"),
    }


def infer_plan_batch(source: LocalSource, headers: list[str], row: list[Any]) -> str:
    name = source.path.name
    note = " ".join([name, value_by_header(headers, row, ("招生类型",)) or "", value_by_header(headers, row, ("专业名称",)) or ""])
    if "3+2" in note:
        return "3+2专本贯通培养批"
    if "高职院校专项" in note:
        return "高职院校专项计划批"
    if "专科" in note:
        return "专科批"
    return "常规批"


def build_special_plan_tag(source: LocalSource, headers: list[str], row: list[Any]) -> str | None:
    values = []
    for keywords in (("类型",), ("招生类型",), ("注意事项",), ("专业类",)):
        value = value_by_header(headers, row, keywords)
        if value and value not in values:
            values.append(value)
    return "；".join(values) or source.parser_note


def parse_filing_result_file(source: LocalSource) -> ParsedBundle:
    rows: list[dict[str, Any]] = []
    warnings: list[str] = []
    for sheet_name, table in read_excel_tables(source.path):
        header_index = find_header_index(table, (("院校",), ("专业",), ("投档", "计划", "最低")))
        if header_index is None:
            warnings.append(f"{sheet_name}: 未找到投档表头")
            continue
        headers = [_cell_text(cell) for cell in table[header_index]]
        meta = infer_result_meta(source, sheet_name)
        for row_number, row in enumerate(table[header_index + 1 :], start=header_index + 2):
            parsed = parse_result_row(source, headers, row, row_number, meta)
            if parsed:
                rows.append(parsed)
    return ParsedBundle(source=source, rows=rows, warnings=warnings)


def parse_result_row(
    source: LocalSource,
    headers: list[str],
    row: list[Any],
    row_number: int,
    meta: dict[str, str | None],
) -> dict[str, Any] | None:
    major_raw = value_by_any_header(headers, row, ("专业代号及名称", "专业"))
    college_raw = value_by_any_header(headers, row, ("院校代号及名称", "院校"))
    if not major_raw or not college_raw:
        return None
    major_code, major_name = split_major(major_raw)
    college_code, college_name = split_college(college_raw)
    plan_count = parse_int(value_by_any_header(headers, row, ("投档计划数", "计划")))
    min_rank = parse_int(value_by_any_header(headers, row, ("最低位次", "位次")))
    min_score = parse_float(value_by_any_header(headers, row, ("投档最低分", "综合分", "最低分")))
    if not college_name or not major_name or (min_rank is None and min_score is None):
        return None
    category = value_by_header(headers, row, ("专业类别",))
    remark = "；".join(item for item in [source.parser_note, f"专业类别={category}" if category else None, f"sheet={meta.get('sheet')}" if meta.get("sheet") else None] if item)
    return {
        "province": "山东",
        "year": source.year,
        "candidate_type": meta["candidate_type"],
        "batch_name": meta["batch_name"],
        "round_no": meta["round_no"],
        "college_code_snapshot": college_code,
        "college_name_snapshot": clean_college_name(college_name),
        "major_code_snapshot": major_code,
        "major_name_snapshot": major_name,
        "min_score": min_score,
        "min_rank": min_rank,
        "avg_score": None,
        "max_score": None,
        "control_line": None,
        "plan_count": plan_count,
        "actual_filed_count": None,
        "original_min_rank_text": value_by_any_header(headers, row, ("最低位次", "位次")),
        "remark": remark,
        "source_record_hash": hash_text(
            f"result|{source.year}|{meta['candidate_type']}|{meta['batch_name']}|{meta['round_no']}|"
            f"{college_code}|{college_name}|{major_code}|{major_name}|{plan_count}|{min_rank}|{min_score}|{category}"
        ),
    }


def infer_result_meta(source: LocalSource, sheet_name: str) -> dict[str, str | None]:
    text = f"{source.path.name} {sheet_name}"
    if "春季高考" in text:
        candidate_type = "春季高考"
        if "本科" in text:
            batch = "春季高考本科批"
        elif "专科" in text:
            batch = "春季高考专科批"
        else:
            batch = "春季高考"
    elif "体育类" in text:
        candidate_type = "体育类"
        batch = "体育类常规批"
    elif "艺术类" in text:
        candidate_type = "艺术类"
        batch = "艺术类本科批" if "本科" in text else "艺术类专科批"
    else:
        candidate_type = "普通类"
        batch = "常规批"
    round_match = re.search(r"第\s*(\d+)\s*次", text)
    return {"candidate_type": candidate_type, "batch_name": batch, "round_no": round_match.group(1) if round_match else "1", "sheet": sheet_name}


def read_excel_tables(path: Path) -> list[tuple[str, list[list[Any]]]]:
    tables = []
    excel = pd.ExcelFile(path)
    for sheet_name in excel.sheet_names:
        df = pd.read_excel(path, sheet_name=sheet_name, header=None, dtype=object)
        if df.dropna(how="all").empty:
            continue
        tables.append((sheet_name, df.where(pd.notna(df), None).values.tolist()))
    return tables


def find_header_index(table: list[list[Any]], required_groups: tuple[tuple[str, ...], ...]) -> int | None:
    for index, row in enumerate(table[:20]):
        joined = " ".join(_cell_text(cell) for cell in row)
        if all(any(keyword in joined for keyword in group) for group in required_groups):
            return index
    return None


def value_by_header(headers: list[str], row: list[Any], keywords: tuple[str, ...]) -> str | None:
    for index, header in enumerate(headers):
        if not header:
            continue
        if all(keyword in header for keyword in keywords):
            return _cell_text(row[index]) if index < len(row) else None
    return None


def value_by_any_header(headers: list[str], row: list[Any], keywords: tuple[str, ...]) -> str | None:
    for index, header in enumerate(headers):
        if not header:
            continue
        if any(keyword in header for keyword in keywords):
            return _cell_text(row[index]) if index < len(row) else None
    return None


def normalize_candidate_type(value: str | None, *, default: str) -> str:
    text = value or ""
    if "春" in text:
        return "春季高考"
    if "体育" in text:
        return "体育类"
    if "艺术" in text or "美术" in text or "音乐" in text or "舞蹈" in text or "书法" in text or "播音" in text or "表" in text:
        return "艺术类"
    if "单招" in text or "单独" in text:
        return "单独招生"
    if "综评" in text or "综合评价" in text:
        return "综合评价招生"
    return default


def normalize_batch(batch: str | None, candidate_type: str) -> str:
    text = batch or ""
    if candidate_type == "春季高考" and "春季高考" not in text:
        if "本科" in text:
            return "春季高考本科批"
        if "专科" in text:
            return "春季高考专科批"
    return text or "常规批"


def infer_education_level(batch: str | None, major_name: str | None) -> str | None:
    text = f"{batch or ''} {major_name or ''}"
    if "专科" in text or "高职" in text:
        return "专科"
    if "本科" in text:
        return "本科"
    return None


def split_college(value: str) -> tuple[str | None, str]:
    text = _cell_text(value)
    match = re.match(r"^([A-Z][A-Z0-9]{3})(.+)$", text)
    if match:
        return match.group(1), match.group(2).strip()
    return None, text


def split_major(value: str) -> tuple[str | None, str]:
    text = _cell_text(value)
    match = re.match(r"^([A-Z0-9]{2})(.+)$", text)
    if match:
        return match.group(1), match.group(2).strip()
    return None, text


def clean_college_name(value: str) -> str:
    text = _cell_text(value)
    text = re.sub(r"\((?:山东|北京|天津|上海|重庆|河北|河南|山西|陕西|辽宁|吉林|黑龙江|江苏|浙江|安徽|福建|江西|湖北|湖南|广东|海南|四川|贵州|云南|甘肃|青海|台湾|内蒙古|广西|西藏|宁夏|新疆|香港|澳门)?(?:公办|民办|中外合作|独立学院|军事类|本科|专科|高职).*?\)$", "", text)
    return text.strip() or _cell_text(value)


def write_bundles(db_path: Path, bundles: list[ParsedBundle]) -> dict[str, Any]:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    years = sorted({bundle.source.year for bundle in bundles})
    source_copy_root = REPO_ROOT / "data" / "imports" / "gaokao" / "user_provided"
    result = {"sources": [], "deleted_user_plan_rows": 0, "deleted_user_result_rows": 0, "inserted_plan_rows": 0, "inserted_result_rows": 0}
    with sqlite3.connect(str(db_path)) as conn:
        conn.row_factory = sqlite3.Row
        if years:
            placeholders = ",".join("?" for _ in years)
            result["deleted_user_plan_rows"] = conn.execute(
                f"DELETE FROM gaokao_admission_plan WHERE data_version_label = ? AND year IN ({placeholders})",
                (DATA_VERSION_LABEL, *years),
            ).rowcount
            result["deleted_user_result_rows"] = conn.execute(
                f"DELETE FROM gaokao_admission_result WHERE data_version_label = ? AND year IN ({placeholders})",
                (DATA_VERSION_LABEL, *years),
            ).rowcount
            conn.execute(
                f"DELETE FROM enrollment_plan WHERE import_batch_name = ? AND year IN ({placeholders})",
                (DATA_VERSION_LABEL, *years),
            )
            conn.execute(
                f"DELETE FROM admission_record WHERE source_note LIKE ? AND year IN ({placeholders})",
                (f"%version={DATA_VERSION_LABEL}%", *years),
            )
        for bundle in bundles:
            copied_path = copy_source_file(bundle.source.path, source_copy_root / str(bundle.source.year))
            file_sha = sha256_file(copied_path)
            source_document_id = upsert_source_document(conn, bundle.source, copied_path, file_sha, now)
            import_run_id = create_import_run(conn, source_document_id, bundle, copied_path, now)
            if bundle.source.import_kind == "plan":
                inserted = insert_plan_rows(conn, bundle, source_document_id, import_run_id, copied_path, now)
                result["inserted_plan_rows"] += inserted
            else:
                inserted = insert_result_rows(conn, bundle, source_document_id, import_run_id, copied_path, now)
                result["inserted_result_rows"] += inserted
            finish_import_run(conn, import_run_id, total=len(bundle.rows), success=inserted, skipped=max(len(bundle.rows) - inserted, 0), now=now)
            conn.execute("UPDATE gaokao_source_document SET status = 'imported', updated_at = ? WHERE id = ?", (now, source_document_id))
            result["sources"].append(
                {
                    "year": bundle.source.year,
                    "source_type": bundle.source.source_type,
                    "title": bundle.source.title,
                    "source_document_id": source_document_id,
                    "import_run_id": import_run_id,
                    "rows": len(bundle.rows),
                    "inserted": inserted,
                    "local_file_path": relative_path(copied_path),
                    "file_sha256": file_sha,
                }
            )
        conn.commit()
    return result


def upsert_source_document(conn: sqlite3.Connection, source: LocalSource, copied_path: Path, file_sha: str, now: str) -> int:
    url = f"user-provided://{file_sha}"
    row = conn.execute(
        "SELECT id FROM gaokao_source_document WHERE province = '山东' AND year = ? AND source_type = ? AND url = ?",
        (source.year, source.source_type, url),
    ).fetchone()
    local_path = relative_path(copied_path)
    note = f"用户提供资料包导入；原始路径：{source.path}；{source.parser_note}；需人工复核。"
    if row:
        source_document_id = int(row["id"])
        conn.execute(
            """
            UPDATE gaokao_source_document
            SET title = ?, official_org = ?, local_file_path = ?, file_sha256 = ?,
                parser_name = ?, parser_version = ?, status = 'file_ready', note = ?,
                updated_at = ?, is_active = 1
            WHERE id = ?
            """,
            (source.title, USER_ORG, local_path, file_sha, IMPORTER_NAME, DATA_VERSION_LABEL, note, now, source_document_id),
        )
        return source_document_id
    cursor = conn.execute(
        """
        INSERT INTO gaokao_source_document (
            province, year, source_type, title, url, official_org,
            source_registry_code, published_at, fetched_at, local_file_path,
            file_sha256, parser_name, parser_version, status, note,
            created_at, updated_at, is_active
        ) VALUES (?, ?, ?, ?, ?, ?, ?, NULL, ?, ?, ?, ?, ?, 'file_ready', ?, ?, ?, 1)
        """,
        ("山东", source.year, source.source_type, source.title, url, USER_ORG, "user_provided", now, local_path, file_sha, IMPORTER_NAME, DATA_VERSION_LABEL, note, now, now),
    )
    return int(cursor.lastrowid)


def create_import_run(conn: sqlite3.Connection, source_document_id: int, bundle: ParsedBundle, copied_path: Path, now: str) -> int:
    cursor = conn.execute(
        """
        INSERT INTO gaokao_import_run (
            source_document_id, importer_name, started_at, status, total_rows,
            success_rows, failed_rows, skipped_rows, created_rows, updated_rows,
            raw_snapshot_path, note, created_at, updated_at, is_active
        ) VALUES (?, ?, ?, 'running', ?, 0, 0, 0, 0, 0, ?, ?, ?, ?, 1)
        """,
        (source_document_id, IMPORTER_NAME, now, len(bundle.rows), relative_path(copied_path), "用户提供资料包导入，来源未核验。", now, now),
    )
    return int(cursor.lastrowid)


def finish_import_run(conn: sqlite3.Connection, import_run_id: int, *, total: int, success: int, skipped: int, now: str) -> None:
    status = "success" if success == total else "partial_success"
    conn.execute(
        """
        UPDATE gaokao_import_run
        SET finished_at = ?, status = ?, total_rows = ?, success_rows = ?,
            skipped_rows = ?, created_rows = ?, updated_rows = 0, updated_at = ?
        WHERE id = ?
        """,
        (now, status, total, success, skipped, success, now, import_run_id),
    )


def insert_plan_rows(
    conn: sqlite3.Connection,
    bundle: ParsedBundle,
    source_document_id: int,
    import_run_id: int,
    copied_path: Path,
    now: str,
) -> int:
    payloads = []
    for row in bundle.rows:
        payload = dict(row)
        payload.update(common_source_fields(bundle.source, source_document_id, import_run_id, copied_path, now))
        payloads.append(payload)
    if not payloads:
        return 0
    conn.executemany(
        """
        INSERT INTO gaokao_admission_plan (
            province, year, candidate_type, batch_name, round_no, pathway_code,
            enrollment_type, education_level, college_code_snapshot, college_name_snapshot,
            major_code_snapshot, major_name_snapshot, major_group_code, plan_count,
            duration_years, tuition, campus, subject_requirement_text,
            subject_requirement_code, special_plan_tag, major_note, authority_scope,
            plan_scope, update_type, merge_status, parse_confidence,
            original_major_text, original_update_text, created_at, updated_at,
            source_level, source_title, source_url, local_source_path,
            parser_script_name, published_at, review_status, source_record_hash,
            data_version_label, source_document_id, import_run_id
        ) VALUES (
            :province, :year, :candidate_type, :batch_name, :round_no, :pathway_code,
            :enrollment_type, :education_level, :college_code_snapshot, :college_name_snapshot,
            :major_code_snapshot, :major_name_snapshot, :major_group_code, :plan_count,
            :duration_years, :tuition, :campus, :subject_requirement_text,
            :subject_requirement_code, :special_plan_tag, :major_note, :authority_scope,
            :plan_scope, :update_type, :merge_status, :parse_confidence,
            :original_major_text, :original_update_text, :created_at, :updated_at,
            :source_level, :source_title, :source_url, :local_source_path,
            :parser_script_name, :published_at, :review_status, :source_record_hash,
            :data_version_label, :source_document_id, :import_run_id
        )
        """,
        payloads,
    )
    return len(payloads)


def insert_result_rows(
    conn: sqlite3.Connection,
    bundle: ParsedBundle,
    source_document_id: int,
    import_run_id: int,
    copied_path: Path,
    now: str,
) -> int:
    payloads = []
    for row in bundle.rows:
        payload = dict(row)
        payload.update(common_source_fields(bundle.source, source_document_id, import_run_id, copied_path, now))
        payloads.append(payload)
    if not payloads:
        return 0
    conn.executemany(
        """
        INSERT INTO gaokao_admission_result (
            province, year, candidate_type, batch_name, round_no,
            college_code_snapshot, college_name_snapshot, major_code_snapshot,
            major_name_snapshot, min_score, min_rank, avg_score, max_score,
            control_line, plan_count, actual_filed_count, original_min_rank_text,
            remark, created_at, updated_at, source_level, source_title, source_url,
            local_source_path, parser_script_name, published_at, review_status,
            source_record_hash, data_version_label, source_document_id, import_run_id
        ) VALUES (
            :province, :year, :candidate_type, :batch_name, :round_no,
            :college_code_snapshot, :college_name_snapshot, :major_code_snapshot,
            :major_name_snapshot, :min_score, :min_rank, :avg_score, :max_score,
            :control_line, :plan_count, :actual_filed_count, :original_min_rank_text,
            :remark, :created_at, :updated_at, :source_level, :source_title, :source_url,
            :local_source_path, :parser_script_name, :published_at, :review_status,
            :source_record_hash, :data_version_label, :source_document_id, :import_run_id
        )
        """,
        payloads,
    )
    return len(payloads)


def common_source_fields(source: LocalSource, source_document_id: int, import_run_id: int, copied_path: Path, now: str) -> dict[str, Any]:
    return {
        "created_at": now,
        "updated_at": now,
        "source_level": SOURCE_LEVEL,
        "source_title": source.title,
        "source_url": f"user-provided://{source.path.name}",
        "local_source_path": relative_path(copied_path),
        "parser_script_name": IMPORTER_NAME,
        "published_at": None,
        "review_status": REVIEW_STATUS,
        "data_version_label": DATA_VERSION_LABEL,
        "source_document_id": source_document_id,
        "import_run_id": import_run_id,
    }


def build_payload(
    *,
    db_path: Path,
    source_dir: Path,
    years: tuple[int, ...],
    bundles: list[ParsedBundle],
    failures: list[dict[str, Any]],
    skipped: list[dict[str, str]],
    dry_run: bool,
) -> dict[str, Any]:
    parsed = [
        {
            "year": bundle.source.year,
            "source_type": bundle.source.source_type,
            "kind": bundle.source.import_kind,
            "title": bundle.source.title,
            "file": str(bundle.source.path),
            "rows": len(bundle.rows),
            "warnings": bundle.warnings,
        }
        for bundle in bundles
    ]
    return {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "db_path": str(db_path),
        "source_dir": str(source_dir),
        "years": list(years),
        "dry_run": dry_run,
        "data_version_label": DATA_VERSION_LABEL,
        "before_counts": collect_counts(db_path) if db_path.exists() else {},
        "parsed_sources": parsed,
        "parsed_plan_rows": sum(len(bundle.rows) for bundle in bundles if bundle.source.import_kind == "plan"),
        "parsed_result_rows": sum(len(bundle.rows) for bundle in bundles if bundle.source.import_kind == "filing_result"),
        "failures": failures,
        "skipped": skipped,
        "backup_path": None,
        "report_path": None,
    }


def collect_counts(db_path: Path) -> dict[str, Any]:
    with sqlite3.connect(str(db_path)) as conn:
        conn.row_factory = sqlite3.Row
        result: dict[str, Any] = {}
        for table in ("gaokao_admission_plan", "gaokao_admission_result", "enrollment_plan", "admission_record", "gaokao_source_document", "gaokao_import_run"):
            result[table] = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        result["plan_by_year"] = [
            dict(row)
            for row in conn.execute(
                """
                SELECT year, COALESCE(candidate_type, '') AS candidate_type, COALESCE(batch_name, '') AS batch_name, COUNT(*) AS count
                FROM gaokao_admission_plan
                WHERE province IN ('山东', 'sd') AND year IN (2023, 2024, 2025)
                GROUP BY year, candidate_type, batch_name
                ORDER BY year, candidate_type, batch_name
                """
            ).fetchall()
        ]
        result["result_by_year"] = [
            dict(row)
            for row in conn.execute(
                """
                SELECT year, COALESCE(candidate_type, '') AS candidate_type, COALESCE(batch_name, '') AS batch_name, COALESCE(round_no, '') AS round_no, COUNT(*) AS count
                FROM gaokao_admission_result
                WHERE province IN ('山东', 'sd') AND year IN (2023, 2024, 2025)
                GROUP BY year, candidate_type, batch_name, round_no
                ORDER BY year, candidate_type, batch_name, round_no
                """
            ).fetchall()
        ]
    return result


def build_skipped_notes(source_dir: Path, years: tuple[int, ...]) -> list[dict[str, str]]:
    notes: list[dict[str, str]] = []
    if 2025 in years:
        notes.append({"year": "2025", "item": "结构化山东 Excel", "reason": "本轮未在资料包中发现比现有 2025 raw 数据更完整、可直接映射的山东招生计划或投档 Excel。"})
    for path in source_dir.rglob("*"):
        if not path.is_file():
            continue
        name = path.name
        if path.suffix.lower() in {".pdf", ".png", ".jpg", ".jpeg", ".mp4", ".flv"} and ("山东" in str(path) or "高考志愿" in str(path)):
            if len(notes) < 12:
                notes.append({"year": "", "item": name, "reason": "PDF/图片/视频暂不作为算法数据库导入，只作为人工参考资料。"})
    return notes


def write_report(report_path: Path, payload: dict[str, Any]) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# 用户提供山东高考资料本地导入报告",
        "",
        f"- 生成时间：{payload['generated_at']}",
        f"- 数据版本：`{payload['data_version_label']}`",
        f"- 来源目录：`{payload['source_dir']}`",
        f"- 主库：`{payload['db_path']}`",
        f"- 写库前备份：`{payload.get('backup_path')}`",
        "- 来源可信度：用户提供资料包，已标记为 `user_provided / pending_local_review`，仍需人工核验。",
        "",
        "## 导入结果",
        "",
        f"- 解析招生计划：{payload['parsed_plan_rows']} 行",
        f"- 解析投档结果：{payload['parsed_result_rows']} 行",
    ]
    write_result = payload.get("write_result") or {}
    if write_result:
        lines.extend(
            [
                f"- 写入 raw 招生计划：{write_result.get('inserted_plan_rows', 0)} 行",
                f"- 写入 raw 投档结果：{write_result.get('inserted_result_rows', 0)} 行",
                f"- 替换旧本地计划行：{write_result.get('deleted_user_plan_rows', 0)} 行",
                f"- 替换旧本地投档行：{write_result.get('deleted_user_result_rows', 0)} 行",
            ]
        )
    materialize = payload.get("materialize_result") or {}
    if materialize:
        stats = materialize.get("stats", {})
        final_counts = materialize.get("final_counts", {})
        lines.extend(
            [
                "",
                "## 物化结果",
                "",
                f"- 应用侧招生计划 upsert：{stats.get('enrollment_plans_upserted')}",
                f"- 应用侧录取结果 upsert：{stats.get('admission_records_upserted')}",
                f"- 当前 `enrollment_plan` 总数：{final_counts.get('enrollment_plan')}",
                f"- 当前 `admission_record` 总数：{final_counts.get('admission_record')}",
            ]
        )

    lines.extend(["", "## 文件明细", "", "| 年份 | 类型 | 行数 | 文件 |", "|---:|---|---:|---|"])
    for item in payload["parsed_sources"]:
        lines.append(f"| {item['year']} | {item['source_type']} | {item['rows']} | `{Path(item['file']).name}` |")
    if payload["failures"]:
        lines.extend(["", "## 失败或未处理", "", "| 年份 | 类型 | 文件 | 原因 |", "|---:|---|---|---|"])
        for item in payload["failures"]:
            lines.append(f"| {item.get('year', '')} | {item.get('source_type', '')} | `{Path(item.get('file', '')).name}` | {item.get('reason', '')} |")

    lines.extend(
        [
            "",
            "## 仍缺数据",
            "",
            "- 2025 若需进一步补齐普通类正式招生计划，需要继续提供可结构化的山东招生计划 Excel 或官方附件。",
            "- 单招、综评仍缺专门录取结果；未找到前只能做方向性初筛。",
            "- 用户提供资料包已可改善 2023/2024 招生计划覆盖，但正式填报前仍建议以山东省教育招生考试院和高校官网最终文件复核。",
            "- 招生章程限制链仍需人工逐校复核，不能由资料包自动关闭。",
        ]
    )
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def backup_database(db_path: Path, backup_dir: Path) -> Path:
    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"app_before_user_gaokao_local_import_{timestamp}.db"
    with sqlite3.connect(str(db_path)) as source_conn, sqlite3.connect(str(backup_path)) as backup_conn:
        source_conn.backup(backup_conn)
    return backup_path


def copy_source_file(source: Path, target_dir: Path) -> Path:
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / sanitize_filename(source.name)
    shutil.copy2(source, target)
    return target


def sanitize_filename(value: str) -> str:
    return re.sub(r"[^\w.\-（）()【】\u4e00-\u9fff]+", "_", value).strip("_") or "gaokao_source.xlsx"


def _cell_text(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if text.lower() == "nan":
        return ""
    if text.endswith(".0") and re.match(r"^\d+\.0$", text):
        return text[:-2]
    return text


def parse_int(value: Any) -> int | None:
    text = _cell_text(value).replace(",", "")
    if not text or text in {"-", "—"}:
        return None
    match = re.search(r"\d+", text)
    return int(match.group(0)) if match else None


def parse_float(value: Any) -> float | None:
    text = _cell_text(value).replace(",", "")
    if not text or text in {"-", "—"}:
        return None
    match = re.search(r"\d+(?:\.\d+)?", text)
    return float(match.group(0)) if match else None


def hash_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def relative_path(path: Path | None) -> str | None:
    if path is None:
        return None
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def print_summary(payload: dict[str, Any]) -> None:
    print("用户提供山东高考资料处理完成")
    print(f"- dry_run: {payload['dry_run']}")
    print(f"- parsed_plan_rows: {payload['parsed_plan_rows']}")
    print(f"- parsed_result_rows: {payload['parsed_result_rows']}")
    if payload.get("backup_path"):
        print(f"- backup: {payload['backup_path']}")
    if payload.get("report_path"):
        print(f"- report: {payload['report_path']}")


if __name__ == "__main__":
    raise SystemExit(main())
