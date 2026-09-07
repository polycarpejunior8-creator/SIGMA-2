"""
Module Vie scolaire — Discipline (cf §27) : observations, avertissements, retenues,
sanctions, exclusions, récompenses. Historique chronologique par élève.
"""
import enum
import uuid
from datetime import date

from sqlalchemy import String, ForeignKey, Enum, Text, Date, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import UUIDPKMixin, TimestampMixin


class DisciplinaryType(str, enum.Enum):
    OBSERVATION = "observation"
    WARNING = "warning"                 # avertissement
    DETENTION = "detention"             # retenue
    SANCTION = "sanction"               # sanction (mesure disciplinaire formelle)
    EXCLUSION = "exclusion"
    REWARD = "reward"                   # récompense / félicitation


class DisciplinarySeverity(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"        # utilisé par le moteur des tableaux d'honneur pour exclure un élève


class DisciplinaryRecord(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "disciplinary_records"

    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"))
    recorded_by_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))

    record_type: Mapped[DisciplinaryType] = mapped_column(Enum(DisciplinaryType), nullable=False)
    severity: Mapped[DisciplinarySeverity] = mapped_column(Enum(DisciplinarySeverity), default=DisciplinarySeverity.LOW)
    record_date: Mapped[date] = mapped_column(Date, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    points: Mapped[float] = mapped_column(Numeric(5, 2), default=0)  # positif = récompense, négatif = sanction

    student: Mapped["object"] = relationship("Student")
