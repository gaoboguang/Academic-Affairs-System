from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260601_0033"
down_revision = "20260510_0032"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "app_user",
        sa.Column("username", sa.String(length=80), nullable=False),
        sa.Column("display_name", sa.String(length=100), nullable=False),
        sa.Column("role", sa.String(length=30), nullable=False),
        sa.Column("teacher_id", sa.Integer(), nullable=True),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("must_change_password", sa.Boolean(), server_default="1", nullable=False),
        sa.Column("failed_login_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("locked_until", sa.DateTime(timezone=False), nullable=True),
        sa.Column("last_login_at", sa.DateTime(timezone=False), nullable=True),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=False), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=False), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="1", nullable=False),
        sa.ForeignKeyConstraint(["teacher_id"], ["teacher.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("username"),
    )
    op.create_index(op.f("ix_app_user_username"), "app_user", ["username"], unique=False)

    op.create_table(
        "app_session",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("csrf_token", sa.String(length=96), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=False), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=False), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=False), nullable=True),
        sa.Column("client_ip", sa.String(length=80), nullable=True),
        sa.Column("user_agent", sa.String(length=255), nullable=True),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=False), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=False), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["app_user.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash"),
    )
    op.create_index(op.f("ix_app_session_expires_at"), "app_session", ["expires_at"], unique=False)
    op.create_index(op.f("ix_app_session_token_hash"), "app_session", ["token_hash"], unique=False)
    op.create_index(op.f("ix_app_session_user_id"), "app_session", ["user_id"], unique=False)

    op.create_table(
        "app_user_class_scope",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("class_id", sa.Integer(), nullable=False),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=False), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=False), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="1", nullable=False),
        sa.ForeignKeyConstraint(["class_id"], ["school_class.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["app_user.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "class_id", name="uq_app_user_class_scope"),
    )
    op.create_index(op.f("ix_app_user_class_scope_class_id"), "app_user_class_scope", ["class_id"], unique=False)
    op.create_index(op.f("ix_app_user_class_scope_user_id"), "app_user_class_scope", ["user_id"], unique=False)

    with op.batch_alter_table("audit_log") as batch_op:
        batch_op.add_column(sa.Column("actor_user_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("actor_username", sa.String(length=80), nullable=True))
        batch_op.add_column(sa.Column("client_ip", sa.String(length=80), nullable=True))
        batch_op.create_foreign_key("fk_audit_log_actor_user", "app_user", ["actor_user_id"], ["id"])


def downgrade() -> None:
    with op.batch_alter_table("audit_log") as batch_op:
        batch_op.drop_constraint("fk_audit_log_actor_user", type_="foreignkey")
        batch_op.drop_column("client_ip")
        batch_op.drop_column("actor_username")
        batch_op.drop_column("actor_user_id")

    op.drop_index(op.f("ix_app_user_class_scope_user_id"), table_name="app_user_class_scope")
    op.drop_index(op.f("ix_app_user_class_scope_class_id"), table_name="app_user_class_scope")
    op.drop_table("app_user_class_scope")
    op.drop_index(op.f("ix_app_session_user_id"), table_name="app_session")
    op.drop_index(op.f("ix_app_session_token_hash"), table_name="app_session")
    op.drop_index(op.f("ix_app_session_expires_at"), table_name="app_session")
    op.drop_table("app_session")
    op.drop_index(op.f("ix_app_user_username"), table_name="app_user")
    op.drop_table("app_user")
