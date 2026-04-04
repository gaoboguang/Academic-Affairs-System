"""Initial schema

Revision ID: 20260403_0001
Revises:
Create Date: 2026-04-03 19:30:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260403_0001"
down_revision: str | None = None
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def _timestamp_columns() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("1"), nullable=False),
    ]


def upgrade() -> None:
    op.create_table(
        "academic_year",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=50), nullable=False, unique=True),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("is_current", sa.Boolean(), server_default=sa.text("0"), nullable=False),
        *_timestamp_columns(),
    )
    op.create_table(
        "grade",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=50), nullable=False, unique=True),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        *_timestamp_columns(),
    )
    op.create_table(
        "subject",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(length=50), nullable=False, unique=True),
        sa.Column("name", sa.String(length=50), nullable=False, unique=True),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("is_in_total_default", sa.Boolean(), server_default=sa.text("1"), nullable=False),
        *_timestamp_columns(),
    )
    op.create_table(
        "dict_type",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(length=50), nullable=False, unique=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        *_timestamp_columns(),
    )
    op.create_table(
        "config_item",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("config_group", sa.String(length=50), nullable=False),
        sa.Column("config_key", sa.String(length=100), nullable=False),
        sa.Column("config_value", sa.Text(), nullable=False),
        sa.Column("value_type", sa.String(length=30), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        *_timestamp_columns(),
        sa.UniqueConstraint("config_group", "config_key", name="uq_config_group_key"),
    )
    op.create_table(
        "import_job",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("job_type", sa.String(length=50), nullable=False),
        sa.Column("source_filename", sa.String(length=255), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("result_json", sa.JSON(), nullable=True),
        *_timestamp_columns(),
    )
    op.create_table(
        "audit_log",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("module", sa.String(length=50), nullable=False),
        sa.Column("action", sa.String(length=50), nullable=False),
        sa.Column("target_type", sa.String(length=50), nullable=True),
        sa.Column("target_id", sa.String(length=50), nullable=True),
        sa.Column("detail_json", sa.JSON(), nullable=True),
        *_timestamp_columns(),
    )
    op.create_table(
        "semester",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("academic_year_id", sa.Integer(), sa.ForeignKey("academic_year.id"), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("week_count", sa.Integer(), server_default="20", nullable=False),
        sa.Column("is_current", sa.Boolean(), server_default=sa.text("0"), nullable=False),
        *_timestamp_columns(),
        sa.UniqueConstraint("academic_year_id", "name", name="uq_semester_year_name"),
    )
    op.create_table(
        "teacher",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("teacher_no", sa.String(length=50), nullable=False, unique=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("gender", sa.String(length=20), nullable=True),
        sa.Column("subject_id", sa.Integer(), sa.ForeignKey("subject.id"), nullable=True),
        sa.Column("phone", sa.String(length=30), nullable=True),
        sa.Column("title_code", sa.String(length=50), nullable=True),
        sa.Column("position_code", sa.String(length=50), nullable=True),
        sa.Column("is_head_teacher", sa.Boolean(), server_default=sa.text("0"), nullable=False),
        sa.Column("employment_status", sa.String(length=50), nullable=True),
        sa.Column("entry_date", sa.Date(), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        *_timestamp_columns(),
    )
    op.create_table(
        "school_class",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("grade_id", sa.Integer(), sa.ForeignKey("grade.id"), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("class_type", sa.String(length=50), nullable=True),
        sa.Column("head_teacher_id", sa.Integer(), sa.ForeignKey("teacher.id"), nullable=True),
        sa.Column("student_count", sa.Integer(), server_default="0", nullable=False),
        *_timestamp_columns(),
        sa.UniqueConstraint("grade_id", "name", name="uq_class_grade_name"),
    )
    op.create_table(
        "dict_item",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("dict_type_id", sa.Integer(), sa.ForeignKey("dict_type.id"), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        *_timestamp_columns(),
        sa.UniqueConstraint("dict_type_id", "code", name="uq_dict_item_code"),
    )
    op.create_table(
        "student",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("student_no", sa.String(length=50), nullable=False, unique=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("gender", sa.String(length=20), nullable=True),
        sa.Column("birth_date", sa.Date(), nullable=True),
        sa.Column("id_number", sa.String(length=30), nullable=True),
        sa.Column("admission_year", sa.Integer(), nullable=True),
        sa.Column("current_grade_id", sa.Integer(), sa.ForeignKey("grade.id"), nullable=True),
        sa.Column("current_class_id", sa.Integer(), sa.ForeignKey("school_class.id"), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=True),
        sa.Column("student_type", sa.String(length=50), nullable=True),
        sa.Column("art_track", sa.String(length=50), nullable=True),
        sa.Column("phone", sa.String(length=30), nullable=True),
        sa.Column("address", sa.String(length=255), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        *_timestamp_columns(),
    )
    op.create_table(
        "student_guardian",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("student_id", sa.Integer(), sa.ForeignKey("student.id"), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("relation", sa.String(length=50), nullable=False),
        sa.Column("phone", sa.String(length=30), nullable=True),
        sa.Column("work_unit", sa.String(length=255), nullable=True),
        sa.Column("is_primary", sa.Boolean(), server_default=sa.text("0"), nullable=False),
        *_timestamp_columns(),
    )
    op.create_table(
        "student_class_history",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("student_id", sa.Integer(), sa.ForeignKey("student.id"), nullable=False),
        sa.Column("grade_id", sa.Integer(), sa.ForeignKey("grade.id"), nullable=True),
        sa.Column("class_id", sa.Integer(), sa.ForeignKey("school_class.id"), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("reason", sa.String(length=255), nullable=True),
        *_timestamp_columns(),
        sa.UniqueConstraint("student_id", "class_id", "start_date", name="uq_student_class_history"),
    )
    op.create_table(
        "teacher_title_history",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("teacher_id", sa.Integer(), sa.ForeignKey("teacher.id"), nullable=False),
        sa.Column("title_code", sa.String(length=50), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        *_timestamp_columns(),
    )
    op.create_table(
        "class_adviser_assignment",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("teacher_id", sa.Integer(), sa.ForeignKey("teacher.id"), nullable=False),
        sa.Column("class_id", sa.Integer(), sa.ForeignKey("school_class.id"), nullable=False),
        sa.Column("semester_id", sa.Integer(), sa.ForeignKey("semester.id"), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        *_timestamp_columns(),
    )
    op.create_table(
        "teaching_assignment",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("teacher_id", sa.Integer(), sa.ForeignKey("teacher.id"), nullable=False),
        sa.Column("semester_id", sa.Integer(), sa.ForeignKey("semester.id"), nullable=False),
        sa.Column("grade_id", sa.Integer(), sa.ForeignKey("grade.id"), nullable=True),
        sa.Column("class_id", sa.Integer(), sa.ForeignKey("school_class.id"), nullable=True),
        sa.Column("subject_id", sa.Integer(), sa.ForeignKey("subject.id"), nullable=True),
        sa.Column("course_type", sa.String(length=50), nullable=True),
        sa.Column("weekly_periods_manual", sa.Integer(), nullable=True),
        *_timestamp_columns(),
        sa.UniqueConstraint(
            "teacher_id",
            "semester_id",
            "class_id",
            "subject_id",
            "course_type",
            name="uq_teaching_assignment",
        ),
    )


def downgrade() -> None:
    op.drop_table("teaching_assignment")
    op.drop_table("class_adviser_assignment")
    op.drop_table("teacher_title_history")
    op.drop_table("student_class_history")
    op.drop_table("student_guardian")
    op.drop_table("student")
    op.drop_table("dict_item")
    op.drop_table("school_class")
    op.drop_table("teacher")
    op.drop_table("semester")
    op.drop_table("audit_log")
    op.drop_table("import_job")
    op.drop_table("config_item")
    op.drop_table("dict_type")
    op.drop_table("subject")
    op.drop_table("grade")
    op.drop_table("academic_year")

