from __future__ import annotations

import json
import re
import sqlite3
from datetime import datetime
from pathlib import Path

from app.importers.admissions import AdmissionImporter
from app.importers.enrollment_plans import EnrollmentPlanImporter


PROVINCE_ALIASES = {
    "sd": "山东",
    "shandong": "山东",
    "山东省": "山东",
}
SYNC_NOTE_PREFIX = "[gaokao-materialize]"
ART_RELATED_TYPES = {"art", "sports"}


def materialize_gaokao_structured_tables(
    db_path: Path,
    *,
    backup_dir: Path | None = None,
) -> dict[str, object]:
    if not db_path.exists():
        raise FileNotFoundError(f"database not found: {db_path}")

    backup_path = None
    if backup_dir is not None:
        backup_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"{db_path.stem}_before_gaokao_materialize_{timestamp}.db"
        backup_sqlite_database(db_path, backup_path)

    with sqlite3.connect(str(db_path)) as conn:
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.create_function("_compact_chinese_college_name", 1, _compact_chinese_college_name)
        stats = {
            "colleges_upserted": _upsert_colleges(conn),
            "majors_upserted": _upsert_majors(conn),
            "admission_records_upserted": _upsert_admission_records(conn),
            "enrollment_plans_upserted": _upsert_enrollment_plans(conn),
            "college_majors_upserted": _upsert_college_major_links(conn),
        }
        conn.commit()

        final_counts = {
            "college": _count_rows(conn, "college"),
            "college_alias": _count_rows(conn, "college_alias"),
            "major": _count_rows(conn, "major"),
            "admission_record": _count_rows(conn, "admission_record"),
            "enrollment_plan": _count_rows(conn, "enrollment_plan"),
            "college_major": _count_rows(conn, "college_major"),
        }

    return {
        "db_path": str(db_path),
        "backup_path": str(backup_path) if backup_path else None,
        "stats": stats,
        "final_counts": final_counts,
    }


def backup_sqlite_database(source_path: Path, backup_path: Path) -> None:
    with sqlite3.connect(str(source_path)) as source_conn, sqlite3.connect(str(backup_path)) as backup_conn:
        source_conn.backup(backup_conn)


def _upsert_colleges(conn: sqlite3.Connection) -> int:
    rows = conn.execute(
        """
        SELECT
            college_code,
            college_name,
            alias_names,
            province,
            city,
            school_type,
            level_tags,
            official_site,
            summary,
            affiliation,
            education_level,
            school_nature
        FROM gaokao_college
        WHERE COALESCE(is_deleted, 0) = 0 AND COALESCE(status, 'active') != 'deleted'
        ORDER BY id
        """
    ).fetchall()

    alias_rows: list[tuple[int, str]] = []

    for row in rows:
        raw_name = _clean_text(row["college_name"])
        aliases = _decode_json_string_list(row["alias_names"])
        name = _preferred_college_display_name(raw_name, aliases)
        if not name:
            continue
        note = _compose_college_note(row)
        supports_art = 1 if _looks_like_art_college(name, row["school_type"]) else 0
        conn.execute(
            """
            INSERT INTO college (
                name, college_code, province, city, school_type,
                school_level_tags_json, intro, website, supports_art, note, is_active
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
            ON CONFLICT(name) DO UPDATE SET
                college_code = excluded.college_code,
                province = excluded.province,
                city = excluded.city,
                school_type = excluded.school_type,
                school_level_tags_json = excluded.school_level_tags_json,
                intro = excluded.intro,
                website = excluded.website,
                supports_art = excluded.supports_art,
                note = excluded.note,
                is_active = 1
            """,
            (
                name,
                _clean_text(row["college_code"]),
                _normalize_province(row["province"]),
                _clean_text(row["city"]),
                _clean_text(row["school_type"]),
                _clean_json_text(row["level_tags"]),
                _clean_text(row["summary"]),
                _clean_text(row["official_site"]),
                supports_art,
                note,
            ),
        )
        college_id = conn.execute("SELECT id FROM college WHERE name = ?", (name,)).fetchone()[0]
        for alias_name in [raw_name, *aliases]:
            cleaned_alias = _clean_text(alias_name)
            if cleaned_alias and cleaned_alias != name:
                alias_rows.append((college_id, cleaned_alias))

    conn.execute(
        """
        INSERT INTO college (name, province, note, is_active)
        SELECT DISTINCT
            college_name_snapshot,
            CASE lower(COALESCE(province, ''))
                WHEN 'sd' THEN '山东'
                WHEN 'shandong' THEN '山东'
                ELSE province
            END,
            ?,
            1
        FROM (
            SELECT province, _compact_chinese_college_name(college_name_snapshot) AS college_name_snapshot
            FROM gaokao_admission_plan
            UNION
            SELECT province, _compact_chinese_college_name(college_name_snapshot) AS college_name_snapshot
            FROM gaokao_admission_result
        ) raw_names
        WHERE COALESCE(college_name_snapshot, '') != ''
          AND NOT EXISTS (SELECT 1 FROM college c WHERE c.name = raw_names.college_name_snapshot)
        """,
        (f"{SYNC_NOTE_PREFIX} 来自原始录取/计划快照的占位院校",),
    )

    for college_id, alias_name in alias_rows:
        conn.execute(
            """
            INSERT INTO college_alias (college_id, alias_name, is_active)
            VALUES (?, ?, 1)
            ON CONFLICT(college_id, alias_name) DO UPDATE SET is_active = 1
            """,
            (college_id, alias_name),
        )

    art_ids: set[int] = set()
    for row in conn.execute(
        """
        SELECT c.id, raw.candidate_type
        FROM college c
        JOIN (
            SELECT _compact_chinese_college_name(college_name_snapshot) AS college_name, candidate_type FROM gaokao_admission_plan
            UNION ALL
            SELECT _compact_chinese_college_name(college_name_snapshot) AS college_name, candidate_type FROM gaokao_admission_result
        ) raw
            ON raw.college_name = c.name
        """
    ).fetchall():
        category = _normalize_admission_category(row["candidate_type"])
        if category["student_type"] in ART_RELATED_TYPES:
            art_ids.add(int(row["id"]))
    if art_ids:
        conn.executemany(
            'UPDATE college SET supports_art = 1 WHERE id = ?',
            [(college_id,) for college_id in sorted(art_ids)],
        )

    return len(rows)


