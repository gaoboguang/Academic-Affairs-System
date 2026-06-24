from __future__ import annotations

import importlib.util
import json
import sqlite3
from pathlib import Path

import pandas as pd
from sqlalchemy import text

from app.models import College


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


def test_scraper_bundle_keeps_college_location_and_skips_misaligned_major_rows(
    app,
    test_settings,
    tmp_path: Path,
) -> None:
    module = _load_importer_module()
    source_dir = _build_scraper_fixture(tmp_path)
    records_path = source_dir / "output_final" / "all_categories_records.json"
    records = json.loads(records_path.read_text(encoding="utf-8"))
    records.extend(
        [
            {
                "year": 2025,
                "category": "普通类",
                "batch": "常规批第1次",
                "data_type": "投档情况表",
                "specialty_code": "01",
                "specialty_name": "酒店管理",
                "school_code": "B123",
                "school_name": "海南样例大学",
                "plan_count": 4,
                "min_rank": 22345,
                "min_score": 580,
            },
            {
                "year": 2025,
                "category": "普通类",
                "batch": "常规批第2次",
                "data_type": "投档情况表",
                "specialty_code": "",
                "specialty_name": "专科",
                "school_code": "AA物联网",
                "school_name": "AA物联网应用技术",
                "plan_count": 0,
                "min_rank": 3,
                "min_score": 620921,
            },
        ]
    )
    records_path.write_text(json.dumps(records, ensure_ascii=False), encoding="utf-8")

    complete_path = source_dir / "output_final" / "complete_database.json"
    complete = json.loads(complete_path.read_text(encoding="utf-8"))
    complete.append(
        {
            "name": "海南样例大学",
            "school_code": "B123",
            "cdn_province": "海南",
            "cdn_city": "三亚市",
            "cdn_type": "综合类",
            "cdn_nature": "民办",
            "f985": False,
            "f211": False,
            "dual_class": "",
            "website": "https://hainan.example.edu.cn",
            "years": {},
        }
    )
    complete_path.write_text(json.dumps(complete, ensure_ascii=False), encoding="utf-8")

    summary_path = source_dir / "output_final" / "school_summary_complete.csv"
    with summary_path.open("a", encoding="utf-8") as handle:
        handle.write("海南样例大学,B123,海南,三亚市,综合类,民办,0,0,,0,0,,\n")

    report = module.run_import(
        source_dir=source_dir,
        db_path=test_settings.db_path,
        dry_run=False,
        apply=True,
        no_backup=True,
    )

    with app.state.db.session_scope() as session:
        hainan_row = session.execute(
            text(
                """
                SELECT province, city
                FROM college
                WHERE name = '海南样例大学'
                """
            )
        ).mappings().one()
        dirty_college_count = session.scalar(text("SELECT COUNT(*) FROM college WHERE name = 'AA物联网应用技术'"))
        dirty_admission_count = session.scalar(
            text(
                """
                SELECT COUNT(*)
                FROM admission_record ar
                JOIN college c ON c.id = ar.college_id
                WHERE c.name = 'AA物联网应用技术'
                """
            )
        )

    assert hainan_row["province"] == "海南"
    assert hainan_row["city"] == "三亚市"
    assert dirty_college_count == 0
    assert dirty_admission_count == 0
    assert any("疑似专业名错位为院校名" in item["reason"] for item in report["conflicts"])


def test_scraper_bundle_reuses_college_by_gaokao_alias_and_preserves_location(
    app,
    test_settings,
    tmp_path: Path,
) -> None:
    module = _load_importer_module()
    source_dir = _build_scraper_fixture(tmp_path)
    records_path = source_dir / "output_final" / "all_categories_records.json"
    records = json.loads(records_path.read_text(encoding="utf-8"))
    records.append(
        {
            "year": 2025,
            "category": "普通类",
            "batch": "常规批第1次",
            "data_type": "投档情况表",
            "specialty_code": "01",
            "specialty_name": "地质学",
            "school_code": "B415",
            "school_name": "中国地质大学(北京)",
            "plan_count": 2,
            "min_rank": 1200,
            "min_score": 640,
        }
    )
    records_path.write_text(json.dumps(records, ensure_ascii=False), encoding="utf-8")

    with sqlite3.connect(test_settings.db_path) as conn:
        conn.execute(
            """
            CREATE TABLE gaokao_college (
                id INTEGER PRIMARY KEY,
                standard_id TEXT,
                college_code TEXT,
                college_name TEXT NOT NULL,
                alias_names TEXT,
                province TEXT,
                city TEXT,
                status TEXT NOT NULL,
                created_at TEXT,
                updated_at TEXT,
                is_deleted BOOLEAN NOT NULL
            )
            """
        )
        conn.execute(
            """
            INSERT INTO gaokao_college (
                standard_id, college_code, college_name, alias_names, province, city,
                status, created_at, updated_at, is_deleted
            ) VALUES (
                'moe-test-cugb', '11415', '中国地质大学（北京）',
                '["中国地质大学(北京)"]', '北京', '北京市',
                'active', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 0
            )
            """
        )

    with app.state.db.session_scope() as session:
        session.add(
            College(
                name="中国地质大学（北京）",
                college_code="11415",
                province="北京",
                city="北京市",
                school_type="理工类",
                is_active=True,
            )
        )

    module.run_import(
        source_dir=source_dir,
        db_path=test_settings.db_path,
        dry_run=False,
        apply=True,
        no_backup=True,
    )

    with app.state.db.session_scope() as session:
        colleges = session.execute(
            text(
                """
                SELECT name, province, city
                FROM college
                WHERE replace(replace(name, '（', '('), '）', ')') = '中国地质大学(北京)'
                ORDER BY name
                """
            )
        ).mappings().all()
        admission_rows = session.execute(
            text(
                """
                SELECT c.name, c.province, c.city
                FROM admission_record ar
                JOIN college c ON c.id = ar.college_id
                WHERE ar.min_rank = 1200
                """
            )
        ).mappings().all()

    assert [row["name"] for row in colleges] == ["中国地质大学（北京）"]
    assert colleges[0]["province"] == "北京"
    assert colleges[0]["city"] == "北京市"
    assert len(admission_rows) == 1
    assert admission_rows[0]["name"] == "中国地质大学（北京）"
    assert admission_rows[0]["province"] == "北京"


