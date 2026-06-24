from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import ActiveMixin, Base, PrimaryKeyMixin, TimestampMixin


class AppUser(PrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "app_user"

    username: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[str] = mapped_column(String(30), nullable=False)
    teacher_id: Mapped[int | None] = mapped_column(ForeignKey("teacher.id"), nullable=True)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    must_change_password: Mapped[bool] = mapped_column(default=True, server_default="1", nullable=False)
    failed_login_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), nullable=True)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), nullable=True)

    teacher = relationship("Teacher")
    sessions = relationship("AppSession", back_populates="user", cascade="all, delete-orphan")
    class_scopes = relationship("AppUserClassScope", back_populates="user", cascade="all, delete-orphan")


class AppSession(PrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "app_session"

    user_id: Mapped[int] = mapped_column(ForeignKey("app_user.id"), nullable=False, index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    csrf_token: Mapped[str] = mapped_column(String(96), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), nullable=False, index=True)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False), nullable=True)
    client_ip: Mapped[str | None] = mapped_column(String(80), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(255), nullable=True)

    user = relationship("AppUser", back_populates="sessions")


class AppUserClassScope(PrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "app_user_class_scope"
    __table_args__ = (UniqueConstraint("user_id", "class_id", name="uq_app_user_class_scope"),)

    user_id: Mapped[int] = mapped_column(ForeignKey("app_user.id"), nullable=False, index=True)
    class_id: Mapped[int] = mapped_column(ForeignKey("school_class.id"), nullable=False, index=True)

    user = relationship("AppUser", back_populates="class_scopes")
    school_class = relationship("SchoolClass")
