from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    AcademicYear,
    ConfigItem,
    DictItem,
    DictType,
    Grade,
    SchoolClass,
    Semester,
    Student,
    Subject,
    Teacher,
    TeachingAssignment,
)


DICT_SEEDS = {
    "class_type": [
        ("normal", "普通班"),
        ("key", "重点班"),
        ("experiment", "实验班"),
        ("art", "艺体班"),
    ],
    "student_status": [
        ("active", "在读"),
        ("suspended", "休学"),
        ("graduated", "毕业"),
        ("transferred", "转出"),
    ],
    "student_type": [
        ("general", "普通生"),
        ("art", "艺体生"),
        ("repeat", "复读生"),
    ],
    "art_track": [
        ("art", "美术"),
        ("sports", "体育"),
        ("music", "音乐"),
        ("dance", "舞蹈"),
        ("media", "传媒"),
    ],
    "teacher_title": [
        ("level_1", "一级教师"),
        ("level_2", "二级教师"),
        ("senior", "高级教师"),
    ],
    "teacher_position": [
        ("subject_teacher", "学科教师"),
        ("grade_leader", "年级组长"),
        ("director", "教研组长"),
    ],
    "teacher_status": [
        ("active", "在岗"),
        ("leave", "请假"),
        ("retired", "离岗"),
    ],
    "course_type": [
        ("regular", "正课"),
        ("self_study", "自习"),
        ("morning_reading", "早读"),
        ("evening_study", "晚修"),
        ("experiment", "实验"),
        ("tutorial", "辅导"),
        ("club", "社团"),
    ],
}

CONFIG_SEEDS = [
    ("analytics", "ranking_mode", "competition", "string", "默认采用竞赛排名"),
    ("analytics", "subject_advantage_gap", "0.10", "float", "优势/薄弱学科判定阈值"),
    ("system", "auto_backup_before_restore", "true", "bool", "恢复前默认自动备份"),
    ("system", "student_profile_exam_limit", "6", "int", "学生详情默认展示最近考试数量"),
    ("system", "dashboard_issue_limit", "4", "int", "工作台默认展示的数据质量提醒数量"),
    ("recommendation", "safe_ratio_max", "0.85", "float", "保底区间上限"),
    ("recommendation", "steady_ratio_max", "1.00", "float", "稳妥区间上限"),
    ("recommendation", "rush_ratio_max", "1.15", "float", "冲刺区间上限"),
    ("recommendation", "whitelist_college_ids_json", "[]", "json", "推荐白名单院校"),
    ("recommendation", "blacklist_college_ids_json", "[]", "json", "推荐黑名单院校"),
    ("recommendation", "strategy_presets_json", "[]", "json", "推荐策略模板"),
]

SUBJECT_SEEDS = [
    ("chinese", "语文"),
    ("math", "数学"),
    ("english", "英语"),
    ("physics", "物理"),
    ("chemistry", "化学"),
    ("biology", "生物"),
    ("politics", "政治"),
    ("history", "历史"),
    ("geography", "地理"),
]


def _upsert_dict_type(session: Session, code: str, name: str) -> DictType:
    existing = session.scalar(select(DictType).where(DictType.code == code))
    if existing:
        existing.name = name
        return existing
    item = DictType(code=code, name=name)
    session.add(item)
    session.flush()
    return item


