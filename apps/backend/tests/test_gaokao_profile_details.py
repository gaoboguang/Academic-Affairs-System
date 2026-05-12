from __future__ import annotations

from app.models import (
    AdmissionRecord,
    College,
    CollegeAlias,
    CollegeMajor,
    CollegeMajorProfile,
    CollegeProfileDetail,
    CollegeYearSummary,
    EnrollmentPlan,
    Major,
    MajorEmploymentMapping,
    MajorProfileDetail,
    EmploymentDirection,
)


def test_college_detail_and_history_return_profiles(client, app) -> None:
    with app.state.db.session_scope() as session:
        college = College(
            name="山东样例大学",
            college_code="10001",
            province="山东",
            city="济南市",
            school_type="综合类",
            school_level_tags_json=["双一流"],
            intro="基础简介",
            website="https://example.edu.cn",
            is_active=True,
        )
        major = Major(name="数据科学与大数据技术", major_code="080910T", category="工学", is_active=True)
        session.add_all([college, major])
        session.flush()
        session.add(
            CollegeProfileDetail(
                college_id=college.id,
                enrollment_code="A001",
                authority_department="山东省教育厅",
                education_level="本科",
                is_985=False,
                is_211=False,
                is_dual_class=True,
                ruanke_rank=120,
                eol_rank=88,
                area="1200亩",
                master_program_count=18,
                doctor_program_count=4,
                official_website="https://example.edu.cn",
                admission_website="https://zsb.example.edu.cn",
                phone="0531-12345678",
                email="zsb@example.edu.cn",
                address="济南市样例路1号",
                summary="画像简介",
                source_path="/fixtures/schools/1001.json",
                source_sha256="a" * 64,
            )
        )
        session.add(
            CollegeYearSummary(
                college_id=college.id,
                province="山东",
                year=2025,
                total_plan_count=42,
                specialty_count=3,
                min_rank=12000,
                estimated_min_score=612.0,
                source_note="按一分一段估算",
            )
        )
        session.add(
            AdmissionRecord(
                year=2025,
                province="山东",
                batch="常规批",
                college_id=college.id,
                major_id=major.id,
                student_type="general",
                art_track="",
                min_score=612,
                min_rank=12000,
                plan_count=42,
                source_note="测试录取",
                is_active=True,
            )
        )
        session.add(
            EnrollmentPlan(
                year=2025,
                province="山东",
                batch="常规批",
                exam_mode="3+3",
                college_id=college.id,
                major_id=major.id,
                college_code_snapshot="A001",
                major_group_code="01",
                major_name_snapshot="数据科学与大数据技术",
                major_code_snapshot="080910T",
                plan_count=42,
                subject_requirement="物理+化学",
                student_type="general",
                source_note="测试计划",
                is_active=True,
            )
        )
        session.add(CollegeMajor(college_id=college.id, major_id=major.id, enrollment_note="测试关系"))
        session.add(
            CollegeMajorProfile(
                college_id=college.id,
                major_id=major.id,
                school_major_feature="省级一流专业",
                is_national_feature=False,
                is_provincial_feature=True,
                is_key_major=True,
                schooling_years="4年",
                education_level="本科",
                source_path="/fixtures/major.json",
            )
        )
        session.flush()
        college_id = college.id

    detail_response = client.get(f"/api/colleges/{college_id}/detail")
    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert detail["college"]["name"] == "山东样例大学"
    assert detail["profile"]["enrollment_code"] == "A001"
    assert detail["profile"]["is_dual_class"] is True
    assert detail["year_summaries"][0]["estimated_min_score"] == 612.0
    assert detail["major_profiles"][0]["major_name"] == "数据科学与大数据技术"
    assert detail["major_profiles"][0]["is_provincial_feature"] is True
    assert detail["source_documents"][0]["source_path"] == "/fixtures/schools/1001.json"

    history_response = client.get(f"/api/colleges/{college_id}/admission-history")
    assert history_response.status_code == 200
    history = history_response.json()
    assert history["college_id"] == college_id
    assert history["admissions"][0]["min_rank"] == 12000
    assert history["plans"][0]["subject_requirement"] == "物理+化学"


