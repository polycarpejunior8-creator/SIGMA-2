"""
Évaluations et notes (cf §20-22, doc2 §10). Cycle de vie d'une note :
DRAFT -> SUBMITTED -> CHECKED -> VALIDATED -> LOCKED -> PUBLISHED
"""
import enum
import uuid

from sqlalchemy import String, ForeignKey, Numeric, Enum, UniqueConstraint, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import UUIDPKMixin, TimestampMixin


class GradeStatus(str, enum.Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    CHECKED = "checked"
    VALIDATED = "validated"
    LOCKED = "locked"
    PUBLISHED = "published"


class Assessment(Base, UUIDPKMixin, TimestampMixin):
    """Une évaluation ponctuelle (devoir, composition, examen...) pour une classe/matière/période."""
    __tablename__ = "assessments"

    class_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("classes.id", ondelete="CASCADE"))
    subject_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("subjects.id", ondelete="CASCADE"))
    academic_period_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("academic_periods.id", ondelete="CASCADE"))
    created_by_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    assessment_type: Mapped[str] = mapped_column(String(50), nullable=False)  # devoir/interro/composition/examen...
    max_score: Mapped[float] = mapped_column(Numeric(6, 2), default=20)
    coefficient: Mapped[float] = mapped_column(Numeric(5, 2), default=1)

    grades: Mapped[list["Grade"]] = relationship(back_populates="assessment", cascade="all, delete-orphan")


class Grade(Base, UUIDPKMixin, TimestampMixin):
    """Une note d'un élève à une évaluation, avec son propre cycle de validation."""
    __tablename__ = "grades"
    __table_args__ = (UniqueConstraint("assessment_id", "student_id", name="uq_grade_assessment_student"),)

    assessment_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("assessments.id", ondelete="CASCADE"))
    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"))

    score: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)  # null = absent / non noté
    is_absent: Mapped[bool] = mapped_column(default=False)

    status: Mapped[GradeStatus] = mapped_column(Enum(GradeStatus), default=GradeStatus.DRAFT)

    submitted_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    validated_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    validated_by_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)

    assessment: Mapped["Assessment"] = relationship(back_populates="grades")
    student: Mapped["object"] = relationship("Student")