def _upsert_majors(conn: sqlite3.Connection) -> int:
    rows = conn.execute(
        """
        SELECT major_code, major_name, discipline_category, major_category, degree_type, summary
        FROM gaokao_major
        WHERE COALESCE(is_deleted, 0) = 0 AND COALESCE(status, 'active') != 'deleted'
        ORDER BY id
        """
    ).fetchall()

    for row in rows:
        name = _clean_text(row["major_name"])
        if not name:
            continue
        category = _clean_text(row["discipline_category"]) or _clean_text(row["major_category"])
        direction = _clean_text(row["degree_type"])
        note = _compose_major_note(row)
        is_art_related = 1 if _looks_like_art_major(name, category) else 0
        conn.execute(
            """
            INSERT INTO major (
                name, major_code, category, direction, career_path,
                is_art_related, note, is_active
            ) VALUES (?, ?, ?, ?, NULL, ?, ?, 1)
            ON CONFLICT(name) DO UPDATE SET
                major_code = excluded.major_code,
                category = excluded.category,
                direction = excluded.direction,
                is_art_related = excluded.is_art_related,
                note = excluded.note,
                is_active = 1
            """,
            (
                name,
                _clean_text(row["major_code"]),
                category,
                direction,
                is_art_related,
                note,
            ),
        )

    conn.execute(
        """
        INSERT INTO major (name, note, is_active, is_art_related)
        SELECT DISTINCT
            major_name_snapshot,
            ?,
            1,
            0
        FROM (
            SELECT major_name_snapshot
            FROM gaokao_admission_plan
            UNION
            SELECT major_name_snapshot
            FROM gaokao_admission_result
        ) raw_names
        WHERE COALESCE(major_name_snapshot, '') != ''
          AND NOT EXISTS (SELECT 1 FROM major m WHERE m.name = raw_names.major_name_snapshot)
        """,
        (f"{SYNC_NOTE_PREFIX} 来自原始录取/计划快照的占位专业",),
    )

    art_major_ids: set[int] = set()
    for row in conn.execute(
        """
        SELECT m.id, raw.candidate_type
        FROM major m
        JOIN (
            SELECT major_name_snapshot AS major_name, candidate_type FROM gaokao_admission_plan
            UNION ALL
            SELECT major_name_snapshot AS major_name, candidate_type FROM gaokao_admission_result
        ) raw
            ON raw.major_name = m.name
        """
    ).fetchall():
        category = _normalize_admission_category(row["candidate_type"])
        if category["student_type"] in ART_RELATED_TYPES:
            art_major_ids.add(int(row["id"]))
    if art_major_ids:
        conn.executemany(
            'UPDATE major SET is_art_related = 1 WHERE id = ?',
            [(major_id,) for major_id in sorted(art_major_ids)],
        )

    return len(rows)