def test_college_catalog_page_returns_read_only_summary_and_filters(client, app) -> None:
    with app.state.db.session_scope() as session:
        profiled = College(
            name="院校目录样例大学A",
            college_code="CATA",
            province="山东",
            city="济南市",
            school_type="综合类",
            school_level_tags_json=["双一流"],
            supports_art=False,
            is_active=True,
        )
        planned = College(
            name="院校目录样例学院B",
            college_code="CATB",
            province="广东",
            city="广州市",
            school_type="理工类",
            school_level_tags_json=["省属重点"],
            supports_art=True,
            is_active=True,
        )
        no_data = College(
            name="院校目录样例学院C",
            college_code="CATC",
            province="山东",
            city="青岛市",
            school_type="师范类",
            school_level_tags_json=[],
            supports_art=False,
            is_active=True,
        )
        dirty_major_named_college = College(name="院校目录样例工程管理", province="山东", is_active=True)
        special_plan_variant = College(name="院校目录样例大学A(高校专项计划)", province="山东", is_active=True)
        inactive = College(name="院校目录样例停用大学", province="山东", is_active=False)
        major = Major(name="院校目录样例专业", is_active=True)
        session.add_all([profiled, planned, no_data, dirty_major_named_college, special_plan_variant, inactive, major])
        session.flush()
        session.add(
            CollegeProfileDetail(
                college_id=profiled.id,
                enrollment_code="A100",
                authority_department="山东省教育厅",
                education_level="本科",
                is_985=False,
                is_211=False,
                is_dual_class=True,
                source_path="/fixtures/catalog-profile.json",
            )
        )
        session.add(
            EnrollmentPlan(
                year=2025,
                province="山东",
                batch="常规批",
                exam_mode="3+3",
                college_id=profiled.id,
                major_id=major.id,
                major_group_code="01",
                major_name_snapshot="院校目录样例专业",
                plan_count=30,
                student_type="general",
                is_active=True,
            )
        )
        session.add(
            AdmissionRecord(
                year=2024,
                province="山东",
                batch="常规批",
                college_id=profiled.id,
                major_id=major.id,
                student_type="general",
                min_score=610,
                min_rank=11000,
                is_active=True,
            )
        )
        session.add(
            EnrollmentPlan(
                year=2026,
                province="广东",
                batch="本科批",
                exam_mode="3+1+2",
                college_id=planned.id,
                major_id=major.id,
                major_group_code="02",
                major_name_snapshot="院校目录样例专业",
                plan_count=12,
                student_type="art",
                is_active=True,
            )
        )
        session.add(
            AdmissionRecord(
                year=2025,
                province="山东",
                batch="常规批",
                college_id=dirty_major_named_college.id,
                major_id=major.id,
                student_type="general",
                min_score=500,
                min_rank=50000,
                is_active=True,
            )
        )
        session.add(
            AdmissionRecord(
                year=2025,
                province="山东",
                batch="常规批",
                college_id=special_plan_variant.id,
                major_id=major.id,
                student_type="general",
                min_score=620,
                min_rank=8000,
                is_active=True,
            )
        )

    response = client.get("/api/colleges/catalog/page?keyword=院校目录样例&page=1&page_size=2")
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 3
    assert payload["page"] == 1
    assert payload["page_size"] == 2
    assert len(payload["items"]) == 2
    first = payload["items"][0]
    assert first["name"] == "院校目录样例大学A"
    assert first["has_profile"] is True
    assert first["plan_count"] == 1
    assert first["admission_count"] == 1
    assert first["latest_plan_year"] == 2025
    assert first["latest_admission_year"] == 2024

    with_profile = client.get("/api/colleges/catalog/page?keyword=院校目录样例&has_profile=true")
    assert with_profile.status_code == 200
    assert with_profile.json()["total"] == 1
    assert with_profile.json()["items"][0]["name"] == "院校目录样例大学A"

    with_admission_data = client.get("/api/colleges/catalog/page?keyword=院校目录样例&has_admission_data=true")
    assert with_admission_data.status_code == 200
    assert with_admission_data.json()["total"] == 2
    assert {item["name"] for item in with_admission_data.json()["items"]} == {
        "院校目录样例大学A",
        "院校目录样例学院B",
    }

    variants = client.get("/api/colleges/catalog/page?keyword=高校专项计划")
    assert variants.status_code == 200
    assert variants.json()["items"] == []
    assert variants.json()["total"] == 0

    by_level = client.get("/api/colleges/catalog/page?keyword=院校目录样例&level_tag=双一流")
    assert by_level.status_code == 200
    assert by_level.json()["total"] == 1

    no_match = client.get("/api/colleges/catalog/page?keyword=院校目录样例&school_type=农林类")
    assert no_match.status_code == 200
    assert no_match.json()["items"] == []
    assert no_match.json()["total"] == 0


