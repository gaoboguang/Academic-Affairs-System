from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from sqlalchemy import text


def _load_importer_module():
    script_path = Path(__file__).resolve().parents[3] / "scripts" / "import_gaokao_scraper_bundle.py"
    spec = importlib.util.spec_from_file_location("import_gaokao_scraper_bundle", script_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_scraper_bundle_dry_run_does_not_write_database(app, test_settings, tmp_path: Path) -> None:
    module = _load_importer_module()
    source_dir = _build_scraper_fixture(tmp_path)
    with app.state.db.session_scope() as session:
        before_college_count = session.scalar(text("SELECT COUNT(*) FROM college"))

    report = module.run_import(
        source_dir=source_dir,
        db_path=test_settings.db_path,
        dry_run=True,
        apply=False,
        no_backup=True,
    )

    with app.state.db.session_scope() as session:
        after_college_count = session.scalar(text("SELECT COUNT(*) FROM college"))

    assert report["mode"] == "dry-run"
    assert report["records"]["total"] == 2
    assert report["records"]["admission_like"] == 1
    assert report["records"]["plan_like"] == 1
    assert report["profiles"]["complete_database_schools"] == 1
    assert report["source_documents"]["registerable"] >= 2
    assert after_college_count == before_college_count


def test_scraper_bundle_apply_imports_profiles_records_and_sources(app, test_settings, tmp_path: Path) -> None:
    module = _load_importer_module()
    source_dir = _build_scraper_fixture(tmp_path)

    report = module.run_import(
        source_dir=source_dir,
        db_path=test_settings.db_path,
        dry_run=False,
        apply=True,
        no_backup=True,
    )

    with app.state.db.session_scope() as session:
        college_row = session.execute(
            text(
                """
                SELECT c.id, c.name, c.province, p.enrollment_code, p.phone, p.admission_website
                FROM college c
                JOIN college_profile_detail p ON p.college_id = c.id
                WHERE c.name = '山东样例大学'
                """
            )
        ).mappings().one()
        admission_row = session.execute(
            text(
                """
                SELECT ar.batch, ar.min_score, ar.min_rank, ar.source_note
                FROM admission_record ar
                JOIN college c ON c.id = ar.college_id
                WHERE c.name = '山东样例大学'
                """
            )
        ).mappings().one()
        plan_row = session.execute(
            text(
                """
                SELECT ep.batch, ep.plan_count, ep.major_name_snapshot, ep.subject_requirement
                FROM enrollment_plan ep
                JOIN college c ON c.id = ep.college_id
                WHERE c.name = '山东样例大学'
                """
            )
        ).mappings().one()
        summary_count = session.scalar(text("SELECT COUNT(*) FROM college_year_summary"))
        source_count = session.scalar(text("SELECT COUNT(*) FROM gaokao_source_document"))
        raw_result_count = session.scalar(text("SELECT COUNT(*) FROM gaokao_admission_result"))
        raw_plan_count = session.scalar(text("SELECT COUNT(*) FROM gaokao_admission_plan"))

    assert report["mode"] == "apply"
    assert report["backup_path"] is None
    assert report["applied"]["admission_records_upserted"] == 1
    assert report["applied"]["enrollment_plans_upserted"] == 1
    assert college_row["province"] == "山东"
    assert college_row["enrollment_code"] == "A999"
    assert college_row["phone"] == "0531-12345678"
    assert college_row["admission_website"] == "https://zsb.example.edu.cn"
    assert admission_row["batch"] == "常规批"
    assert admission_row["min_score"] == 612
    assert admission_row["min_rank"] == 12345
    assert "按一分一段估算" in admission_row["source_note"]
    assert plan_row["batch"] == "常规批第3次"
    assert plan_row["plan_count"] == 5
    assert plan_row["subject_requirement"] == "物理+化学"
    assert summary_count >= 1
    assert source_count >= 3
    assert raw_result_count == 1
    assert raw_plan_count == 1


def _build_scraper_fixture(tmp_path: Path) -> Path:
    source_dir = tmp_path / "gaokao-scraper"
    output_final = source_dir / "output_final"
    schools_dir = source_dir / "data" / "schools"
    specialty_dir = source_dir / "data" / "specialty_scores"
    docs_dir = source_dir / "data" / "all_toudang"
    output_final.mkdir(parents=True)
    schools_dir.mkdir(parents=True)
    specialty_dir.mkdir(parents=True)
    docs_dir.mkdir(parents=True)

    (output_final / "all_categories_records.json").write_text(
        json.dumps(
            [
                {
                    "year": 2025,
                    "category": "普通类",
                    "batch": "常规批第1次",
                    "data_type": "投档情况表",
                    "specialty_code": "01",
                    "specialty_name": "数据科学与大数据技术",
                    "school_code": "A999",
                    "school_name": "山东样例大学",
                    "plan_count": 12,
                    "min_rank": 12345,
                    "min_score": None,
                },
                {
                    "year": 2025,
                    "category": "普通类",
                    "batch": "常规批第3次院校计划",
                    "data_type": "院校计划",
                    "specialty_code": "02",
                    "specialty_name": "数据科学与大数据技术",
                    "school_code": "A999",
                    "school_name": "山东样例大学",
                    "plan_count": 5,
                    "min_rank": 0,
                    "min_score": None,
                },
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (output_final / "complete_database.json").write_text(
        json.dumps(
            [
                {
                    "name": "山东样例大学",
                    "school_code": "A999",
                    "cdn_province": "山东",
                    "cdn_city": "济南市",
                    "cdn_type": "综合类",
                    "cdn_nature": "公办",
                    "f985": False,
                    "f211": False,
                    "dual_class": "双一流",
                    "website": "https://example.edu.cn",
                    "phone": "0531-12345678",
                    "years": {
                        "2025": {
                            "total_plan": 17,
                            "specialty_count": 2,
                            "min_rank": 12345,
                            "approx_min_score": 612,
                            "specialties": [
                                {
                                    "code": "01",
                                    "name": "数据科学与大数据技术",
                                    "plan": 12,
                                    "min_rank": 12345,
                                    "approx_score": 612,
                                }
                            ],
                        }
                    },
                }
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (output_final / "school_summary_complete.csv").write_text(
        "\ufeffschool_name,school_code,province,city,type,nature,f985,f211,dual_class,total_plan_2025,specialty_count_2025,min_rank_2025,approx_min_score_2025\n"
        "山东样例大学,A999,山东,济南市,综合类,公办,0,0,双一流,17,2,12345,612\n",
        encoding="utf-8",
    )
    (schools_dir / "1001.json").write_text(
        json.dumps(
            {
                "code": "0000",
                "data": {
                    "name": "山东样例大学",
                    "zs_code": "A999",
                    "belong": "山东省教育厅",
                    "level_name": "本科",
                    "f985": "2",
                    "f211": "2",
                    "dual_class_name": "双一流",
                    "ruanke_rank": "120",
                    "eol_rank": "88",
                    "area": 1200,
                    "num_master": "18",
                    "num_doctor": "4",
                    "school_site": "https://example.edu.cn",
                    "site": "https://zsb.example.edu.cn",
                    "phone": "0531-12345678",
                    "email": "zsb@example.edu.cn",
                    "address": "济南市样例路1号",
                    "content": "山东样例大学简介",
                    "province_name": "山东",
                    "city_name": "济南市",
                    "type_name": "综合类",
                    "school_nature_name": "公办",
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (specialty_dir / "school_1001_2025.json").write_text(
        json.dumps(
            {
                "school_id": "1001",
                "name": "山东样例大学",
                "year": 2025,
                "schoolRow": {"batch": "普通类一段", "type": "普通类", "min": 612, "min_section": 12345},
                "specialties": [
                    {
                        "name": "数据科学与大数据技术",
                        "subject_requirement": "物理+化学",
                        "min_score": 612,
                        "min_section": 12345,
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (docs_dir / "2025_fixture.html").write_text("<html>官方页面</html>", encoding="utf-8")
    (docs_dir / "2025_fixture.pdf").write_bytes(b"%PDF-1.4 fixture")
    return source_dir
