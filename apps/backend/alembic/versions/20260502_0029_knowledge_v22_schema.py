"""Add knowledge tree aliases and error tags

Revision ID: 20260502_0029
Revises: 20260502_0028
Create Date: 2026-05-02 23:40:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect


revision: str = "20260502_0029"
down_revision: str | None = "20260502_0028"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


DEFAULT_ERROR_TAGS = [
    "概念不清",
    "审题失误",
    "计算错误",
    "方法不会",
    "步骤不全",
    "表达不规范",
    "时间分配",
    "知识遗忘",
    "粗心漏答",
    "其他",
]


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    tables = set(inspector.get_table_names())
    if "knowledge_point" not in tables:
        return
    knowledge_columns = {item["name"] for item in inspector.get_columns("knowledge_point")}
    score_link_columns = (
        {item["name"] for item in inspector.get_columns("score_question_knowledge_point")}
        if "score_question_knowledge_point" in tables
        else set()
    )
    score_record_columns = (
        {item["name"] for item in inspector.get_columns("score_question_record")}
        if "score_question_record" in tables
        else set()
    )
    snapshot_columns = (
        {item["name"] for item in inspector.get_columns("score_knowledge_snapshot")}
        if "score_knowledge_snapshot" in tables
        else set()
    )

    if {"parent_id", "sort_order", "source_type"} - knowledge_columns:
        with op.batch_alter_table("knowledge_point") as batch_op:
            if "parent_id" not in knowledge_columns:
                batch_op.add_column(sa.Column("parent_id", sa.Integer(), nullable=True))
                batch_op.create_foreign_key(
                    "fk_knowledge_point_parent_id",
                    "knowledge_point",
                    ["parent_id"],
                    ["id"],
                )
                batch_op.create_index("ix_knowledge_point_parent_id", ["parent_id"])
            if "sort_order" not in knowledge_columns:
                batch_op.add_column(sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"))
            if "source_type" not in knowledge_columns:
                batch_op.add_column(sa.Column("source_type", sa.String(length=30), nullable=False, server_default="manual"))

    if "knowledge_point_alias" not in tables:
        op.create_table(
            "knowledge_point_alias",
            sa.Column("subject_id", sa.Integer(), nullable=False),
            sa.Column("knowledge_point_id", sa.Integer(), nullable=False),
            sa.Column("alias_name", sa.String(length=120), nullable=False),
            sa.Column("normalized_alias", sa.String(length=120), nullable=False),
            sa.Column("source_type", sa.String(length=30), nullable=False, server_default="manual"),
            sa.Column("note", sa.Text(), nullable=True),
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=False), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=False), server_default=sa.func.now(), nullable=False),
            sa.Column("is_active", sa.Boolean(), server_default="1", nullable=False),
            sa.ForeignKeyConstraint(["knowledge_point_id"], ["knowledge_point.id"]),
            sa.ForeignKeyConstraint(["subject_id"], ["subject.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("subject_id", "alias_name", name="uq_knowledge_point_alias_subject_name"),
        )
        op.create_index("ix_knowledge_point_alias_subject", "knowledge_point_alias", ["subject_id"])
        op.create_index("ix_knowledge_point_alias_point", "knowledge_point_alias", ["knowledge_point_id"])
        op.create_index(
            "ix_knowledge_point_alias_normalized",
            "knowledge_point_alias",
            ["subject_id", "normalized_alias"],
        )

    created_error_tag_table = "error_reason_tag" not in tables
    if created_error_tag_table:
        op.create_table(
            "error_reason_tag",
            sa.Column("name", sa.String(length=80), nullable=False),
            sa.Column("normalized_name", sa.String(length=80), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("is_builtin", sa.Boolean(), nullable=False, server_default="0"),
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=False), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=False), server_default=sa.func.now(), nullable=False),
            sa.Column("is_active", sa.Boolean(), server_default="1", nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("name", name="uq_error_reason_tag_name"),
        )
        op.create_index("ix_error_reason_tag_normalized", "error_reason_tag", ["normalized_name"])

    if "match_source" not in score_link_columns:
        op.add_column(
            "score_question_knowledge_point",
            sa.Column("match_source", sa.String(length=30), nullable=False, server_default="standard"),
        )
        op.add_column(
            "score_question_knowledge_point",
            sa.Column("raw_knowledge_text", sa.String(length=255), nullable=True),
        )

    if "error_tags_json" not in score_record_columns:
        op.add_column("score_question_record", sa.Column("error_tags_json", sa.JSON(), nullable=False, server_default="[]"))
        op.add_column("score_question_record", sa.Column("error_note", sa.Text(), nullable=True))
    if "error_tags_json" not in snapshot_columns:
        op.add_column("score_knowledge_snapshot", sa.Column("error_tags_json", sa.JSON(), nullable=False, server_default="[]"))
        op.add_column("score_knowledge_snapshot", sa.Column("dominant_error_tag", sa.String(length=80), nullable=True))

    if created_error_tag_table:
        for index, name in enumerate(DEFAULT_ERROR_TAGS):
            normalized = "".join(str(name).strip().lower().split())
            bind.execute(
                sa.text(
                    "INSERT INTO error_reason_tag "
                    "(name, normalized_name, sort_order, is_builtin, created_at, updated_at, is_active) "
                    "VALUES (:name, :normalized_name, :sort_order, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 1)"
                ),
                {"name": name, "normalized_name": normalized, "sort_order": index},
            )


def downgrade() -> None:
    op.drop_column("score_knowledge_snapshot", "dominant_error_tag")
    op.drop_column("score_knowledge_snapshot", "error_tags_json")
    op.drop_column("score_question_record", "error_note")
    op.drop_column("score_question_record", "error_tags_json")
    op.drop_column("score_question_knowledge_point", "raw_knowledge_text")
    op.drop_column("score_question_knowledge_point", "match_source")
    op.drop_index("ix_error_reason_tag_normalized", table_name="error_reason_tag")
    op.drop_table("error_reason_tag")
    op.drop_index("ix_knowledge_point_alias_normalized", table_name="knowledge_point_alias")
    op.drop_index("ix_knowledge_point_alias_point", table_name="knowledge_point_alias")
    op.drop_index("ix_knowledge_point_alias_subject", table_name="knowledge_point_alias")
    op.drop_table("knowledge_point_alias")
    with op.batch_alter_table("knowledge_point") as batch_op:
        batch_op.drop_index("ix_knowledge_point_parent_id")
        batch_op.drop_constraint("fk_knowledge_point_parent_id", type_="foreignkey")
        batch_op.drop_column("source_type")
        batch_op.drop_column("sort_order")
        batch_op.drop_column("parent_id")