def test_college_catalog_page_searches_alias_and_excludes_inactive_duplicate(client, app) -> None:
    with app.state.db.session_scope() as session:
        canonical = College(
            name="目录别名样例大学",
            college_code="ALIAS100",
            province="江西",
            city="抚州市",
            school_type="理工类",
            is_active=True,
        )
        dirty_duplicate = College(
            name="目录别名 样例大学",
            province="山东",
            city="南昌市",
            school_type="理工类",
            is_active=False,
        )
        session.add_all([canonical, dirty_duplicate])
        session.flush()
        session.add(CollegeAlias(college_id=canonical.id, alias_name="目录别名 样例大学", is_active=True))

    response = client.get("/api/colleges/catalog/page?keyword=目录别名%20样例大学")

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["items"][0]["name"] == "目录别名样例大学"
    assert payload["items"][0]["province"] == "江西"
    assert payload["items"][0]["city"] == "抚州市"


def test_major_detail_and_history_return_profiles(client, app) -> None:
    with app.state.db.session_scope() as session:
        college = College(name="专业样例大学", province="山东", is_active=True)
        major = Major(
            name="智能科学与技术",
            major_code="080907T",
            category="工学",
            direction="人工智能方向",
            career_path="算法工程",
            is_active=True,
        )
        direction = EmploymentDirection(name="人工智能工程", category="技术研发类", is_active=True)
        session.add_all([college, major, direction])
        session.flush()
        session.add(
            MajorProfileDetail(
                major_id=major.id,
                major_code="080907T",
                education_level="本科",
                schooling_years="4年",
                direction="人工智能方向",
                tags_json=["新工科", "交叉学科"],
                summary="专业画像简介",
                source_path="/fixtures/majors/080907T.json",
                source_sha256="b" * 64,
            )
        )
        session.add(
            CollegeMajorProfile(
                college_id=college.id,
                major_id=major.id,
                school_major_feature="国家特色专业",
                is_national_feature=True,
                is_provincial_feature=False,
                is_key_major=True,
                schooling_years="4年",
                education_level="本科",
                source_path="/fixtures/college-major.json",
            )
        )
        session.add(
            MajorEmploymentMapping(
                major_id=major.id,
                direction_id=direction.id,
                strength="high",
                recommendation_note="适合算法研发",
                is_active=True,
            )
        )
        session.add(
            AdmissionRecord(
                year=2025,
                province="山东",
                batch="常规批",
                college_id=college.id,
                major_id=major.id,
                student_type="general",
                art_track="",
                min_score=608,
                min_rank=15000,
                plan_count=20,
                source_note="测试录取",
                is_active=True,
            )
        )
        session.add(
            EnrollmentPlan(
                year=2025,
                province="山东",
                batch="常规批",
                exam_mode="3+3",
                college_id=college.id,
                major_id=major.id,
                major_group_code="02",
                major_name_snapshot="智能科学与技术",
                major_code_snapshot="080907T",
                plan_count=20,
                subject_requirement="物理+化学",
                student_type="general",
                is_active=True,
            )
        )
        session.flush()
        major_id = major.id

    detail_response = client.get(f"/api/majors/{major_id}/detail")
    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert detail["major"]["name"] == "智能科学与技术"
    assert detail["profile"]["tags_json"] == ["新工科", "交叉学科"]
    assert detail["college_profiles"][0]["college_name"] == "专业样例大学"
    assert detail["college_profiles"][0]["is_national_feature"] is True
    assert detail["employment_mappings"][0]["direction_name"] == "人工智能工程"
    assert detail["subject_requirement_samples"][0] == "物理+化学"

    history_response = client.get(f"/api/majors/{major_id}/admission-history")
    assert history_response.status_code == 200
    history = history_response.json()
    assert history["major_id"] == major_id
    assert history["admissions"][0]["college_name"] == "专业样例大学"
    assert history["plans"][0]["plan_count"] == 20
