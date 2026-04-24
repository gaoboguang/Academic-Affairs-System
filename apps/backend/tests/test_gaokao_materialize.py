from __future__ import annotations

import sqlite3
from pathlib import Path

from app.models import Base
from sqlalchemy import create_engine
from app.utils.gaokao_materialize import materialize_gaokao_structured_tables


def _create_minimal_raw_tables(db_path: Path) -> None:
    with sqlite3.connect(db_path) as conn:
        conn.executescript(
            """
            CREATE TABLE gaokao_college (
                id INTEGER PRIMARY KEY,
                college_code TEXT,
                college_name TEXT NOT NULL,
                alias_names TEXT,
                province TEXT,
                city TEXT,
                school_type TEXT,
                level_tags TEXT,
                official_site TEXT,
                summary TEXT,
                affiliation TEXT,
                education_level TEXT,
                school_nature TEXT,
                status TEXT NOT NULL,
                is_deleted BOOLEAN NOT NULL
            );

            CREATE TABLE gaokao_major (
                id INTEGER PRIMARY KEY,
                major_code TEXT,
                major_name TEXT NOT NULL,
                discipline_category TEXT,
                major_category TEXT,
                degree_type TEXT,
                summary TEXT,
                status TEXT NOT NULL,
                is_deleted BOOLEAN NOT NULL,
                is_special_major BOOLEAN NOT NULL,
                is_controlled_major BOOLEAN NOT NULL
            );

            CREATE TABLE gaokao_admission_result (
                id INTEGER PRIMARY KEY,
                province TEXT NOT NULL,
                year INTEGER NOT NULL,
                candidate_type TEXT,
                batch_name TEXT,
                college_code_snapshot TEXT,
                college_name_snapshot TEXT,
                major_code_snapshot TEXT,
                major_name_snapshot TEXT,
                min_score REAL,
                min_rank INTEGER,
                avg_score REAL,
                max_score REAL,
                plan_count INTEGER,
                source_title TEXT,
                source_url TEXT,
                data_version_label TEXT
            );

            CREATE TABLE gaokao_admission_plan (
                id INTEGER PRIMARY KEY,
                province TEXT NOT NULL,
                year INTEGER NOT NULL,
                candidate_type TEXT,
                batch_name TEXT,
                college_name_snapshot TEXT,
                major_name_snapshot TEXT,
                college_code_snapshot TEXT,
                major_code_snapshot TEXT,
                major_group_code TEXT,
                plan_count INTEGER,
                subject_requirement_text TEXT,
                tuition TEXT,
                duration_years TEXT,
                campus TEXT,
                source_title TEXT,
                source_url TEXT,
                data_version_label TEXT
            );
            """
        )
        conn.execute(
            """
            INSERT INTO gaokao_college (
                id, college_code, college_name, alias_names, province, city,
                school_type, level_tags, official_site, summary, affiliation,
                education_level, school_nature, status, is_deleted
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                1,
                "A001",
                "测试大学",
                '["测试大学（分校）"]',
                "sd",
                "济南市",
                "综合",
                '["双一流"]',
                "https://example.edu",
                "学校简介",
                "教育厅",
                "undergrad",
                "公办",
                "active",
                0,
            ),
        )
        conn.execute(
            """
            INSERT INTO gaokao_college (
                id, college_code, college_name, alias_names, province, city,
                school_type, level_tags, official_site, summary, affiliation,
                education_level, school_nature, status, is_deleted
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                2,
                "A002",
                "测试艺术学院",
                '["测试艺术学院（老校区）"]',
                "sd",
                "青岛市",
                "艺术",
                '["艺术类"]',
                "https://art.example.edu",
                "艺术院校简介",
                "教育厅",
                "undergrad",
                "公办",
                "active",
                0,
            ),
        )
        conn.execute(
            """
            INSERT INTO gaokao_major (
                id, major_code, major_name, discipline_category, major_category,
                degree_type, summary, status, is_deleted, is_special_major, is_controlled_major
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                1,
                "080901",
                "计算机科学与技术",
                "工学",
                "计算机类",
                "工学学士",
                "专业简介",
                "active",
                0,
                0,
                0,
            ),
        )
        conn.execute(
            """
            INSERT INTO gaokao_major (
                id, major_code, major_name, discipline_category, major_category,
                degree_type, summary, status, is_deleted, is_special_major, is_controlled_major
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                2,
                "130502",
                "视觉传达设计",
                "艺术学",
                "设计学类",
                "艺术学学士",
                "艺术专业简介",
                "active",
                0,
                0,
                0,
            ),
        )
        conn.execute(
            """
            INSERT INTO gaokao_admission_result (
                id, province, year, candidate_type, batch_name,
                college_code_snapshot, college_name_snapshot, major_code_snapshot, major_name_snapshot,
                min_score, min_rank, avg_score, max_score, plan_count, source_title, source_url, data_version_label
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                1,
                "sd",
                2025,
                "普通类",
                "常规批",
                "A001",
                "测试大学",
                "080901",
                "计算机科学与技术",
                612,
                10234,
                618,
                625,
                10,
                "结果来源",
                "https://result.example",
                "db-head",
            ),
        )
        conn.execute(
            """
            INSERT INTO gaokao_admission_result (
                id, province, year, candidate_type, batch_name,
                college_code_snapshot, college_name_snapshot, major_code_snapshot, major_name_snapshot,
                min_score, min_rank, avg_score, max_score, plan_count, source_title, source_url, data_version_label
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                2,
                "sd",
                2025,
                "艺术类",
                "艺术类本科批统考",
                "A002",
                "测试艺术学院",
                "130502",
                "视觉传达设计",
                560,
                2034,
                566,
                578,
                6,
                "艺术结果来源",
                "https://art-result.example",
                "db-head",
            ),
        )
        conn.execute(
            """
            INSERT INTO gaokao_admission_plan (
                id, province, year, candidate_type, batch_name,
                college_name_snapshot, major_name_snapshot, college_code_snapshot,
                major_code_snapshot, major_group_code, plan_count, subject_requirement_text,
                tuition, duration_years, campus, source_title, source_url, data_version_label
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                1,
                "sd",
                2025,
                "普通类",
                "常规批",
                "测试大学",
                "计算机科学与技术",
                "A001",
                "080901",
                "01",
                15,
                "物理+化学",
                "6000",
                "4年",
                "主校区",
                "计划来源",
                "https://plan.example",
                "db-head",
            ),
        )
        conn.execute(
            """
            INSERT INTO gaokao_admission_plan (
                id, province, year, candidate_type, batch_name,
                college_name_snapshot, major_name_snapshot, college_code_snapshot,
                major_code_snapshot, major_group_code, plan_count, subject_requirement_text,
                tuition, duration_years, campus, source_title, source_url, data_version_label
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                2,
                "sd",
                2025,
                "春季高考",
                "春季高考本科批",
                "测试大学",
                "计算机科学与技术",
                "A001",
                "080901",
                "SG01",
                20,
                None,
                "5800",
                "4年",
                "春季校区",
                "春季计划来源",
                "https://spring-plan.example",
                "db-head",
            ),
        )
        conn.commit()


