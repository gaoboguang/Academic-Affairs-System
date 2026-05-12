#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "app.db"
IMPORTER_NAME = "gaokao_scraper_bundle"
PARSER_VERSION = "20260508_0030"
DATA_VERSION_LABEL = "gaokao_scraper_bundle_20260508"
ART_PLAN_DETAIL_DATA_VERSION_LABEL = "gaokao_scraper_art_plan_detail_20260511"
PROVINCE = "山东"


def run_import(
    *,
    source_dir: Path,
    db_path: Path = DEFAULT_DB_PATH,
    dry_run: bool = True,
    apply: bool = False,
    json_output: bool = False,
    no_backup: bool = False,
) -> dict[str, Any]:
    source_dir = source_dir.expanduser().resolve()
    db_path = db_path.expanduser().resolve()
    if not source_dir.exists():
        raise FileNotFoundError(f"source dir not found: {source_dir}")
    if not db_path.exists():
        raise FileNotFoundError(f"database not found: {db_path}")
    if apply and dry_run:
        dry_run = False
    bundle = _load_bundle(source_dir)
    report = _build_report(source_dir, bundle)
    report["mode"] = "apply" if apply and not dry_run else "dry-run"
    report["db_path"] = str(db_path)
    report["backup_path"] = None
    if dry_run or not apply:
        return report

    backup_path = None
    if not no_backup:
        backup_path = _backup_database(db_path)
        report["backup_path"] = str(backup_path)

    with sqlite3.connect(str(db_path)) as conn:
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        _ensure_raw_tables(conn)
        _ensure_required_profile_tables(conn)
        context = _ApplyContext(conn=conn, source_dir=source_dir, bundle=bundle, report=report)
        context.apply()
        conn.commit()
    return report


