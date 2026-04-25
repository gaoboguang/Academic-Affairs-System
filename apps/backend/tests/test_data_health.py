from __future__ import annotations

import sqlite3
from pathlib import Path

from app.utils.data_health import build_data_health_report, format_data_health_report


def test_data_health_report_marks_p0_gaps(tmp_path: Path) -> None:
    db_path = tmp_path / "app.db"
    with sqlite3.connect(db_path) as conn:
        conn.executescript(
            """
            CREATE TABLE alembic_version (version_num TEXT NOT NULL);
            INSERT INTO alembic_version VALUES ('20260424_0015_special_type_rule_schema');

            CREATE TABLE college (id INTEGER PRIMARY KEY);
            CREATE TABLE major (id INTEGER PRIMARY KEY);
            CREATE TABLE college_major (id INTEGER PRIMARY KEY);
            CREATE TABLE enrollment_plan (
                id INTEGER PRIMARY KEY,
                year INTEGER,
                province TEXT,
                student_type TEXT,
                batch TEXT
            );
            CREATE TABLE admission_record (
                id INTEGER PRIMARY KEY,
                year INTEGER,
                province TEXT,
                student_type TEXT,
                batch TEXT
            );
            CREATE TABLE province_volunteer_rule (id INTEGER PRIMARY KEY);
            CREATE TABLE province_score_transform_rule (id INTEGER PRIMARY KEY);
            CREATE TABLE subject_requirement_dict (id INTEGER PRIMARY KEY);
            CREATE TABLE special_type_rule (id INTEGER PRIMARY KEY);
            CREATE TABLE employment_direction (id INTEGER PRIMARY KEY);
            CREATE TABLE major_employment_mapping (id INTEGER PRIMARY KEY);
            CREATE TABLE score_rank_segment (
                id INTEGER PRIMARY KEY,
                year INTEGER,
                province TEXT,
                score_type TEXT
            );
            CREATE TABLE gaokao_score_line (
                id INTEGER PRIMARY KEY,
                year INTEGER,
                province TEXT,
                candidate_type TEXT,
                batch TEXT
            );
            CREATE TABLE gaokao_policy_reference (
                id INTEGER PRIMARY KEY,
                year INTEGER,
                province TEXT,
                policy_type TEXT
            );
            CREATE TABLE gaokao_college_chapter_rule (
                id INTEGER PRIMARY KEY,
                year INTEGER,
                province TEXT,
                review_status TEXT
            );
            """
        )
        conn.executemany(
            "INSERT INTO enrollment_plan (year, province, student_type, batch) VALUES (?, ?, ?, ?)",
            [(2025, "山东", "general", "常规批"), (2025, "山东", "art", "艺术类本科批")],
        )
        conn.execute(
            "INSERT INTO admission_record (year, province, student_type, batch) VALUES (?, ?, ?, ?)",
            (2025, "山东", "general", "常规批"),
        )
        conn.execute(
            "INSERT INTO score_rank_segment (year, province, score_type) VALUES (?, ?, ?)",
            (2025, "sd", "general"),
        )
        conn.execute(
            "INSERT INTO gaokao_score_line (year, province, candidate_type, batch) VALUES (?, ?, ?, ?)",
            (2025, "山东", "普通类", "一段线"),
        )
        conn.execute(
            "INSERT INTO gaokao_policy_reference (year, province, policy_type) VALUES (?, ?, ?)",
            (2025, "山东", "province_rule"),
        )
        conn.execute(
            "INSERT INTO gaokao_college_chapter_rule (year, province, review_status) VALUES (?, ?, ?)",
            (2025, "山东", "pending_manual_review"),
        )

    report = build_data_health_report(db_path)

    assert report["exists"] is True
    assert report["schema_version"] == "20260424_0015_special_type_rule_schema"
    assert report["field_explanations"]
    assert report["delivery_assessment"]["status"] == "blocked"
    assert any("特殊类型已有招生计划但缺专门录取结果" in item for item in report["gaps"])
    assert any("一分一段缺少年份" in item for item in report["gaps"])
    assert any(item["key"] == "gaokao_policy_reference" and item["status"] == "gap" for item in report["tables"])
    assert report["expected_years"] == [2020, 2021, 2022, 2023, 2024, 2025]
    enrollment_coverage = next(item for item in report["coverage"] if item["key"] == "enrollment_plan")
    assert enrollment_coverage["missing_years"] == [2020, 2021, 2022, 2023, 2024]
    assert enrollment_coverage["readiness"] == "partial"
    assert enrollment_coverage["explanation"]
    assert enrollment_coverage["batch_distribution"] == [
        {"key": "常规批", "label": "常规批", "count": 1},
        {"key": "艺术类本科批", "label": "艺术类本科批", "count": 1},
    ]
    assert enrollment_coverage["year_breakdown"][0]["year"] == 2025
    assert enrollment_coverage["year_breakdown"][0]["batches"] == [
        {"key": "常规批", "label": "常规批", "count": 1},
        {"key": "艺术类本科批", "label": "艺术类本科批", "count": 1},
    ]
    art_risk = next(item for item in report["special_type_risks"] if item["key"] == "art")
    assert art_risk["readiness"] == "screening_only"
    assert "缺少该类型专门录取结果" in art_risk["notes"][0]
    admission_audit = next(item for item in report["audit_summary"] if item["key"] == "admission_record")
    assert admission_audit["status"] == "gap"
    assert admission_audit["updated"] == 1
    assert admission_audit["pending_review"] == 0
    assert any("仅可做初筛" in note for note in admission_audit["notes"])
    formatted_report = format_data_health_report(report)
    assert "数据健康检查" in formatted_report
    assert "P0 交付判断" in formatted_report
    assert "考生类型可用性" in formatted_report
    assert "导入审计摘要" in formatted_report


def test_data_health_report_handles_missing_database(tmp_path: Path) -> None:
    report = build_data_health_report(tmp_path / "missing.db")

    assert report["exists"] is False
    assert report["gaps"]
    assert report["audit_summary"] == []
