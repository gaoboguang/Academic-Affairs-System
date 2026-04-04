from __future__ import annotations

from io import BytesIO

from openpyxl import Workbook

from app.importers.students import StudentImporter
from app.models import SchoolClass


def build_student_workbook() -> bytes:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "数据"
    sheet.append(["学号", "姓名", "性别", "出生日期", "入学年份", "年级", "班级", "学生状态", "学生类别", "艺体方向", "联系电话", "家庭住址", "备注"])
    sheet.append(["2026101", "导入学生", "男", "2009-04-01", "2024", "高一", "10班", "在读", "普通生", "", "13800001111", "测试地址", ""])
    sheet.append(["", "缺学号学生", "女", "", "2024", "高一", "10班", "在读", "普通生", "", "", "", ""])
    buffer = BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


def test_student_importer_creates_error_report(app, test_settings) -> None:
    with app.state.db.session_scope() as session:
        session.add(
            SchoolClass(
                grade_id=1,
                name="10班",
                class_type="normal",
                student_count=0,
            )
        )
        session.flush()

        importer = StudentImporter(session, test_settings)
        result = importer.execute(
            filename="students.xlsx",
            content=build_student_workbook(),
            strategy="skip_existing",
        )

    assert result.total_rows == 2
    assert result.success_rows == 1
    assert result.failed_rows == 1
    assert result.error_report_path is not None

