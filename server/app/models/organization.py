"""
Modèles de la structure institutionnelle : Organisation > École > Campus > Année scolaire.
Cf. cahier des charges §7 (gestion des établissements) et §9 (années scolaires).
"""
import uuid
from datetime import date

from sqlalchemy import String, Boolean, ForeignKey, Date, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import UUIDPKMixin, TimestampMixin


class Organization(Base, UUIDPKMixin, TimestampMixin):
    """
    Niveau le plus haut : une organisation peut être un groupe scolaire
    (plusieurs écoles) ou une école unique (mode simple, cf §7).
    """
    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    schools: Mapped[list["School"]] = relationship(back_populates="organization", cascade="all, delete-orphan")


class School(Base, UUIDPKMixin, TimestampMixin):
    """Un établissement scolaire au sens strict (cf §8 configuration initiale)."""
    __tablename__ = "schools"

    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"))

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    logo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    website: Mapped[str | None] = mapped_column(String(255), nullable=True)

    school_type: Mapped[str | None] = mapped_column(String(100), nullable=True)   # général, technique, professionnel...
    regime: Mapped[str | None] = mapped_column(String(100), nullable=True)        # externat, internat, semi-internat...
    language: Mapped[str] = mapped_column(String(10), default="fr")               # fr / en
    currency: Mapped[str] = mapped_column(String(10), default="XAF")
    grading_system: Mapped[str] = mapped_column(String(50), default="20")         # /20, /100, lettres...

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    organization: Mapped["Organization"] = relationship(back_populates="schools")
    campuses: Mapped[list["Campus"]] = relationship(back_populates="school", cascade="all, delete-orphan")
    academic_years: Mapped[list["AcademicYear"]] = relationship(back_populates="school", cascade="all, delete-orphan")


class Campus(Base, UUIDPKMixin, TimestampMixin):
    """Un site physique d'un établissement (mode multisite, cf §7)."""
    __tablename__ = "campuses"

    school_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("schools.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    school: Mapped["School"] = relationship(back_populates="campuses")


class AcademicYear(Base, UUIDPKMixin, TimestampMixin):
    """
    Année scolaire (cf §9). Plusieurs années peuvent coexister ;
    une année clôturée devient archivée et protégée en écriture.
    """
    __tablename__ = "academic_years"

    school_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("schools.id", ondelete="CASCADE"))
    label: Mapped[str] = mapped_column(String(20), nullable=False)   # ex: "2026/2027"
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)

    is_current: Mapped[bool] = mapped_column(Boolean, default=False)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False)  # verrouillée en écriture si True

    school: Mapped["School"] = relationship(back_populates="academic_years")
    periods: Mapped[list["AcademicPeriod"]] = relationship(back_populates="academic_year", cascade="all, delete-orphan")


class AcademicPeriod(Base, UUIDPKMixin, TimestampMixin):
    """Trimestre / semestre au sein d'une année scolaire (utilisé par le moteur de notes, §20-22)."""
    __tablename__ = "academic_periods"

    academic_year_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("academic_years.id", ondelete="CASCADE"))
    label: Mapped[str] = mapped_column(String(50), nullable=False)  # ex: "Trimestre 1"
    order_index: Mapped[int] = mapped_column(default=1)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    is_open_for_grading: Mapped[bool] = mapped_column(Boolean, default=True)  # verrou global de saisie (§21)

    academic_year: Mapped["AcademicYear"] = relationship(back_populates="periods")