def test_scraper_bundle_prefers_canonical_gaokao_college_when_dirty_alias_already_exists(
    app,
    test_settings,
    tmp_path: Path,
) -> None:
    module = _load_importer_module()
    source_dir = _build_scraper_fixture(tmp_path)
    records_path = source_dir / "output_final" / "all_categories_records.json"
    records = json.loads(records_path.read_text(encoding="utf-8"))
    records.append(
        {
            "year": 2025,
            "category": "普通类",
            "batch": "常规批第1次",
            "data_type": "投档情况表",
            "specialty_code": "09",
            "specialty_name": "应用化学",
            "school_code": "D405",
            "school_name": "东华理工 大学",
            "plan_count": 2,
            "min_rank": 1000,
            "min_score": 640,
        }
    )
    records_path.write_text(json.dumps(records, ensure_ascii=False), encoding="utf-8")

    with sqlite3.connect(test_settings.db_path) as conn:
        conn.execute(
            """
            CREATE TABLE gaokao_college (
                id INTEGER PRIMARY KEY,
                standard_id TEXT,
                college_code TEXT,
                college_name TEXT NOT NULL,
                alias_names TEXT,
                province TEXT,
                city TEXT,
                status TEXT NOT NULL,
                created_at TEXT,
                updated_at TEXT,
                is_deleted BOOLEAN NOT NULL
            )
            """
        )
        conn.execute(
            """
            INSERT INTO gaokao_college (
                standard_id, college_code, college_name, alias_names, province, city,
                status, created_at, updated_at, is_deleted
            ) VALUES (
                'moe-test-ecit', '10405', '东华理工大学',
                '["东华理工大学", "东华理工 大学"]', '江西', '抚州市',
                'active', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 0
            )
            """
        )

    with app.state.db.session_scope() as session:
        session.add_all(
            [
                College(
                    name="东华理工大学",
                    college_code="10405",
                    province="江西",
                    city="抚州市",
                    school_type="理工类",
                    is_active=True,
                ),
                College(
                    name="东华理工 大学",
                    province="山东",
                    city="南昌市",
                    school_type="理工类",
                    is_active=True,
                ),
            ]
        )

    module.run_import(
        source_dir=source_dir,
        db_path=test_settings.db_path,
        dry_run=False,
        apply=True,
        no_backup=True,
    )

    with app.state.db.session_scope() as session:
        admission_rows = session.execute(
            text(
                """
                SELECT c.name, c.province, c.city
                FROM admission_record ar
                JOIN college c ON c.id = ar.college_id
                JOIN major m ON m.id = ar.major_id
                WHERE m.name = '应用化学'
                """
            )
        ).mappings().all()

    assert len(admission_rows) == 1
    assert admission_rows[0]["name"] == "东华理工大学"
    assert admission_rows[0]["province"] == "江西"
    assert admission_rows[0]["city"] == "抚州市"


