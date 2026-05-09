from __future__ import annotations

from app.models import (
    AdmissionRecord,
    College,
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