def test_materialize_gaokao_structured_tables_is_idempotent(tmp_path: Path) -> None:
    db_path = tmp_path / "materialize.db"
    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(engine)
    engine.dispose()
    _create_minimal_raw_tables(db_path)

    first = materialize_gaokao_structured_tables(db_path)
    second = materialize_gaokao_structured_tables(db_path)

    assert first["stats"]["colleges_upserted"] == 2
    assert first["stats"]["majors_upserted"] == 2
    assert first["stats"]["admission_records_upserted"] == 2
    assert first["stats"]["enrollment_plans_upserted"] == 2
    assert first["stats"]["college_majors_upserted"] == 2
    assert second["final_counts"] == first["final_counts"]

    with sqlite3.connect(db_path) as conn:
        college_count = conn.execute("SELECT COUNT(*) FROM college").fetchone()[0]
        alias_count = conn.execute("SELECT COUNT(*) FROM college_alias").fetchone()[0]
        major_count = conn.execute("SELECT COUNT(*) FROM major").fetchone()[0]
        admission_count = conn.execute("SELECT COUNT(*) FROM admission_record").fetchone()[0]
        plan_count = conn.execute("SELECT COUNT(*) FROM enrollment_plan").fetchone()[0]
        college_major_count = conn.execute("SELECT COUNT(*) FROM college_major").fetchone()[0]
        admission_rows = conn.execute(
            "SELECT province, batch, student_type, art_track, min_rank FROM admission_record ORDER BY student_type, min_rank"
        ).fetchall()
        plan_rows = conn.execute(
            "SELECT province, batch, exam_mode, student_type, subject_requirement FROM enrollment_plan ORDER BY student_type, batch"
        ).fetchall()

    assert college_count == 2
    assert alias_count == 2
    assert major_count == 2
    assert admission_count == 2
    assert plan_count == 2
    assert college_major_count == 2
    assert admission_rows == [
        ("山东", "艺术类本科批统考", "art", "", 2034),
        ("山东", "常规批", "general", "", 10234),
    ]
    assert plan_rows == [
        ("山东", "常规批", "3+3", "general", "物理+化学"),
        ("山东", "春季高考本科批", "春季高考", "spring_exam", None),
    ]
