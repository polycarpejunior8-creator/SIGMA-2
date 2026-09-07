"""
Structure académique : Niveaux, Séries, Classes, Matières, Affectations enseignants
(cf cahier des charges §17, §18).
"""
import uuid

from sqlalchemy import String, ForeignKey, Integer, UniqueConstraint, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import UUIDPKMixin, TimestampMixin


class Level(Base, UUIDPKMixin, TimestampMixin):
    """Niveau scolaire (ex: 3e, Terminale)."""
    __tablename__ = "levels"
    __table_args__ = (UniqueConstraint("school_id", "name", name="uq_level_per_school"),)

    school_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("schools.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, default=0)

    streams: Mapped[list["Stream"]] = relationship(back_populates="level", cascade="all, delete-orphan")


class Stream(Base, UUIDPKMixin, TimestampMixin):
    """Série / filière (ex: Scientifique, Littéraire) — optionnelle selon le niveau."""
    __tablename__ = "streams"

    level_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("levels.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    level: Mapped["Level"] = relationship(back_populates="streams")


class ClassGroup(Base, UUIDPKMixin, TimestampMixin):
    """Une classe précise (ex: 3e A) pour une année scolaire donnée."""
    __tablename__ = "classes"

    academic_year_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("academic_years.id", ondelete="CASCADE"))
    level_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("levels.id", ondelete="CASCADE"))
    stream_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("streams.id", ondelete="SET NULL"), nullable=True)
    campus_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("campuses.id", ondelete="SET NULL"), nullable=True)

    name: Mapped[str] = mapped_column(String(100), nullable=False)  # ex: "3e A"
    homeroom_teacher_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)  # titulaire
    capacity: Mapped[int | None] = mapped_column(Integer, nullable=True)

    memberships: Mapped[list["ClassMembership"]] = relationship(back_populates="class_group", cascade="all, delete-orphan")


class Subject(Base, UUIDPKMixin, TimestampMixin):
    """Matière enseignée."""
    __tablename__ = "subjects"
    __table_args__ = (UniqueConstraint("school_id", "code", name="uq_subject_code_per_school"),)

    school_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("schools.id", ondelete="CASCADE"))
    code: Mapped[str] = mapped_column(String(30), nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    default_coefficient: Mapped[float] = mapped_column(Numeric(5, 2), default=1)


class TeacherAssignment(Base, UUIDPKMixin, TimestampMixin):
    """Affectation d'un enseignant à une matière pour une classe (cf §18)."""
    __tablename__ = "teacher_assignments"
    __table_args__ = (UniqueConstraint("teacher_id", "subject_id", "class_id", name="uq_teacher_subject_class"),)

    teacher_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    subject_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("subjects.id", ondelete="CASCADE"))
    class_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("classes.id", ondelete="CASCADE"))
    coefficient_override: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    weekly_hours: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)

    teacher: Mapped["object"] = relationship("User")
    subject: Mapped["Subject"] = relationship()
    class_group: Mapped["ClassGroup"] = relationship()