class _ApplyContext:
    def __init__(self, *, conn: sqlite3.Connection, source_dir: Path, bundle: dict[str, Any], report: dict[str, Any]) -> None:
        self.conn = conn
        self.source_dir = source_dir
        self.bundle = bundle
        self.report = report
        self.now = datetime.now().isoformat(sep=" ", timespec="seconds")
        self.colleges_by_name: dict[str, int] = {}
        self.colleges_by_canonical_name: dict[str, int] = {}
        self.colleges_by_canonical_name_scores: dict[str, int] = {}
        self.colleges_by_code: dict[str, int] = {}
        self.colleges_by_enrollment_code: dict[str, int] = {}
        self.majors_by_name: dict[str, int] = {}
        self.majors_by_code: dict[str, int] = {}
        self.source_docs: dict[str, int] = {}
        self.source_runs: dict[str, int] = {}
        self.records_path: Path | None = bundle.get("records_path")
        self.records_source_path = _relative_path(self.records_path) if self.records_path else None
        self.records_source_sha = _sha256_file(self.records_path) if self.records_path and self.records_path.exists() else None
        self._path_meta_cache: dict[str, tuple[str | None, str | None]] = {}
        self.complete_specialty_scores = _build_complete_specialty_score_map(bundle["complete_database"])
        self.touched_admission_scopes: set[tuple[int, str, str]] = set()
        self.touched_plan_scopes: set[tuple[int, str, str]] = set()

    def apply(self) -> None:
        self._load_entity_maps()
        self._register_source_documents()
        self._import_complete_database_profiles()
        self._import_school_summary()
        self._import_school_profiles()
        self._import_specialty_score_profiles()
        self._deactivate_touched_business_rows()
        self._import_category_records()
        self._import_art_plan_detail_records()
        self._finish_import_runs()

    def _load_entity_maps(self) -> None:
        self.colleges_by_name.clear()
        self.colleges_by_canonical_name.clear()
        self.colleges_by_canonical_name_scores.clear()
        self.colleges_by_code.clear()
        for row in self.conn.execute("SELECT id, name, college_code, province, city FROM college"):
            college_id = int(row["id"])
            self.colleges_by_name[_normalize_key(row["name"])] = college_id
            code = _clean_text(row["college_code"])
            self._remember_canonical_college_name(
                row["name"],
                college_id,
                row["province"],
                row["city"],
                source_priority=40 if code else 10,
            )
            if code:
                self.colleges_by_code[_normalize_code(code)] = college_id
        for row in self._iter_gaokao_college_alias_rows():
            college_id = self._find_existing_college_for_gaokao_row(row)
            if college_id is None:
                continue
            self._remember_canonical_college_name(
                row["college_name"],
                college_id,
                row["province"],
                row["city"],
                source_priority=100,
            )
            for alias_name in _decode_json_string_list(row["alias_names"]):
                self._remember_canonical_college_name(
                    alias_name,
                    college_id,
                    row["province"],
                    row["city"],
                    source_priority=100,
                )
        for row in self.conn.execute(
            "SELECT college_id, enrollment_code FROM college_profile_detail WHERE enrollment_code IS NOT NULL"
        ):
            code = _clean_text(row["enrollment_code"])
            if code:
                self.colleges_by_enrollment_code[_normalize_code(code)] = int(row["college_id"])
        for row in self.conn.execute("SELECT id, name, major_code FROM major"):
            self.majors_by_name[_normalize_key(row["name"])] = int(row["id"])
            code = _clean_text(row["major_code"])
            if code:
                self.majors_by_code[_normalize_code(code)] = int(row["id"])

    def _register_source_documents(self) -> None:
        for source in self.bundle["registerable_sources"]:
            source_id = self._upsert_source_document(source)
            self.source_docs[str(source["path"])] = source_id
            if source.get("create_run"):
                self.source_runs[str(source["path"])] = self._create_import_run(source_id, source["source_type"], source["path"])
        self.report["applied"]["source_documents_upserted"] = len(self.source_docs)

    def _path_meta(self, path: Path | None) -> tuple[str | None, str | None]:
        if path is None:
            return None, None
        key = str(path)
        if key not in self._path_meta_cache:
            self._path_meta_cache[key] = (_relative_path(path), _sha256_file(path) if path.exists() else None)
        return self._path_meta_cache[key]

    def _upsert_source_document(self, source: dict[str, Any]) -> int:
        path = Path(source["path"])
        rel = _relative_path(path)
        file_sha = _sha256_file(path) if path.exists() and path.is_file() else None
        url = f"local:{rel}"
        existing = self.conn.execute(
            """
            SELECT id FROM gaokao_source_document
            WHERE province = ? AND year = ? AND source_type = ? AND url = ?
            """,
            (PROVINCE, int(source["year"]), source["source_type"], url),
        ).fetchone()
        if existing:
            self.conn.execute(
                """
                UPDATE gaokao_source_document
                SET title = ?, official_org = ?, local_file_path = ?, file_sha256 = ?,
                    parser_name = ?, parser_version = ?, status = ?, note = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (
                    source["title"],
                    source["official_org"],
                    rel,
                    file_sha,
                    IMPORTER_NAME,
                    PARSER_VERSION,
                    "file_ready",
                    source.get("note"),
                    int(existing["id"]),
                ),
            )
            return int(existing["id"])
        cursor = self.conn.execute(
            """
            INSERT INTO gaokao_source_document (
                province, year, source_type, title, url, official_org, source_registry_code,
                local_file_path, file_sha256, parser_name, parser_version, status, note,
                created_at, updated_at, is_active
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 1)
            """,
            (
                PROVINCE,
                int(source["year"]),
                source["source_type"],
                source["title"],
                url,
                source["official_org"],
                "gaokao_scraper_local",
                rel,
                file_sha,
                IMPORTER_NAME,
                PARSER_VERSION,
                "file_ready",
                source.get("note"),
            ),
        )
        return int(cursor.lastrowid)

    def _create_import_run(self, source_document_id: int, source_type: str, source_path: Path) -> int:
        cursor = self.conn.execute(
            """
            INSERT INTO gaokao_import_run (
                source_document_id, importer_name, started_at, finished_at, status,
                total_rows, success_rows, failed_rows, skipped_rows, created_rows, updated_rows,
                raw_snapshot_path, note, created_at, updated_at, is_active
            ) VALUES (?, ?, CURRENT_TIMESTAMP, NULL, 'running', 0, 0, 0, 0, 0, 0, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 1)
            """,
            (source_document_id, f"{IMPORTER_NAME}:{source_type}", _relative_path(source_path), "scraper bundle 导入运行。"),
        )
        return int(cursor.lastrowid)

    def _finish_import_runs(self) -> None:
        for source_path, run_id in self.source_runs.items():
            path = Path(source_path)
            total = 0
            success = 0
            if path.name == "all_categories_records.json":
                total = self.report["records"]["total"]
                success = self.report["applied"]["raw_admission_results_upserted"] + self.report["applied"]["raw_enrollment_plans_upserted"]
            elif path.name == "complete_database.json":
                total = self.report["profiles"]["complete_database_schools"]
                success = self.report["applied"]["college_profiles_upserted"]
            self.conn.execute(
                """
                UPDATE gaokao_import_run
                SET finished_at = CURRENT_TIMESTAMP, status = 'success', total_rows = ?, success_rows = ?,
                    failed_rows = ?, skipped_rows = ?, created_rows = ?, updated_rows = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (
                    total,
                    success,
                    len(self.report["conflicts"]),
                    self.report["records"]["skipped"],
                    self.report["applied"]["created_colleges"] + self.report["applied"]["created_majors"],
                    self.report["applied"]["updated_rows"],
                    run_id,
                ),
            )

    def _ensure_college(
        self,
        *,
        name: str,
        enrollment_code: str | None = None,
        national_code: str | None = None,
        province: str | None = None,
        city: str | None = None,
        school_type: str | None = None,
        tags: list[str] | None = None,
        website: str | None = None,
        intro: str | None = None,
        note: str | None = None,
        supports_art: bool = False,
    ) -> int:
        normalized_name = _normalize_key(name)
        college_id = None
        if national_code:
            college_id = self.colleges_by_code.get(_normalize_code(national_code))
        if college_id is None:
            college_id = self.colleges_by_canonical_name.get(_canonical_college_name_key(name))
        if college_id is None:
            college_id = self.colleges_by_name.get(normalized_name)
        if college_id is None and enrollment_code:
            college_id = self.colleges_by_enrollment_code.get(_normalize_code(enrollment_code))
        if college_id is None and enrollment_code:
            by_location = self._find_college_by_name_and_location(
                normalized_name=normalized_name,
                province=province,
                city=city,
            )
            if by_location is not None:
                college_id = by_location
        if college_id is None:
            cursor = self.conn.execute(
                """
                INSERT INTO college (
                    name, college_code, province, city, school_type, school_level_tags_json,
                    intro, website, supports_art, note, created_at, updated_at, is_active
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 1)
                """,
                (
                    name,
                    national_code,
                    province,
                    city,
                    school_type,
                    json.dumps(tags or [], ensure_ascii=False) if tags else None,
                    intro,
                    website,
                    1 if supports_art else 0,
                    note,
                ),
            )
            college_id = int(cursor.lastrowid)
            self.report["applied"]["created_colleges"] += 1
        else:
            self.conn.execute(
                """
                UPDATE college
                SET province = COALESCE(NULLIF(?, ''), province),
                    city = COALESCE(NULLIF(?, ''), city),
                    school_type = COALESCE(NULLIF(?, ''), school_type),
                    school_level_tags_json = COALESCE(?, school_level_tags_json),
                    intro = COALESCE(NULLIF(?, ''), intro),
                    website = COALESCE(NULLIF(?, ''), website),
                    supports_art = CASE WHEN ? THEN 1 ELSE supports_art END,
                    note = COALESCE(NULLIF(?, ''), note),
                    is_active = 1,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (
                    province,
                    city,
                    school_type,
                    json.dumps(tags or [], ensure_ascii=False) if tags else None,
                    intro,
                    website,
                    1 if supports_art else 0,
                    note,
                    college_id,
                ),
            )
            self.report["applied"]["updated_rows"] += 1
        self.colleges_by_name[normalized_name] = college_id
        self._remember_canonical_college_name(name, college_id, province, city)
        if national_code:
            self.colleges_by_code[_normalize_code(national_code)] = college_id
        if enrollment_code:
            self.colleges_by_enrollment_code[_normalize_code(enrollment_code)] = college_id
        return college_id

    def _remember_canonical_college_name(
        self,
        name: Any,
        college_id: int,
        province: Any = None,
        city: Any = None,
        source_priority: int = 0,
    ) -> None:
        key = _canonical_college_name_key(name)
        if not key:
            return
        current_score = _college_canonical_match_score(
            name,
            province=province,
            city=city,
            source_priority=source_priority,
        )
        existing_score = self.colleges_by_canonical_name_scores.get(key)
        if existing_score is None or current_score > existing_score:
            self.colleges_by_canonical_name[key] = college_id
            self.colleges_by_canonical_name_scores[key] = current_score

    def _iter_gaokao_college_alias_rows(self) -> list[sqlite3.Row]:
        if not _table_exists(self.conn, "gaokao_college"):
            return []
        columns = _table_columns(self.conn, "gaokao_college")
        name_column = "college_name" if "college_name" in columns else "name" if "name" in columns else None
        if name_column is None:
            return []
        select_columns = [
            "id",
            "college_code" if "college_code" in columns else "NULL AS college_code",
            f"{name_column} AS college_name",
            "alias_names" if "alias_names" in columns else "NULL AS alias_names",
            "province" if "province" in columns else "NULL AS province",
            "city" if "city" in columns else "NULL AS city",
        ]
        deleted_filter = "COALESCE(is_deleted, 0) = 0" if "is_deleted" in columns else "1 = 1"
        return self.conn.execute(
            f"""
            SELECT {", ".join(select_columns)}
            FROM gaokao_college
            WHERE {deleted_filter}
            ORDER BY id
            """
        ).fetchall()

    def _find_existing_college_for_gaokao_row(self, row: sqlite3.Row) -> int | None:
        code = _clean_text(row["college_code"])
        if code:
            college_id = self.colleges_by_code.get(_normalize_code(code))
            if college_id is not None:
                return college_id
        for candidate_name in [row["college_name"], *_decode_json_string_list(row["alias_names"])]:
            college_id = self.colleges_by_name.get(_normalize_key(candidate_name))
            if college_id is not None:
                return college_id
            college_id = self.colleges_by_canonical_name.get(_canonical_college_name_key(candidate_name))
            if college_id is not None:
                return college_id
        return None

    def _find_college_by_name_and_location(
        self,
        *,
        normalized_name: str,
        province: str | None,
        city: str | None,
    ) -> int | None:
        if not province and not city:
            return None
        if not _table_exists(self.conn, "gaokao_college"):
            return None
        row = self.conn.execute(
            """
            SELECT c.id
            FROM college c
            LEFT JOIN gaokao_college g ON (g.college_code = c.college_code OR g.college_name = c.name)
               AND COALESCE(g.is_deleted, 0) = 0
            WHERE lower(replace(c.name, ' ', '')) = ?
              AND (
                COALESCE(NULLIF(g.province, ''), c.province) = ?
                OR COALESCE(NULLIF(g.city, ''), c.city) = ?
              )
            ORDER BY c.is_active DESC, c.id
            LIMIT 1
            """,
            (normalized_name, province, city),
        ).fetchone()
        return int(row["id"]) if row else None

    def _ensure_major(self, *, name: str, major_code: str | None = None, category: str | None = None) -> int:
        normalized_name = _normalize_key(name)
        major_id = self.majors_by_name.get(normalized_name)
        if major_id is None and major_code:
            major_id = self.majors_by_code.get(_normalize_code(major_code))
        if major_id is None:
            cursor = self.conn.execute(
                """
                INSERT INTO major (
                    name, major_code, category, is_art_related, created_at, updated_at, is_active
                ) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 1)
                """,
                (name, major_code if _looks_like_national_major_code(major_code) else None, category, 1 if _looks_like_art_major(name, category) else 0),
            )
            major_id = int(cursor.lastrowid)
            self.report["applied"]["created_majors"] += 1
        else:
            self.conn.execute(
                """
                UPDATE major
                SET major_code = COALESCE(NULLIF(?, ''), major_code),
                    category = COALESCE(NULLIF(?, ''), category),
                    is_art_related = CASE WHEN ? THEN 1 ELSE is_art_related END,
                    is_active = 1,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (
                    major_code if _looks_like_national_major_code(major_code) else None,
                    category,
                    1 if _looks_like_art_major(name, category) else 0,
                    major_id,
                ),
            )
            self.report["applied"]["updated_rows"] += 1
        self.majors_by_name[normalized_name] = major_id
        if major_code and _looks_like_national_major_code(major_code):
            self.majors_by_code[_normalize_code(major_code)] = major_id
        return major_id

    def _ensure_college_major(self, college_id: int, major_id: int, note: str | None = None) -> None:
        self.conn.execute(
            """
            INSERT INTO college_major (college_id, major_id, enrollment_note, created_at, updated_at, is_active)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 1)
            ON CONFLICT(college_id, major_id) DO UPDATE SET
                enrollment_note = COALESCE(excluded.enrollment_note, college_major.enrollment_note),
                is_active = 1,
                updated_at = CURRENT_TIMESTAMP
            """,
            (college_id, major_id, note),
        )

    def _import_complete_database_profiles(self) -> None:
        path = self.bundle.get("complete_database_path")
        source_sha = _sha256_file(path) if path and path.exists() else None
        source_path = _relative_path(path) if path else None
        for school in self.bundle["complete_database"]:
            name = _clean_text(school.get("name"))
            if not name:
                continue
            enrollment_code = _clean_text(school.get("school_code"))
            tags = _school_tags(school)
            college_id = self._ensure_college(
                name=name,
                enrollment_code=enrollment_code,
                province=_clean_text(school.get("cdn_province")),
                city=_clean_text(school.get("cdn_city")),
                school_type=_clean_text(school.get("cdn_type")),
                tags=tags,
                website=_clean_text(school.get("website")),
                note=f"[gaokao-scraper] complete_database；性质={_clean_text(school.get('cdn_nature')) or ''}",
                supports_art=_looks_like_art_college(name, _clean_text(school.get("cdn_type"))),
            )
            self._upsert_college_profile(
                college_id=college_id,
                enrollment_code=enrollment_code,
                is_985=bool(school.get("f985")),
                is_211=bool(school.get("f211")),
                is_dual_class=bool(_clean_text(school.get("dual_class"))),
                official_website=_clean_text(school.get("website")),
                phone=_clean_text(school.get("phone")),
                raw_json=school,
                source_path=source_path,
                source_sha256=source_sha,
            )
            for year_text, summary in (school.get("years") or {}).items():
                year = _parse_int(year_text)
                if year is None:
                    continue
                self._upsert_college_year_summary(
                    college_id=college_id,
                    year=year,
                    total_plan_count=_parse_int(summary.get("total_plan")),
                    specialty_count=_parse_int(summary.get("specialty_count")),
                    min_rank=_parse_int(summary.get("min_rank")),
                    estimated_min_score=_parse_float(summary.get("approx_min_score")),
                    source_note="[gaokao-scraper] complete_database 汇总；按一分一段估算" if summary.get("approx_min_score") is not None else "[gaokao-scraper] complete_database 汇总",
                    raw_json=summary,
                    source_path=source_path,
                    source_sha256=source_sha,
                )
                for specialty in summary.get("specialties") or []:
                    major_name = _clean_text(specialty.get("name"))
                    if not major_name:
                        continue
                    major_id = self._ensure_major(name=major_name)
                    self._ensure_college_major(college_id, major_id, "[gaokao-scraper] complete_database 专业关系")
                    self._upsert_major_profile(
                        major_id=major_id,
                        summary=None,
                        raw_json=specialty,
                        source_path=source_path,
                        source_sha256=source_sha,
                    )
                    self._upsert_college_major_profile(
                        college_id=college_id,
                        major_id=major_id,
                        school_major_feature=_specialty_feature_text(specialty),
                        raw_json=specialty,
                        source_path=source_path,
                        source_sha256=source_sha,
                    )

    def _import_school_summary(self) -> None:
        path = self.bundle.get("school_summary_path")
        if not path or not path.exists():
            return
        source_sha = _sha256_file(path)
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                name = _clean_text(row.get("school_name"))
                if not name:
                    continue
                college_id = self._ensure_college(
                    name=name,
                    enrollment_code=_clean_text(row.get("school_code")),
                    province=_clean_text(row.get("province")),
                    city=_clean_text(row.get("city")),
                    school_type=_clean_text(row.get("type")),
                    tags=_school_tags(row),
                    note=f"[gaokao-scraper] school_summary_complete；性质={_clean_text(row.get('nature')) or ''}",
                )
                for key, value in row.items():
                    match = re.match(r"total_plan_(\d{4})", key or "")
                    if not match:
                        continue
                    year = int(match.group(1))
                    self._upsert_college_year_summary(
                        college_id=college_id,
                        year=year,
                        total_plan_count=_parse_int(value),
                        specialty_count=_parse_int(row.get(f"specialty_count_{year}")),
                        min_rank=_parse_int(row.get(f"min_rank_{year}")),
                        estimated_min_score=_parse_float(row.get(f"approx_min_score_{year}")),
                        source_note="[gaokao-scraper] school_summary_complete 汇总；按一分一段估算",
                        raw_json=row,
                        source_path=_relative_path(path),
                        source_sha256=source_sha,
                    )

    def _import_school_profiles(self) -> None:
        for path in self.bundle["school_profile_paths"]:
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except Exception as exc:
                self.report["conflicts"].append({"path": str(path), "reason": f"院校画像 JSON 读取失败: {exc}"})
                continue
            data = payload.get("data") if isinstance(payload, dict) else None
            if not isinstance(data, dict):
                continue
            name = _clean_text(data.get("name"))
            if not name:
                continue
            enrollment_code = _clean_text(data.get("zs_code")) or _clean_text(data.get("code_enroll"))
            national_code = _clean_text(data.get("data_code"))
            college_id = self._ensure_college(
                name=name,
                enrollment_code=enrollment_code,
                national_code=national_code,
                province=_clean_text(data.get("province_name")),
                city=_clean_text(data.get("city_name")),
                school_type=_clean_text(data.get("type_name")),
                tags=_school_tags(data),
                website=_clean_text(data.get("school_site")) or _clean_text(data.get("weiwangzhan")),
                intro=_clean_text(data.get("content")),
                note=f"[gaokao-scraper] data/schools；性质={_clean_text(data.get('school_nature_name')) or ''}",
                supports_art=_looks_like_art_college(name, _clean_text(data.get("type_name"))),
            )
            self._upsert_college_profile(
                college_id=college_id,
                enrollment_code=enrollment_code,
                authority_department=_clean_text(data.get("belong")),
                education_level=_clean_text(data.get("level_name")) or _clean_text(data.get("school_type_name")),
                is_985=_flag_true(data.get("f985")),
                is_211=_flag_true(data.get("f211")),
                is_dual_class=_dual_class_true(data),
                ruanke_rank=_parse_positive_int(data.get("ruanke_rank")),
                eol_rank=_parse_positive_int(data.get("eol_rank")),
                area=_format_area(data.get("area")),
                master_program_count=_parse_positive_int(data.get("num_master")) or _parse_positive_int(data.get("num_master2")),
                doctor_program_count=_parse_positive_int(data.get("num_doctor")) or _parse_positive_int(data.get("num_doctor2")),
                official_website=_clean_text(data.get("school_site")) or _clean_text(data.get("weiwangzhan")),
                admission_website=_clean_text(data.get("site")),
                phone=_clean_text(data.get("phone")) or _clean_text(data.get("school_phone")),
                email=_clean_text(data.get("email")) or _clean_text(data.get("school_email")),
                address=_clean_text(data.get("address")),
                summary=_clean_text(data.get("content")),
                raw_json=data,
                source_path=_relative_path(path),
                source_sha256=_sha256_file(path),
            )

    def _import_specialty_score_profiles(self) -> None:
        for path in self.bundle["specialty_score_paths"]:
            source_path, source_sha = self._path_meta(path)
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except Exception as exc:
                self.report["conflicts"].append({"path": str(path), "reason": f"专业分 JSON 读取失败: {exc}"})
                continue
            school_name = _clean_text(payload.get("name"))
            if not school_name:
                continue
            college_id = self._ensure_college(name=school_name)
            year = _parse_int(payload.get("year"))
            school_row = payload.get("schoolRow") or {}
            if isinstance(school_row, dict) and year:
                self._upsert_college_year_summary(
                    college_id=college_id,
                    year=year,
                    min_rank=_parse_int(school_row.get("min_section")),
                    estimated_min_score=_parse_float(school_row.get("min")),
                    source_note="[gaokao-scraper] specialty_scores 学校最低分/位次",
                    raw_json=school_row,
                    source_path=source_path,
                    source_sha256=source_sha,
                )
            for specialty in payload.get("specialties") or []:
                if not isinstance(specialty, dict):
                    continue
                major_name = _clean_text(specialty.get("name"))
                if not major_name:
                    continue
                major_id = self._ensure_major(name=major_name)
                self._ensure_college_major(college_id, major_id, "[gaokao-scraper] specialty_scores 专业关系")
                self._upsert_major_profile(
                    major_id=major_id,
                    summary=None,
                    raw_json=specialty,
                    source_path=source_path,
                    source_sha256=source_sha,
                )
                self._upsert_college_major_profile(
                    college_id=college_id,
                    major_id=major_id,
                    school_major_feature=_specialty_score_feature_text(specialty),
                    raw_json=specialty,
                    source_path=source_path,
                    source_sha256=source_sha,
                )

    def _upsert_college_profile(self, *, college_id: int, **values: Any) -> None:
        existing = self.conn.execute(
            "SELECT id FROM college_profile_detail WHERE college_id = ?",
            (college_id,),
        ).fetchone()
        payload = _profile_payload(values)
        if existing:
            self.conn.execute(
                """
                UPDATE college_profile_detail
                SET enrollment_code = COALESCE(?, enrollment_code),
                    authority_department = COALESCE(?, authority_department),
                    education_level = COALESCE(?, education_level),
                    is_985 = CASE WHEN ? THEN 1 ELSE is_985 END,
                    is_211 = CASE WHEN ? THEN 1 ELSE is_211 END,
                    is_dual_class = CASE WHEN ? THEN 1 ELSE is_dual_class END,
                    ruanke_rank = COALESCE(?, ruanke_rank),
                    eol_rank = COALESCE(?, eol_rank),
                    area = COALESCE(?, area),
                    master_program_count = COALESCE(?, master_program_count),
                    doctor_program_count = COALESCE(?, doctor_program_count),
                    official_website = COALESCE(?, official_website),
                    admission_website = COALESCE(?, admission_website),
                    phone = COALESCE(?, phone),
                    email = COALESCE(?, email),
                    address = COALESCE(?, address),
                    summary = COALESCE(?, summary),
                    raw_json = COALESCE(?, raw_json),
                    source_path = COALESCE(?, source_path),
                    source_sha256 = COALESCE(?, source_sha256),
                    is_active = 1,
                    updated_at = CURRENT_TIMESTAMP
                WHERE college_id = ?
                """,
                (*payload, college_id),
            )
        else:
            self.conn.execute(
                """
                INSERT INTO college_profile_detail (
                    college_id, enrollment_code, authority_department, education_level,
                    is_985, is_211, is_dual_class, ruanke_rank, eol_rank, area,
                    master_program_count, doctor_program_count, official_website, admission_website,
                    phone, email, address, summary, raw_json, source_path, source_sha256,
                    created_at, updated_at, is_active
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 1)
                """,
                (college_id, *payload),
            )
        self.report["applied"]["college_profiles_upserted"] += 1

    def _upsert_college_year_summary(self, *, college_id: int, year: int, **values: Any) -> None:
        self.conn.execute(
            """
            INSERT INTO college_year_summary (
                college_id, province, year, total_plan_count, specialty_count, min_rank,
                estimated_min_score, source_note, raw_json, source_path, source_sha256,
                created_at, updated_at, is_active
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 1)
            ON CONFLICT(college_id, province, year) DO UPDATE SET
                total_plan_count = COALESCE(excluded.total_plan_count, college_year_summary.total_plan_count),
                specialty_count = COALESCE(excluded.specialty_count, college_year_summary.specialty_count),
                min_rank = COALESCE(excluded.min_rank, college_year_summary.min_rank),
                estimated_min_score = COALESCE(excluded.estimated_min_score, college_year_summary.estimated_min_score),
                source_note = COALESCE(excluded.source_note, college_year_summary.source_note),
                raw_json = COALESCE(excluded.raw_json, college_year_summary.raw_json),
                source_path = COALESCE(excluded.source_path, college_year_summary.source_path),
                source_sha256 = COALESCE(excluded.source_sha256, college_year_summary.source_sha256),
                is_active = 1,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                college_id,
                PROVINCE,
                year,
                values.get("total_plan_count"),
                values.get("specialty_count"),
                values.get("min_rank"),
                values.get("estimated_min_score"),
                values.get("source_note"),
                _json_or_none(values.get("raw_json")),
                values.get("source_path"),
                values.get("source_sha256"),
            ),
        )
        self.report["applied"]["year_summaries_upserted"] += 1

    def _upsert_major_profile(self, *, major_id: int, **values: Any) -> None:
        self.conn.execute(
            """
            INSERT INTO major_profile_detail (
                major_id, major_code, education_level, schooling_years, direction, tags_json,
                summary, raw_json, source_path, source_sha256, created_at, updated_at, is_active
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 1)
            ON CONFLICT(major_id) DO UPDATE SET
                major_code = COALESCE(excluded.major_code, major_profile_detail.major_code),
                education_level = COALESCE(excluded.education_level, major_profile_detail.education_level),
                schooling_years = COALESCE(excluded.schooling_years, major_profile_detail.schooling_years),
                direction = COALESCE(excluded.direction, major_profile_detail.direction),
                tags_json = COALESCE(excluded.tags_json, major_profile_detail.tags_json),
                summary = COALESCE(excluded.summary, major_profile_detail.summary),
                raw_json = COALESCE(excluded.raw_json, major_profile_detail.raw_json),
                source_path = COALESCE(excluded.source_path, major_profile_detail.source_path),
                source_sha256 = COALESCE(excluded.source_sha256, major_profile_detail.source_sha256),
                is_active = 1,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                major_id,
                values.get("major_code"),
                values.get("education_level"),
                values.get("schooling_years"),
                values.get("direction"),
                _json_or_none(values.get("tags_json")),
                values.get("summary"),
                _json_or_none(values.get("raw_json")),
                values.get("source_path"),
                values.get("source_sha256"),
            ),
        )
        self.report["applied"]["major_profiles_upserted"] += 1

    def _upsert_college_major_profile(self, *, college_id: int, major_id: int, **values: Any) -> None:
        self.conn.execute(
            """
            INSERT INTO college_major_profile (
                college_id, major_id, school_major_feature, is_national_feature, is_provincial_feature,
                is_key_major, schooling_years, education_level, raw_json, source_path, source_sha256,
                created_at, updated_at, is_active
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 1)
            ON CONFLICT(college_id, major_id) DO UPDATE SET
                school_major_feature = COALESCE(excluded.school_major_feature, college_major_profile.school_major_feature),
                is_national_feature = CASE WHEN excluded.is_national_feature THEN 1 ELSE college_major_profile.is_national_feature END,
                is_provincial_feature = CASE WHEN excluded.is_provincial_feature THEN 1 ELSE college_major_profile.is_provincial_feature END,
                is_key_major = CASE WHEN excluded.is_key_major THEN 1 ELSE college_major_profile.is_key_major END,
                schooling_years = COALESCE(excluded.schooling_years, college_major_profile.schooling_years),
                education_level = COALESCE(excluded.education_level, college_major_profile.education_level),
                raw_json = COALESCE(excluded.raw_json, college_major_profile.raw_json),
                source_path = COALESCE(excluded.source_path, college_major_profile.source_path),
                source_sha256 = COALESCE(excluded.source_sha256, college_major_profile.source_sha256),
                is_active = 1,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                college_id,
                major_id,
                values.get("school_major_feature"),
                1 if values.get("is_national_feature") else 0,
                1 if values.get("is_provincial_feature") else 0,
                1 if values.get("is_key_major") else 0,
                values.get("schooling_years"),
                values.get("education_level"),
                _json_or_none(values.get("raw_json")),
                values.get("source_path"),
                values.get("source_sha256"),
            ),
        )
        self.report["applied"]["college_major_profiles_upserted"] += 1

    def _deactivate_touched_business_rows(self) -> None:
        for record in self.bundle["category_records"]:
            if _is_obviously_header_record(record):
                continue
            year = _parse_int(record.get("year"))
            if year not in {2023, 2024, 2025}:
                continue
            category = _clean_text(record.get("category")) or "普通类"
            batch = _normalize_batch(_clean_text(record.get("batch")), category)
            student_type = _normalize_student_type(category)
            if _can_import_application_admission(record):
                self.touched_admission_scopes.add((year, batch, student_type))
            elif _can_import_application_plan(record):
                self.touched_plan_scopes.add((year, batch, student_type))
        for year, batch, student_type in self.touched_admission_scopes:
            self.conn.execute(
                """
                UPDATE admission_record
                SET is_active = 0, updated_at = CURRENT_TIMESTAMP
                WHERE province = ? AND year = ? AND batch = ? AND student_type = ? AND is_active = 1
                """,
                (PROVINCE, year, batch, student_type),
            )
        for year, batch, student_type in self.touched_plan_scopes:
            self.conn.execute(
                """
                UPDATE enrollment_plan
                SET is_active = 0, updated_at = CURRENT_TIMESTAMP
                WHERE province = ? AND year = ? AND batch = ? AND student_type = ? AND is_active = 1
                """,
                (PROVINCE, year, batch, student_type),
            )

    def _import_category_records(self) -> None:
        records_path = self.bundle.get("records_path")
        source_document_id = self.source_docs.get(str(records_path)) if records_path else None
        import_run_id = self.source_runs.get(str(records_path)) if records_path else None
        for record in self.bundle["category_records"]:
            if _is_obviously_header_record(record):
                continue
            if _is_admission_like(record):
                self._upsert_admission_record(record, source_document_id, import_run_id)
            elif _is_plan_like(record):
                self._upsert_plan_record(record, source_document_id, import_run_id)
            else:
                self.report["records"]["skipped"] += 1

    def _upsert_admission_record(self, record: dict[str, Any], source_document_id: int | None, import_run_id: int | None) -> None:
        year = _parse_int(record.get("year"))
        school_name = _clean_text(record.get("school_name"))
        major_name = _clean_text(record.get("specialty_name"))
        if year is None or not school_name or not major_name:
            self.report["conflicts"].append({"record": record, "reason": "投档/录取记录缺少年份、院校或专业，已跳过应用表。"})
            return
        if _is_misaligned_major_as_school_record(record):
            self.report["conflicts"].append({"record": record, "reason": "疑似专业名错位为院校名，已跳过应用表。"})
            self._upsert_raw_admission(record, source_document_id, import_run_id)
            return
        category = _clean_text(record.get("category")) or "普通类"
        data_type = _clean_text(record.get("data_type")) or ""
        if data_type == "录取情况表" and category == "春季高考" and _clean_text(record.get("school_code") or "").isdigit():
            self._upsert_raw_admission(record, source_document_id, import_run_id)
            self.report["conflicts"].append({"record": record, "reason": "春季高考录取情况表疑似类别矩阵，已只入 raw。"})
            return
        batch = _normalize_batch(_clean_text(record.get("batch")), category)
        enrollment_code = _clean_text(record.get("school_code"))
        specialty_code = _clean_text(record.get("specialty_code"))
        college_id = self._ensure_college(
            name=school_name,
            enrollment_code=enrollment_code,
            supports_art=category in {"艺术类", "体育类"},
        )
        major_id = self._ensure_major(name=major_name)
        self._ensure_college_major(college_id, major_id, "[gaokao-scraper] 投档/录取关系")
        raw_min_score = _parse_float(record.get("min_score"))
        score_from_rank_field = _score_from_rank_field(record)
        min_rank = None if score_from_rank_field is not None else _parse_positive_int(record.get("min_rank"))
        app_min_score, estimated = self._resolve_app_min_score(record)
        if score_from_rank_field is not None:
            app_min_score = score_from_rank_field
            estimated = False
        plan_count = _parse_int(record.get("plan_count"))
        student_type = _normalize_student_type(category)
        art_track = _normalize_art_track(category)
        source_note = _source_note(record, estimated=estimated, score_from_rank_field=score_from_rank_field is not None)

        self._upsert_raw_admission(record, source_document_id, import_run_id)
        self.conn.execute(
            """
            INSERT INTO admission_record (
                year, province, batch, college_id, major_id, student_type, art_track, subject_requirement,
                min_score, min_rank, plan_count, source_note, source_document_id, import_run_id,
                created_at, updated_at, is_active
            ) VALUES (?, ?, ?, ?, ?, ?, ?, NULL, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 1)
            ON CONFLICT(year, province, batch, college_id, major_id, student_type, art_track) DO UPDATE SET
                min_score = excluded.min_score,
                min_rank = excluded.min_rank,
                plan_count = excluded.plan_count,
                source_note = excluded.source_note,
                source_document_id = excluded.source_document_id,
                import_run_id = excluded.import_run_id,
                is_active = 1,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                year,
                PROVINCE,
                batch,
                college_id,
                major_id,
                student_type,
                art_track,
                app_min_score if app_min_score is not None else raw_min_score,
                min_rank,
                plan_count,
                source_note,
                source_document_id,
                import_run_id,
            ),
        )
        self._upsert_college_major_profile(
            college_id=college_id,
            major_id=major_id,
            school_major_feature=f"山东{year}{batch}：专业代号 {specialty_code or '-'}，计划 {plan_count or '-'}，最低位次 {min_rank or '-'}",
            raw_json=record,
            source_path=self.records_source_path,
            source_sha256=self.records_source_sha,
        )
        self.report["applied"]["admission_records_upserted"] += 1

    def _upsert_plan_record(self, record: dict[str, Any], source_document_id: int | None, import_run_id: int | None) -> None:
        year = _parse_int(record.get("year"))
        school_name = _clean_text(record.get("school_name"))
        major_name = _clean_text(record.get("specialty_name"))
        plan_count = _parse_int(record.get("plan_count"))
        if year is None or not school_name or not major_name or plan_count is None or plan_count <= 0:
            self.report["conflicts"].append({"record": record, "reason": "招生计划记录缺少年份、院校、专业或有效计划数，已跳过应用表。"})
            self._upsert_raw_plan(record, source_document_id, import_run_id)
            return
        category = _clean_text(record.get("category")) or "普通类"
        batch = _normalize_batch(_clean_text(record.get("batch")), category)
        enrollment_code = _clean_text(record.get("school_code"))
        specialty_code = _clean_text(record.get("specialty_code")) or ""
        college_id = self._ensure_college(name=school_name, enrollment_code=enrollment_code, supports_art=category in {"艺术类", "体育类"})
        major_id = self._ensure_major(name=major_name)
        self._ensure_college_major(college_id, major_id, "[gaokao-scraper] 招生计划关系")
        subject_requirement = self._subject_requirement_for_record(record)
        student_type = _normalize_student_type(category)

        self._upsert_raw_plan(record, source_document_id, import_run_id)
        self.conn.execute(
            """
            INSERT INTO enrollment_plan (
                year, province, batch, exam_mode, college_id, major_id, college_code_snapshot,
                major_group_code, major_name_snapshot, major_code_snapshot, plan_count, subject_requirement,
                student_type, source_note, import_batch_name, source_document_id, import_run_id,
                created_at, updated_at, is_active
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 1)
            ON CONFLICT(year, province, batch, exam_mode, college_id, major_group_code, major_name_snapshot, student_type)
            DO UPDATE SET
                major_id = excluded.major_id,
                college_code_snapshot = excluded.college_code_snapshot,
                major_code_snapshot = excluded.major_code_snapshot,
                plan_count = excluded.plan_count,
                subject_requirement = excluded.subject_requirement,
                source_note = excluded.source_note,
                import_batch_name = excluded.import_batch_name,
                source_document_id = excluded.source_document_id,
                import_run_id = excluded.import_run_id,
                is_active = 1,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                year,
                PROVINCE,
                batch,
                _infer_exam_mode(category),
                college_id,
                major_id,
                enrollment_code,
                specialty_code,
                major_name,
                specialty_code,
                plan_count,
                subject_requirement,
                student_type,
                _source_note(record, estimated=False),
                DATA_VERSION_LABEL,
                source_document_id,
                import_run_id,
            ),
        )
        self.report["applied"]["enrollment_plans_upserted"] += 1

    def _import_art_plan_detail_records(self) -> None:
        for record in self.bundle.get("art_plan_detail_records", []):
            source_path = record.get("_source_path")
            source_document_id = self.source_docs.get(str(source_path)) if source_path else None
            self._upsert_art_plan_detail_record(record, source_document_id, None)

    def _upsert_art_plan_detail_record(
        self,
        record: dict[str, Any],
        source_document_id: int | None,
        import_run_id: int | None,
    ) -> None:
        year = _parse_int(record.get("year"))
        school_name = _clean_text(record.get("school_name"))
        school_code = _clean_text(record.get("school_code"))
        major_snapshot = _clean_text(record.get("specialty_name"))
        base_major_name = _clean_text(record.get("base_specialty_name")) or major_snapshot
        specialty_code = _clean_text(record.get("specialty_code")) or ""
        plan_count = _parse_int(record.get("plan_count"))
        if year is None or not school_name or not major_snapshot or plan_count is None or plan_count <= 0:
            self.report["conflicts"].append({"record": record, "reason": "艺术院校专业计划缺少年份、院校、专业或有效计划数，已跳过应用表。"})
            return

        batch = _clean_text(record.get("batch")) or "艺术类本科批"
        source_path = record.get("_source_path")
        rel_path = _relative_path(source_path) if isinstance(source_path, Path) else None
        college_id = self._ensure_college(
            name=school_name,
            enrollment_code=school_code,
            province=PROVINCE,
            supports_art=True,
        )
        major_id = self._ensure_major(name=base_major_name or major_snapshot, category="艺术学")
        self._ensure_college_major(college_id, major_id, "[gaokao-scraper] 艺术院校专业计划关系")
        source_note = _art_plan_detail_source_note(record)
        self._upsert_raw_art_plan_detail(record, source_document_id, import_run_id, source_note)

        exact = self.conn.execute(
            """
            SELECT id FROM enrollment_plan
            WHERE year = ? AND province = ? AND batch = ? AND exam_mode = ? AND college_id = ?
              AND major_group_code = ? AND major_name_snapshot = ? AND student_type = ?
            LIMIT 1
            """,
            (year, PROVINCE, batch, "3+3", college_id, specialty_code, major_snapshot, "art"),
        ).fetchone()
        fallback_blank = None
        if exact is None and specialty_code:
            fallback_blank = self.conn.execute(
                """
                SELECT id FROM enrollment_plan
                WHERE year = ? AND province = ? AND batch = ? AND exam_mode = ? AND college_id = ?
                  AND COALESCE(major_group_code, '') = '' AND major_name_snapshot = ? AND student_type = ?
                LIMIT 1
                """,
                (year, PROVINCE, batch, "3+3", college_id, major_snapshot, "art"),
            ).fetchone()

        existing_id = int(exact["id"] if exact else fallback_blank["id"]) if (exact or fallback_blank) else None
        if existing_id is not None:
            self.conn.execute(
                """
                UPDATE enrollment_plan
                SET major_id = ?, college_code_snapshot = ?, major_group_code = ?,
                    major_name_snapshot = ?, major_code_snapshot = ?, plan_count = ?,
                    subject_requirement = ?, tuition_fee = ?, schooling_years = ?,
                    source_note = ?, import_batch_name = ?, source_document_id = ?,
                    import_run_id = ?, is_active = 1, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (
                    major_id,
                    school_code,
                    specialty_code,
                    major_snapshot,
                    specialty_code,
                    plan_count,
                    _clean_text(record.get("subject_requirement")),
                    _clean_text(record.get("tuition")),
                    _clean_text(record.get("duration_years")),
                    source_note,
                    ART_PLAN_DETAIL_DATA_VERSION_LABEL,
                    source_document_id,
                    import_run_id,
                    existing_id,
                ),
            )
        else:
            self.conn.execute(
                """
                INSERT INTO enrollment_plan (
                    year, province, batch, exam_mode, college_id, major_id, college_code_snapshot,
                    major_group_code, major_name_snapshot, major_code_snapshot, plan_count,
                    subject_requirement, tuition_fee, schooling_years, student_type, source_note,
                    import_batch_name, source_document_id, import_run_id,
                    created_at, updated_at, is_active
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 1)
                """,
                (
                    year,
                    PROVINCE,
                    batch,
                    "3+3",
                    college_id,
                    major_id,
                    school_code,
                    specialty_code,
                    major_snapshot,
                    specialty_code,
                    plan_count,
                    _clean_text(record.get("subject_requirement")),
                    _clean_text(record.get("tuition")),
                    _clean_text(record.get("duration_years")),
                    "art",
                    source_note,
                    ART_PLAN_DETAIL_DATA_VERSION_LABEL,
                    source_document_id,
                    import_run_id,
                ),
            )
        self._upsert_college_major_profile(
            college_id=college_id,
            major_id=major_id,
            school_major_feature=f"山东{year}{batch}：专业代号 {specialty_code or '-'}，计划 {plan_count}，来源 {rel_path or '-'}",
            schooling_years=_clean_text(record.get("duration_years")),
            raw_json={key: value for key, value in record.items() if not key.startswith("_")},
            source_path=rel_path,
            source_sha256=_sha256_file(source_path) if isinstance(source_path, Path) and source_path.exists() else None,
        )
        self.report["applied"]["art_plan_detail_rows_upserted"] += 1
        self.report["applied"]["enrollment_plans_upserted"] += 1

    def _upsert_raw_admission(self, record: dict[str, Any], source_document_id: int | None, import_run_id: int | None) -> None:
        record_hash = _record_hash("admission", record)
        existing = self.conn.execute(
            "SELECT id FROM gaokao_admission_result WHERE source_record_hash = ? LIMIT 1",
            (record_hash,),
        ).fetchone()
        values = (
            PROVINCE,
            _parse_int(record.get("year")),
            _clean_text(record.get("category")),
            _clean_text(record.get("batch")),
            _round_no(_clean_text(record.get("batch"))),
            _clean_text(record.get("school_code")),
            _clean_text(record.get("school_name")),
            _clean_text(record.get("specialty_code")),
            _clean_text(record.get("specialty_name")),
            _semantic_record_min_score(record),
            _semantic_record_min_rank(record),
            _parse_int(record.get("plan_count")),
            str(record.get("min_rank")) if record.get("min_rank") is not None else None,
            _clean_text(record.get("data_type")),
            self.now,
            self.now,
            "local_scraper",
            "gaokao-scraper all_categories_records.json",
            None,
            self.records_source_path,
            IMPORTER_NAME,
            "pending_review",
            record_hash,
            DATA_VERSION_LABEL,
            source_document_id,
            import_run_id,
        )
        if existing:
            self.conn.execute(
                """
                UPDATE gaokao_admission_result
                SET province = ?, year = ?, candidate_type = ?, batch_name = ?, round_no = ?,
                    college_code_snapshot = ?, college_name_snapshot = ?, major_code_snapshot = ?,
                    major_name_snapshot = ?, min_score = ?, min_rank = ?, plan_count = ?,
                    original_min_rank_text = ?, remark = ?, updated_at = ?, source_level = ?,
                    source_title = ?, source_url = ?, local_source_path = ?, parser_script_name = ?,
                    review_status = ?, source_record_hash = ?, data_version_label = ?,
                    source_document_id = ?, import_run_id = ?
                WHERE id = ?
                """,
                (*values[:14], values[15], *values[16:], int(existing["id"])),
            )
        else:
            self.conn.execute(
                """
                INSERT INTO gaokao_admission_result (
                    province, year, candidate_type, batch_name, round_no, college_code_snapshot,
                    college_name_snapshot, major_code_snapshot, major_name_snapshot, min_score, min_rank,
                    plan_count, original_min_rank_text, remark, created_at, updated_at, source_level,
                    source_title, source_url, local_source_path, parser_script_name, review_status,
                    source_record_hash, data_version_label, source_document_id, import_run_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                values,
            )
        self.report["applied"]["raw_admission_results_upserted"] += 1

    def _upsert_raw_plan(self, record: dict[str, Any], source_document_id: int | None, import_run_id: int | None) -> None:
        record_hash = _record_hash("plan", record)
        existing = self.conn.execute(
            "SELECT id FROM gaokao_admission_plan WHERE source_record_hash = ? LIMIT 1",
            (record_hash,),
        ).fetchone()
        values = (
            PROVINCE,
            _parse_int(record.get("year")),
            _clean_text(record.get("category")),
            _clean_text(record.get("batch")),
            _round_no(_clean_text(record.get("batch"))),
            _normalize_student_type(_clean_text(record.get("category")) or ""),
            _clean_text(record.get("school_code")),
            _clean_text(record.get("school_name")),
            _clean_text(record.get("specialty_code")),
            _clean_text(record.get("specialty_name")),
            _clean_text(record.get("specialty_code")) or "",
            _parse_int(record.get("plan_count")) or 0,
            self._subject_requirement_for_record(record),
            _clean_text(record.get("data_type")),
            self.now,
            self.now,
            "local_scraper",
            "gaokao-scraper all_categories_records.json",
            None,
            self.records_source_path,
            IMPORTER_NAME,
            "pending_review",
            record_hash,
            DATA_VERSION_LABEL,
            source_document_id,
            import_run_id,
        )
        if existing:
            self.conn.execute(
                """
                UPDATE gaokao_admission_plan
                SET province = ?, year = ?, candidate_type = ?, batch_name = ?, round_no = ?,
                    pathway_code = ?, college_code_snapshot = ?, college_name_snapshot = ?,
                    major_code_snapshot = ?, major_name_snapshot = ?, major_group_code = ?, plan_count = ?,
                    subject_requirement_text = ?, major_note = ?, updated_at = ?, source_level = ?,
                    source_title = ?, source_url = ?, local_source_path = ?, parser_script_name = ?,
                    review_status = ?, source_record_hash = ?, data_version_label = ?,
                    source_document_id = ?, import_run_id = ?
                WHERE id = ?
                """,
                (*values[:14], values[15], *values[16:], int(existing["id"])),
            )
        else:
            self.conn.execute(
                """
                INSERT INTO gaokao_admission_plan (
                    province, year, candidate_type, batch_name, round_no, pathway_code,
                    college_code_snapshot, college_name_snapshot, major_code_snapshot,
                    major_name_snapshot, major_group_code, plan_count, subject_requirement_text,
                    major_note, created_at, updated_at, source_level, source_title, source_url,
                    local_source_path, parser_script_name, review_status, source_record_hash,
                    data_version_label, source_document_id, import_run_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                values,
            )
        self.report["applied"]["raw_enrollment_plans_upserted"] += 1

    def _upsert_raw_art_plan_detail(
        self,
        record: dict[str, Any],
        source_document_id: int | None,
        import_run_id: int | None,
        source_note: str,
    ) -> None:
        record_hash = _record_hash("art_plan_detail", record)
        existing = self.conn.execute(
            "SELECT id FROM gaokao_admission_plan WHERE source_record_hash = ? LIMIT 1",
            (record_hash,),
        ).fetchone()
        source_path = record.get("_source_path")
        rel_path = _relative_path(source_path) if isinstance(source_path, Path) else None
        values = (
            PROVINCE,
            _parse_int(record.get("year")),
            "艺术类",
            _clean_text(record.get("batch")),
            _round_no(_clean_text(record.get("batch"))),
            "art",
            _clean_text(record.get("school_code")),
            _clean_text(record.get("school_name")),
            _clean_text(record.get("specialty_code")),
            _clean_text(record.get("specialty_name")),
            _clean_text(record.get("specialty_code")) or "",
            _parse_int(record.get("plan_count")) or 0,
            _clean_text(record.get("subject_requirement")),
            _clean_text(record.get("duration_years")),
            _clean_text(record.get("tuition")),
            source_note,
            _clean_text(record.get("_source_title")),
            f"local:{rel_path}" if rel_path else None,
            rel_path,
            IMPORTER_NAME,
            "pending_review",
            record_hash,
            ART_PLAN_DETAIL_DATA_VERSION_LABEL,
            source_document_id,
            import_run_id,
        )
        if existing:
            self.conn.execute(
                """
                UPDATE gaokao_admission_plan
                SET province = ?, year = ?, candidate_type = ?, batch_name = ?, round_no = ?,
                    pathway_code = ?, college_code_snapshot = ?, college_name_snapshot = ?,
                    major_code_snapshot = ?, major_name_snapshot = ?, major_group_code = ?, plan_count = ?,
                    subject_requirement_text = ?, duration_years = ?, tuition = ?, major_note = ?,
                    updated_at = CURRENT_TIMESTAMP, source_level = 'local_scraper',
                    source_title = ?, source_url = ?, local_source_path = ?, parser_script_name = ?,
                    review_status = ?, source_record_hash = ?, data_version_label = ?,
                    source_document_id = ?, import_run_id = ?
                WHERE id = ?
                """,
                (*values, int(existing["id"])),
            )
        else:
            self.conn.execute(
                """
                INSERT INTO gaokao_admission_plan (
                    province, year, candidate_type, batch_name, round_no, pathway_code,
                    college_code_snapshot, college_name_snapshot, major_code_snapshot,
                    major_name_snapshot, major_group_code, plan_count, subject_requirement_text,
                    duration_years, tuition, major_note, created_at, updated_at, source_level,
                    source_title, source_url, local_source_path, parser_script_name, review_status,
                    source_record_hash, data_version_label, source_document_id, import_run_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'local_scraper', ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                values,
            )
        self.report["applied"]["raw_enrollment_plans_upserted"] += 1

    def _resolve_app_min_score(self, record: dict[str, Any]) -> tuple[float | None, bool]:
        raw = _parse_float(record.get("min_score"))
        if raw is not None:
            return raw, False
        year = _parse_int(record.get("year"))
        rank = _parse_positive_int(record.get("min_rank"))
        school_code = _clean_text(record.get("school_code"))
        specialty_code = _clean_text(record.get("specialty_code"))
        if year and school_code and specialty_code:
            score = self.complete_specialty_scores.get((year, _normalize_code(school_code), _normalize_code(specialty_code)))
            if score is not None:
                return score, True
        if year and rank:
            score = _estimate_score_by_rank(self.conn, year=year, rank=rank)
            if score is not None:
                return score, True
        return None, False

    def _subject_requirement_for_record(self, record: dict[str, Any]) -> str | None:
        year = _parse_int(record.get("year"))
        school_code = _clean_text(record.get("school_code"))
        school_name = _clean_text(record.get("school_name"))
        specialty_code = _clean_text(record.get("specialty_code"))
        specialty_name = _clean_text(record.get("specialty_name"))
        if not year:
            return None
        if school_code and specialty_code:
            value = self.bundle["subject_requirements"].get((year, _normalize_code(school_code), _normalize_code(specialty_code)))
            if value:
                return value
        if school_code and specialty_name:
            value = self.bundle["subject_requirements"].get((year, _normalize_code(school_code), _normalize_key(specialty_name)))
            if value:
                return value
        if school_name and specialty_name:
            value = self.bundle["subject_requirements"].get((year, _normalize_key(school_name), _normalize_key(specialty_name)))
            if value:
                return value
        return None


def _load_bundle(source_dir: Path) -> dict[str, Any]:
    output_final = source_dir / "output_final"
    records_path = output_final / "all_categories_records.json"
    complete_database_path = output_final / "complete_database.json"
    school_summary_path = output_final / "school_summary_complete.csv"
    category_records = _read_json_list(records_path)
    complete_database = _read_json_list(complete_database_path)
    school_profile_paths = sorted((source_dir / "data" / "schools").glob("*.json")) if (source_dir / "data" / "schools").exists() else []
    specialty_score_paths = sorted((source_dir / "data" / "specialty_scores").glob("*.json")) if (source_dir / "data" / "specialty_scores").exists() else []
    art_plan_detail_records = _load_art_plan_detail_records(source_dir)
    registerable_sources = _discover_registerable_sources(
        source_dir,
        records_path=records_path,
        complete_database_path=complete_database_path,
        school_summary_path=school_summary_path,
    )
    subject_requirements = _load_subject_requirements(specialty_score_paths)
    return {
        "records_path": records_path if records_path.exists() else None,
        "complete_database_path": complete_database_path if complete_database_path.exists() else None,
        "school_summary_path": school_summary_path if school_summary_path.exists() else None,
        "category_records": category_records,
        "complete_database": complete_database,
        "school_profile_paths": school_profile_paths,
        "specialty_score_paths": specialty_score_paths,
        "art_plan_detail_records": art_plan_detail_records,
        "registerable_sources": registerable_sources,
        "subject_requirements": subject_requirements,
    }


def _build_report(source_dir: Path, bundle: dict[str, Any]) -> dict[str, Any]:
    records = bundle["category_records"]
    skipped = sum(1 for item in records if _is_obviously_header_record(item))
    return {
        "source_dir": str(source_dir),
        "records": {
            "total": len(records),
            "admission_like": sum(1 for item in records if _is_admission_like(item) and not _is_obviously_header_record(item)),
            "plan_like": sum(1 for item in records if _is_plan_like(item) and not _is_obviously_header_record(item)),
            "skipped": skipped,
        },
        "art_plan_detail": {
            "parsed_rows": len(bundle.get("art_plan_detail_records", [])),
            "positive_rows": sum(1 for item in bundle.get("art_plan_detail_records", []) if (_parse_int(item.get("plan_count")) or 0) > 0),
            "source_files": len({str(item.get("_source_path")) for item in bundle.get("art_plan_detail_records", []) if item.get("_source_path")}),
        },
        "profiles": {
            "complete_database_schools": len(bundle["complete_database"]),
            "school_profile_files": len(bundle["school_profile_paths"]),
            "specialty_score_files": len(bundle["specialty_score_paths"]),
        },
        "source_documents": {
            "registerable": len(bundle["registerable_sources"]),
            "structured_sources": sum(1 for item in bundle["registerable_sources"] if item.get("create_run")),
            "evidence_sources": sum(1 for item in bundle["registerable_sources"] if not item.get("create_run")),
        },
        "conflicts": [],
        "applied": {
            "source_documents_upserted": 0,
            "created_colleges": 0,
            "created_majors": 0,
            "updated_rows": 0,
            "college_profiles_upserted": 0,
            "major_profiles_upserted": 0,
            "college_major_profiles_upserted": 0,
            "year_summaries_upserted": 0,
            "raw_admission_results_upserted": 0,
            "raw_enrollment_plans_upserted": 0,
            "admission_records_upserted": 0,
            "enrollment_plans_upserted": 0,
            "art_plan_detail_rows_upserted": 0,
        },
    }


def _discover_registerable_sources(
    source_dir: Path,
    *,
    records_path: Path,
    complete_database_path: Path,
    school_summary_path: Path,
) -> list[dict[str, Any]]:
    sources: list[dict[str, Any]] = []
    for path, source_type, title in [
        (records_path, "scraper_bundle_records", "gaokao-scraper 汇总投档/计划记录"),
        (complete_database_path, "scraper_profile_database", "gaokao-scraper 院校专业画像汇总"),
        (school_summary_path, "scraper_school_summary", "gaokao-scraper 院校年度汇总"),
    ]:
        if path.exists():
            sources.append(_source_item(path, source_type=source_type, title=title, create_run=True))
    for path in sorted(source_dir.rglob("*")):
        if not path.is_file() or "node_modules" in path.parts:
            continue
        suffix = path.suffix.lower()
        if suffix not in {".xls", ".xlsx", ".docx", ".pdf", ".html", ".htm"}:
            continue
        sources.append(
            _source_item(
                path,
                source_type=f"official_{suffix.lstrip('.')}",
                title=f"gaokao-scraper 本地证据文件 {path.name}",
                create_run=False,
            )
        )
    return sources


def _source_item(path: Path, *, source_type: str, title: str, create_run: bool) -> dict[str, Any]:
    return {
        "path": path,
        "source_type": source_type,
        "title": title,
        "year": _infer_year_from_path(path),
        "official_org": "山东省教育招生考试院 / 本地 gaokao-scraper",
        "note": "本地 gaokao-scraper 目录登记；结构化文件用于导入，网页/PDF/Word/Excel 文件作为来源证据。",
        "create_run": create_run,
    }


def _read_json_list(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    return []


def _load_subject_requirements(paths: list[Path]) -> dict[tuple[int, str, str], str]:
    requirements: dict[tuple[int, str, str], str] = {}
    for path in paths:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        year = _parse_int(payload.get("year"))
        school_id = _clean_text(payload.get("school_id"))
        school_name = _clean_text(payload.get("name"))
        if not year:
            continue
        for specialty in payload.get("specialties") or []:
            if not isinstance(specialty, dict):
                continue
            name = _clean_text(specialty.get("name"))
            requirement = _clean_text(specialty.get("subject_requirement"))
            if name and requirement:
                if school_id:
                    requirements[(year, _normalize_code(school_id), _normalize_key(name))] = requirement
                if school_name:
                    requirements[(year, _normalize_key(school_name), _normalize_key(name))] = requirement
    return requirements


def _load_art_plan_detail_records(source_dir: Path) -> list[dict[str, Any]]:
    data_dir = source_dir / "data" / "all_toudang"
    if not data_dir.exists():
        return []
    records: list[dict[str, Any]] = []
    for path in sorted(data_dir.glob("*.xls*")):
        records.extend(_parse_art_plan_detail_workbook(path))
    return records


def _parse_art_plan_detail_workbook(path: Path) -> list[dict[str, Any]]:
    try:
        table = pd.read_excel(path, header=None, dtype=object)
    except Exception:
        return []
    if table.empty:
        return []
    title = _first_non_empty_cell(table)
    if not _is_art_plan_detail_title(title):
        return []
    header_index = _find_art_plan_detail_header(table)
    if header_index is None:
        return []
    year = _infer_year_from_text(title) or _infer_year_from_path(path)
    batch = _infer_art_plan_detail_batch(title)
    current_school_code: str | None = None
    current_school_name: str | None = None
    records: list[dict[str, Any]] = []
    for row_number in range(header_index + 1, len(table)):
        values = [_clean_text(value) for value in table.iloc[row_number].tolist()]
        if not any(values):
            continue
        first = values[0]
        name_cell = values[1] if len(values) > 1 else None
        subject_requirement = values[2] if len(values) > 2 else None
        duration_years = values[3] if len(values) > 3 else None
        plan_count = _parse_int(values[4] if len(values) > 4 else None)
        tuition = values[5] if len(values) > 5 else None
        if first and name_cell and _looks_like_school_summary_row(first, name_cell, subject_requirement, duration_years, tuition):
            current_school_code = first
            current_school_name = name_cell
            continue
        if not current_school_name or not name_cell or plan_count is None or plan_count <= 0:
            continue
        specialty_code, specialty_name = _split_specialty_code_and_name(name_cell)
        if not specialty_name:
            continue
        records.append(
            {
                "year": year,
                "category": "艺术类",
                "batch": batch,
                "data_type": "院校专业计划",
                "school_code": current_school_code,
                "school_name": current_school_name,
                "specialty_code": specialty_code,
                "specialty_name": specialty_name,
                "base_specialty_name": _base_specialty_name(specialty_name),
                "subject_requirement": subject_requirement,
                "duration_years": duration_years,
                "plan_count": plan_count,
                "tuition": tuition,
                "_source_path": path,
                "_source_title": title,
                "_row_number": row_number + 1,
            }
        )
    return records


def _first_non_empty_cell(table: pd.DataFrame) -> str | None:
    for value in table.to_numpy().flatten().tolist():
        text = _clean_text(value)
        if text:
            return text
    return None


def _is_art_plan_detail_title(title: str | None) -> bool:
    text = title or ""
    return "山东省" in text and "艺术类" in text and "院校专业计划" in text and "计划" in text


def _find_art_plan_detail_header(table: pd.DataFrame) -> int | None:
    for index, row in table.iterrows():
        joined = "|".join(_clean_text(value) or "" for value in row.tolist())
        if "院校代号" in joined and "院校、专业" in joined and "计划数" in joined:
            return int(index)
    return None


def _infer_art_plan_detail_batch(title: str | None) -> str:
    text = title or ""
    if "专科批" in text:
        return "专科批"
    return "本科批"


def _looks_like_school_summary_row(
    first: str | None,
    name_cell: str | None,
    subject_requirement: str | None,
    duration_years: str | None,
    tuition: str | None,
) -> bool:
    if not first or not name_cell:
        return False
    if subject_requirement or duration_years or tuition:
        return False
    return bool(re.fullmatch(r"[A-Z]\d{3}", first.strip(), flags=re.IGNORECASE))


def _split_specialty_code_and_name(value: str | None) -> tuple[str | None, str | None]:
    text = (value or "").strip()
    if not text:
        return None, None
    match = re.match(r"^([A-Za-z0-9]{2})\s*(.+)$", text)
    if match:
        return match.group(1).upper(), match.group(2).strip()
    return None, text


def _base_specialty_name(value: str | None) -> str | None:
    text = (value or "").strip()
    if not text:
        return None
    marker_positions = [position for marker in ("（", "(") if (position := text.find(marker)) >= 0]
    if marker_positions:
        text = text[: min(marker_positions)]
    return text.strip() or None


def _build_complete_specialty_score_map(items: list[dict[str, Any]]) -> dict[tuple[int, str, str], float]:
    scores: dict[tuple[int, str, str], float] = {}
    for school in items:
        school_code = _clean_text(school.get("school_code"))
        if not school_code:
            continue
        for year_text, summary in (school.get("years") or {}).items():
            year = _parse_int(year_text)
            if year is None:
                continue
            for specialty in summary.get("specialties") or []:
                code = _clean_text(specialty.get("code"))
                score = _parse_float(specialty.get("approx_score"))
                if code and score is not None:
                    scores[(year, _normalize_code(school_code), _normalize_code(code))] = score
    return scores


def _ensure_raw_tables(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS gaokao_admission_result (
            province TEXT NOT NULL,
            year INTEGER NOT NULL,
            candidate_type TEXT,
            batch_name TEXT,
            round_no TEXT,
            college_id INTEGER,
            college_code_snapshot TEXT,
            college_name_snapshot TEXT,
            major_id INTEGER,
            major_code_snapshot TEXT,
            major_name_snapshot TEXT,
            min_score NUMERIC,
            min_rank INTEGER,
            avg_score NUMERIC,
            max_score NUMERIC,
            control_line NUMERIC,
            plan_count INTEGER,
            actual_filed_count INTEGER,
            original_min_rank_text TEXT,
            remark TEXT,
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            source_level TEXT,
            source_title TEXT,
            source_url TEXT,
            local_source_path TEXT,
            parser_script_name TEXT,
            published_at TEXT,
            review_status TEXT,
            source_record_hash TEXT,
            data_version_label TEXT,
            import_batch_id INTEGER,
            source_document_id INTEGER,
            import_run_id INTEGER
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS ix_gaokao_admission_result_source_record_hash ON gaokao_admission_result (source_record_hash)")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS gaokao_admission_plan (
            province TEXT NOT NULL,
            year INTEGER NOT NULL,
            candidate_type TEXT,
            batch_name TEXT,
            round_no TEXT,
            pathway_code TEXT,
            enrollment_type TEXT,
            education_level TEXT,
            college_id INTEGER,
            college_code_snapshot TEXT,
            college_name_snapshot TEXT,
            major_id INTEGER,
            major_code_snapshot TEXT,
            major_name_snapshot TEXT,
            major_group_code TEXT,
            plan_count INTEGER,
            duration_years TEXT,
            tuition TEXT,
            campus TEXT,
            subject_requirement_text TEXT,
            subject_requirement_code TEXT,
            special_plan_tag TEXT,
            major_note TEXT,
            authority_scope TEXT,
            plan_scope TEXT,
            update_type TEXT,
            merge_status TEXT,
            parse_confidence TEXT,
            original_major_text TEXT,
            original_update_text TEXT,
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            source_level TEXT,
            source_title TEXT,
            source_url TEXT,
            local_source_path TEXT,
            parser_script_name TEXT,
            published_at TEXT,
            review_status TEXT,
            source_record_hash TEXT,
            data_version_label TEXT,
            import_batch_id INTEGER,
            source_document_id INTEGER,
            import_run_id INTEGER
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS ix_gaokao_admission_plan_source_record_hash ON gaokao_admission_plan (source_record_hash)")


def _ensure_required_profile_tables(conn: sqlite3.Connection) -> None:
    required = {"college_profile_detail", "college_year_summary", "major_profile_detail", "college_major_profile"}
    existing = {row["name"] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    missing = sorted(required - existing)
    if missing:
        raise RuntimeError(f"数据库缺少画像表 {', '.join(missing)}，请先运行 Alembic 迁移。")


def _table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    return bool(
        conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,),
        ).fetchone()
    )


def _table_columns(conn: sqlite3.Connection, table_name: str) -> set[str]:
    return {str(row["name"]) for row in conn.execute(f'PRAGMA table_info("{table_name}")').fetchall()}


def _backup_database(db_path: Path) -> Path:
    backup_dir = db_path.parent / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"{db_path.stem}_before_gaokao_scraper_bundle_{timestamp}.db"
    with sqlite3.connect(str(db_path)) as source, sqlite3.connect(str(backup_path)) as target:
        source.backup(target)
    return backup_path


def _estimate_score_by_rank(conn: sqlite3.Connection, *, year: int, rank: int) -> float | None:
    if not _table_exists(conn, "score_rank_segment"):
        return None
    row = conn.execute(
        """
        SELECT score
        FROM score_rank_segment
        WHERE province = ? AND year = ? AND cumulative_count IS NOT NULL AND cumulative_count >= ?
        ORDER BY score DESC
        LIMIT 1
        """,
        (PROVINCE, year, rank),
    ).fetchone()
    return _parse_float(row["score"]) if row else None


def _profile_payload(values: dict[str, Any]) -> tuple[Any, ...]:
    return (
        values.get("enrollment_code"),
        values.get("authority_department"),
        values.get("education_level"),
        1 if values.get("is_985") else 0,
        1 if values.get("is_211") else 0,
        1 if values.get("is_dual_class") else 0,
        values.get("ruanke_rank"),
        values.get("eol_rank"),
        values.get("area"),
        values.get("master_program_count"),
        values.get("doctor_program_count"),
        values.get("official_website"),
        values.get("admission_website"),
        values.get("phone"),
        values.get("email"),
        values.get("address"),
        values.get("summary"),
        _json_or_none(values.get("raw_json")),
        values.get("source_path"),
        values.get("source_sha256"),
    )


def _is_admission_like(record: dict[str, Any]) -> bool:
    data_type = _clean_text(record.get("data_type")) or ""
    return "投档" in data_type or "录取" in data_type


def _is_plan_like(record: dict[str, Any]) -> bool:
    data_type = _clean_text(record.get("data_type")) or ""
    batch = _clean_text(record.get("batch")) or ""
    return "计划" in data_type or "院校计划" in batch


def _can_import_application_admission(record: dict[str, Any]) -> bool:
    if not _is_admission_like(record):
        return False
    category = _clean_text(record.get("category")) or ""
    data_type = _clean_text(record.get("data_type")) or ""
    if data_type == "录取情况表" and category == "春季高考" and _clean_text(record.get("school_code") or "").isdigit():
        return False
    return bool(
        _parse_int(record.get("year")) is not None
        and _clean_text(record.get("school_name"))
        and _clean_text(record.get("specialty_name"))
    )


def _can_import_application_plan(record: dict[str, Any]) -> bool:
    if not _is_plan_like(record):
        return False
    plan_count = _parse_int(record.get("plan_count"))
    return bool(
        _parse_int(record.get("year")) is not None
        and _clean_text(record.get("school_name"))
        and _clean_text(record.get("specialty_name"))
        and plan_count is not None
        and plan_count > 0
    )


def _is_obviously_header_record(record: dict[str, Any]) -> bool:
    joined = " ".join(str(record.get(key) or "") for key in ("school_name", "school_code", "specialty_name", "specialty_code"))
    return any(keyword in joined for keyword in ("院校、专业", "院校代号", "专业（类）名称", "备注"))


def _normalize_batch(batch: str | None, category: str) -> str:
    text = (batch or "").strip() or "未知批次"
    text = text.replace("院校计划", "")
    if category == "普通类":
        if text == "常规批第1次":
            return "常规批"
        if text == "常规批第2次":
            return "常规批第2次"
        if text == "常规批第3次":
            return "常规批第3次"
    return text


def _normalize_student_type(category: str) -> str:
    mapping = {
        "普通类": "general",
        "艺术类": "art",
        "体育类": "sports",
        "春季高考": "spring_exam",
        "高职": "independent_recruitment",
        "单独招生": "independent_recruitment",
        "综合评价招生": "comprehensive_evaluation",
    }
    return mapping.get((category or "").strip(), (category or "").strip() or "general")


def _normalize_art_track(category: str) -> str:
    if category == "体育类":
        return "sports"
    if category == "艺术类":
        return "art"
    return ""


def _infer_exam_mode(category: str) -> str:
    if category == "春季高考":
        return "春季高考"
    return "3+3"


def _source_note(record: dict[str, Any], *, estimated: bool, score_from_rank_field: bool = False) -> str:
    parts = [
        "[gaokao-scraper]",
        f"category={_clean_text(record.get('category')) or ''}",
        f"data_type={_clean_text(record.get('data_type')) or ''}",
        f"batch={_clean_text(record.get('batch')) or ''}",
    ]
    if estimated:
        parts.append("最低分按一分一段估算")
    if score_from_rank_field:
        parts.append("投档分字段识别为最低分")
    return "；".join(part for part in parts if part)


def _art_plan_detail_source_note(record: dict[str, Any]) -> str:
    parts = [
        "[gaokao-scraper]",
        "category=艺术类",
        "data_type=院校专业计划",
        f"batch={_clean_text(record.get('batch')) or ''}",
        "缺额/新增计划",
    ]
    source_title = _clean_text(record.get("_source_title"))
    if source_title:
        parts.append(f"title={source_title}")
    row_number = _parse_int(record.get("_row_number"))
    if row_number:
        parts.append(f"row={row_number}")
    return "；".join(part for part in parts if part)


def _record_hash(kind: str, record: dict[str, Any]) -> str:
    payload = json.dumps({"kind": kind, "record": record}, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _score_from_rank_field(record: dict[str, Any]) -> float | None:
    category = _clean_text(record.get("category")) or ""
    if category not in {"艺术类", "体育类"}:
        return None
    if _parse_float(record.get("min_score")) is not None:
        return None
    value = _parse_float(record.get("min_rank"))
    if value is None:
        return None
    return value if 100 <= value <= 750 else None


def _semantic_record_min_score(record: dict[str, Any]) -> float | None:
    score_from_rank = _score_from_rank_field(record)
    if score_from_rank is not None:
        return score_from_rank
    return _parse_float(record.get("min_score"))


def _semantic_record_min_rank(record: dict[str, Any]) -> int | None:
    if _score_from_rank_field(record) is not None:
        return None
    return _parse_positive_int(record.get("min_rank"))


def _round_no(batch: str | None) -> str | None:
    if not batch:
        return None
    match = re.search(r"第(\d+)次", batch)
    return match.group(1) if match else None


def _school_tags(row: dict[str, Any]) -> list[str]:
    tags: list[str] = []
    attr_list = row.get("attr_list")
    if isinstance(attr_list, list):
        tags.extend(str(item) for item in attr_list if item)
    if _truthy(row.get("f985")):
        tags.append("985")
    if _truthy(row.get("f211")):
        tags.append("211")
    dual = _clean_text(row.get("dual_class") or row.get("dual_class_name"))
    if dual and dual not in {"0", "2", "38003", "否", "无"}:
        tags.append("双一流" if "双" in dual or dual == "1" else dual)
    return _dedupe(tags)


def _specialty_feature_text(specialty: dict[str, Any]) -> str | None:
    parts = []
    code = _clean_text(specialty.get("code"))
    if code:
        parts.append(f"专业代号 {code}")
    plan = _parse_int(specialty.get("plan"))
    if plan:
        parts.append(f"计划 {plan}")
    rank = _parse_positive_int(specialty.get("min_rank"))
    if rank:
        parts.append(f"最低位次 {rank}")
    score = _parse_float(specialty.get("approx_score"))
    if score is not None:
        parts.append(f"估算最低分 {score:g}")
    return "；".join(parts) if parts else None


def _specialty_score_feature_text(specialty: dict[str, Any]) -> str | None:
    parts = []
    requirement = _clean_text(specialty.get("subject_requirement"))
    if requirement:
        parts.append(f"选科要求 {requirement}")
    score = _parse_float(specialty.get("min_score"))
    if score is not None:
        parts.append(f"最低分 {score:g}")
    rank = _parse_positive_int(specialty.get("min_section"))
    if rank:
        parts.append(f"最低位次 {rank}")
    return "；".join(parts) if parts else None


def _flag_true(value: Any) -> bool:
    return str(value).strip() in {"1", "true", "True", "是"}


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return _flag_true(value)


def _dual_class_true(data: dict[str, Any]) -> bool:
    text = _clean_text(data.get("dual_class_name") or data.get("dual_class"))
    return bool(text and text not in {"0", "2", "38003", "否", "无"})


def _format_area(value: Any) -> str | None:
    current = _clean_text(value)
    if not current or current in {"0", "0.0"}:
        return None
    if current.endswith("亩"):
        return current
    return f"{current}亩"


def _looks_like_art_college(name: str, school_type: str | None) -> bool:
    return "艺术" in name or "体育" in name or "艺术" in (school_type or "") or "体育" in (school_type or "")


def _looks_like_art_major(name: str, category: str | None) -> bool:
    return any(keyword in f"{name} {category or ''}" for keyword in ("艺术", "美术", "音乐", "舞蹈", "传媒", "戏剧", "体育"))


def _looks_like_national_major_code(value: str | None) -> bool:
    if not value:
        return False
    return bool(re.fullmatch(r"\d{6}[A-Z]?", value.strip(), flags=re.IGNORECASE))


def _looks_shandong_enrollment_code(value: str | None) -> bool:
    return bool(value and re.fullmatch(r"[A-Z]\d{3}", value.strip(), flags=re.IGNORECASE))


def _is_misaligned_major_as_school_record(record: dict[str, Any]) -> bool:
    school_name = _clean_text(record.get("school_name")) or ""
    school_code = _clean_text(record.get("school_code")) or ""
    specialty_name = _clean_text(record.get("specialty_name")) or ""
    plan_count = _parse_int(record.get("plan_count"))
    min_rank = _parse_int(record.get("min_rank"))
    min_score = _parse_float(record.get("min_score"))
    looks_like_specialty_name = bool(re.match(r"^[A-Z]{2}\s*[\u4e00-\u9fff]", school_name)) and not any(
        keyword in school_name
        for keyword in ("大学", "学院", "学校", "职业技术学院", "高等专科学校", "研究院")
    )
    code_derived_from_name = bool(school_code and school_name and school_name.startswith(school_code[:2]))
    degree_cell_shifted_to_specialty = specialty_name in {"本科", "专科", "高职", "高职专科"}
    rank_score_swapped = bool(min_score is not None and min_score > 1000 and min_rank is not None and min_rank < 1000)
    zero_plan_in_filing_row = plan_count == 0
    return looks_like_specialty_name and code_derived_from_name and (
        degree_cell_shifted_to_specialty or rank_score_swapped or zero_plan_in_filing_row
    )


def _parse_int(value: Any) -> int | None:
    if value is None:
        return None
    text = str(value).strip().replace(",", "")
    if not text or text.lower() in {"null", "none", "nan"}:
        return None
    try:
        return int(float(text))
    except ValueError:
        return None


def _parse_positive_int(value: Any) -> int | None:
    parsed = _parse_int(value)
    return parsed if parsed and parsed > 0 else None


def _parse_float(value: Any) -> float | None:
    if value is None:
        return None
    text = str(value).strip().replace(",", "")
    if not text or text.lower() in {"null", "none", "nan"}:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _parse_positive_float(value: Any) -> float | None:
    parsed = _parse_float(value)
    return parsed if parsed and parsed > 0 else None


def _clean_text(value: Any) -> str | None:
    if value is None:
        return None
    current = str(value).strip()
    if not current or current.lower() in {"null", "none", "nan"}:
        return None
    return current


def _normalize_key(value: Any) -> str:
    return re.sub(r"\s+", "", str(value or "")).strip().lower()


def _canonical_college_name_key(value: Any) -> str:
    current = _normalize_key(value)
    return current.replace("（", "(").replace("）", ")")


def _college_canonical_match_score(
    name: Any,
    *,
    province: Any = None,
    city: Any = None,
    source_priority: int = 0,
) -> int:
    score = source_priority
    if _clean_text(province):
        score += 3
    if _clean_text(city):
        score += 2
    if " " not in str(name or ""):
        score += 1
    return score


def _normalize_code(value: Any) -> str:
    return re.sub(r"\s+", "", str(value or "")).strip().upper()


def _dedupe(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        current = _clean_text(value)
        if current and current not in seen:
            result.append(current)
            seen.add(current)
    return result


def _json_or_none(value: Any) -> str | None:
    if value is None:
        return None
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)


def _decode_json_string_list(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        current = value.strip()
        if not current:
            return []
        try:
            parsed = json.loads(current)
            if isinstance(parsed, list):
                return [str(item) for item in parsed]
        except Exception:
            return [current]
    if isinstance(value, list):
        return [str(item) for item in value]
    return []


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _relative_path(path: Path | None) -> str | None:
    if path is None:
        return None
    try:
        return str(path.resolve().relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def _infer_year_from_path(path: Path) -> int:
    match = re.search(r"(20\d{2})", str(path))
    return int(match.group(1)) if match else 0


def _infer_year_from_text(value: str | None) -> int | None:
    match = re.search(r"(20\d{2})", value or "")
    return int(match.group(1)) if match else None


def main() -> None:
    parser = argparse.ArgumentParser(description="导入本地 gaokao-scraper 数据包到 data/app.db")
    parser.add_argument("--source-dir", type=Path, default=Path("/Users/gao/Desktop/高考志愿/gaokao-scraper"))
    parser.add_argument("--db-path", type=Path, default=DEFAULT_DB_PATH)
    parser.add_argument("--dry-run", action="store_true", help="只输出差异和可用性报告，不写数据库")
    parser.add_argument("--apply", action="store_true", help="执行写库导入")
    parser.add_argument("--json", action="store_true", help="以 JSON 输出报告")
    parser.add_argument("--no-backup", action="store_true", help="apply 时跳过默认数据库备份")
    args = parser.parse_args()
    dry_run = args.dry_run or not args.apply
    report = run_import(
        source_dir=args.source_dir,
        db_path=args.db_path,
        dry_run=dry_run,
        apply=args.apply,
        json_output=args.json,
        no_backup=args.no_backup,
    )
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, default=str))
    else:
        print(f"模式：{report['mode']}")
        print(f"结构化记录：{report['records']['total']} 条")
        print(f"投档/录取类：{report['records']['admission_like']} 条")
        print(f"计划类：{report['records']['plan_like']} 条")
        print(f"可登记来源：{report['source_documents']['registerable']} 个")
        if report.get("backup_path"):
            print(f"备份：{report['backup_path']}")
        if report.get("conflicts"):
            print(f"冲突/跳过：{len(report['conflicts'])} 条")


if __name__ == "__main__":
    main()
