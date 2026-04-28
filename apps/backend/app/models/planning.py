from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Date, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import ActiveMixin, Base, PrimaryKeyMixin, TimestampMixin


class StudentPlanningGoal(PrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "student_planning_goal"
    __table_args__ = (
        UniqueConstraint(
            "student_id",
            "target_year",
            "pathway_code",
            "is_active",
            name="uq_student_planning_goal_active_pathway",
        ),
    )

    student_id: Mapped[int] = mapped_column(ForeignKey("student.id"), nullable=False)
    target_year: Mapped[int] = mapped_column(Integer, nullable=False)
    pathway_code: Mapped[str] = mapped_column(String(80), nullable=False)
    pathway_name: Mapped[str] = mapped_column(String(120), nullable=False)
    target_college: Mapped[str | None] = mapped_column(String(150), nullable=True)
    target_major: Mapped[str | None] = mapped_column(String(150), nullable=True)
    target_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    target_rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    backup_pathways: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="in_progress", nullable=False)
    priority: Mapped[str] = mapped_column(String(20), default="medium", nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    student = relationship("Student")
    tasks = relationship("StudentPlanningTask", back_populates="goal")
    notes = relationship("StudentPlanningNote", back_populates="goal")


class StudentPlanningTask(PrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "student_planning_task"
    __table_args__ = (
        UniqueConstraint(
            "student_id",
            "source_type",
            "source_ref_id",
            "task_type",
            "title",
            "is_active",
            name="uq_student_planning_task_source",
        ),
    )

    student_id: Mapped[int] = mapped_column(ForeignKey("student.id"), nullable=False)
    goal_id: Mapped[int | None] = mapped_column(ForeignKey("student_planning_goal.id"), nullable=True)
    source_type: Mapped[str] = mapped_column(String(50), default="manual", nullable=False)
    source_ref_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    task_type: Mapped[str] = mapped_column(String(50), default="other", nullable=False)
    title: Mapped[str] = mapped_column(String(180), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="not_started", nullable=False)
    priority: Mapped[str] = mapped_column(String(20), default="medium", nullable=False)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(nullable=True)
    related_route: Mapped[str | None] = mapped_column(String(255), nullable=True)

    student = relationship("Student")
    goal = relationship("StudentPlanningGoal", back_populates="tasks")
    notes = relationship("StudentPlanningNote", back_populates="task")


class StudentPlanningNote(PrimaryKeyMixin, TimestampMixin, ActiveMixin, Base):
    __tablename__ = "student_planning_note"

    student_id: Mapped[int] = mapped_column(ForeignKey("student.id"), nullable=False)
    goal_id: Mapped[int | None] = mapped_column(ForeignKey("student_planning_goal.id"), nullable=True)
    task_id: Mapped[int | None] = mapped_column(ForeignKey("student_planning_task.id"), nullable=True)
    note_type: Mapped[str] = mapped_column(String(50), default="review", nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    student = relationship("Student")
    goal = relationship("StudentPlanningGoal", back_populates="notes")
    task = relationship("StudentPlanningTask", back_populates="notes")