def test_scraper_bundle_treats_art_and_sports_rank_field_as_score_when_score_missing(
    app,
    test_settings,
    tmp_path: Path,
) -> None:
    module = _load_importer_module()
    source_dir = _build_scraper_fixture(tmp_path)
    records_path = source_dir / "output_final" / "all_categories_records.json"
    records = json.loads(records_path.read_text(encoding="utf-8"))
    records.extend(
        [
            {
                "year": 2025,
                "category": "艺术类",
                "batch": "本科批第1次",
                "data_type": "投档情况表",
                "specialty_code": "03",
                "specialty_name": "音乐表演",
                "school_code": "A999",
                "school_name": "山东样例大学",
                "plan_count": 2,
                "min_rank": 482.75,
                "min_score": None,
            },
            {
                "year": 2025,
                "category": "体育类",
                "batch": "常规批第1次",
                "data_type": "投档情况表",
                "specialty_code": "04",
                "specialty_name": "休闲体育",
                "school_code": "A999",
                "school_name": "山东样例大学",
                "plan_count": 3,
                "min_rank": 574.46,
                "min_score": None,
            },
        ]
    )
    records_path.write_text(json.dumps(records, ensure_ascii=False), encoding="utf-8")

    module.run_import(
        source_dir=source_dir,
        db_path=test_settings.db_path,
        dry_run=False,
        apply=True,
        no_backup=True,
    )

    with app.state.db.session_scope() as session:
        rows = session.execute(
            text(
                """
                SELECT ar.student_type, ar.min_score, ar.min_rank, ar.source_note
                FROM admission_record ar
                JOIN major m ON m.id = ar.major_id
                WHERE m.name IN ('音乐表演', '休闲体育')
                ORDER BY ar.student_type
                """
            )
        ).mappings().all()

    assert len(rows) == 2
    assert rows[0]["student_type"] == "art"
    assert rows[0]["min_score"] == 482.75
    assert rows[0]["min_rank"] is None
    assert "投档分字段识别" in rows[0]["source_note"]
    assert rows[1]["student_type"] == "sports"
    assert rows[1]["min_score"] == 574.46
    assert rows[1]["min_rank"] is None
    assert "投档分字段识别" in rows[1]["source_note"]


def test_scraper_bundle_parses_art_plan_detail_workbook_into_enrollment_plan(app, test_settings, tmp_path: Path) -> None:
    module = _load_importer_module()
    source_dir = _build_scraper_fixture(tmp_path)
    docs_dir = source_dir / "data" / "all_toudang"
    _write_art_plan_workbook(docs_dir / "6992.xls")

    report = module.run_import(
        source_dir=source_dir,
        db_path=test_settings.db_path,
        dry_run=False,
        apply=True,
        no_backup=True,
    )

    with app.state.db.session_scope() as session:
        music_plan = session.execute(
            text(
                """
                SELECT ep.year, ep.batch, ep.student_type, ep.major_group_code, ep.major_name_snapshot,
                       ep.plan_count, ep.tuition_fee, ep.source_note, ep.import_batch_name
                FROM enrollment_plan ep
                JOIN college c ON c.id = ep.college_id
                WHERE c.name = '吉林艺术学院' AND ep.major_group_code = '23'
                """
            )
        ).mappings().one()
        music_major = session.execute(
            text(
                """
                SELECT m.name, m.is_art_related
                FROM major m
                JOIN enrollment_plan ep ON ep.major_id = m.id
                JOIN college c ON c.id = ep.college_id
                WHERE c.name = '吉林艺术学院' AND ep.major_group_code = '23'
                """
            )
        ).mappings().one()
        raw_plan_count = session.scalar(
            text(
                """
                SELECT COUNT(*)
                FROM gaokao_admission_plan
                WHERE data_version_label = 'gaokao_scraper_art_plan_detail_20260511'
                  AND year = 2025
                """
            )
        )

    assert report["art_plan_detail"]["parsed_rows"] == 2
    assert report["art_plan_detail"]["positive_rows"] == 2
    assert report["applied"]["art_plan_detail_rows_upserted"] == 2
    assert report["applied"]["enrollment_plans_upserted"] >= 3
    assert music_plan["year"] == 2025
    assert music_plan["batch"] == "本科批"
    assert music_plan["student_type"] == "art"
    assert music_plan["major_group_code"] == "23"
    assert music_plan["major_name_snapshot"].startswith("音乐表演(小号)")
    assert music_plan["plan_count"] == 1
    assert music_plan["tuition_fee"] == "13200"
    assert "缺额/新增计划" in music_plan["source_note"]
    assert music_plan["import_batch_name"] == "gaokao_scraper_art_plan_detail_20260511"
    assert music_major["name"] == "音乐表演"
    assert music_major["is_art_related"] == 1
    assert raw_plan_count == 2


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


def _write_art_plan_workbook(path: Path) -> None:
    rows = [
        ["山东省2025年艺术类本科批第2次志愿院校专业计划", None, None, None, None, None],
        ["本次公布的院校专业计划主要来源于：高校未完成的计划和新增计划。", None, None, None, None, None],
        ["院校代号", "院校、专业（类）名称及备注", "考试科目要求", "学制（年）", "计划数", "年收费（元）"],
        ["A209", "吉林艺术学院", None, None, 2, None],
        [None, "23 音乐表演(小号)（（音乐类（音乐表演）统考成绩）招收器乐且技能项为小号的考生）", "不限", 4, 1, 13200],
        [None, "34 音乐表演(流行电吉他)（（音乐类（音乐表演）统考成绩）招收器乐且技能项为电吉他的考生）（新增计划）", "不限", 4, 1, 13200],
    ]
    pd.DataFrame(rows).to_excel(path, index=False, header=False)