def seed_reference_data(session: Session) -> None:
    for dict_code, items in DICT_SEEDS.items():
        dict_type = _upsert_dict_type(session, dict_code, dict_code.replace("_", " ").title())
        existing_codes = {
            row.code: row
            for row in session.scalars(select(DictItem).where(DictItem.dict_type_id == dict_type.id)).all()
        }
        for index, (code, name) in enumerate(items, start=1):
            if code in existing_codes:
                existing_codes[code].name = name
                existing_codes[code].sort_order = index
                continue
            session.add(
                DictItem(
                    dict_type_id=dict_type.id,
                    code=code,
                    name=name,
                    sort_order=index,
                )
            )

    existing_subjects = {
        row.code: row for row in session.scalars(select(Subject)).all()
    }
    for index, (code, name) in enumerate(SUBJECT_SEEDS, start=1):
        if code in existing_subjects:
            existing_subjects[code].name = name
            existing_subjects[code].sort_order = index
            continue
        session.add(
            Subject(
                code=code,
                name=name,
                category="academic",
                sort_order=index,
                is_in_total_default=True,
            )
        )

    existing_grades = {row.name: row for row in session.scalars(select(Grade)).all()}
    for index, grade_name in enumerate(["高一", "高二", "高三"], start=1):
        if grade_name in existing_grades:
            existing_grades[grade_name].sort_order = index
            continue
        session.add(Grade(name=grade_name, sort_order=index))

    existing_config = {
        (row.config_group, row.config_key): row for row in session.scalars(select(ConfigItem)).all()
    }
    for config_group, config_key, config_value, value_type, description in CONFIG_SEEDS:
        key = (config_group, config_key)
        if key in existing_config:
            existing_config[key].config_value = config_value
            existing_config[key].value_type = value_type
            existing_config[key].description = description
            continue
        session.add(
            ConfigItem(
                config_group=config_group,
                config_key=config_key,
                config_value=config_value,
                value_type=value_type,
                description=description,
            )
        )

    session.flush()

    academic_year = session.scalar(
        select(AcademicYear).where(AcademicYear.name == "2025-2026")
    )
    if not academic_year:
        academic_year = AcademicYear(
            name="2025-2026",
            start_date=date(2025, 9, 1),
            end_date=date(2026, 8, 31),
            is_current=True,
        )
        session.add(academic_year)
        session.flush()

    semester_names = {
        row.name
        for row in session.scalars(
            select(Semester).where(Semester.academic_year_id == academic_year.id)
        ).all()
    }
    if "上学期" not in semester_names:
        session.add(
            Semester(
                academic_year_id=academic_year.id,
                name="上学期",
                start_date=date(2025, 9, 1),
                end_date=date(2026, 1, 20),
                week_count=20,
                is_current=False,
            )
        )
    if "下学期" not in semester_names:
        session.add(
            Semester(
                academic_year_id=academic_year.id,
                name="下学期",
                start_date=date(2026, 2, 15),
                end_date=date(2026, 7, 15),
                week_count=20,
                is_current=True,
            )
        )


def seed_demo_data(session: Session) -> None:
    seed_reference_data(session)
    session.flush()

    teachers = session.scalars(select(Teacher)).all()
    if teachers:
        return

    subject_map = {
        subject.name: subject
        for subject in session.scalars(select(Subject)).all()
    }
    grade_map = {grade.name: grade for grade in session.scalars(select(Grade)).all()}
    semester = session.scalar(select(Semester).where(Semester.is_current.is_(True)))

    teachers_to_create = [
        Teacher(
            teacher_no="T001",
            name="李语文",
            gender="女",
            subject_id=subject_map["语文"].id,
            phone="13900000001",
            title_code="level_1",
            position_code="subject_teacher",
            is_head_teacher=True,
            employment_status="active",
            entry_date=date(2021, 8, 1),
        ),
        Teacher(
            teacher_no="T002",
            name="王数学",
            gender="男",
            subject_id=subject_map["数学"].id,
            phone="13900000002",
            title_code="senior",
            position_code="grade_leader",
            is_head_teacher=False,
            employment_status="active",
            entry_date=date(2018, 8, 1),
        ),
    ]
    session.add_all(teachers_to_create)
    session.flush()

    class_one = SchoolClass(
        grade_id=grade_map["高一"].id,
        name="1班",
        class_type="key",
        head_teacher_id=teachers_to_create[0].id,
        student_count=2,
    )
    class_two = SchoolClass(
        grade_id=grade_map["高一"].id,
        name="2班",
        class_type="normal",
        head_teacher_id=None,
        student_count=1,
    )
    session.add_all([class_one, class_two])
    session.flush()

    students = [
        Student(
            student_no="2026001",
            name="张三",
            gender="男",
            admission_year=2024,
            current_grade_id=grade_map["高一"].id,
            current_class_id=class_one.id,
            status="active",
            student_type="general",
            phone="13800000001",
        ),
        Student(
            student_no="2026002",
            name="李四",
            gender="女",
            admission_year=2024,
            current_grade_id=grade_map["高一"].id,
            current_class_id=class_one.id,
            status="active",
            student_type="general",
            phone="13800000002",
        ),
        Student(
            student_no="2026003",
            name="王五",
            gender="男",
            admission_year=2024,
            current_grade_id=grade_map["高一"].id,
            current_class_id=class_two.id,
            status="active",
            student_type="art",
            art_track="art",
            phone="13800000003",
        ),
    ]
    session.add_all(students)
    session.flush()

    if semester:
        session.add_all(
            [
                TeachingAssignment(
                    teacher_id=teachers_to_create[0].id,
                    semester_id=semester.id,
                    grade_id=grade_map["高一"].id,
                    class_id=class_one.id,
                    subject_id=subject_map["语文"].id,
                    course_type="regular",
                    weekly_periods_manual=5,
                ),
                TeachingAssignment(
                    teacher_id=teachers_to_create[1].id,
                    semester_id=semester.id,
                    grade_id=grade_map["高一"].id,
                    class_id=class_one.id,
                    subject_id=subject_map["数学"].id,
                    course_type="regular",
                    weekly_periods_manual=6,
                ),
            ]
        )
