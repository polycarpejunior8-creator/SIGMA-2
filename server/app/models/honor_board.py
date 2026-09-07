"""
Tableaux d'honneur (cf §24) : moteur configurable — l'établissement définit ses propres
règles (seuils ou pondérations), sans intervention du développeur.

Deux styles de règles possibles, illustrés au §24 :
  1. Seuils      : moyenne >= X, absences injustifiées <= Y, aucune sanction grave.
  2. Pondération : score = 70% moyenne + 15% discipline + 10% assiduité + 5% progression.

Une HonorBoardRule peut combiner les deux : les seuils servent de filtre d'éligibilité,
la pondération sert ensuite à classer les élèves éligibles.
"""
import enum
import uuid
from datetime import datetime

from sqlalchemy import String, ForeignKey, Numeric, Boolean, Enum, Integer, DateTime, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import UUIDPKMixin, TimestampMixin


class HonorBoardScopeType(str, enum.Enum):
    CLASS = "class"
    LEVEL = "level"
    SCHOOL = "school"


class HonorBoardRule(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "honor_board_rules"

    school_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("schools.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(150), nullable=False)  # ex: "Tableau d'excellence"

    # --- Filtre d'éligibilité (seuils, tous optionnels) ---
    min_average: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    max_unjustified_absences: Mapped[int | None] = mapped_column(Integer, nullable=True)
    disallow_high_severity_sanction: Mapped[bool] = mapped_column(Boolean, default=True)

    # --- Pondération du score de classement (doit sommer à 100, vérifié côté API) ---
    weight_average: Mapped[float] = mapped_column(Numeric(5, 2), default=100)
    weight_discipline: Mapped[float] = mapped_column(Numeric(5, 2), default=0)
    weight_attendance: Mapped[float] = mapped_column(Numeric(5, 2), default=0)
    weight_progression: Mapped[float] = mapped_column(Numeric(5, 2), default=0)

    max_winners: Mapped[int | None] = mapped_column(Integer, nullable=True)  # ex: top 10 ; nul = tous les éligibles


class HonorBoard(Base, UUIDPKMixin, TimestampMixin):
    """Une génération concrète d'un tableau d'honneur pour une période/périmètre donnés."""
    __tablename__ = "honor_boards"

    rule_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("honor_board_rules.id", ondelete="CASCADE"))
    academic_period_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("academic_periods.id", ondelete="CASCADE"))
    scope_type: Mapped[HonorBoardScopeType] = mapped_column(Enum(HonorBoardScopeType), nullable=False)
    class_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("classes.id", ondelete="CASCADE"), nullable=True)
    level_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("levels.id", ondelete="CASCADE"), nullable=True)

    generated_by_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False)

    rule: Mapped["HonorBoardRule"] = relationship()
    entries: Mapped[list["HonorBoardEntry"]] = relationship(back_populates="honor_board", cascade="all, delete-orphan")


class HonorBoardEntry(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "honor_board_entries"
    __table_args__ = (UniqueConstraint("honor_board_id", "student_id", name="uq_honor_board_student"),)

    honor_board_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("honor_boards.id", ondelete="CASCADE"))
    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"))

    average: Mapped[float] = mapped_column(Numeric(5, 2), default=0)
    unjustified_absences: Mapped[int] = mapped_column(Integer, default=0)
    discipline_points: Mapped[float] = mapped_column(Numeric(6, 2), default=0)
    score: Mapped[float] = mapped_column(Numeric(6, 2), default=0)
    rank: Mapped[int] = mapped_column(Integer, default=0)

    honor_board: Mapped["HonorBoard"] = relationship(back_populates="entries")
    student: Mapped["object"] = relationship("Student")