def _upsert_admission_records(conn: sqlite3.Connection) -> int:
    rows = conn.execute(
        """
        SELECT
            r.year,
            r.province,
            r.candidate_type,
            r.batch_name,
            r.college_code_snapshot,
            r.college_name_snapshot,
            r.major_code_snapshot,
            r.major_name_snapshot,
            r.min_score,
            r.min_rank,
            r.avg_score,
            r.max_score,
            r.plan_count,
            r.source_title,
            r.source_url,
            r.data_version_label,
            c.id AS app_college_id,
            m.id AS app_major_id
        FROM gaokao_admission_result r
        JOIN college c
            ON c.name = _compact_chinese_college_name(r.college_name_snapshot)
        LEFT JOIN major m
            ON m.name = r.major_name_snapshot
        """,
    ).fetchall()

    payloads = []
    for row in rows:
        if not row["app_college_id"]:
            continue
        category = _normalize_admission_category(row["candidate_type"])
        payloads.append(
            (
                int(row["year"]),
                _normalize_province(row["province"]),
                _clean_text(row["batch_name"]) or "未知批次",
                int(row["app_college_id"]),
                int(row["app_major_id"]) if row["app_major_id"] is not None else None,
                category["student_type"],
                category["art_track"],
                None,
                row["min_score"],
                row["min_rank"],
                row["avg_score"],
                row["max_score"],
                row["plan_count"],
                _compose_source_note(category["source_label"], row["source_title"], row["source_url"], row["data_version_label"]),
            )
        )

    conn.executemany(
        """
        INSERT INTO admission_record (
            year, province, batch, college_id, major_id,
            student_type, art_track, subject_requirement,
            min_score, min_rank, avg_score, max_score, plan_count, source_note, is_active
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
        ON CONFLICT(year, province, batch, college_id, major_id, student_type, art_track) DO UPDATE SET
            min_score = excluded.min_score,
            min_rank = excluded.min_rank,
            avg_score = excluded.avg_score,
            max_score = excluded.max_score,
            plan_count = excluded.plan_count,
            source_note = excluded.source_note,
            is_active = 1
        """,
        payloads,
    )
    return len(payloads)


def _upsert_enrollment_plans(conn: sqlite3.Connection) -> int:
    rows = conn.execute(
        """
        SELECT
            p.year,
            p.province,
            p.candidate_type,
            p.batch_name,
            p.college_code_snapshot,
            p.college_name_snapshot,
            p.major_code_snapshot,
            p.major_name_snapshot,
            p.major_group_code,
            p.plan_count,
            p.subject_requirement_text,
            p.tuition,
            p.duration_years,
            p.campus,
            p.source_title,
            p.source_url,
            p.data_version_label,
            c.id AS app_college_id,
            m.id AS app_major_id
        FROM gaokao_admission_plan p
        JOIN college c
            ON c.name = _compact_chinese_college_name(p.college_name_snapshot)
        LEFT JOIN major m
            ON m.name = p.major_name_snapshot
        """,
    ).fetchall()

    payloads = []
    for row in rows:
        if not row["app_college_id"]:
            continue
        category = _normalize_plan_category(row["candidate_type"])
        province = _normalize_province(row["province"])
        payloads.append(
            (
                int(row["year"]),
                province,
                _clean_text(row["batch_name"]) or "未知批次",
                _infer_exam_mode(province, category["source_label"]),
                int(row["app_college_id"]),
                int(row["app_major_id"]) if row["app_major_id"] is not None else None,
                _clean_text(row["college_code_snapshot"]),
                _clean_text(row["major_group_code"]) or "",
                _clean_text(row["major_name_snapshot"]) or "",
                _clean_text(row["major_code_snapshot"]),
                int(row["plan_count"]) if row["plan_count"] is not None else 0,
                _clean_text(row["subject_requirement_text"]),
                _clean_text(row["tuition"]),
                _clean_text(row["duration_years"]),
                _clean_text(row["campus"]),
                category["student_type"],
                _compose_source_note(category["source_label"], row["source_title"], row["source_url"], row["data_version_label"]),
                _clean_text(row["data_version_label"]),
            )
        )

    conn.executemany(
        """
        INSERT INTO enrollment_plan (
            year, province, batch, exam_mode, college_id, major_id,
            college_code_snapshot, major_group_code, major_name_snapshot, major_code_snapshot,
            plan_count, subject_requirement, tuition_fee, schooling_years, training_location,
            student_type, source_note, import_batch_name, is_active
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
        ON CONFLICT(year, province, batch, exam_mode, college_id, major_group_code, major_name_snapshot, student_type) DO UPDATE SET
            major_id = excluded.major_id,
            college_code_snapshot = excluded.college_code_snapshot,
            major_code_snapshot = excluded.major_code_snapshot,
            plan_count = excluded.plan_count,
            subject_requirement = excluded.subject_requirement,
            tuition_fee = excluded.tuition_fee,
            schooling_years = excluded.schooling_years,
            training_location = excluded.training_location,
            source_note = excluded.source_note,
            import_batch_name = excluded.import_batch_name,
            is_active = 1
        """,
        payloads,
    )
    return len(payloads)


def _upsert_college_major_links(conn: sqlite3.Connection) -> int:
    rows = conn.execute(
        """
        SELECT DISTINCT college_id, major_id
        FROM (
            SELECT college_id, major_id FROM admission_record
            UNION
            SELECT college_id, major_id FROM enrollment_plan
        )
        WHERE major_id IS NOT NULL
        """
    ).fetchall()
    payloads = [(int(row["college_id"]), int(row["major_id"])) for row in rows]
    conn.executemany(
        """
        INSERT INTO college_major (college_id, major_id, enrollment_note, is_active)
        VALUES (?, ?, ?, 1)
        ON CONFLICT(college_id, major_id) DO UPDATE SET is_active = 1
        """,
        [(college_id, major_id, f"{SYNC_NOTE_PREFIX} 由高考原始录取/计划关系补齐") for college_id, major_id in payloads],
    )
    return len(payloads)


def _count_rows(conn: sqlite3.Connection, table: str) -> int:
    return conn.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]


def _normalize_province(value: object) -> str | None:
    current = _clean_text(value)
    if not current:
        return None
    normalized = PROVINCE_ALIASES.get(current.lower())
    return normalized or current


def _clean_text(value: object) -> str | None:
    if value is None:
        return None
    current = str(value).strip()
    return current or None


def _compact_chinese_college_name(value: object) -> str | None:
    current = _clean_text(value)
    if not current:
        return None
    return re.sub(r"(?<=[\u4e00-\u9fff])\s+(?=[\u4e00-\u9fff])", "", current)


def _preferred_college_display_name(raw_name: object, aliases: list[str]) -> str | None:
    name = _clean_text(raw_name)
    if not name:
        return None
    compacted = _compact_chinese_college_name(name)
    if compacted and compacted != name:
        for alias in aliases:
            cleaned_alias = _clean_text(alias)
            if cleaned_alias == compacted:
                return compacted
    return name


def _clean_json_text(value: object) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        current = value.strip()
        return current or None
    try:
        return json.dumps(value, ensure_ascii=False)
    except Exception:
        return None


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


def _compose_college_note(row: sqlite3.Row) -> str | None:
    notes = [SYNC_NOTE_PREFIX]
    for label, raw in [
        ("隶属", row["affiliation"]),
        ("层次", row["education_level"]),
        ("性质", row["school_nature"]),
    ]:
        value = _clean_text(raw)
        if value:
            notes.append(f"{label}:{value}")
    return "；".join(notes)


def _compose_major_note(row: sqlite3.Row) -> str | None:
    notes = [SYNC_NOTE_PREFIX]
    summary = _clean_text(row["summary"])
    if summary:
        notes.append(summary)
    return "；".join(notes)


def _compose_source_note(
    candidate_type: str,
    source_title: object,
    source_url: object,
    data_version_label: object,
) -> str:
    segments = [SYNC_NOTE_PREFIX, f"candidate_type={candidate_type}"]
    title = _clean_text(source_title)
    if title:
        segments.append(f"title={title}")
    url = _clean_text(source_url)
    if url:
        segments.append(f"url={url}")
    version_label = _clean_text(data_version_label)
    if version_label:
        segments.append(f"version={version_label}")
    return "；".join(segments)


def _looks_like_art_college(name: str, school_type: object) -> bool:
    school_type_text = _clean_text(school_type) or ""
    return "艺术" in name or "艺术" in school_type_text


def _looks_like_art_major(name: str, category: str | None) -> bool:
    category_text = category or ""
    joined = f"{name} {category_text}"
    return any(keyword in joined for keyword in ("艺术", "美术", "音乐", "舞蹈", "传媒", "戏剧", "体育"))


def _infer_exam_mode(province: str | None, candidate_type: str | None = None) -> str:
    if candidate_type == "春季高考":
        return "春季高考"
    if province == "山东":
        return "3+3"
    if province in {"北京", "天津", "上海", "浙江", "海南"}:
        return "3+3"
    return "3+3"


def _normalize_admission_category(value: object) -> dict[str, str | None]:
    category = AdmissionImporter._normalize_student_category(_clean_text(value))
    return {
        "student_type": category.student_type,
        "art_track": category.art_track or "",
        "source_label": _clean_text(value) or category.student_type,
    }


def _normalize_plan_category(value: object) -> dict[str, str | None]:
    category = EnrollmentPlanImporter._normalize_student_category(_clean_text(value))
    return {
        "student_type": category.student_type,
        "source_label": _clean_text(value) or category.student_type,
    }
